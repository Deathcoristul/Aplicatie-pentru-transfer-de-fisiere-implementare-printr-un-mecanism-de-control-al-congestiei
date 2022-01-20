import sender
import window as w


class Algoritm_Tahoe:
    ssthresh = 30  # int(window.App.Threshold)  # valoarea de prag
    cwnd = 1  # dimensiunea initiala a ferestrei
    unconfirmed_packs = []
    wait_time = 15
    retransmit_packs = []  # pachete ce vor fi retrimise
    send_blocked = False  # flag care arata daca este blocata trimiterea
    last_ACK = ['0']

    @staticmethod
    def slow_start():
        # determinarea dimensiunii ferestrei congestiei
        if Algoritm_Tahoe.ssthresh > Algoritm_Tahoe.cwnd:
            Algoritm_Tahoe.cwnd *= 2  # crestere exponentiala
        else:
            Algoritm_Tahoe.cwnd += 1  # crestere liniara

    @staticmethod
    def fast_retransmit():
        print('Am intrat in trimitere')
        print('timp_asteptare=' + str(sender.Receive.wait_time[0]))
        print(sender.Receive.last_ACK)
        # se verifica conditiile pt existenta congestiei
        if (Algoritm_Tahoe.wait_time < sender.Receive.wait_time[0]) or (sender.Receive.last_ACK[0] == 3):
            # congestie detectata
            w.App.recv.wait_time.insert(0, 0)  # modific timpul de asteptare
            if Algoritm_Tahoe.cwnd > 1:
                Algoritm_Tahoe.ssthresh = Algoritm_Tahoe.cwnd / 2  # pragul va fi jumatatea dimensiunii ferestrei la care s-a ajuns
            Algoritm_Tahoe.cwnd = 1  # se va reseta dimensiunea la 1
            if len(Algoritm_Tahoe.unconfirmed_packs) == 1:
                el = Algoritm_Tahoe.unconfirmed_packs.pop(0)  # mut pachetele neconfirmate
                Algoritm_Tahoe.retransmit_packs.append(el)  # in colectia de pachete de retransimisie
            if len(Algoritm_Tahoe.unconfirmed_packs):
                for i in range(0, len(Algoritm_Tahoe.unconfirmed_packs)):
                    el = Algoritm_Tahoe.unconfirmed_packs.pop(0)
                    Algoritm_Tahoe.retransmit_packs.append(el)
            print('Coada de pachete retransmise:')
            print(Algoritm_Tahoe.retransmit_packs)
            Algoritm_Tahoe.unconfirmed_packs = []  # resetez pe vid
            Algoritm_Tahoe.send_blocked = True  # flag pt determinarea congestiei
            w.App.recv.last_ACK[0] = 0  # resetez datele
            w.App.recv.last_ACK[1] = ' '
            return True  # am determinat congestia
        Algoritm_Tahoe.send_blocked = False  # in cazul in care n-am detectat congestia
        return False
