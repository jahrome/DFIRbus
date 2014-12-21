#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import pytsk3
import subprocess


@Agent.register
class UsnJrnl(Agent):
    _name_ = "usnjrnl"
    _desc_ = "Extract and process UsnJrnl"

    def selector_filter(self, selector):
        return selector.startswith("slice_ntfs_partition/")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        try:
            img = pytsk3.Img_Info(case['device'])
            fs = pytsk3.FS_Info(img)
            directory = fs.open_dir(path='/windows/system32/config')

            f = fs.open('/$Extend/$UsnJrnl')
            for attr in f:
                print attr.info.name
                if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA and attr.info.name == '$J':
                    print 'UsnJrnl found'
                    break

            file('%s/filesystem/%s_usnjrnl' % (case['casedir'], case['slicenum']), 'w').write( \
                    f.read_random(0, attr.info.size, attr.info.type, attr.info.id))

            bodyfilename = '%s_body_usnjrnl' % case['slicenum']
            command = 'usnjrnl.py -f %s/filesystem/%s_usnjrnl -a -t body -o %s/filesystem/%s' % \
                    (case['casedir'], case['slicenum'], case['casedir'], bodyfilename)
            print command
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()

            desc = Descriptor(bodyfilename, 'body_file', json.dumps(case), descriptor.domain,
                    agent=self._name_, processing_time=(time.time()-start))
            self.push(desc)
        except Exception, e:
            import traceback
            print traceback.format_exc()

