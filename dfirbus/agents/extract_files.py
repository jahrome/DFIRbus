import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import pytsk3


@Agent.register
class ExtractFiles(Agent):
    _name_ = "extract_files"
    _desc_ = "Extract files from image"

    def selector_filter(self, selector):
        return selector.startswith("file_list/")

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

        print 'Processing %s' % case['file_list']
        img = pytsk3.Img_Info(case['device'])
        fs = pytsk3.FS_Info(img)
        if not os.path.exists(case['file_list']['out_dir']):
            os.makedirs(case['file_list']['out_dir'])

        for i in case['file_list']['files']:
            try:
                f = fs.open(i)
                tsk_data = self.read_tsk_data(f)
                out_file = os.path.join(case['file_list']['out_dir'], i.replace('/', '_'))
                if not os.path.exists(out_file):
                    file(out_file, 'w').write(tsk_data)
                else:
                    print '%s already exist, skipping...' % out_file
            except IOError:
                print '%s not found' % i

        case['extracted_files'] = case['file_list']['out_dir']
        basedir = os.path.basename(os.path.join(case['file_list']['out_dir']))
        desc = Descriptor('%s_extract_files' % basedir, 'extracted_files', json.dumps(case),
                          descriptor.domain, agent=self._name_, processing_time=(time.time()-start))
        self.push(desc)
