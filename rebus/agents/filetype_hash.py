#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import pytsk3
import magic
import hashlib
import sys


MAX_SIZE = 10000000

NTFS_TYPES_TO_PRINT = [
    pytsk3.TSK_FS_ATTR_TYPE_NTFS_IDXROOT,
    pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA,
    pytsk3.TSK_FS_ATTR_TYPE_DEFAULT,
]

@Agent.register
class FiletypeHash(Agent):
    _name_ = "filetype_hash"
    _desc_ = "Guess filetypes and hash PE files"

    def selector_filter(self, selector):
        return selector.startswith("slice_ntfs_partition/")

    def read_tsk_data(self, f):
        if not f.info.meta:
            print "\nWARNING: No meta for file %s\n" % f.info.name.name
            return ''

        offset = 0
        size = f.info.meta.size
        tsk_data = ''
        while offset < size:
            available_to_read = min(1024 * 1024, size - offset)
            data = f.read_random(offset, available_to_read)
            if not data: break
            offset += len(data)
            tsk_data += data

        return tsk_data

    def process_inode(self, f, prefix=''):
        for attr in f:
            if int(attr.info.type) in NTFS_TYPES_TO_PRINT:
                if attr.info.name and attr.info.name != "$Data" and attr.info.name != "$I30":
                    filename = "%s:%s" % (f.info.name.name, attr.info.name)
                else:
                    filename = f.info.name.name

                if filename == '.' or filename == '..':
                    sys.stderr.write('In process_inode, skipping %s\n' % filename)
                    continue

                full_path = os.path.join(self.mntpoint, prefix, filename).replace('\\', '/')
                #print "%s %d %d %s" % (full_path, f.info.meta.size, attr.info.flags, f.info.name.flags)

                if 0 < f.info.meta.size < MAX_SIZE:
                    tsk_data = self.read_tsk_data(f)
                    file_type = self.ms.buffer(tsk_data)
                    self.filetypes[full_path] = file_type

                    if file_type.startswith('PE32') and f.info.meta.size:
                        hasher = hashlib.md5()
                        hasher.update(tsk_data)
                        self.md5s[full_path] = hasher.hexdigest()

    def process_directory(self, directory, stack=None, prefix=None):
        stack.append(directory.info.fs_file.meta.addr)
        for f in directory:
            if f.info.name.name in ['.', '..']:
                continue

            if f.info.name.name in ['$AttrDef', '$Extend', '$MFTMirr', '$UpCase', '$Secure', '$BadClus', '$Boot', '$LogFile', '$MFT', '$Bitmap', '$Volume']:
                sys.stderr.write('skipping %s\n' % f.info.name.name)
                continue

            try:
                dir_ = f.as_directory()
                inode = f.info.meta.addr
                if inode not in stack:
                    prefix.append(f.info.name.name)
                    self.process_directory(dir_, stack, prefix)

            except IOError:
                try:
                    if f.info.meta:  # It may happend that as_directory() fails so we don't want a dir to be treated as a file, may need some improvements...
                        if f.info.meta.type != pytsk3.TSK_FS_META_TYPE_DIR:
                            self.process_inode(f, '/'.join(prefix))
                    else:
                        self.process_inode(f, '/'.join(prefix))

                except Exception, e:
                    msg = '%s for %s' % (','.join([repr(i) for i in e.args]), os.path.join('/'.join(prefix), f.info.name.name))
                    self.warnings.append(msg)
                    sys.stderr.write(msg+'\n')
                    import traceback
                    sys.stderr.write(traceback.format_exc()+'\n')

        if len(stack):
            stack.pop(-1)
        if len(prefix):
            prefix.pop(-1)

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print '\nProcessing slice %s' % case['slicenum']
        self.ms = magic.open(magic.MAGIC_NONE)
        self.ms.load()
        img = pytsk3.Img_Info(case['device'])
        fs = pytsk3.FS_Info(img)
        directory = fs.open_dir(path='/')
        self.warnings = []
        self.md5s = {}
        self.filetypes = {}
        self.mntpoint = case['slicenum']
        self.process_directory(directory, [], [])

        md5sfile = '%s_md5s.json' % case['slicenum']
        file('%s/hashes/%s_warnings.txt' % (case['casedir'], \
                case['slicenum']), 'w').write('\n'.join(self.warnings))
        file('%s/hashes/%s' % (case['casedir'], \
                md5sfile), 'w').write(json.dumps(self.md5s))
        file('%s/hashes/%s_filetypes.json' % (case['casedir'], \
                case['slicenum']), 'w').write(json.dumps(self.filetypes))

        desc = Descriptor(md5sfile, 'md5_list', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
