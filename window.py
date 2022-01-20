from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import *
import subprocess, socket, sender, receiver
import sys
import Tahoe

global running, started
started = False


class App:
    send = sender.Send()
    recv = sender.Receive()
    ACK_proc = sender.ACK_Process()
    process = sender.Prelucrare_Thread()
    send_ACK = receiver.Send_ACK()
    recv_data = receiver.Receive_Data()
    threadData = receiver.DataThread()
    sender_text = None
    receiver_text = None
    SenderIP = ''
    ReceiverIP = ''
    SenderPort = 0
    ReceiverPort = 0
    PackLoss = 0
    PackLen = 0
    Threshold = 0
    path = ''
    text = ''
    packs = []
    sent_packs = []
    status = 0  # 1-sender 2-receiver

    def open_file(self):
        filename = askopenfilename()
        App.sender_text.insert(END, 'S-a deschis:' + filename + '\n')
        App.path = filename

    @staticmethod
    def getTextfromFile(path):
        f = open(path)
        text = f.read()
        f.close()
        App.text = text
        return text

    @staticmethod
    def splitText(text):
        queue = []
        for i in range(0, len(text), int(App.PackLen)):
            # daca nu se imparte exact dimensiunea textului cu dimensiunea pachetului facem ultimul sir cu cate caractere au mai ramas
            if (i + int(App.PackLen) > len(text)):
                pck = str(text[i:len(text)])
            else:
                pck = str(text[i:i + int(App.PackLen)])
            queue.insert(len(App.packs), pck)  # inseram sirul in coada de pachete
        App.packs = queue
        return queue

    @staticmethod
    def format_packs(text):  # nr.secventa+sir caractere
        vect = App.splitText(text)
        for i in range(0, len(vect)):
            vect[i] = str(i) + '|' + vect[i]
        App.packs = vect
        return vect

    @staticmethod
    def add_limits():
        start_pck = 'Begin' + '|' + str(len(App.packs))  # Begin si numarul de pachete transimise
        App.packs.insert(0, start_pck)
        stop_pck = 'End' + '|' + str(len(App.text))  # End si numarul de caractere transmise
        App.packs.insert(len(App.packs), stop_pck)
        return App.packs

    @staticmethod
    def check_string(text):
        buff = text.split('|')
        if (buff[0] == 'Begin'):
            App.receiver_text.insert(END, 'A fost primit un pachet de Begin si se primesc ' + buff[1] + ' pachete.\n')
        elif (buff[0] == 'End'):
            App.receiver_text.insert(END, 'A fost primit un pachet de End si se primesc ' + buff[1] + ' caractere.\n')
        return buff

    def __init__(self):
        self.interface = Tk()
        self.interface.title(
            "Aplicatie pentru transfer de fisiere implementare printr-un mecanism de control al congestiei")
        self.interface.geometry("1350x400")
        self.interface.configure(bg='cyan')
        self.menu = Menu(self.interface)
        self.menu.add_command(label='About', command=self.AboutMenu)
        self.menu.add_command(label='Exit', command=self.interface.destroy)
        self.menu.config(bg='blue')
        self.interface.config(menu=self.menu)

        self.IPlist = []
        self.getIPlist()

        # sender IP
        self.ip_sender_label = Label(self.interface, text='IP sursă', bg='cyan', fg='Black',
                                     font=('ARIAL BLACK', 12, 'bold'))
        self.ip_sender_label.place(x=0, y=20)
        self.ip_sender_text = ttk.Combobox(self.interface, textvariable='IP Sursa')
        self.ip_sender_text.place(x=175, y=23)
        self.ip_sender_text['values'] = self.IPlist
        self.ip_sender_text.set('127.0.0.1')  # setam valori implicite

        # sender port
        self.port_sender_label = Label(self.interface, text='Port sursă', bg='cyan', fg='Black',
                                       font=('ARIAL BLACK', 12, 'bold'))
        self.port_sender_label.place(x=0, y=60)
        self.port_sender_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.port_sender_text.place(x=175, y=63)
        self.port_sender_text.insert(END, '20001')

        # receiver IP
        self.ip_receiver_label = Label(self.interface, text='IP receiver', bg='cyan', fg='Black',
                                       font=('ARIAL BLACK', 12, 'bold'))
        self.ip_receiver_label.place(x=0, y=100)
        self.ip_receiver_text = ttk.Combobox(self.interface, textvariable='IP Receiver')
        self.ip_receiver_text.place(x=175, y=103)
        self.ip_receiver_text['values'] = self.IPlist
        self.ip_receiver_text.set('127.0.0.1')

        # receiver port
        self.port_receiver_label = Label(self.interface, text='Port receiver', bg='cyan', fg='Black',
                                         font=('ARIAL BLACK', 12, 'bold'))
        self.port_receiver_label.place(x=0, y=140)
        self.port_receiver_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.port_receiver_text.place(x=175, y=143)
        self.port_receiver_text.insert(END, '20001')

        # procent pierdere pachet
        self.pack_loss_label = Label(self.interface, text='Pierdere pachet(%)', bg='cyan', fg='Black',
                                     font=('ARIAL BLACK', 12, 'bold'))
        self.pack_loss_label.place(x=0, y=180)
        self.pack_loss_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.pack_loss_text.place(x=175, y=183)
        self.pack_loss_text.insert(END, '5')
        # dimensiune pachet
        self.pack_dim_label = Label(self.interface, text='Dimensiune pachet', bg='cyan', fg='Black',
                                    font=('ARIAL BLACK', 12, 'bold'))
        self.pack_dim_label.place(x=0, y=220)
        self.pack_dim_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.pack_dim_text.place(x=175, y=223)
        self.pack_dim_text.insert(END, '2')

        # threshold(valoare de prag)
        self.threshold_label = Label(self.interface, text='Valoare de prag', bg='cyan', fg='Black',
                                     font=('ARIAL BLACK', 12, 'bold'))
        self.threshold_label.place(x=0, y=260)
        self.threshold_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.threshold_text.place(x=175, y=265)
        self.threshold_text.insert(END, str(Tahoe.Algoritm_Tahoe.ssthresh))

        # caseta text pentru sender
        self.sender_label = Label(self.interface, text='Sender', bg='cyan', fg='Black',
                                  font=('ARIAL BLACK', 15, 'bold'))
        self.sender_label.place(x=575, y=0)
        App.sender_text = Text(self.interface, bg='green', fg='yellow', font=('Arial', 10, 'normal'), width=65,
                               height=20)
        App.sender_text.place(x=400, y=35)

        # caseta text pentru receiver
        self.receiver_label = Label(self.interface, text='Receiver', bg='cyan', fg='Black',
                                    font=('ARIAL BLACK', 15, 'bold'))
        self.receiver_label.place(x=1050, y=0)
        App.receiver_text = Text(self.interface, bg='black', fg='white', font=('Arial', 10, 'normal'), width=65,
                                 height=20)
        App.receiver_text.place(x=870, y=35)

        # butoane
        self.start = Button(self.interface, text="Start", bg='lime', fg='black', font=('ARIAL BLACK', 12, 'bold'),
                            width=10, height=1,
                            command=self.start)
        self.start.place(x=0, y=305)
        self.stop = Button(self.interface, text="Stop", bg='red', fg='black', font=('ARIAL BLACK', 12, 'bold'),
                           width=10, height=1, command=self.stop)
        self.stop.place(x=121, y=305)
        self.choose = Button(self.interface, text="Caută", bg='white', fg='black', font=('ARIAL BLACK', 12, 'bold'),
                             width=10, height=1,
                             command=self.open_file)
        self.choose.place(x=242, y=305)

        self.sender_btt = Button(self.interface, text="Set Sender", bg='grey', fg='black',
                                 font=('ARIAL BLACK', 12, 'bold'), width=10, height=1,
                                 command=self.set_sender)
        self.sender_btt.place(x=0, y=350)
        self.receiver_btt = Button(self.interface, text="Set Receiver", bg='grey', fg='black',
                                   font=('ARIAL BLACK', 12, 'bold'), width=10, height=1,
                                   command=self.set_receiver)
        self.receiver_btt.place(x=121, y=350)

    def set_sender(self):
        if App.status == 1:
            messagebox.showinfo('Avertisment', 'Este setat deja pe SENDER.')
        else:
            App.status = 1
            App.sender_text.insert(END, 'S-a schimbat pe SENDER.\n')

    def set_receiver(self):
        if App.status == 2:
            messagebox.showinfo('Avertisment', 'Este setat deja pe RECEIVER.')
        else:
            App.status = 2
            App.sender_text.insert(END, 'S-a schimbat pe RECEIVER.\n')

    def start(self):
        global running, started
        running = True

        if App.status == 0:
            messagebox.showinfo('Eroare', 'N-ai setat postul.')
            return
        if App.path == '':
            messagebox.showinfo('Eroare', 'Nu exista fisier deschis.')
            return
        App.SenderIP = self.ip_sender_text.get()
        App.ReceiverIP = self.ip_receiver_text.get()
        App.SenderPort = self.port_sender_text.get()  # preluam valori din casete
        App.ReceiverPort = self.port_receiver_text.get()
        App.PackLoss = self.pack_loss_text.get()
        App.PackLen = self.pack_dim_text.get()
        App.Threshold = self.threshold_text.get()
        Tahoe.Algoritm_Tahoe.ssthresh = int(self.threshold_text.get())
        if not self.isNumber(App.PackLen):
            self.pack_dim_text.delete(0, 'end')
            return
        if not self.isNumber(App.Threshold):
            self.threshold_text.delete(0, 'end')
            return
        if not self.isProb(App.PackLoss):
            self.pack_loss_text.delete(0, 'end')
            return
        if not self.isIP(App.SenderIP):
            messagebox.showinfo('Error', 'IP-ul sender-ului nu este bun.')
            return
        if not self.isIP(App.ReceiverIP):
            messagebox.showinfo('Error', 'IP-ul receiver-ului nu este bun.')
            return

        if App.status == 1:
            Socket.sender_init()
            # sender
            if not started:
                started = True
                App.process.start()
                App.send.start()
                App.recv.start()
                App.ACK_proc.start()

        else:
            Socket.receiver_init()
            # receiver
            if not started:
                started = True
                App.recv_data.start()
                App.threadData.start()
                App.send_ACK.start()

        """self.getTextfromFile(App.path)
        self.splitText(App.text)
        self.format_packs(App.text)
        self.add_limits()
        for i in range(0, len(self.packs)):
            self.check_string(str(self.packs[i]))"""
        # self.packs.clear()

    def stop(self):
        global running
        running = False
        """if App.status == 1:
            App.process.join()
            App.send.join()
            App.recv.join()
            App.ACK_proc.join()
        else:
            App.threadData.join()
            App.send_ACK.join()
            App.recv_data.join()"""

    def getIPlist(self):
        data = str(subprocess.check_output('ipconfig'),
                   'UTF-8')  # preluam ce se afiseaza pe terminal folosind comanda ipconfig
        DataList = data.splitlines()  # impartim pe linii
        for line in DataList:  # cautam linia care incepe cu IPv4 Address
            if line.find('IPv4 Address') != -1:  # -1 adica nu se afla
                idx = line.find(':')  # cautam caracterul ':'
                self.IPlist.append(line[idx + 2:])  # copiem tot ce se afla dupa sirul ":  "

    @staticmethod
    def isNumber(num):
        for i in num:  # num e de fapt un string
            if not (i >= '0' and i <= '9'):
                messagebox.showinfo('Eroare', 'Trebuie sa fie numar, nu cuvant!!')
                return False
        return True

    @staticmethod
    def isIP(IP):
        if IP.count('.') != 3:
            return False
        for number in IP.split('.'):
            if int(number) < 0 or int(number) > 255:
                return False
        for ch in range(0, len(IP)):
            if IP[ch] not in '0123456789.':
                return False
        return True

    @staticmethod
    def isPort(num):
        if num[0] == '0':
            messagebox.showinfo('Eroare', 'Un port nu poate fi 0!!')
            return False
        App.isNumber(num)
        return True

    @staticmethod
    def isProb(num):
        if App.isNumber(num) and int(num) < 100:
            App.PackLoss = int(num) / 100
        else:
            messagebox.showinfo('Eroare', 'Probabilitatea nu e buna!!')
            return False
        return True

    def AboutMenu(self):
        messagebox.showinfo(title="About",
                            message='Aceasta este o aplicație pentru proiectul de Rețele de Calculatoare.')

    def mainloop(self):
        try:
            self.interface.mainloop()
        except KeyboardInterrupt:
            if App.status == 1:
                App.process.join()
                App.send.join()
                App.recv.join()
                App.ACK_proc.join()
            elif App.status == 2:
                App.recv_data.join()
                App.threadData.join()
                App.send_ACK.join()
            sys.exit()

    @staticmethod
    def number_pack(string):  # functie de a afisa pe interfata doar nr pachetului
        if string[1] == '\'':
            s = string.split('\'')
            aux = s[1].split('|')
            if aux[0] == 'Begin':
                return 'deschis: ' + aux[1][0:len(aux[1]) - 1]
            elif aux[0] == 'End':
                return 'inchis: ' + aux[1][0:len(aux[1]) - 1]
            else:
                return aux[0]
        else:
            print("EROARE")
            return "Niciun numar"


class Socket:
    bufferLen = 1024  # dimensiune port
    UDPServerSock = None
    flag = False  # daca conexiunea la socket s-a facut sau nu.

    @staticmethod
    def sender_init():
        if Socket.flag:  # vedem daca s-a apasat de mai multe ori
            return
        Socket.flag = True
        # creez socket-ul
        Socket.UDPServerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Socket.UDPServerSock.bind((App.SenderIP, int(App.SenderPort)))
        App.recv.status.acquire()  # thread-urile isi pot incepe treaba
        App.recv.status.notify()
        App.recv.status.release()

        App.send.status.acquire()
        App.send.status.notify()
        App.send.status.release()

    @staticmethod
    def receiver_init():
        if Socket.flag:  # vedem daca s-a apasat de mai multe ori
            return
        Socket.flag = True
        # creez socket-ul
        Socket.UDPServerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        Socket.UDPServerSock.bind((App.ReceiverIP, int(App.ReceiverPort)))
        App.recv_data.status.acquire()
        App.recv_data.status.notify()
        App.recv_data.status.release()

        App.send_ACK.status.acquire()
        App.send_ACK.status.notify()
        App.send_ACK.status.release()
