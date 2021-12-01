import tkinter
from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showinfo
from tkinter.filedialog import *
class App(Tk):
    def button_clicked(self):
        Tk().withdraw()
        filename=askopenfilename()
        self.text.delete('1.0',END)
        self.text.insert(END,filename)#print(filename)
    def __init__(self):
        super().__init__()
        super().title("Aplicatie pentru transfer de fisiere implementare printr-un mecanism de control al congestiei")
        self.geometry=('1900x700')
        self.label=ttk.Label(self,text='Salut!')
        self.label.pack()
        self.text=Text(self,height=1)
        self.text.pack(side=tkinter.LEFT)
        self.button=ttk.Button(self,text='Choose',command=self.button_clicked)
        self.button.pack()

