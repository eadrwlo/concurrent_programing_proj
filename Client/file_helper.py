import os

def printFilesInDir(path):
    dirsAndFiles = os.listdir(path)
    print(dirsAndFiles)
    for x in dirsAndFiles:
        currentFile = path + '\\' + x
        if (os.path.isdir(currentFile) == True):
            print (currentFile, " is a dir")
            printFilesInDir(currentFile)
        elif (os.path.isfile(currentFile) == True):
            print (currentFile, " is a file")
			
def getFilesNamesFromDisk(path):
    files = []
    dirsAndFiles = os.listdir(path)
    print(dirsAndFiles)
    for x in dirsAndFiles:
        currentFile = path + '\\' + x
        if (os.path.isfile(currentFile) == True):
            files.append(currentFile)
    return files
	
def getFilesToSend(filesFromServer, filesFromDisk, path):
	filesToSend = []
	for fileFromDisk in filesFromDisk:
		fileName = fileFromDisk.replace(path + '\\' , '')
		if fileName not in filesFromServer:
			print (fileFromDisk, "not found on server. Addind to list to send to server.")
			filesToSend.append(fileFromDisk)
	return filesToSend
