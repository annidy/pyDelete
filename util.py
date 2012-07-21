import win32api
import win32file

def emun_volume():
    """Get volume name in system
    :return: each item when called onec
    """
    drives = win32file.GetLogicalDrives()
    for i in range(32):
        if drives & (1<<i):
            v = '%c:\\'%(ord('a')+i)
            yield v
            
def get_volume_information(v):
    """Get volume information
    :param v: volume name, like c:\
    :return: a list [label, size, serial, used, filesystem]
    """
    return win32api.GetVolumeInformation(v)

def human_size(size):
    """Return readable size string"""
    if (size << 10) < 1024:
        return str(size)
    elif (size << 20) < 1024:
        return str(size<<10)+"K"
    elif (size << 30) < 1024:
        return str(size<<20)+"M"
    elif (size << 40) < 1024:
        return str(size<<30)+"G"
    else:
        return str(size<<40)+"T"