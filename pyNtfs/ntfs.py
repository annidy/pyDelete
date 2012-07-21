# -*- code: utf8 -*-
# author: fengxing <annidy@gmail.com>
# date: 2012-6-30

from construct import *



# see layout.h in ntfs-3g 
bpb = Struct('BPB',
             ULInt16('bytes_per_sector'),
             ULInt8('sectors_per_cluster'),
             ULInt16('reserved_sectors'),
             ULInt8('fats'),
             ULInt16('root_entries'),
             ULInt16('sectors'),
             ULInt8('media_type'),
             ULInt16('sectors_per_fat'),
             ULInt16('sectors_per_track'),
             ULInt16('heads'),
             ULInt32('hidden_sectors'),
             ULInt32('large_sectors'),
             )

dbr = Struct("DBR",
            Field('jump', 3),
            String('oem_id', 8),
            bpb,
            ULInt8('physical_drive'),
            ULInt8('current_head'),
            ULInt8('extended_boot_signature'),
            Padding(1), #Field('reserved2', 1),
            SLInt64('number_of_sectors'),
            SLInt64('mft_len'),
            SLInt64('mftmirr_len'),
            SLInt8('clusters_per_mft_record'),
            Padding(3), #Field('reserved0', 3),
            SLInt8('clusters_per_index_record'),
            Padding(3), #Field('reserved1', 3),
            ULInt64('volume_serial_number'),
            ULInt32('checksum'),
            HexDumpAdapter(Bytes('bootstrap', 426)),
            Const(ULInt16('signature'), 0xaa55)
            )

mft_record = Struct('MFTRecord',
                    Const(String('magic', 4), 'FILE'),
                    ULInt16('usa_ofs'),
                    ULInt16('usa_count'),
                    ULInt64('lsn'),
                    ULInt16('sequence_number'),
                    ULInt16('link_count'),
                    ULInt16('attrs_offset'),
                    BitStruct('record_flags',
                            Padding(6),
                            Flag('IS_DIR'),
                            Flag('IN_USE'),
                            Padding(8),
                            ),
                    ULInt32('bytes_in_use'),
                    ULInt32('bytes_allocated'),
                    ULInt64('base_mft_record'),
                    ULInt16('next_attr_instance'),
                    Padding(2), #ULInt16('reserved'),
                    ULInt32('mft_record_number'),
                    )

resident_attr = Struct('resident_attr',
                        ULInt32('value_length'),
                        ULInt16('value_offset'),
                        ULInt8('resident_flags'),
                        Padding(1),
                        String('name', lambda ctx: ctx['name_length']*2, encoding='utf16'),
                        Field(('attr_data'), lambda ctx: ctx['length']-ctx['name_length']*2-0x18),
                        )
nonresident_attr = Struct('non-resident_attr',
                            ULInt64('lowest_vcn'),
                            ULInt64('highest_vcn'),
                            ULInt16('mapping_pairs_offset'),
                            ULInt8('compression_unit'),
                            Padding(5),
                            SLInt64('allocated_size'),
                            SLInt64('data_size'),
                            SLInt64('initialized_size'),
                            String('name', lambda ctx: ctx['name_length']*2, encoding='utf16'),
                            Field(('attr_data'), lambda ctx: ctx['length']-ctx['name_length']*2-0x40),
                            )
attr_record = Struct('ATTRRecord',
                     NoneOf(ULInt32('type'), [0xFFFFFFFF]),
                     ULInt32('length'),
                     ULInt8('non_resident'),
                     ULInt8('name_length'),
                     ULInt16('name_offset'),
                     BitStruct('flags',
                                Padding(14),
                                Flag('IS_ENCRYPTED'),
                                Flag('IS_SPARSE'),
                                ),
                     ULInt16('instance'),
                     If(lambda ctx: ctx['non_resident'] == 0, Embedded(resident_attr)),
                     If(lambda ctx: ctx['non_resident'] != 0, Embedded(nonresident_attr)),
                     )

dos_file_attribute = BitStruct('file_attributes',
                                Flag('READONLY'),
                                Flag('HIDDEN'),
                                Flag('SYSTEM'),
                                Padding(2),
                                Flag('ARCHIVE'),
                                Flag('DEVICE'),
                                Flag('NORMAL'),
                                Flag('TEMPORARY'),
                                Flag('SPARSE_FILE'),
                                Flag('REPARSE_POINT'),
                                Flag('COMPRESSED'),
                                Flag('OFFLINE'),
                                Flag('NOT_CONTENT_INDEXED'),
                                Flag('ENCRYPTED'),
                                Padding(17),
                                )

STANDARD_INFORMATION = 0x10
std_info = Struct('STANDARD_INFORMATION', # 0x10
                    SLInt64('creation_time'),
                    SLInt64('last_data_change_time'),
                    SLInt64('last_mft_change_time'),
                    SLInt64('last_access_time'),
                    Embedded(dos_file_attribute),
                    )

FILE_NAME_ATTR = 0x30
file_name_attr = Struct('FILE_NAME_ATTR',
                        ULInt32('parent_directory'),
                        Padding(4),
                        SLInt64('creation_time'),
                        SLInt64('last_data_change_time'),
                        SLInt64('last_mft_change_time'),
                        SLInt64('last_access_time'),
                        SLInt64('allocated_size'),
                        SLInt64('data_size'),
                        Embedded(dos_file_attribute),
                        ULInt32('reparse_point_tag'),
                        ULInt8('file_name_length'),
                        Enum(Byte('file_name_type'), POSIX=0x00, WIN32=0x01, DOS=0x02, WIN32_AND_DOS=0x03),
                        String('file_name', lambda ctx: ctx['file_name_length']*2, encoding='utf16')
                        )

DATA = 0x80
data_attr = Struct('DATA', OptionalGreedyRange(Byte('data')))