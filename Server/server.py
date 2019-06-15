import socket                   # Import socket module
import pickle
import json
import logging
import threading
import concurrent.futures
import queue
import csv
import time
import os

ports = [50001, 50002, 50003, 50004, 50005]
reservedPorts = []
usersAndFiles = {}
usersAndFilesFullPath = {}

def getFreePortForTransmission():
   selectedPort = -1
   for port in ports:
      if port not in reservedPorts:
         reservedPorts.append(port)
         selectedPort = port
         break
   return selectedPort

class Receiver:

   def findFileFullPath(self, fileToSend, userName):
      print("findFileFullPath", fileToSend, fileToSend)
      filesFullPath = usersAndFilesFullPath[userName]
      for fileFullPath in filesFullPath:
         if fileToSend in fileFullPath:
            print("Found full path for file = ", fileToSend, "for user = ", userName, " fileFullPath =",fileFullPath)
            return fileFullPath

   def createDir(self, path):
      if not os.path.exists(path):
         os.mkdir(path)
         print("Directory " , path ,  " created ")
      else:
         print("Directory ", path ,  " already exists")

   def receive(self, queue, event, lock, lockForFilesPath, id, path):
      self.createDir(path)
      print ('Receiver ID= ', id, 'waiting for connections...')
      while not event.is_set():
         if not queue.empty():
            dataObject = queue.get()
            if dataObject["command"] == "file_send_accept":
               print ('From queue ', dataObject)
               port = dataObject["port"]
               s = socket.socket()
               s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
               host = "127.0.0.1"
               s.bind((host, port))
               s.listen(5)
               print("Waiting for connection for file receiving...")
               conn, addr = s.accept()
               print ('Receiver ID= ', id, 'Got connection from', addr, ' on port ', port)
               fileName = dataObject["file_name"]
               fileNameForSaveInDict = fileName
               self.createDir(path + "\\" + dataObject["client_name"])
               fileName = os.path.join(path, dataObject["client_name"], fileName)
               with open(fileName, 'wb') as f:
                  print ('file opened')
                  while True:
                     print('receiving data...')
                     data = conn.recv(1024)
                     #print('data=%s', (data))
                     print(data)
                     if not data:
                        break
                     # write data to a file
                     f.write(data)
                  f.flush()
               s.close()
               print("Before lock")
               with lock:
                  reservedPorts.remove(port)
                  usersAndFiles[dataObject["client_name"]].add(fileNameForSaveInDict)
                  print("Appended file = ", fileNameForSaveInDict)
                  #dbUpdater()
            elif dataObject["command"] == "file_download_accept":
               print("Starting send file to client...")
               print ('From queue ', dataObject)
               port = dataObject["port"]
               s = socket.socket()
               #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
               host = "127.0.0.1"
               s.bind((host, port))
               s.listen(5)
               conn, addr = s.accept()
               print ('Receiver ID = ', id, 'file_download_accept Got connection from', addr, ' on port ', port)
               fileName = dataObject["file_name"]
               #with lockForFilesPath:
               print('filename = ', fileName, 'client_name = ', dataObject["client_name"])
               with lockForFilesPath:
                  fileToSend = self.findFileFullPath(fileName, dataObject["client_name"])
               f = open(fileToSend, 'rb')
               l = f.read(1024)
               print("File opened in file_download_accept")
               while (l):
                  print ("Sending file with name = ", fileToSend, " ... ")
                  conn.send(l)
                  # print('Sent ',repr(l))
                  l = f.read(1024)
               f.close()
               conn.close()
               with lock:
                  reservedPorts.remove(port)
            else:
               print("Command not found...!")
            print("Done in receiver!")

               

