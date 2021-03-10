from collections import defaultdict
import hashlib
import os
import sys


def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
    hashobj = hash()
    file_object = open(filename, 'rb')

    if first_chunk_only:
        hashobj.update(file_object.read(1024))
    else:
        for chunk in chunk_reader(file_object):
            hashobj.update(chunk)
    hashed = hashobj.digest()

    file_object.close()
    return hashed

def get_files_by_size(paths):
    """Build a dictionary containing lists of files with the same size. 
    Those lists of files contains potential duplicates that will be analysee further

    Args: 
        :paths (list): List of folder to walk to build the output
    
    Return: dictionary { file size : [list of files of that size],...}
    """
    hashes_by_size = defaultdict(list)  # dict of size_in_bytes: [full_path_to_file1, full_path_to_file2, ]
    for path in paths:
        for dirpath, __, filenames in os.walk(path):
            # get all files that have the same size - they are the collision candidates
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                try:
                    # if the target is a symlink (soft one), this will 
                    # dereference it - change the value to the actual target file
                    full_path = os.path.realpath(full_path)
                    file_size = os.path.getsize(full_path)
                    hashes_by_size[file_size].append(full_path)
                except (OSError,):
                    # not accessible (permissions, etc) - pass on
                    continue
    print('List by size, done')
    return hashes_by_size

def get_files_by_1k(hashes_by_size, hash=hashlib.sha1):
    """Build a dictionary containing lists of files with the same size 
    and hash on their first 1024 bits. Those lists of files contains 
    potential duplicates that will be analysee further

    Args: 
        :hashes_by_size (dict): dictionary { file size : [list of files of that size],...}
    
    Return: dictionary { (hash on 1024 bits, file size) : [list of files matching the key hash and size],...}
    """
    hashes_on_1k = defaultdict(list)  # dict of (hash1k, size_in_bytes): [full_path_to_file1, full_path_to_file2, ]
    # For all files with the same file size, get their hash on the 1st 1024 bytes only
    for size_in_bytes, files in hashes_by_size.items():
        if len(files) < 2:
            continue    # this file size is unique, no need to spend CPU cycles on it

        for filename in files:
            try:
                small_hash = get_hash(filename, first_chunk_only=True)
                # the key is the hash on the first 1024 bytes plus the size - to
                # avoid collisions on equal hashes in the first part of the file
                # credits to @Futal for the optimization
                hashes_on_1k[(small_hash, size_in_bytes)].append(filename)
            except (OSError,):
                # the file access might've changed till the exec point got here 
                continue
    print('List hash 1k, done')
    return hashes_on_1k

def get_files_by_full(hashes_on_1k, hash=hashlib.sha1):
    # For all files with the same file size, and hash on the 1st 1024 bytes
    hashes_full = defaultdict(list)   # dict of full_file_hash: full_path_to_file_string
    for k, files_list in hashes_on_1k.items():
        if len(files_list) < 2:
            continue    # this hash of fist 1k file bytes is unique, no need to spend cpy cycles on it

        for filename in files_list:
            try:
                full_hash = get_hash(filename, first_chunk_only=False)
                hashes_full[(full_hash, k[1])].append(filename)
            except (OSError,):
                # the file access might've changed till the exec point got here 
                continue
    print('List full hash, done')
    return hashes_full

def is_in_dir(file_name=None, folder=None):
    """Check if the file_name is in the folder or any of its subfolder
    Both are expected to be absolute path

    Args:
        :file_name (str): Mandatory, file to check
        :folder (str): Mandatory, folder to check
        
    Return: True if file_name is under folder, False otherwise"""
    # verify that both args are provided and are string
    if not ( isinstance(file_name, str) and isinstance(folder, str) ):
        raise KeyError('is_in_dir require 2 strings')
    return file_name.find(folder, 0) == 0

def delete_files(delete_list):
    """Remove every files in the list provided, handle exceptions

    Args:
        :delete_list (list): list of file to remove
    
    Return: (int) number of files removed
    """
    nb_deleted = 0 # count nbr of deleted files
    for fn in delete_list:
        try:
            os.remove(fn)
            nb_deleted += 1 
        except (OSError):
            # file access issue, lock...
            print(f'Error removing: {fn}')
            continue # continue the loop
    return nb_deleted

