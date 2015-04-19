import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import pytsk3
import subprocess


@Agent.register
class WindowsPartition(Agent):
    _name_ = "windows_volume"
    _desc_ = "Detect and extract Windows OS related files"

    def selector_filter(self, selector):
        return selector.startswith("slice_ntfs_partition/")

    def read_tsk_data(self, f):
        if not f.info.meta:
            print "\nWARNING: No meta for file %s\n" % f.info.name.name
            return ''

        offset = 0
        size = f.info.meta.size
        tsk_data = ''
        while offset < size:
            available_to_read = min(1024 * 1024, size - offset)
            data = f.read_random(offset, available_to_read)
            if not data:
                break
            offset += len(data)
            tsk_data += data

        return tsk_data

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print '\nProcessing slice %s' % case['slicenum']
        try:
            img = pytsk3.Img_Info(case['device'])
            fs = pytsk3.FS_Info(img)
        except:
            print 'Unable to read partition, aborting'
            return

        try:
            directory = fs.open_dir(path='/windows/system32/config')
        except:
            print '/windows/system32/config not found'
        else:
            for f in directory:
                if f.info.name.name.lower().endswith('.evt'):
                    file('%s/eventlog/%s' % (case['casedir'], f.info.name.name),
                         'w').write(self.read_tsk_data(f))

                elif f.info.name.name.lower() == 'sam':
                    hivefile = '%s/registry/SAM' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

                elif f.info.name.name.lower() == 'system':
                    hivefile = '%s/registry/SYSTEM' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

                elif f.info.name.name.lower() == 'software':
                    hivefile = '%s/registry/SOFTWARE' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

                elif f.info.name.name.lower() == 'security':
                    hivefile = '%s/registry/SECURITY' % case['casedir']
                    file(hivefile, 'w').write(self.read_tsk_data(f))

            out_dir = os.path.join(case['casedir'], 'registry')
            command = 'auto_rip.pl -s %s -r %s -c all' % (out_dir, out_dir)
            print command
            proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()

            case['auto_rip'] = out_dir
            desc = Descriptor('%s_auto_rip' % case['slicenum'], 'auto_rip', json.dumps(case),
                              descriptor.domain, agent=self._name_,
                              processing_time=(time.time()-start))
            self.push(desc)

        try:
            directory = fs.open_dir(path='/windows/system32/winevt/logs')
        except:
            print '/windows/system32/winevt/logs not found'
        else:
            out_dir = os.path.join(case['casedir'], 'eventlogs')
            for f in directory:
                if f.info.name.name.lower().endswith('.evtx'):
                    print '%s' % f.info.name.name
                    data = self.read_tsk_data(f)
                    file('%s/%s' % (out_dir, f.info.name.name), 'w').write(data)

            case['eventlogs'] = out_dir
            desc = Descriptor('%s_eventlogs' % case['slicenum'], 'eventlogs', json.dumps(case),
                              descriptor.domain, agent=self._name_,
                              processing_time=(time.time()-start))
            self.push(desc)
