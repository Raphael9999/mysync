# documentation of the package https://pypi.org/project/dirsync/
from dirsync import sync

sourcedir = r'C:\Users\raphael.louvrier\OneDrive - Vallourec\1 Support\Archive\OEE Vallourec Drilling'
targetdir = r'C:\Users\raphael.louvrier\OneDrive - Vallourec\OEE Vallourec Drilling'
action = 'sync'
# options = 

sync(sourcedir, targetdir, action) #, **options)