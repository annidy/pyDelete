# -*- coding: utf8 -*-
import ntfs
import io
import logging
import itertools
from construct import *
from struct import *
import adapter
import win32file, winioctlcon, win32api

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
					filename='c:\pyDelete.log',
                    filemode='w+')


class NTFSVolume(object):
    """Volume object, support read / write and some basic function"""
    def __init__(self, vol):
        """init the NTFSVolume, open a volume
        :param vol: the volume name or drive letter which opened
        """
        self._cache = []
        self._cache_pos = -1
        logging.info('open volume %s'%vol)
        self.vh = win32file.CreateFile(vol,                                                 #fileName
                                       win32file.GENERIC_WRITE|win32file.GENERIC_READ,      #desiredAccess
                                       win32file.FILE_SHARE_WRITE|win32file.FILE_SHARE_READ,#shareMode 
                                       None,                                                #attributes 
                                       win32file.OPEN_EXISTING,                             #CreationDisposition 
                                       0,                                                   #flagsAndAttributes
                                       None,                                                #hTemplateFile 
                                       )
        if not self.isXp():
            logging.info('Not Xp')
            win32file.DeviceIoControl(self.vh, winioctlcon.FSCTL_LOCK_VOLUME, None, None)
        self.dbr = ntfs.dbr.parse(self.raw_read(0, 512))        
        logging.debug(self.dbr)
        self.cluster_size = self.dbr.BPB.bytes_per_sector * self.dbr.BPB.sectors_per_cluster

    def __del__(self):
        if self.vh:
            win32file.CloseHandle(self.vh)

    def isXp(self):
        (majorVer, minorVer, _1, _2, _3) = win32api.GetVersionEx()
        if (majorVer > 5) or ((majorVer == 5) and (minorVer >= 1)):
            return False
        else:
            return True

    def total_mft(self):
        """ return the total mftno.
        """
        try:
            mftsize = adapter.DataAdapter(self.read_mft(0))
            return mftsize.get_size() / 1024
        except adapter.AdapterException:
            return 0
    
    def read_mft(self, mftno):
        """read a mft and return MFTRecord
        :param mftno: MFT Record Number
        :return: MFTRecord object
        """
        assert mftno >= 0
        try:
            off = self.dbr.mft_len * self.cluster_size
            MFT = self.raw_read(off+mftno*1024, 1024)
            return MFTRecord(MFT)
        except AdaptationError:
            print 'MFT#%d is not a mft'%mftno
        
    def raw_read(self, off, size):
        """
        :return: buf what is read
        """
        if off < self._cache_pos or off+size > self._cache_pos+len(self._cache):
            win32file.SetFilePointer(self.vh, off, win32file.FILE_BEGIN)
            _, buf = win32file.ReadFile(self.vh, 1024*1024) # Cache for 1M
            self._cache_pos = off
            self._cache = list(buf)
            print 'Page fault.'
        return ''.join(self._cache[(off-self._cache_pos):(off-self._cache_pos+size)])
    
    def raw_write(self, off, size):
        """
        :return: size has written
        """
        win32file.SetFilePointer(self.vh, off, win32file.FILE_BEGIN)
        _, rsize  = win32file.WriteFile(self.vh, '\x00'*size)
        return rsize
    
    def read_cluster(self, cluster, size=1):
        return self.raw_read(self.cluster_size*cluster, self.cluster_size*size)
    
    def shred(self, mftno, filled):
        logging.error('shred MFT#%d [%d]'%(mftno, filled))
        off = self.dbr.mft_len * self.cluster_size
        self.raw_write(off+mftno*1024, 1024)
    
class MFTRecord(object):
    """MFT algriothm"""
    attr_map = {ntfs.STANDARD_INFORMATION: ntfs.std_info,
                ntfs.FILE_NAME_ATTR: ntfs.file_name_attr,
                ntfs.DATA: ntfs.data_attr,}
    def __init__(self, MFT):
        """:param MFT: the record data"""
        self.mft = ntfs.mft_record.parse(MFT)
        self.next_attr = self.mft.attrs_offset
        self.MFT = MFT

    def next(self):
        """Enumater
        :return: (record data, struct object)
        """
        while self.next_attr < self.mft.bytes_in_use and unpack('i', self.MFT[self.next_attr:self.next_attr+4])[0] != -1:
            try:
                attr_record = ntfs.attr_record.parse(self.MFT[self.next_attr:])
                self.next_attr += attr_record.length
                return attr_record, self.attr_map[attr_record.type].parse(attr_record.attr_data)
            except KeyError:
                logging.info("unknown attribute type: %s"%hex(attr_record.type))
                continue
            except Exception, e:
                print e
                raise StopIteration
        else:
            raise StopIteration

    def __iter__(self):
        self.next_attr = self.mft.attrs_offset
        return self

    def get_attr_list(self, type):
        """ get user define type attribute.
        :return: if the type(s) is undefined, return None
        """
        return [a for a in self if a[0].type == type]
