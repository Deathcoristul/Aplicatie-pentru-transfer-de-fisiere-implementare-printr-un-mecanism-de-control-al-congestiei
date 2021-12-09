from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import *
import subprocess

class App:
    SenderIP=''
    ReceiverIP=''
    SenderPort=0
    ReceiverPort=0
    PackLoss=0
    PackLen=0
    Threshold=0
    path=''
    text=''
    packs=[]
    def open_file(self):
        filename=askopenfilename()
        self.sender_text.insert(END,'S-a deschis:'+filename+'\n')
        self.path=filename

    def getTextfromFile(self):
        f=open(self.path)
        self.text=f.read()
        f.close()

    def splitText(self,text):
        for i in range(0,len(text),int(self.PackLen)):
            # daca nu se imparte exact dimensiunea textului cu dimensiunea pachetului facem ultimul sir cu cate caractere au mai ramas
            if(i+int(self.PackLen)>len(text)):
                pck=str(text[i:len(text)])
            else:
                pck=str(text[i:i+int(self.PackLen)])
            self.packs.insert(len(self.packs),pck) #inseram sirul in coada de pachete

    def format_packs(self):#nr.secventa+sir caractere
        vect=self.packs
        for i in range(0,len(vect)):
            vect[i]=str(i)+'|'+vect[i]
        self.packs=vect

    def add_limits(self):
        start_pck='Begin'+'|'+str(len(self.packs))#START si numarul de pachete transimise
        stop_pck='End'+'|'+str(len(self.text))#STOP si numarul de caractere transmise
        self.packs.insert(0,start_pck)
        self.packs.insert(len(self.packs),stop_pck)

    def check_string(self,text):
        buff=text.split('|')
        if(buff[0]=='START'):
            self.receiver_text.insert(END, 'A fost primit un pachet de Begin si se primesc ' + buff[1] + ' pachete.\n')
        if(buff[0]=='STOP'):
            self.receiver_text.insert(END, 'A fost primit un pachet de End si se primesc ' + buff[1] + ' caractere.\n')

    def __init__(self):
        self.interface=Tk()
        self.interface.title("Aplicatie pentru transfer de fisiere implementare printr-un mecanism de control al congestiei")
        self.interface.geometry("1350x400")
        self.interface.configure(bg='cyan')
        self.menu=Menu(self.interface)
        self.menu.add_command(label='About', command=self.AboutMenu)
        self.menu.add_command(label='Exit', command=self.interface.destroy)
        self.menu.config(bg='blue')
        self.interface.config(menu=self.menu)

        self.IPlist=[]
        self.getIPlist()

        #sender IP
        self.ip_sender_label=Label(self.interface,text='IP sursă', bg='cyan', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.ip_sender_label.place(x=0,y=20)
        self.ip_sender_text=ttk.Combobox(self.interface, textvariable='IP Sursa')
        self.ip_sender_text.place(x=175,y=23)
        self.ip_sender_text['values']=self.IPlist

        #sender port
        self.port_sender_label=Label(self.interface,text='Port sursă', bg='cyan', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.port_sender_label.place(x=0,y=60)
        self.port_sender_text=Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.port_sender_text.place(x=175, y=63)

        #receiver IP
        self.ip_receiver_label = Label(self.interface, text='IP receiver', bg='cyan', fg='Black',font=('ARIAL BLACK', 12, 'bold'))
        self.ip_receiver_label.place(x=0, y=100)
        self.ip_receiver_text = ttk.Combobox(self.interface, textvariable='IP Receiver')
        self.ip_receiver_text.place(x=175, y=103)
        self.ip_receiver_text['values'] = self.IPlist

        #receiver port
        self.port_receiver_label = Label(self.interface, text='Port receiver', bg='cyan', fg='Black',font=('ARIAL BLACK', 12, 'bold'))
        self.port_receiver_label.place(x=0, y=140)
        self.port_receiver_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.port_receiver_text.place(x=175, y=143)

        #procent pierdere pachet
        self.pack_loss_label = Label(self.interface, text='Pierdere pachet(%)', bg='cyan', fg='Black',font=('ARIAL BLACK', 12, 'bold'))
        self.pack_loss_label.place(x=0,y=180)
        self.pack_loss_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.pack_loss_text.place(x=175, y=183)

        #dimensiune pachet
        self.pack_dim_label = Label(self.interface, text='Dimensiune pachet', bg='cyan', fg='Black',font=('ARIAL BLACK', 12, 'bold'))
        self.pack_dim_label.place(x=0, y=220)
        self.pack_dim_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.pack_dim_text.place(x=175, y=223)

        #threshold(valoare de prag)
        self.threshold_label = Label(self.interface, text='Valoare de prag', bg='cyan', fg='Black',font=('ARIAL BLACK', 12, 'bold'))
        self.threshold_label.place(x=0, y=260)
        self.threshold_text = Entry(self.interface, bg='white', fg='Black', font=('ARIAL BLACK', 12, 'bold'))
        self.threshold_text.place(x=175, y=265)

        #caseta text pentru sender
        self.sender_label=Label(self.interface, text='Sender', bg='cyan', fg='Black',font=('ARIAL BLACK', 15, 'bold'))
        self.sender_label.place(x=575,y=0)
        self.sender_text=Text(self.interface, bg='green', fg='yellow', font=('Arial', 10, 'normal'), width=65, height=20)
        self.sender_text.place(x=400,y=35)

        #caseta text pentru receiver
        self.receiver_label = Label(self.interface, text='Receiver', bg='cyan', fg='Black',font=('ARIAL BLACK', 15, 'bold'))
        self.receiver_label.place(x=1050, y=0)
        self.receiver_text = Text(self.interface, bg='black', fg='white', font=('Arial', 10, 'normal'),width=65, height=20)
        self.receiver_text.place(x=870, y=35)

        #butoane
        self.start=Button(self.interface, text="Start",bg='lime', fg='black', font=('ARIAL BLACK', 12, 'bold'), width=10, height=1,
                          command=self.start)
        self.start.place(x=0,y=305)
        self.stop = Button(self.interface, text="Stop", bg='red', fg='black', font=('ARIAL BLACK', 12, 'bold'),width=10, height=1)
        self.stop.place(x=121, y=305)
        self.choose = Button(self.interface, text="Caută", bg='white', fg='black', font=('ARIAL BLACK', 12, 'bold'),width=10, height=1,
                             command=self.open_file)
        self.choose.place(x=242, y=305)

    def start(self):
        if self.path=='':
            messagebox.showinfo('Eroare','Nu exista fisier deschis.')
        self.SenderIP=self.ip_sender_text.get()
        self.ReceiverIP=self.ip_receiver_text.get()
        self.SenderPort=self.port_sender_text.get()#preluam valori din casete
        self.ReceiverPort=self.port_receiver_text.get()
        self.PackLoss=self.pack_loss_text.get()
        self.PackLen=self.pack_dim_text.get()
        self.Threshold=self.threshold_text.get()
        if not self.isNumber(self.PackLen):
            self.pack_dim_text.delete(0,'end')
        if not self.isNumber(self.Threshold):
            self.threshold_text.delete(0,'end')
        if not self.isProb(self.PackLoss):
            self.pack_loss_text.delete(0,'end')
        if not self.isIP(self.SenderIP):
            messagebox.showinfo('Error','IP-ul sender-ului nu este bun.')
        if not self.isIP(self.ReceiverIP):
            messagebox.showinfo('Error','IP-ul receiver-ului nu este bun.')
        self.getTextfromFile()
        self.splitText(self.text)
        self.format_packs()
        self.add_limits()
        for i in range(0, len(self.packs)):
            self.check_string(str(self.packs[i]))
        self.packs.clear()


    def getIPlist(self):
        data = str(subprocess.check_output('ipconfig'), 'UTF-8')#preluam ce se afiseaza pe terminal folosind comanda ipconfig
        DataList = data.splitlines()# impartim pe linii
        for line in DataList:# cautam linia care incepe cu IPv4 Address
            if line.find('IPv4 Address') != -1:#-1 adica nu se afla
                idx = line.find(':')# cautam caracterul ':'
                self.IPlist.append(line[idx + 2:])# copiem tot ce se afla dupa sirul ":  "

    def isNumber(self,num):
        for i in num: #num e de fapt un string
            if not (i >= '0' and i <= '9'):
                messagebox.showinfo('Eroare','Trebuie sa fie numar, nu cuvant!!')
                return False
        return True

    def isIP(self,IP):
        if IP.count('.')!=3:
            return False
        for number in IP.split('.'):
            if int(number)<0 or int(number)>255:
                return False
        for ch in range(0,len(IP)):
            if IP[ch] not in '0123456789.':
                return False
        return True

    def isPort(self,num):
        if(num[0]=='0'):
            messagebox.showinfo('Eroare','Un port nu poate fi 0!!')
            return False
        self.isNumber(num)

    def isProb(self,num):
        if(self.isNumber(num) and int(num)<100):
            self.PackLoss=int(num)/100
        else:
            messagebox.showinfo('Eroare','Probabilitatea nu e buna!!')
            return False
        return True

    def AboutMenu(self):
        messagebox.showinfo(title="About", message='Aceasta este o aplicație pentru proiectul de Rețele de Calculatoare.')

    def mainloop(self):
        self.interface.mainloop()