def print_df(nb_duplicates, nb_deleted, nb_kept, keep_list):
    """Print out synthesis for delete_duplicates routine

    Args:
        :nb_duplicates (int): nb of duplicated files
        :nb_deleted (int): nb of deleted files
        :nb_kept (int): nb of duplicated files that are kept
        :keep_list (list): List of files that are kept
    """
    print(f'\n{nb_duplicates} duplicates found, \
            {nb_deleted} deleted, \
            {nb_kept} kept')
    print(f'Keeping: {keep_list}')

def delete_duplicates(duplicate_dict, sourcedir, targetdir, printout=True):
    """Delete duplicated files in the target directory,
    keep all the files in the source directory, 
    always keep at least one copy of the file

    Args:
        :duplicate_dict (dict): Dictionary hash: [list of files with that hash value]
        :sourcedir (str): directory and all its subfolders that will be left unchanged
        :targetdir (str): directory and all its subfolders from which we want to delete duplicate
        :printout (bool): True to print the synthesis, False for no print out"""
    for __, files_list in duplicate_dict.items():
        # all the files in files_list share the same hash and are duplicates
        files_list = list(set(files_list))
        # if there is only one file, no need to processs as we keep it
        if len(files_list) >= 2:
            # delete the file in target dir
            delete_list = [fn for fn in files_list if is_in_dir(fn, targetdir) 
                                                      and ~is_in_dir(fn, sourcedir)] # for src & trg overlap
            # keep the files in source dir
            keep_list = [fn for fn in files_list if is_in_dir(fn, sourcedir)]
            # ensure that no matter what we keep at least one file
            if keep_list == list() and len(delete_list) > 0:
                # as keep_list is empty we transfer the first of delete_list
                keep_list = [delete_list[0]]
                delete_list.pop(0)
            if len(keep_list) >= 1: # safety check, 
                # delete the files, retrieve nb successful deletion
                nb_deleted = delete_files(delete_list)
            if printout:
                # print out the result for this set of duplicated files
                print_df(len(files_list), nb_deleted, len(keep_list), keep_list)

def drop_empty_folders(directory):
    """Walk a folder and all its sub folder, delete any empty (sub)folder

    Args:
        :directory (str): directory"""
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        if not dirnames and not filenames:
            # we have an empty folder
            try:
                os.rmdir(dirpath)
                print(f'Deleted empty folder: {dirpath}')  
            except (OSError):
                # we were not able to delete the folder (lock...)
                print(f'Error deleting empty folder: {dirpath}')
                continue
            
def print_duplicate(hash_dict):
    """Print list of duplicate files based on their hash from the input dictionary

    Args:
        :hash_dict (dict): Dictionary hash: [list of files with that hash value]"""
    # For all files with the hash on the 1st 1024 bytes, get their hash on the full file - collisions will be duplicates
    for __, files_list in hash_dict.items():
        # make sure we only have one time each file for the given hash
        files_list = list(set(files_list)) 
        if len(files_list) >= 2:
            # at least 2 files bytes have this hash
            print("\nDuplicate found:")
            # print with a loop with return carriage for the sake of readability
            for filename in files_list:
                print(filename)


def check_for_duplicates(paths, hash=hashlib.sha1, del_target=False):
    hashes_by_size = get_files_by_size(paths)
    hashes_on_1k = get_files_by_1k(hashes_by_size)
    hashes_full = get_files_by_full(hashes_on_1k)
    if del_target:
        delete_duplicates(hashes_full, sourcedir, targetdir)
        for _ in range(10):
            drop_empty_folders(targetdir)
    else:
        print_duplicate(hashes_full)

# master directory, will be kept untouched
# sourcedir = r'E:\BackUp\HPWL0621\Documents'
# sourcedir = r'E:\BackUp\HPWL0621\Pictures'
# sourcedir = r'E:\BackUp\HPWL0621\OneDrive'
# sourcedir = r'E:\BackUp\HPWL0621\Documents'
# sourcedir = r'E:\BackUp\HPWL0621\OneDrive - Vallourec'
sourcedir = r'E:\BackUp\HPWL0621'

# directory where we want to delete the duplicates
# targetdir = r'E:\BackUp\HPWL0432\raphael.louvrier\Documents'
# targetdir = r'E:\BackUp\HPWL0432\raphael.louvrier\Pictures'
# targetdir = r'E:\BackUp\HPWL0432\raphael.louvrier\One Drive - Vallourec'
# targetdir = r'E:\BackUp\HPWL0432'
targetdir = r'E:\BackUp\Old Pro\Vallourec'
# targetdir = r'E:\BackUp\Install'
# targetdir = r'E:\BackUp\HPWL0621\FormerOrg'

check_for_duplicates([sourcedir, targetdir], del_target=True)