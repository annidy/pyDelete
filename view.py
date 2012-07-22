# -*- coding:utf8 -*-
__author__ = 'fengxing<annidy@gmail.com>'

import Tkinter as Tk
import Tix
import os

class TreeView(Tix.CheckList):
    def __init__(self, master, model, **kw):
        kw['options'] = 'hlist.separator /'
        Tix.CheckList.__init__(self, master, kw)
        self.model = model
        self.fileStyle = Tix.DisplayStyle(Tix.IMAGETEXT, refwindow=self.hlist, fg='red')
        self.folderStyle = Tix.DisplayStyle(Tix.IMAGETEXT, refwindow=self.hlist, fg='blue')
        self.build_tree()
        self.autosetmode()
        
    def build_tree(self):    
        for mfti in self.model.enum_mft(isFile=False, isDel=False):        
            try:
                path = self.model.find_path(mfti)
                if mfti.isDir:
                    self.build_dir(path, mfti)
                else:
                    self.build_file(path, mfti)
            except:
                continue
            
    def build_dir(self, path, mfti):
        """ Build 
        :return: True this dir is deled
        """
        hlist = self.hlist        
        parent = os.path.dirname(path)
        if parent and hlist.info_exists(parent)!= u'1': # ? bool
            self.build_dir(parent, self.model.get_parent(mfti))
            
        if hlist.info_exists(path) != u'1':
            if mfti == None:
                hlist.add(path, text=os.path.basename(path), style=self.folderStyle, data=0)
            elif mfti.isExists == False:
                hlist.add(path, text=os.path.basename(path), style=self.folderStyle, data=mfti.mftno)
            else:
                hlist.add(path, text=os.path.basename(path), data=mfti.mftno)
            self.setstatus(path, 'off')
        
    def build_file(self, path, mfti):
        hlist = self.hlist        
        parent = os.path.dirname(path)
        if parent and hlist.info_exists(parent) != u'1':
            self.build_dir(parent, self.model.get_parent(mfti))
            
        if hlist.info_exists(path) != u'1':
            if mfti.isExists == False:
                hlist.add(path, text=os.path.basename(path), style=self.fileStyle, data=mfti.mftno)
            else:
                hlist.add(path, text=os.path.basename(path), data=mfti.mftno)            
            self.setstatus(path, 'off')            

    def get_selects(self):
        """ Return selects """
        
        selects = []
        it = iter(self.getselection('on'))
        try:
            while True:
                # hack for full path
                sel = next(it)
                if isinstance(sel, tuple):
                    sel = ' '.join(sel)
                else:
                    while self.hlist.info_exists(sel) != u'1':
                        sel = sel + ' ' + next(it)
                selects.append(sel)
        except StopIteration:
            selects.sort()
            selects.reverse()
            return selects
                
