import socket                  
import json
import time
import os
import file_helper
host = "127.0.0.1"
port = 50000
client_name = "Adam"
file_name = 'test'
command = {
    "command" : "hello",
    "client_name" : client_name,
}
path = "files"

while(1):
    filesOnDisk = file_helper.getFilesNamesFromDisk(path)
    for file in filesOnDisk:
        print (file)
    s = socket.socket()
    s.connect((host, port))
    s.sendall(json.dumps(command).encode('utf-8'))
    print('Send ', command)
    data = s.recv(1024)
    dataObject = json.loads(data.decode('utf-8'))
    print (dataObject)
    filesToSend = file_helper.getFilesToSend(dataObject["files_on_server"], filesOnDisk, path)
    s.close()
    for fileToSend in filesToSend:
        s = socket.socket()
        print('Connecting on port', dataObject["port"])
        s.connect((host, dataObject["port"]))
        f = open(fileToSend,'rb')
        l = f.read(1024)
        command["file_name"] = fileToSend.replace(path + '\\' , '')
        print(json.dumps(command).encode('utf-8'))
        s.sendall(json.dumps(command).encode('utf-8'))
        while(l):
            s.send(l)
            print('Sent ',repr(l))
            l = f.read(1024)
        f.close()
        print('Done sending')
        s.close()
        print('connection closed')
    time.sleep(20)

