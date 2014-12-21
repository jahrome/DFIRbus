#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Blkls(Agent):
    _name_ = "blkls"
    _desc_ = "Extract unallocated space"

    def selector_filter(self, selector):
        return "_partition/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        outfilename = '%s_unalloc' % case['slicenum']
        command = 'blkls -A %s > %s/foremost/%s' % (case['device'], case['casedir'], outfilename)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        desc = Descriptor(outfilename, 'unallocated_space', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
