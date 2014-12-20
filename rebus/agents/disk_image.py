#! /usr/bin/env python

import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
from rebus.agents.inject import guess_selector
import pytsk3
import sys


@Agent.register
class DiskImage(Agent):
    _name_ = "disk_image"
    _desc_ = "Guess the partition layout of a volume system"

    def selector_filter(self, selector):
        return selector.startswith("diskimage/")

    def process(self, descriptor, sender_id):
        start = time.time()
        data = descriptor.value.strip()
        selector = descriptor.selector

        img = pytsk3.Img_Info(data)
        volume = pytsk3.Volume_Info(img)
        for part in volume:
            partname = '%d_%s_%d_%d' % (part.addr, part.desc, part.start, part.len)
            loopname = '/dev/loop%d' % part.addr

            if 'Primary Table' in part.desc:
                selector = 'partition_table'
            elif 'Unallocated' in part.desc:
                selector = 'unallocated_space'
            elif 'NTFS' in part.desc:
                selector = 'ntfs_partition'
            else:
                selector = 'unknown_partition'

            done = time.time()
            desc = Descriptor(partname, selector, loopname, descriptor.domain,
                              agent=self._name_, processing_time=(done-start))
            self.push(desc)
            self.declare_link(descriptor, desc, "Image_slice", "%s has been \
                              found in %s" % (partname, descriptor.label))
