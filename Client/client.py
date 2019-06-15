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

def send(fileToSend):
    command = {
            "command": "file_send_req",
            "client_name": client_name
        }
    command["file_name"] = fileToSend
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
    f = open("files\\" + fileToSend, 'rb')

    l = f.read(1024)
    while (l):
        #time.sleep(0.5)
        print ("Sending file with name = ", fileToSend, " ... ")
        sForFile.send(l)
        # print('Sent ',repr(l))
        l = f.read(1024)
    sForFile.close()

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
    filesToDownload = file_helper.getFilesToDownload(dataObject["files_on_server"], filesOnDisk, path)
    print("Files to download = ", filesToDownload)
    s.close()

    for fileToSend in filesToSend:
        send(fileToSend)

    for fileToDownload in filesToDownload:
        command = {
            "command": "file_download_req",
            "client_name": client_name,
            "file_name" : fileToDownload
        }
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
        s.close()
        #File sending
        sForFile = socket.socket()
        noOfRetry = 0
        while noOfRetry < 6:
            try:
                sForFile.connect((host, dataObject["port"]))
            except:
                print("FAILED. Sleep briefly & try again")
                noOfRetry += 1
                time.sleep(1)
                continue
            print("Connected!")
            with open("files\\" + fileToDownload, 'wb') as f:
                print ('file opened for download')
                while True:
                    print('receiving data...')
                    data = sForFile.recv(1024)
                    #print('data=%s', (data))
                    print(data)
                    if not data:
                        break
                         # write data to a file
                    f.write(data)
            break
        sForFile.close()

    time.sleep(10)
