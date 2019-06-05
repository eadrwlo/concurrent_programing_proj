import socket                   # Import socket module
import json
s = socket.socket()             # Create a socket object
host = "127.0.0.1"  #Ip address that the TCPServer  is there
port = 50000                     # Reserve a port for your service every new transfer wants a new port or you must wait.

s.connect((host, port))

client_name = "Adam"
file_name = "test"
command = {
    "command" : "hello",
    "client_name" : client_name,
    "file_name" : file_name 
}

s.sendall(json.dumps(command).encode('utf-8'))
data = s.recv(1024)
dataObject = json.loads(data.decode('utf-8'))
s.close()
s = socket.socket() 
print('Connecting on port', dataObject["port"])
s.connect((host, dataObject["port"]))

f = open(file_name,'rb')
l = f.read(1024)
while(l):
    s.send(l)
    print('Sent ',repr(l))
    l = f.read(1024)
f.close()
print('Done sending')

print('Successfully get the file')
s.close()
print('connection closed')

