#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Strings(Agent):
    _name_ = "strings"
    _desc_ = "Extract strings of various encodings"

    def selector_filter(self, selector):
        return selector.startswith("slice_")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        resdir = '%s_strings' % case['slicenum']
        if not os.path.exists('%s/strings/%s' % (case['casedir'], resdir)):
            os.makedirs('%s/strings/%s' % (case['casedir'], resdir))

        command = "bash -c 'cat %s | tee >(strings -t d -n 4 > %s/strings/%s/strings_7b.txt) \
                >(strings -e l -t d -n 4 > %s/strings/%s/strings_16le.txt) \
                >(strings -e b -t d -n 4 > %s/strings/%s/strings_16be.txt) \
                > /dev/null'" % (case['device'], case['casedir'], resdir, \
                case['casedir'], resdir, case['casedir'], resdir)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        desc = Descriptor(resdir, 'strings_results', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
