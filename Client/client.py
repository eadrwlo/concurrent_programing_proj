import socket                  
import json
import time
import sys
import file_helper
host = "127.0.0.1"
port = 50000
client_name = "Adam"
file_name = 'test'
path = "files"

if len(sys.argv) > 1:
    client_name = sys.argv[1]
    path = sys.argv[2]

while(1):
    command = {
        "command" : "hello",
        "client_name" : client_name
    }
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
        command = {
            "command": "file_send_req",
            "client_name": client_name
        }
        command["file_name"] = fileToSend.replace(path + '\\' , '')
        s = socket.socket()
        s.connect((host, port))
        ##Hanshake
        msg = json.dumps(command).encode('utf-8')
        s.sendall(msg)
        print('Send in loop', command)

        #Response
        data = s.recv(1024)
        dataObject = json.loads(data.decode('utf-8'))
        print("received", dataObject)

        #File sending
        sForFile = socket.socket()
        sForFile.connect((host, dataObject["port"]))
        f = open(fileToSend, 'rb')
        l = f.read(1024)
        while (l):
            print ("Sending file with name = ", fileToSend, " ... ")
            sForFile.send(l)
            # print('Sent ',repr(l))
            l = f.read(1024)
        sForFile.close()
    time.sleep(10)
