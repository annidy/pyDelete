# -*- coding: utf8 -*-
__author__ = 'fengxing'
from datetime import datetime, timedelta
import ntfs

class AdapterException(Exception):
    pass

class FileNameAdapter(object):
    def __init__(self, mft):
        """
        :param mft: MFTRecord
        """
        attrs = mft.get_attr_list(ntfs.FILE_NAME_ATTR)
        if not attrs:
            raise AdapterException('No File Name Attribute')
        self.attrs = [attr[0] for attr in attrs]
        self.file_name_attrs = [attr[1] for attr in attrs]

    def get_dos_name(self):
        """get short file name
        """
        for file_name_attr in self.file_name_attrs:
            if file_name_attr.file_name_type == "DOS" or file_name_attr.file_name_type == 'WIN32_AND_DOS':
                if not file_name_attr.file_name:
                    continue # ignore no name
                return file_name_attr.file_name
        else:
            raise AdapterException('No File Name')
        
    def get_name(self):
        """get the name showing in system, default win32 name.
        if not file, return dos name
        :return: str
        """
        for file_name_attr in self.file_name_attrs:
            if not file_name_attr.file_name:
                continue # ignore no name
            if file_name_attr.file_name_type == "WIN32" or file_name_attr.file_name_type == 'WIN32_AND_DOS':
                return file_name_attr.file_name.encode('utf8', 'ignore')
        else:
            return self.get_dos_name()
    
    def get_parent(self):
        """Get parent cnid(mft)"""
        return self.file_name_attrs[0].parent_directory
    

class StdInfoAdapter(object):
    tv = 10000000
    def __init__(self, mft):
        attrs = mft.get_attr_list(ntfs.STANDARD_INFORMATION)
        if not attrs:
            raise AdapterException('No Standard information')
        self.attr = attrs[0][0]
        self.std_info_attr = attrs[0][1]
        
    def nt2datetime(self, timesptamp):
        time = datetime.utcfromtimestamp(timesptamp/self.tv)
        return time.replace(year=time.year-369)

    def get_creation_time(self):
        """return datetime of file create"""
        return self.nt2datetime(self.std_info_attr.creation_time)

    def get_changed_time(self):
        """return datetime of file change"""
        return self.nt2datetime(self.std_info_attr.last_data_change_time)

    def get_access_time(self):
        """return datetime of file access"""
        return self.nt2datetime(self.std_info_attr.last_access_time)

class DataAdapter(object):
    def __init__(self, mft):
        attrs = mft.get_attr_list(ntfs.DATA)
        if not attrs:
            raise AdapterException('No Data Attribute')
        self.attr = attrs[0][0]
        self.data = attrs[0][1]
        
    def get_size(self):
        """return the file size"""
        if self.attr.non_resident:
            return self.attr.data_size
        else:
            return len(self.data.data)