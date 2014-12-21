#! /usr/bin/env python

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

        bodyfilename = '%s_body_mftindx' % case['slicenum']
        command = 'MFTINDX.py -t image -o 0 -l -s -m -d %s' % (case['device'])
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        print err
        file('%s/filesystem/%s' % (case['casedir'], bodyfilename), 'w').write(out)

        desc = Descriptor(bodyfilename, 'body_file', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
