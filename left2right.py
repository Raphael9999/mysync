import os, shutil
from numpy.lib.arraysetops import setxor1d
import pandas as pd

def get_files_and_size(path:str) -> pd.DataFrame:
    """Build a dictionary containing lists of files with the same size. 
    Those lists of files contains potential duplicates that will be analysee further

    Args: 
        :path (str): a folder to walk to build the output
    
    Return: dataframe, one row per file with path minus root as the index, path_to_file and size as columns
    """
    _df = pd.DataFrame(columns=['short', 'path', 'size'])
    _df.astype({'short': 'object', 'path': 'object', 'size': 'int64'})
    for dirpath, subfolders, filenames in os.walk(path):
        # get all files that have the same size - they are the collision candidates
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            try:
                _size = os.path.getsize(full_path)
            except:
                _size = 0
            new_row = {'short': full_path.replace(path, '', 1).lstrip('\\').lstrip('//'), 
                       'path': full_path, 
                       'size': _size}
            _df = _df.append(new_row, ignore_index=True)
    _df.set_index('short', drop=True, inplace=True)
    return _df

def copy_left_to_right(source, target, test:bool=True):
    # collect files
    source_files = get_files_and_size(source)
    target_files = get_files_and_size(target)

    # loop on source files
    for short, src_row in source_files.iterrows():
        # if source file is already in target but their size differ
        if short in target_files.index:
            if src_row['size'] != target_files.loc[short, 'size']:
                # we overwrite the file in the target folder
                
                if not test:
                    try: 
                        shutil.copy2(src_row['path'], target_files.loc[short, 'path'])
                        print(f"Source and target file have different size, copy from source to target for: {short}")
                    except:
                        print(f"fail to copy from source to target for: {short}")
            else: 
                print(f"Source and target file have same size, no action for: {short}")
        else:
            # source file is not in target, we copy it
            
            if not test:
                trg_path = os.path.join(target, short)
                trg_dir = os.path.dirname(trg_path)
                if not os.path.isdir(trg_dir):
                    try:
                        os.makedirs(trg_dir)
                    except:
                        print(f"fail to create folder {trg_dir}")
                try:
                    shutil.copy2(src_row['path'], trg_path)
                    print(f"Source file is not in target folder, copy from source to target for: {short}")
                except:
                    print(f"fail to copy from source to target for: {short}")

    

# root directory of the source directories and files
source = r'C:\Users\Raphael.Louvrier\OneDrive - Vallourec\1 Support'

# root directory of the target directories and files, 
# the structure is expected to be the same as in the source
target = r'D:\1 Support'

# Done , 2, 3, 5
copy_left_to_right(source, target, False)