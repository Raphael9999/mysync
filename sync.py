# documentation of the package https://pypi.org/project/dirsync/
from dirsync import sync

def one_way_sync(sourcedir, targetdir):
    """One way synchronization from source folder to target folder

    Args:
        sourcedir (str): source folder
        targetdir (str): target folder
    """
    action = 'sync'
    sync(sourcedir, targetdir, action)

# define source and target folder, run the synchronization
source = r'C:\Users\Raphael.Louvrier\OneDrive - Vallourec\Desktop\a'
target = r'C:\Users\Raphael.Louvrier\OneDrive - Vallourec\Desktop\b'
one_way_sync(source, target)