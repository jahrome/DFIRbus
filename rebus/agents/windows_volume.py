#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import pytsk3
import subprocess


@Agent.register
class WindowsPartition(Agent):
    _name_ = "windows_volume"
    _desc_ = "Detect and extract Windows OS related files"

    def selector_filter(self, selector):
        return selector.startswith("slice_ntfs_partition/")

    def read_tsk_data(self, f):
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

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        try:
            img = pytsk3.Img_Info(case['device'])
            fs = pytsk3.FS_Info(img)
            directory = fs.open_dir(path='/windows/system32/config')
        except Exception, e:
            import traceback
            print traceback.format_exc()
        else:
            for f in directory:
                if f.info.name.name.lower() == 'sam':
                    hivefile = '%s/registry/SAM' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

                if f.info.name.name.lower() == 'system':
                    hivefile = '%s/registry/SYSTEM' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

                if f.info.name.name.lower() == 'software':
                    hivefile = '%s/registry/SOFTWARE' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

                if f.info.name.name.lower() == 'security':
                    hivefile = '%s/registry/SECURITY' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

            regdir = '%s/registry' % case['casedir']
            command = '/mnt/jer/Sources/Forensics/regripper_git/auto_rip.pl -s %s -r %s -c all' % (regdir, regdir)
            print command
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, \
                    stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            desc = Descriptor('%s_auto_rip' % case['slicenum'], 'auto_rip', json.dumps(case), descriptor.domain, \
                    agent=self._name_, processing_time=(time.time()-start))
            self.push(desc)
