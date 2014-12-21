#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
from rebus.agents.inject import guess_selector
import json
import pytsk3
import subprocess


class ImageSliceDescriptor(Descriptor):
    def __del__(self):
        case = json.loads(self.value)
        if 'loop' in case['device']:
            command = 'sudo losetup -d %s' % case['device']
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            loopname, err = proc.communicate()


@Agent.register
class ImageDetect(Agent):
    _name_ = "image_detect"
    _desc_ = "Guess the partition layout of a volume system"

    def selector_filter(self, selector):
        return selector.startswith("case/")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        img = pytsk3.Img_Info(case['hdd_location'])
        volume = pytsk3.Volume_Info(img)
        encrypted = False
        for part in volume:
            partname = '%d_%s_%d_%d' % (part.addr, part.desc, part.start, part.len)
            command = 'sudo losetup -P -f --show --offset %d --sizelimit %d %s' % \
                    (part.start*volume.info.block_size, part.len*volume.info.block_size, case['hdd_location'])
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            case['device'] = out.strip()
            case['slicenum'] = str(part.addr)
            time.sleep(0.5) 

            if 'Primary Table' in part.desc:
                selector = 'slice_partition_table'
            elif 'Unallocated' in part.desc:
                selector = 'slice_unallocated_space'
            elif 'NTFS' in part.desc:
                if 'FVE-FS' in file(case['device'], 'rb').read(10):
                    encrypted = True
                    loopname = case['device'].split('/')[-1]
                    bdemntdir = '/mnt/%s_bde' % loopname
                    if not os.path.exists(bdemntdir):
                        os.makedirs(bdemntdir)

                    enc_key = file(os.path.join(case['casedir'], 'hdd', 'encrypted'), 'r').read().strip()
                    command = 'bdemount -X allow_other -r %s %s %s' % (enc_key, case['device'], bdemntdir)
                    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    out, err = proc.communicate()
                    #command = 'cp %s %s; umount %s; rmdir %s' % (os.path.join(bdemntdir, 'bde1'), os.path.join(case['casedir'], 'hdd'), bdemntdir, bdemntdir)
                    command = 'umount %s; rmdir %s' % (bdemntdir, bdemntdir)
                    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    out, err = proc.communicate()
                    case['device'] = os.path.join(case['casedir'], 'hdd', 'bde1')
                    encrypted = os.path.join(case['casedir'], 'hdd', 'bde1')
                selector = 'slice_ntfs_partition'
            else:
                selector = 'slice_partition_unknown'

            print partname
            desc = ImageSliceDescriptor(partname, selector, json.dumps(case), descriptor.domain, \
                    agent=self._name_, processing_time=(time.time()-start))
            self.push(desc)
