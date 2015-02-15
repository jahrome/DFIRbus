#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Mactime(Agent):
    _name_ = "mactime"
    _desc_ = "Create a timeline from body file"

    def selector_filter(self, selector):
        return selector.startswith("body_file/")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing %s' % case['body_file']
        out_file = '%s_mactime.csv' % case['body_file']
        command = 'mactime -z %s -y -d -b %s > %s' % \
                (case['timezone'], case['body_file'], out_file)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        print err

        case['timeline'] = out_file
        desc = Descriptor(out_file, 'timeline', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
