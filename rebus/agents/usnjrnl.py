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
    _desc_ = "Extract and process NTFS UsnJrnl"

    def selector_filter(self, selector):
        return selector.startswith("slice_ntfs_partition/")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        img = pytsk3.Img_Info(case['device'])
        fs = pytsk3.FS_Info(img)
        f = fs.open('/$Extend/$UsnJrnl')
        found = False
        for attr in f:
            print attr.info.name
            if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA and attr.info.name == '$J':
                print 'UsnJrnl found'
                found = True
                break

        if not found:
            return

        offset = 0
        size = attr.info.size
        bodyfilename = '%s/filesystem/%s_usnjrnl' % (case['casedir'], case['slicenum'])
        bodyf = file(bodyfilename, 'w')
        while offset < size:
            available_to_read = min(1024 * 1024, size - offset)
            data = f.read_random(offset, available_to_read, attr.info.type, attr.info.id)
            if not data:
                break
            bodyf.write(data)
            offset += len(data)
        f.close()

        bodyfilename = '%s_body_usnjrnl' % case['slicenum']
        out_file = os.path.join(case['casedir'], 'filesystem', bodyfilename)
        command = 'usnjrnl.py -f %s -a -t body -o %s' % (bodyfilename, out_file)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        print err

        case['body_file'] = out_file
        desc = Descriptor(bodyfilename, 'body_file', json.dumps(case), descriptor.domain,
                          agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
