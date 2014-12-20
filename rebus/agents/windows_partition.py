#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
from rebus.agents.inject import guess_selector
import json
import pytsk3
import subprocess


@Agent.register
class WindowsPartition(Agent):
    _name_ = "windows_partition"
    _desc_ = "Detect and extract Windows OS related files"

    def selector_filter(self, selector):
        return selector.startswith("ntfs_partition/")

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

    def run_regripper(self, case, start, descriptor, plugin, hivefile):
        command = '/mnt/jer/Sources/Forensics/regripper/rip.pl -p %s -r %s' % (plugin, hivefile)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        outfile = '%s/regripper/%s.txt' % (case['casedir'], plugin)
        file(outfile, 'w').write(out)
        desc = Descriptor(plugin, plugin, out, descriptor.domain, \
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)
        selector = descriptor.selector

        img = pytsk3.Img_Info(case['loopdev'])
        fs = pytsk3.FS_Info(img)
        try:
            directory = fs.open_dir(path='/windows/system32/config')
        except IOError:
            pass
        else:
            for f in directory:
                if f.info.name.name.lower() == 'sam':
                    hivefile = '%s/regripper/SAM' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))
                    self.run_regripper(case, start, descriptor, 'samparse', hivefile)

                if f.info.name.name.lower() == 'system':
                    hivefile = '%s/regripper/SYSTEM' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))
                    for plugin in ['compname', 'services', 'svc_plus', 'nic', 'nic2', 'nic_mst2', 'shares']:
                        self.run_regripper(case, start, descriptor, plugin, hivefile)

                if f.info.name.name.lower() == 'software':
                    hivefile = '%s/regripper/SOFTWARE' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))
                    for plugin in ['winver', 'profilelist', 'soft_runplus']:
                        self.run_regripper(case, start, descriptor, plugin, hivefile)
