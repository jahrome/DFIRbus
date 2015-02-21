import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class BulkExtractor(Agent):
    _name_ = "bulk_extractor"
    _desc_ = "Run bulk_extractor on raw image"

    def selector_filter(self, selector):
        return selector.startswith("slice_")

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        resdir = '%s_bulk' % (case['slicenum'])
        out_dir = os.path.join(case['casedir'], 'bulk', resdir)
        command = 'ionice -c 3 bulk_extractor -e wordlist -o %s %s' % (out_dir, case['device'])
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        case['bulk_results'] = out_dir
        desc = Descriptor(resdir, 'bulk_results', json.dumps(case), descriptor.domain,
                          agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
