DFIRbus
========

**This software is under development so please consider it as alpha quality.**


Introduction
------------
The goal of this tool is to provide some level of automation in digital forensics to help analysts in their daily tasks. However, given the high level of expertise necessary to perform complex analysis, DFIRbus mainly addresses the `case bootstrapping` and `data extraction` aspects of an investigation. The idea is to preprocess data carrier images with existing forensic tools in order to quickly provide exploitable data so that analysts can focus on evidence gathering tasks.

This tool leverages [*REbus*](https://bitbucket.org/iwseclabs/rebus) by IWSecLabs to coordinate the various forensic tools, allowing to use one's output as the input of others. For now, DFIRbus mainly focuses on Windows operating system.


Dependencies
------------
- [PyTSK](https://github.com/py4n6/pytsk.git)
- [Sleuthkit](https://github.com/sleuthkit/sleuthkit.git)
- [INDXParse](https://github.com/williballenthin/INDXParse.git)
- [usnjrnl.py](https://github.com/superponible/DFIR.git)
- [Bulk Extractor](https://github.com/simsong/bulk_extractor.git)
- [Plaso](https://github.com/log2timeline/plaso.git)
- [RegRipper + auto_rip.pl](https://github.com/keydet89/RegRipper2.8.git)
- [libbde](https://github.com/libyal/libbde) (for BitLocker Drive Encryption support)


Implemented tasks (agents)
--------------------------
- List NTFS Alternate Data Streams (ads.py)
- Identify executable images of Windows autorun locations (autoruns.py)
- Extract unallocated space for carving purpose (blkls.py)
- Run bulk_extractor on raw image (bulk_extractor.py)
- Extract files from image (extract_files.py)
- Guess filetypes and hash PE files from a NTFS partition (filetype_hash.py)
- List file and directory names in a partition (fls.py)
- Guess the partition layout of a volume system (image_detect.py)
- Run plaso on a filesystem (plaso.py)
- Create a timeline from a body file (mactime.py)
- Parse NTFS filesystem structures (mftindx.py)
- Extract strings of various encodings (strings.py)
- Extract and process NTFS UsnJrnl (usnjrnl.py)
- Detect and extract Windows OS related files (windows_volume.py)


Installation
------------
    python setup.py install


Usage
-----
    rebus_agent -m dfirbus.agents agent_name

A convenient way to launch DFIRbus agents is through the use of a `screenrc` file (sample `screenrc` and `rebus.conf` files are provided in `extra` directory):

    export CASENAME="nromanoff"
    export CASEDIR="/mnt/cases/20141114_nromanoff"
    export TIMEZONE="Europe/Paris"
    export HDD_LOCATION="/mnt/ewf/ewf1"
    dbus-launch --config-file=rebus.conf screen -h 10000 -c screenrc

See REbus [documentation](https://bitbucket.org/iwseclabs/rebus/overview) for general guidance on using REbus.


Summary of agents interractions
-------------------------------
    inject_case -> image_detect
                        |--------> windows_volume -> autoruns -> extract_files
                        |--------> fls ------------> mactime
                        |--------> mftindx --------> mactime
                        |--------> usnjrnl --------> mactime
                        |--------> ads
                        |--------> blkls
                        |--------> bulk_extractor
                        |--------> filetype_hash
                        |--------> plaso
                        |--------> strings

Agent image_detect splits the disk image into slices based on the layout of the partitions on the volume system, allocates a loop device and sends a descriptor based on the type of each slice (unallocated space, partition table, filesystem). The slice number is then used as a prefix in the result filenames.


TODO / future developments
--------------------------
- Ability to tune tools invocation through configuration file
- Ability to search for markers in result files
- Support more tools and tasks (foremost, sorter, volatility, bootloader checks, etc.)


Agents reference
----------------
- ads.py:
  - Selector: slice_ntfs_partition
  - Output descriptor: ads_results
  - Result file(s): $CASEDIR/filesystem/${slicenum}_ads.csv

- autoruns.py:
  - Selector: auto_rip
  - Output descriptor: file_list
  - Result file(s): none

- blkls.py:
  - Selector: *_partition
  - Output descriptor: unallocated_space
  - Result file(s): $CASEDIR/carving/${slicenum}_unalloc

- bulk_extractor.py:
  - Selector: slice_*
  - Output descriptor: bulk_results
  - Result file(s): $CASEDIR/bulk/${slicenum}_bulk/*

- extract_files.py:
  - Selector: file_list
  - Output descriptor: extracted_files
  - Result file(s): descriptor dependent

- filetype_hash.py:
  - Selector: slice_ntfs_partition
  - Output descriptor: md5_list, filetype_list
  - Result file(s): $CASEDIR/hashes/${slicenum}_filetypes.csv, $CASEDIR/hashes/${slicenum}_md5s.csv

- fls.py:
  - Selector: *_partition
  - Output descriptor: body_file
  - Result file(s): $CASEDIR/filesystem/${slicenum}_body_fls

- image_detect.py:
  - Selector: case
  - Output descriptor: slice_partition_table, slice_unallocated_space, slice_ntfs_partition, slice_partition_unknown
  - Result file(s): none

- mactime.py:
  - Selector: body_file
  - Output descriptor: timeline
  - Result file(s): ${body_filename}_mactime

- mftindx.py:
  - Selector: slice_ntfs_partition
  - Output descriptor: body_file
  - Result file(s): $CASEDIR/filesystem/${slicenum}_body_mftindx

- plaso.py:
  - Selector: *_partition
  - Output descriptor: timeline
  - Result file(s): $CASEDIR/plaso/${slicenum}_plaso.dump, $CASEDIR/plaso/${slicenum}_plaso.csv

- strings.py:
  - Selector: slice_*
  - Output descriptor: strings_results
  - Result file(s): $CASEDIR/strings/${slicenum}_strings/(strings_7b.txt strings_16le.txt strings_16be.txt)

- usnjrnl.py:
  - Selector: slice_ntfs_partition
  - Output descriptor: body_file
  - Result file(s): $CASEDIR/filesystem/${slicenum}_usnjrnl, $CASEDIR/filesystem/${slicenum}_body_usnjrnl

- windows_volume.py:
  - Selector: slice_ntfs_partition
  - Output descriptor: auto_rip, eventlogs
  - Result file(s): $CASEDIR/evenlogs/*, $CASEDIR/registry/*


License
-------
TODO
