#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess
import pprint


@Agent.register
class Autoruns(Agent):
    _name_ = "autoruns"
    _desc_ = "Identify executables in autorun locations"

    def selector_filter(self, selector):
        return "auto_rip/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        progs = []
        for i in file('%s/registry/07_autoruns_information.txt' %
                case['casedir'], 'r').readlines():
            if 'ImagePath = ' in i:
                key = i.split(' = ', 1)[1].strip()
                if key:
                    keyl = key.strip().strip('"')\
                            .split('/')[0].strip().strip('"')\
                            .split(' -')[0].strip().strip('"')\
                            .lower().strip('c:\\')\
                            .replace('\\', '/')\
                            .replace('%programfiles%', 'program files')\
                            .replace('%windir%', 'windows')\
                            .replace('%systemroot%', 'windows')\
                            .replace('systemroot', 'windows')\

                    if keyl.startswith('system32'):
                        keyl = 'windows/' + keyl
                    progs.append(keyl)

        if not len(progs):
            return

        case['file_list'] = {'out_dir': os.path.join(case['casedir'], 'extracted', 'autoruns'),
                             'files': list(set(progs))}
        pprint.pprint(case)
        desc = Descriptor('autoruns', 'file_list', json.dumps(case), descriptor.domain,
                agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
