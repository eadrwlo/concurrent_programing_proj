import socket                   # Import socket module
import pickle
import json
import logging
import threading
import concurrent.futures
import queue
import csv
import time

ports = [50001, 50002, 50003, 50004, 50005]
reservedPorts = []
usersAndFiles = {}

def getFreePortForTransmission():
   foundFreePort = False
   selectedPort = -1
   for port in ports:
      if port not in reservedPorts:
         reservedPorts.append(port)
         selectedPort = port
         break
   return selectedPort

class Receiver:
   def receive(self, queue, event, lock, id):
      print ('Receiver ID= ', id, 'waiting for connections...')
      while not event.is_set():
         if not queue.empty():
            dataObject = queue.get()
            print ('From queue ', dataObject)
            port = dataObject["port"]                    
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            host = "127.0.0.1"
            s.bind((host, port))           
            s.listen(5)
            conn, addr = s.accept()  
            print ('Receiver ID= ', id, 'Got connection from', addr, ' on port ', port)
            #data = conn.recv(1024)
            #dataObject = json.loads(data.decode('utf-8'))
            #print (dataObject)
            fileName = dataObject["file_name"]
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
               usersAndFiles[dataObject["client_name"]].append(fileName)
               print("Appended")
               #dbUpdater()
               

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
            usersAndFiles[dataObject["client_name"]] = []
         command = {
                "command": "hello",
                "files_on_server": usersAndFiles[dataObject["client_name"]]
         }
         msg = json.dumps(command).encode('utf-8')
         print('data=', (msg))
         conn.sendall(msg)
      elif dataObject["command"] == 'file_send_req':
         print("received", dataObject)
         portForTransmission = getFreePortForTransmission()
         if portForTransmission != -1:
            command = {
                     "command": "hello",
                     "port": portForTransmission,
                     "client_name": dataObject["client_name"],
                     "file_name": dataObject["file_name"]
                }
            msg = json.dumps(command).encode('utf-8')
            print('data=', (msg))
            conn.sendall(msg)
            queue.put(command)
         else:
            print("All ports busy!")
      else:
         print("Command not known!")
      print("Done")

def dbUpdater(event, lock):
   while not event.is_set():
      time.sleep(5)
      print ("dbUpdater started!")
      path = 'clients.csv'
      with lock:
         with open(path, 'wt') as f:
            print ('file opened')
            for key, values in usersAndFiles.items():
               print(key, ":", values)
               content = key + ","
               i=0
               for value in values:
                  if i < len(value):
                     content = content + value + ","
                  else:
                     content = content + value
                  i+=1
               print(content)
               f.write(content + '\n')
            f.flush()
            print('Saved to file')

   
def getFilesForClient(client):
   path = 'clients.csv'
   lines = [line for line in open(path)]
   for line in lines:
      clientAndFiles = line.strip().split(",")
      if (clientAndFiles[0] == client):
         return clientAndFiles[1].split(" ")

def loadFilesDb():
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
   #print (getFilesForClient("Jan"))
   lock = threading.Lock()
   loadFilesDb()
   receiver = Receiver()
   pipeline = queue.Queue(maxsize=5)
   event = threading.Event()
   with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
         executor.submit(dispatcher, pipeline, event)
         executor.submit(receiver.receive, pipeline, event, lock, 1)
         executor.submit(receiver.receive, pipeline, event, lock, 2)
         executor.submit(receiver.receive, pipeline, event, lock, 3)
         executor.submit(dbUpdater, event, lock)
   print('Main: about to set event')

