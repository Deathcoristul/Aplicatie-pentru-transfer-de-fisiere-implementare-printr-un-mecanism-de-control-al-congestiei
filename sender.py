import select
import tkinter
from threading import *
import window as w
from Tahoe import Algoritm_Tahoe


class Send(Thread):
    status = Condition()  # variabila de conditie pentru comunicarea prin socket

    def __init__(self):
        super(Send, self).__init__()  # constructor din clasa parinte

    def run(self):
        while w.running:  # se asteapta
            Send.status.acquire()  # primesc lock
            send_packs = []  # coada in care voi insera pachete de trimis
            print("Send")
            if len(Prelucrare_Thread.packs) == 0 and len(Algoritm_Tahoe.retransmit_packs) == 0:
                Send.status.wait()  # daca nu exista pachete de trimis cozile din care le pot lua, mai astept
            # trimit din coada de pachete daca este vida coada de retransmisie iar pachetele trimise au primit ack
            if len(Prelucrare_Thread.packs) and len(Algoritm_Tahoe.retransmit_packs) == 0 and len(
                    Algoritm_Tahoe.unconfirmed_packs) == 0:
                p = Prelucrare_Thread.packs[0]  # verific daca primul pachet este de tip Begin sau End
                if p[0] in 'BE':  # il trimit direct fara sa il pun in coada si fara sa tin cont de cwnd
                    b = Prelucrare_Thread.packs.pop(0)  # scot din coada
                    # trimit
                    w.Socket.UDPServerSock.sendto(bytearray(b.encode('utf-8')),(w.App.ReceiverIP, int(w.App.ReceiverPort)))
                # preiau din coada doar cate imi spune cwnd
                # se verifica daca nu sunt mai putine pachete in coada decat dimensiunea ferestrei
                if len(Prelucrare_Thread.packs) < Algoritm_Tahoe.cwnd:
                    for i in range(0, len(Prelucrare_Thread.packs)):
                        if Prelucrare_Thread.packs[0][0] not in 'BE':  # verific sa nu fie pachet de begin/end
                            p = Prelucrare_Thread.packs.pop(0)  # scot din coada
                            send_packs += [p]  # si le adaug in coada de trimitere si cea de neconfirmate
                            Algoritm_Tahoe.unconfirmed_packs += [p]
                else:  # scot cwnd pachete din coada
                    for i in range(0, Algoritm_Tahoe.cwnd):
                        if Prelucrare_Thread.packs[0][0] not in 'BE':  # verific sa nu fie pachet de begin/end
                            p = Prelucrare_Thread.packs.pop(0)  # scot din coada
                            send_packs += [p]  # si le adaug in coada de trimitere si cea de neconfirmate
                            Algoritm_Tahoe.unconfirmed_packs += [p]
                for i in range(0, len(send_packs)):
                    p = send_packs.pop(0)  # scot din coada
                    w.Socket.UDPServerSock.sendto(bytearray(p.encode('utf-8')),(w.App.ReceiverIP, int(w.App.ReceiverPort)))
                    w.App.sender_text.insert(tkinter.END, 'Pachet: ' + p)
            elif len(Algoritm_Tahoe.unconfirmed_packs) == 0 and len(Algoritm_Tahoe.retransmit_packs) != 0:
                # in caz ca avem elemente de retransmis iar pachetele trimise au primit ACK
                if len(Algoritm_Tahoe.retransmit_packs) == 1:  # trimitem direct din coada de retransmisie
                    p = Algoritm_Tahoe.retransmit_packs.pop(0)
                    send_packs += [p]
                    Algoritm_Tahoe.unconfirmed_packs += [p]
                if len(Algoritm_Tahoe.retransmit_packs) <= Algoritm_Tahoe.cwnd:  # daca avem putine pachete
                    for i in range(0, len(Algoritm_Tahoe.retransmit_packs)):  # le trimit pe toate
                        p = Algoritm_Tahoe.retransmit_packs.pop(0)
                        send_packs += [p]
                        Algoritm_Tahoe.unconfirmed_packs += [p]
                else:  # scot doar cwnd pachete
                    for i in range(0, Algoritm_Tahoe.cwnd):
                        p = Algoritm_Tahoe.retransmit_packs.pop(0)
                        send_packs += [p]
                        Algoritm_Tahoe.unconfirmed_packs += [p]
                for i in range(0, len(send_packs)):  # acum trimitem din coada de trimis
                    s = send_packs.pop(0)
                    w.Socket.UDPServerSock.sendto(bytearray(s.encode('utf-8')),(w.App.ReceiverIP, int(w.App.ReceiverPort)))
                    w.App.sender_text.insert(tkinter.END, 'Pachet: ' + s)
                if len(Algoritm_Tahoe.retransmit_packs) == 0:  # daca nu mai avem pachete de retransmisie
                    Algoritm_Tahoe.send_blocked = False
            Send.status.release()  # eliberez lock


