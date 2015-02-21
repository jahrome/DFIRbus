import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import subprocess


@Agent.register
class Plaso(Agent):
    _name_ = "plaso"
    _desc_ = "Run plaso on a filesystem"

    def selector_filter(self, selector):
        return "_partition/" in selector

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        logfile = os.path.join(case['casedir'], 'plaso', '%s_plaso.log' % case['slicenum'])
        dumpfile = os.path.join(case['casedir'], 'plaso', '%s_plaso.dump' % case['slicenum'])
        command = 'log2timeline.py --workers 8 -z %s --logfile=%s %s %s' % (case['timezone'],
                                                                            logfile, dumpfile,
                                                                            case['device'])
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        outfilename = '%s_plaso.csv' % case['slicenum']
        out_file = os.path.join(case['casedir'], 'plaso', outfilename)
        command = 'psort.py -o L2tcsv -z %s %s > %s' % (case['timezone'], dumpfile, out_file)
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()

        case['timeline'] = out_file
        desc = Descriptor(outfilename, 'timeline', json.dumps(case), descriptor.domain,
                          agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
