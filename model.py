# -*- coding:utf8 -*-
import pyNtfs.adapter as adapter
import pyNtfs.ntfs as ntfs
import logging

class MftItem(object):
    """ get every of it """
    def __init__(self, mftr):
        """
        :param mftr: MFTRecord
        """
        fn_attr_ad = adapter.FileNameAdapter(mftr)
        self.file_name = fn_attr_ad.get_name()
        self.parent = fn_attr_ad.get_parent()
        
        self.isDir = mftr.mft.record_flags.IS_DIR    # 1 = dir
        self.isInUse = mftr.mft.record_flags.IN_USE  # 0 = deleted
        self.mftno = mftr.mft.mft_record_number

    def under_root(self):
        return self.parent == 5

class MftModel(object):
    """Store all mft record find in volume"""
    def __init__(self):
        self.mfts_dict = {}
        self.root = ''

    def add(self, mftno, mftr):
        """ Add one mft record
        :param mftno: the mft number
        :param mftr: MFTRecord
        """
        try:
            mftitem = MftItem(mftr)
            if mftno == mftitem.mftno:
                self.mfts_dict[mftno] = mftitem
        except adapter.AdapterException, e:
            print e

    def enum_mft(self, isFile=True, isDel=True, isNormal=True):
        """ 
        :param isDel: Enum file all deleted? Defualt is Yes
        :param isFile: ignore folder if True
        :param isNormal: ignore meta record if True
        :return: MftItem
        """
        self._exists()
        for (mftno, item) in self.mfts_dict.items():
            if isFile and item.isDir:
                continue
            if isNormal:
                if mftno < 24:
                    continue
                if item.parent < 24 and item.parent != 5:
                    continue
            if isDel:
                if not item.isExists:                
                    yield item
            else:
                yield item
    
    def find_path(self, mftitem):
        """ Find one file(MftItem)'s full path 
        :return: full path
        """

        dirs = [mftitem.file_name]
        if not mftitem.under_root():
            mftitem = self.mfts_dict.get(mftitem.parent, None)
            while mftitem and mftitem.isDir:
                dirs.append(mftitem.file_name)
                if mftitem.under_root():
                    break
                mftitem = self.mfts_dict.get(mftitem.parent, None)
            else:
                dirs.append('??')
        dirs.append(self.root)
        dirs = dirs[-1::-1] # reverse        
        return '/'.join(dirs)        
    
    def get_parent(self, mfti):
        if mfti:
            return self.mfts_dict.get(mfti.parent, None)
        else:
            return None
    
    def mfti_exists(self, mfti):
        """ check if an exist mft """
        if mfti is None:
            return False
        elif not mfti.isInUse:
            return False
        elif mfti.parent == 5:
            return True
        
        parent = self.get_parent(mfti)
        if parent is None:
            return False
        elif hasattr(parent, 'isExist'):
            return parent.isExist
        else:
            return self.mfti_exists(parent)            
        
    def _exists(self):
        for item in self.mfts_dict.values():
            item.isExists = self.mfti_exists(item)