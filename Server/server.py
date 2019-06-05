import socket                   # Import socket module
import pickle
import json
import logging
import threading
import concurrent.futures
import queue

ports = [50001, 50002, 50003, 500043, 50005]
reservedPorts = []

def getFreePortForTransmission():
   for port in ports:
      if port not in reservedPorts:
         reservedPorts.append(port)
         return port
      else:
         return -1

def receiver(queue, event):
   print ('Receiver waiting for connections...')
   while not event.is_set():
      if not queue.empty():
         dataObject = queue.get()
         print ('From queue ', dataObject)
         port = dataObject["port"]                    
         s = socket.socket()           
         host = "127.0.0.1"
         s.bind((host, port))           
         s.listen(5)
         conn, addr = s.accept()  
         print ('Got connection from', addr, ' on port ', port)
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
   
         

def dispatcher(queue, event):
   while not event.is_set():
      print ('Server waiting for connections...')
      port = 50000                    
      s = socket.socket()           
      host = "127.0.0.1"
      s.bind((host, port))           
      s.listen(5)
      conn, addr = s.accept()  
      print ('Got connection from', addr)
      data = conn.recv(1024)
      dataObject = json.loads(data.decode('utf-8'))
      #print('Server received data ', repr(data))
      print('Server received dataObject', dataObject)
      if dataObject["command"] == 'hello':
         portForTransmission = getFreePortForTransmission()
         if portForTransmission != -1:
            command = {
               "command" : "hello",
               "port" : portForTransmission
            }
            dataObject["port"] = portForTransmission
            msg = json.dumps(command).encode('utf-8')
            print('data=', (msg))
            conn.sendall(msg)
            queue.put(dataObject)

if __name__ == "__main__":
   pipeline = queue.Queue(maxsize=5)
   event = threading.Event()
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
         executor.submit(dispatcher, pipeline, event)
         executor.submit(receiver, pipeline, event)
   print('Main: about to set event')

