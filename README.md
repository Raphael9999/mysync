# MySync

## Description
_sync_, is a very simple and basic Basic one way synchronization from a source folder to a target folder.  
It makes sure all files and subfolders of the source are in the target directory.  
The option parameter can be used to delete files of the target that are not in the source anymore.  
I used this little program as a work around to replicate a folder in a O365 SharePoint as I was unable to obtain credential to use the proper API. It will synchronize the sourcedir to the targetdir, then the targetdir will be sync to O365 by Microsoft OneDrive. 

_duplicates_, identify duplicates files within a given list of folders 
adding features to automaticaly delete the one in the targetdir

## Installation
Install required packages `pip install dirsync`  
From the O365 SharePoint, sync the folder on your computer, this will be your targetdir.  

## Example
* Update sourcedir to your source drirectory that you want to replicate  
* Update targetdir to the desired folder  
* Run

## License
MIT License  
Copyright (c) 2021 Raphael Louvrier  