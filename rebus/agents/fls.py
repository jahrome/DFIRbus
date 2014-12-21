#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Fls(Agent):
    _name_ = "fls"
    _desc_ = "List file and directory names in a partition"

    def selector_filter(self, selector):
        return "_partition/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        command = 'fls -z %s -m %s -r %s' % \
                (case['timezone'], case['casename'][:4]+case['slicenum'], case['device'])
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        bodyfilename = '%s_body_fls' % case['slicenum']
        file('%s/filesystem/%s' % (case['casedir'], bodyfilename), 'w').write(out)

        desc = Descriptor(bodyfilename, 'body_file', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
