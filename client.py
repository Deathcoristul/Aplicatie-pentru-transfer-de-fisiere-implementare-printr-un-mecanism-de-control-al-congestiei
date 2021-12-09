import socket
import time
from window import App
# Creaza un socket IPv4, TCP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,socket.IPPROTO_UDP)
s.connect((App.ReceiverIP, App.ReceiverPort))

for i in range(3,10):
    # Trimite date
    s.sendall(bytes('Ana are ' + str(i) + ' mere', encoding="ascii"))
    # Asteapta date
    data = s.recv(1024)
    print('Am receptionat: ', data)
    # Asteapta o secunda
    time.sleep(1)
# Inchide conexiune
s.close()