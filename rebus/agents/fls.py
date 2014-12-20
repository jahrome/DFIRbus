#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
from rebus.agents.inject import guess_selector
import json
import subprocess


@Agent.register
class Fls(Agent):
    _name_ = "fls"
    _desc_ = "List file and directory names in a partition"

    def selector_filter(self, selector):
        return selector.startswith("ntfs_partition/")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)
        selector = descriptor.selector

        command = 'fls -z %s -m %s -r %s' % \
                (case['timezone'], case['casename'][:4]+case['slicenum'], case['loopdev'])
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        bodyfilename = 'body_fls_%s' % case['slicenum']
        file('%s/filesystem/%s' % (case['casedir'], bodyfilename), 'w').write(out)

        selector = 'bodyfile'
        done = time.time()
        desc = Descriptor(bodyfilename, selector, json.dumps(case), descriptor.domain,
                          agent=self._name_, processing_time=(done-start))
        self.push(desc)