class Receive(Thread):
    ACK_packs = []  # coada de ACK-uri primite
    last_ACK = [0, ' ']
    wait_time = [0]  # timp de asteptare
    status = Condition()

    def __init__(self):
        super(Receive, self).__init__()

    def run(self):
        cnt = 0  # contor pentru a afla cat timp am de asteptat pana a primi ceva
        while w.running:
            print("Receive")
            Receive.status.acquire()  # primesc lock
            if not w.Socket.flag:  # verific daca s-a apasat butonul de start
                Receive.status.wait()
            s = select.select([w.Socket.UDPServerSock], [], [], 1)  # timeout de 1 secunda
            # select= functie de a verifica daca socket-ul are date in buffer de receptie
            if not s:
                cnt += 1  # incrementez contorul
            else:  # primesc pe socket ceva
                data, address = w.Socket.UDPServerSock.recvfrom(w.Socket.bufferLen)
                string = str(data).split('|')[1]  # convertesc in string si prelucrez textul
                w.App.sender_text.insert(tkinter.END, string)
                ACK_Process.Duplicated_ACK(string)  # verific daca avem duplicari si daca nu avm retransmisise
                Algoritm_Tahoe.fast_retransmit()
                Receive.ACK_packs += [string]  # inserez in coada de prelucrare
                ACK_Process.status.acquire()  # dau lock-ul thread-ului de prelucrare ACK
                ACK_Process.status.notify()  # il anunt ca poate sa-si faca treaba
                ACK_Process.status.release()  # eliberez lock
                Receive.wait_time.insert(0, cnt)  # resetez contorul
            Receive.status.release()  # eliberez lock


class ACK_Process(Thread):
    status = Condition()

    def __init__(self):
        super(ACK_Process, self).__init__()

    def run(self):
        while w.running:  # rulez pana la infinit
            print("ACK Process")
            ACK_Process.status.acquire()  # primesc lock
            if len(Receive.ACK_packs) == 0:  # astept cat timp nu avem ACK-uri
                ACK_Process.status.wait()
            else:
                string = Receive.ACK_packs.pop(0)
                # scot din pachete neconfirmate cel pentru care am primit ACK
                for i in range(0, len(Algoritm_Tahoe.unconfirmed_packs)):
                    p = Algoritm_Tahoe.unconfirmed_packs[i]
                    nr = p.split('|')[0]  # numarul pachetului
                    if nr == string:
                        Algoritm_Tahoe.last_ACK[0] = Algoritm_Tahoe.unconfirmed_packs.pop(i)
                        break
                if len(Algoritm_Tahoe.unconfirmed_packs) == 0:
                    Algoritm_Tahoe.slow_start()  # daca nu mai avem pachete neconfirmate, voi creste cwnd
            ACK_Process.status.release()  # eliberez lock

    @staticmethod
    def Duplicated_ACK(string):
        # verificam daca avem mai multe ACK-uri pentru un pachet
        if string == Receive.last_ACK[1]:
            Receive.last_ACK[0] += 1  # incrementez contorul
        else:
            Receive.last_ACK[0] = 0
            Receive.last_ACK[1] = string


class Prelucrare_Thread(Thread):
    read_status = Condition()  # o variabila de conditie pentru sincronizarea thread-ului de citire
    packs = []  # coada de pachete prelucrate

    def __init__(self):
        super(Prelucrare_Thread, self).__init__()  # constructor din clasa parinte

    def run(self):  # supraincarc din threading.Thread
        while w.running:  # astept la infinit pana apare vreo problema
            print("Prelucrare Thread")
            Prelucrare_Thread.read_status.acquire()  # primesc lock
            txt = w.App.getTextfromFile(w.App.path)  # prelucrez continutul fisierului
            w.App.packs = w.App.format_packs(txt)  # impartim in pachete
            w.App.packs = w.App.add_limits()  # adaug pachetele de start si stop
            Prelucrare_Thread.packs = w.App.packs
            if w.Socket.flag:
                Send.status.acquire()  # de acum thread-ul poate sa isi inceapa treaba
                Send.status.notify()
                Send.status.release()
            Prelucrare_Thread.read_status.release()  # eliberez lock
