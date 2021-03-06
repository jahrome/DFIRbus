#! /usr/bin/env python

import os
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import time
import json
import pprint


@Agent.register
class InjectCase(Agent):
    _name_ = "inject_case"
    _desc_ = "Inject forensic case related files into the bus"

    @classmethod
    def add_arguments(cls, subparser):
        subparser.add_argument("--file", "-f",
                               help="Inject FILES into the bus")
        subparser.add_argument("--selector", "-s", default='case',
                               help="Use SELECTOR")
        subparser.add_argument("--label", "-l", default='case_description',
                               help="Use LABEL instead of default")

    def run(self):
        case = {"casename": os.getenv('CASENAME'),
                "casedir": os.getenv('CASEDIR'),
                "timezone": os.getenv('TIMEZONE'),
                "hdd_location": os.getenv('HDD_LOCATION'),
                "volatility_location": os.getenv('VOLATILITY_LOCATION'),
                "volatility_profile": os.getenv('VOLATILITY_PROFILE'),
               }
        #TODO: load case from file

        pprint.pprint(case)
        start = time.time()
        label = self.options.label if self.options.label else case["casename"]
        selector = self.options.selector
        desc = Descriptor(label, selector, json.dumps(case), self.domain,
                          agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