def dispatcher(queue, event):
   s = socket.socket()
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   host = "127.0.0.1"
   port = 50000
   s.bind((host, port))
   while not event.is_set():
      print ('Server waiting for connections...')
      #print(usersAndFiles)
      #dbUpdater()
      s.listen(5)
      conn, addr = s.accept()  
      print ('Dispatcher Got connection from', addr)
      data = conn.recv(2024)
      dataObject = json.loads(data.decode('utf-8'))
      #print('Server received data ', repr(data))
      print('Server received dataObject', dataObject)
      if dataObject["command"] == 'hello':
         if dataObject["client_name"] not in usersAndFiles:
            usersAndFiles[dataObject["client_name"]] = set()
         command = {
                "command": "hello",
                "files_on_server": list( usersAndFiles[dataObject["client_name"]] )
         }
         msg = json.dumps(command).encode('utf-8')
         print('data=', (msg))
         conn.sendall(msg)
      elif dataObject["command"] == 'file_send_req':
         print("received", dataObject)
         portForTransmission = getFreePortForTransmission()
         if portForTransmission != -1:
            command = {
                     "command": "file_send_accept",
                     "port": portForTransmission,
                     "client_name": dataObject["client_name"],
                     "file_name": dataObject["file_name"]
                }
            msg = json.dumps(command).encode('utf-8')
            print('data=', (msg))
            conn.sendall(msg)
            queue.put(command)
         else:
            print("All ports busy in handling file_send_req!")
      elif dataObject["command"] == 'file_download_req':
         print("received", dataObject)
         portForTransmission = getFreePortForTransmission()
         if portForTransmission != -1:
            command = {
                     "command": "file_download_accept",
                     "port": portForTransmission,
                     "client_name": dataObject["client_name"],
                     "file_name": dataObject["file_name"]
                }
            msg = json.dumps(command).encode('utf-8')
            print('data=', (msg))
            conn.sendall(msg)
            queue.put(command)
         else:
            print("All ports busy in handling file_download_req!")
      else:
         print("Command not known!")
      print("Done")

def dbUpdater(event, lockForFilesPath):
   while not event.is_set():
      time.sleep(10)
      with lockForFilesPath:
         loadFilesDbBasedOnDirsNames('Files')

   
def getFilesForClient(client):
   path = 'clients.csv'
   lines = [line for line in open(path)]
   for line in lines:
      clientAndFiles = line.strip().split(",")
      if (clientAndFiles[0] == client):
         return clientAndFiles[1].split(" ")

def loadFilesDbBasedOnCsv():
   path = 'clients.csv'
   lines = [line for line in open(path)]
   for line in lines:
      listOfFiles =  []
      clientAndFiles = line.strip().split(",")
      print (clientAndFiles)
      i = 0
      for filename in clientAndFiles:
         if i > 0:
            listOfFiles.append(filename)
         i += 1
      usersAndFiles[clientAndFiles[0]] = listOfFiles
   #print (usersAndFiles)

def loadFilesDbBasedOnDirsNames(path):
   dirs = os.listdir(path)
   #print(dirs)
   usersAndFiles.clear()
   usersAndFilesFullPath.clear()
   for dir in dirs:
      usersDirs = os.listdir(path + "\\" + dir)
      #print("usersDirs = ", usersDirs)
      for userDir in usersDirs:
         usersFiles = os.listdir(path + "\\" + dir + "\\" + userDir)
         for userFile in usersFiles:
            if userDir in usersAndFiles:
               #print ("Adding ", userFile)
               usersAndFiles[userDir].add(userFile)
               usersAndFilesFullPath[userDir].add(path + "\\" + dir + "\\" + userDir + "\\" + userFile)
            else:
               usersAndFiles[userDir] = set()
               usersAndFiles[userDir].add(userFile)
               usersAndFilesFullPath[userDir] = set()
               usersAndFilesFullPath[userDir].add(path + "\\" + dir + "\\" + userDir + "\\" + userFile)
   print("Loaded = ", usersAndFiles)
   print("Loaded = ", usersAndFilesFullPath)


def addFileForClientToFilesDb(fileToAdd, clientName):
   path = 'clients.csv'
   f = open(path, "r")
   contents = f.readlines()
   f.close()
   contents.insert(0, " " + fileToAdd)
   f = open("path", "w")
   contents = "".join(contents)
   f.write(contents)
   f.close()
      
if __name__ == "__main__":
   print("Loaded = ", usersAndFiles)
   print("Loaded = ", usersAndFilesFullPath)
   lock = threading.Lock()
   lockForFilesPath = threading.Lock()
   #loadFilesDb()
   loadFilesDbBasedOnDirsNames('Files')
   receiver = Receiver()
   pipeline = queue.Queue(maxsize=100)
   event = threading.Event()
   rootPath = "Files"
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
      executor.submit(dispatcher, pipeline, event)
      executor.submit(receiver.receive, pipeline, event, lock, lockForFilesPath, 1, rootPath + "\\Folder1")
      executor.submit(receiver.receive, pipeline, event, lock, lockForFilesPath, 2, rootPath + "\\Folder2")
      #executor.submit(receiver.receive, pipeline, event, lock, 3, rootPath + "\\Folder3")
      #executor.submit(receiver.receive, pipeline, event, lock, 4, rootPath + "\\Folder4")
      #executor.submit(receiver.receive, pipeline, event, lock, 5, rootPath + "\\Folder5")
      #executor.submit(dbUpdater, event, lockForFilesPath)
   print('Main: about to set event')

