import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Blkls(Agent):
    _name_ = "blkls"
    _desc_ = "Extract unallocated space for carving purpose"

    def selector_filter(self, selector):
        return "_partition/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        outfilename = '%s_unalloc' % case['slicenum']
        out_file = os.path.join(case['casedir'], 'carving', outfilename)
        command = 'ionice -c 3 blkls -A %s > %s' % (case['device'], out_file)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        case['unallocated_space'] = out_file
        desc = Descriptor(outfilename, 'unallocated_space', json.dumps(case), descriptor.domain,
                          agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
