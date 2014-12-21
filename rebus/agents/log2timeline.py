#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Log2timeline(Agent):
    _name_ = "log2timeline"
    _desc_ = "Run log2timeline on a filesystem"

    def selector_filter(self, selector):
        return "_partition/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        device = case['device'].split('/')[-1]
        command = 'log2timeline.py --workers 8 -z %s --logfile=%s/plaso/%s_plaso.log -i %s/plaso/%s_plaso.dump %s' \
                % (case['timezone'], case['casedir'], case['slicenum'], case['casedir'], case['slicenum'], case['device'])
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        command = 'psort.py -o L2tcsv -z %s %s/plaso/%s_plaso.dump > %s/plaso/%s_plaso.csv' \
                % (case['timezone'], case['casedir'], case['slicenum'], case['casedir'], case['slicenum'])
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        desc = Descriptor('%s_plaso.csv' % case['slicenum'], 'l2t_results', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
