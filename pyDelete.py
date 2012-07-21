# -*- coding: utf8 -*-
import pyNtfs
import util
import Tkinter as Tk
import tkMessageBox
import threading
from model import MftModel
import Tix
from view import TreeView

class Application(Tk.Frame):
    def __init__(self, master):
        Tk.Frame.__init__(self, master)
        Tk.Label(master, text="Please select one volume to scan").pack()

        # HList
        fmb = Tk.Frame(master, relief=Tk.RAISED, bd=1, pady=5)
        self.hlist = Tix.HList(fmb, columns=3, header=True, width=40)
        hlist = self.hlist
        hlist.column_width(0, 80)
        hlist.column_width(1, 80)
        hlist.column_width(2, 80)
        hlist.header_create(0, text='Drive')
        hlist.header_create(1, text='Label')
        hlist.header_create(2, text='FileSystem')
        hlist.pack(expand=Tk.YES, fill=Tk.BOTH)
        fmb.pack(expand=Tk.YES, fill=Tk.BOTH)
        self.fill_hlist(hlist)

        Tk.Button(master, text="Scan", command=self.scan).pack(pady=5)
        
    def scan(self):
        now = self.hlist.info_selection()
        if not now:
            tkMessageBox.showwarning(message="Please select one driver first!")
        elif self.volumes[now[0]]['fs'] != 'NTFS':
            tkMessageBox.showwarning(message="Not support Non-NTFS!")
        else:
            try:
                ntfsvol = pyNtfs.NTFSVolume("\\\\.\\%c:"%now[0][0])
            except Exception, e:
                tkMessageBox.showwarning(message=e)
                return
            progress = ProgressGui(Tk.Toplevel(), now[0], ntfsvol)
            progress.start()
            self.after(100, self.wait_scan_finish, progress)
            self.master.withdraw() # hide 

    def fill_hlist(self, hlist):
        """ Fill the data of hlist """
        self.volumes = {}
        hlist.delete_all()
        for item in util.emun_volume():
            try:
                label, _1, _2, _3, fs = util.get_volume_information(item)
            except:
                continue # some exception happend when some driver
            
            if label:
                label = label.decode('gbk')
            else:
                label = 'Local Disk'
            # there was a design bug of Tix.HList, which can only add but can't get item!        
            self.volumes[item] = {'label':label, 'fs':fs}
            hlist.add(item, itemtype=Tix.TEXT, text=item)
            hlist.item_create(item, 1, text=label)
            hlist.item_create(item, 2, text=fs)

    def wait_scan_finish(self, progressgui):
        if progressgui.isAlive():
            self.after(200, self.wait_scan_finish, progressgui)
            return
        self.master.deiconify()
        ResaultGui(Tk.Toplevel(), progressgui.model, progressgui.ntfsvol)


class ProgressGui(threading.Thread):
    def __init__(self, master, device, ntfsvol):
        threading.Thread.__init__(self)
        self.model = MftModel()
        self.model.root = device[0]
        self.ntfsvol = ntfsvol

        master.title('Scaning...')
        self.canvas = Tk.Canvas(master, relief=Tk.GROOVE, width=400, height=50)
        self.canvas.pack()
        self.cancel = False
        Tk.Button(master, text='Cancel', command=self.exit).pack(pady=5)
        master.protocol("WM_DELETE_WINDOW", self.exit)

    def show(self, pos):
        """display progress
        :param percent: 0-100
        """
        self.canvas.create_rectangle(0, 0, 4*pos, 50, fill="blue")
    
    def run(self):
        total = self.ntfsvol.total_mft()
        #total = 200
        pos = 0
        for i in range(24, total):
            if self.cancel:
                break
            if pos < int(i*100/total):
                pos = pos + 1
                self.show(pos) # gui refresh cost time much!
            mftr = self.ntfsvol.read_mft(i)
            if mftr:
                self.model.add(i, mftr)
        else:
            self.canvas.master.after(100, self.exit)

    def exit(self):
        self.cancel = True
        self.join()
        self.canvas.master.destroy()
        
class ResaultGui(object):
    def __init__(self, master, model, ntfsvol):
        """
        :param model: MftModel object
        """
        self.ntfsvol = ntfsvol
        self.filled = Tk.IntVar()
        # Gui
        Tk.Label(master, text='Delete file/folder browse', width=80).pack()
        self.tree = TreeView(master, model, height=400)
        self.tree.pack(expand=Tk.YES, fill=Tk.BOTH, pady=5)
        fill_btn = Tk.Checkbutton(master, text='Fill data with zero', variable=self.filled, state=Tk.DISABLED)
        fill_btn.pack(side=Tk.LEFT, anchor=Tk.SW)
        Tk.Button(master, text='Shred', command=self.shared).pack(side=Tk.RIGHT, anchor=Tk.SE, padx=15, pady=5)
        
    def shared(self):
        """Shared file"""
        it = iter(self.tree.getselection('on'))
        try:
            while True:
                sel = next(it)
                if isinstance(sel, tuple):
                    sel = ' '.join(sel)
                else:
                    while self.tree.hlist.info_exists(sel) != u'1':
                        sel = sel + ' ' + next(it)
                mftno = int(self.tree.hlist.info_data(sel)) #info_data return unicode
                if mftno:
                    if self.tree.model.mfts_dict[mftno].isExists == False:
                        self.ntfsvol.shred(mftno, self.filled.get())
                        self.tree.hlist.delete_entry(sel)
                else:
                    self.tree.hlist.delete_entry(sel) # like DIRXXXX
        except StopIteration:
            return
    
root = Tix.Tk()
mainWindow = Application(root)
        
if __name__ == '__main__':
    root.mainloop()
