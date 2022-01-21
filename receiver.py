
import random
from select import select
from threading import *
import tkinter
import window as w


class Send_ACK(Thread):
    status = Condition()
    ACK_packs = []  # ACK-uri de trimis
    send_blocked = False  # daca am blocat trimiterea
    last_ACK = ['%0%']
    index = [0]  # pentru contorizarea ACK-ului Duplicat
    send_stop = False  # flag daca am oprit trimiterea

    def __init__(self):
        super(Send_ACK, self).__init__()

    def run(self):
        while w.running:
            #print("ACK Send")
            Send_ACK.status.acquire()  # primesc lock
            if len(Send_ACK.ACK_packs) == 0:
                Send_ACK.status.wait()  # astept cat timp n-am niciun ACK
            if len(Send_ACK.ACK_packs):  # daca am ACK-uri, scot si trimit pe socket
                if Send_ACK.last_ACK[0] != Send_ACK.ACK_packs[0]:
                    # nu mai fac duplicat ultimul pachet daca am primit din nou
                    Send_ACK.unsended_ACK()  # verific daca trimit ACK pentru pachetul curent sau nu
                # daca trimiterea nu e blocata, se trimite pe socket
                print("coada ACK de trimis")
                print(Send_ACK.ACK_packs)  # daca am in coada de ACK si trimiterea nu e blocata, se trimite pe socket
                if len(Send_ACK.ACK_packs) and not Send_ACK.send_blocked:
                    print("Trimit normal")
                    p = Send_ACK.ACK_packs.pop(0)
                    print("Trimit " + p)
                    string = p
                    string = '%' + string + '%'
                    w.Socket.UDPServerSock.sendto(bytearray(string.encode('utf-8')), (w.App.SenderIP, int(w.App.SenderPort)))
                    Send_ACK.last_ACK.insert(0, string)  # actualizez ultima ACK
                    w.App.receiver_text.insert(tkinter.END, p + '\n')
                else:
                    Send_ACK.send_stop = True
                    string = Send_ACK.last_ACK[0]  # scot din coada ultima Ack
                    p = string
                    string = '%' + string + '%'  # impachetez sirul
                    for i in range(0, 4):  # trimit 4 copii pentru ultima ACK daca trimiterea e blocata
                        print("Trimit " + string)
                        w.Socket.UDPServerSock.sendto(bytearray(string.encode('utf-8')), (w.App.SenderIP, int(w.App.SenderPort)))
                        Send_ACK.index[0] += 1  # incrementez contorul
                        w.App.receiver_text.insert(tkinter.END, p + '\n')
                    Send_ACK.ACK_packs = []  # curatam cozile
                    Receive_Data.packs = []
                    Send_ACK.send_stop = False  # schimbam starea
            Send_ACK.status.release()  # eliberez

    @staticmethod
    def unsended_ACK():
        if not Send_ACK.send_blocked:  #
            Send_ACK.send_blocked = Send_ACK.sendornot()  # arunc cu banul daca nu e oprita
            print(Send_ACK.send_blocked)  # nu mai apelam functia daca am hotarat ca nu mai trimit pachete
            if Send_ACK.send_blocked:
                print("Trimit cerere duplicat pt " + Send_ACK.ACK_packs[
                    0])  # daca am oprit trimiterea, mut totul in coada de ACK-uri netrimise
                Send_ACK.last_ACK[0] = Send_ACK.ACK_packs[0]  # si inserez ultima ACK trimis
                print("am blocat trimiterea")
                Receive_Data.packs = []

    @staticmethod
    def sendornot():
        nr = random.random()
        print("Probabilitatea: " + str(nr))
        if nr < int(w.App.PackLoss)/100:
            print('trimit')
            return False
        else:
            print('nu trimit')
            return True


class Receive_Data(Thread):
    status = Condition()
    packs = []
    buffer_socket = []

    def __init__(self):
        super(Receive_Data, self).__init__()

    def run(self):
        while w.running:
            #print("Receive_data")
            Receive_Data.status.acquire()  # primesc lock
            if not w.Socket.flag:  # verific daca s-a apasat pe start
                Receive_Data.status.wait()
            r, _, _ = select([w.Socket.UDPServerSock], [], [], 1)
            if r:  # scot date de pe socket
                data, address = w.Socket.UDPServerSock.recvfrom(w.Socket.bufferLen)
                Receive_Data.buffer_socket.append(str(data))  # daca am blocata trimiterea,verific daca poate fi deblocata
                if Send_ACK.send_blocked:
                    self.unblock_send(str(data))
                Receive_Data.packs.append(str(data))  # data=informatia citita
                print("Am primit " + str(data))  # debug
                print(Send_ACK.send_blocked)
                # anunt thread-ul de prelucrarea datelor ca poate incepe treaba
                DataThread.status.acquire()
                DataThread.status.notify()
                DataThread.status.release()
                # actualizez informatia de pe interfata
                string = w.App.number_pack(str(data))
                w.App.receiver_text.insert(tkinter.END, string + '\n')
                print('buffer')
                print(Receive_Data.buffer_socket)
            Receive_Data.status.release()  # eliberez lock

    def unblock_send(self, param):
        print('Deblocam acum')  # daca primesc ceva de la emitator voi debloca
        Send_ACK.send_blocked = False
        # debug
        print('Din fct de deblocare coada de pachete arata asa:')
        print(Receive_Data.packs)
        print(Send_ACK.send_blocked)
        print("coada ACK")
        print(Send_ACK.ACK_packs)


class DataThread(Thread):
    status = Condition()

    def __init__(self):
        super(DataThread, self).__init__()

    def run(self):
        while w.running:
            #print("DataThread")
            DataThread.status.acquire()
            if len(Receive_Data.packs) == 0:
                DataThread.status.wait()  # astept cat timp nu am primit pachete de prelucrat
            else:
                p = Receive_Data.packs.pop(0)
                print("Prelucrez sirul " + p)
                buff = w.App.check_string(p)
                if len(buff):
                    Send_ACK.ACK_packs += buff  # inserez lista in coada de trimis ACK-uri
                    Send_ACK.status.acquire()  # anunt thread pentru trimitere ACK
                    Send_ACK.status.notify()
                    Send_ACK.status.release()
            DataThread.status.release()
