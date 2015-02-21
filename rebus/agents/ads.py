import os
import time
from rebus.agent import Agent
from rebus.descriptor import Descriptor
import json
import pytsk3
import traceback


@Agent.register
class Ads(Agent):
    _name_ = "ads"
    _desc_ = "List NTFS Alternate Data Streams"

    def selector_filter(self, selector):
        return selector.startswith("slice_ntfs_partition/")

    def process_inode(self, f, prefix=''):
        for attr in f:
            if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA and attr.info.name:
                filename = f.info.name.name
                full_path = os.path.join(prefix, filename).replace('\\', '/')
                self.results.append(','.join([full_path, attr.info.name, '%d' % attr.info.size]))

    def list_directory(self, directory, stack=None, prefix=None):
        stack.append(directory.info.fs_file.meta.addr)
        for f in directory:
            if f.info.name.name in ['.', '..']:
                continue

            try:
                dir_ = f.as_directory()
                inode = f.info.meta.addr
                if inode not in stack:
                    prefix.append(f.info.name.name)
                    self.list_directory(dir_, stack, prefix)
            except IOError:
                try:
                    if f.info.meta:
                        if f.info.meta.type != pytsk3.TSK_FS_META_TYPE_DIR:
                            self.process_inode(f, '/'.join(prefix))
                    else:
                        self.process_inode(f, '/'.join(prefix))
                except:
                    print traceback.format_exc()

        if len(stack):
            stack.pop(-1)
        if len(prefix):
            prefix.pop(-1)

    def process(self, descriptor, sender_id):
        start = time.time()
        case = json.loads(descriptor.value)

        print 'Processing slice %s' % case['slicenum']
        try:
            img = pytsk3.Img_Info(case['device'])
            fs = pytsk3.FS_Info(img)
            directory = fs.open_dir(path='/')
            self.results = []
            self.list_directory(directory, [], [])

            outfilename = '%s_ads.csv' % case['slicenum']
            out_file = os.path.join(case['casedir'], 'filesystem', outfilename)
            file(out_file, 'w').write('\n'.join(self.results))

            case['ads_results'] = out_file
            desc = Descriptor(outfilename, 'ads_results', json.dumps(case), descriptor.domain,
                              agent=self._name_, processing_time=(time.time()-start))
            self.push(desc)
        except:
            print traceback.format_exc()
