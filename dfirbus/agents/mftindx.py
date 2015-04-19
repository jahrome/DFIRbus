import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class MftIndx(Agent):
    _name_ = "mftindx"
    _desc_ = "Parse NTFS filesystem structures"

    def selector_filter(self, selector):
        return "_partition/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing %s' % case['device']
        bodyfilename = '%s_body_mftindx' % case['slicenum']
        out_file = os.path.join(case['casedir'], 'filesystem', bodyfilename)
        command = 'MFTINDX.py -t image -o 0 -l -s -m -d %s > %s' % (case['device'], out_file)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        print err

        case['body_file'] = out_file
        desc = Descriptor(bodyfilename, 'body_file', json.dumps(case), descriptor.domain,
                          agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
