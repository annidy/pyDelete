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
        hlist = self.hlist        
        for mfti in self.model.enum_mft(isFile=False, isDel=False):        
            path = self.model.find_path(mfti)
            if mfti.isDir:
                self.build_dir(path, mfti)
            else:
                self.build_file(path, mfti)
            
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