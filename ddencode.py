#!/usr/bin/python
######################################################################
## Description:   Encode images to h.264 mp4 using ffmpeg
## Author:        David Dumas <david@dumas.io>
## Modified at:   Wed Jun 29 15:44:03 2016
##                
## This program is free software distributed under the GNU General
## Public License (http://www.gnu.org/licenses/gpl.txt).
######################################################################

'''Encode images to h.264 mp4 using ffmpeg with sensible defaults.'''

_VERSION = '0.0.2'

import sys
import subprocess
import os

with open(os.devnull, "w") as f_devnull:
    try:
        subprocess.call(['ffmpeg', '-version'], stdout=f_devnull)
    except OSError:
        sys.stderr.write('ERROR: "ffmpeg" executable not found.  (It must be in the search path to use this utility).\n')
        sys.exit(1)

import argparse
import os.path

parser = argparse.ArgumentParser(
    description='Encode a sequence of images to an h.264 video file',
    epilog='''The main options affecting output quality are -b/--bitrate and
-c/--crf, and most of the time just one of these should be used.
Using -b/--bitrate sets a *bit rate maximum* and attempts to maximize
perceived quality.  Using -c/--crf sets a *quality goal* and attempts
to minimize the bit rate required to meet that goal.''',
)

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    '-f','--framespec',
    help='Printf-style template for names of the image files (e.g. "frame-%%03d.png")'
)
group.add_argument(
    '-m','--manifest',
    help='Text file with list of image filenames, one per line'
)

parser.add_argument(
    '-n','--numframes',
    help='Maximum number of frames to encode, 0=all',
    type=int,
    default=0,
)
parser.add_argument(
    '-o','--output',
    help='Output filename; default is to generate a name',
)
parser.add_argument(
    '-b','--bitrate',
    help='Bitrate (units "k", "m", etc. known to ffmpeg are accepted)',
    default=None,
)
parser.add_argument(
    '-c','--crf',
    help='Target CRF (18 to 28, lower is better)',
    default=None,
)
parser.add_argument(
    '-r','--framerate',
    help='Frames per second',
    type=int,
    default=24,
)
parser.add_argument(
    '-p','--passes',
    help='Number of passes (default: 2 if --bitrate given, else 1)',
    type=int
)
parser.add_argument(
    '--keep-temp',
    help='Do not delete ffmpeg temporary files',
    action='store_true',
    )
parser.add_argument(
    '-v','--verbose',
    help='Show full ffmpeg output',
    action='store_true',
)
parser.add_argument(
    '--dry-run',
    help='Show what would be done, but don\'t do it.',
    action='store_true',
)

args = parser.parse_args()

if args.passes == None:
    if args.bitrate:
        args.passes = 2
        sys.stderr.write('INFO: Using 2-pass encoding since --bitrate given.\n')
    else:
        args.passes = 1
        sys.stderr.write('INFO: Using 1-pass encoding.\n')
        
if args.passes not in [1,2]:
    sys.stderr.write('ERROR: Number of passes must be 1 or 2.\n')
    sys.exit(1)
    
if not args.output:
    fn = os.path.basename(os.getcwd())
    fn = fn + '-r%s' % args.framerate
    if args.bitrate:
        fn = fn + '-%s' % args.bitrate
    if args.crf:
        fn = fn + '-crf%s' % args.crf
    if args.numframes:
	fn = fn + '-n%d' % args.numframes
    fn  = fn + '.mp4'

    args.output = fn
    sys.stderr.write('INFO: Using output filename "%s".\n' % args.output)


if args.numframes:
    args.numframestr = '-vframes %d' % args.numframes
else:
    args.numframestr = ''

qualstr = ''
if args.bitrate != None:
    qualstr += '-b:v %s' % args.bitrate

if args.crf != None:
    qualstr += '-crf %s' % args.crf
args.qualstr = qualstr

    
temps = []
if args.manifest:
    import warnings
    warnings.filterwarnings('ignore')
    framedir = os.tempnam('/tmp','ddenc')
    args.framespec = os.path.join(framedir,'%05d.png')
    os.mkdir(framedir)
    temps.append(framedir)
    i = 0
    sys.stderr.write('INFO: Making frame symlinks.\n')
    extn = None
    with file(args.manifest,'rt') as manifest:
        for line in manifest:
            line = line.strip()
            if not line:
                continue
            if not extn:
                _,extn = os.path.splitext(line)
                sys.stderr.write('INFO: Using frame image extension "%s".\n' % extn)
                args.framespec = os.path.join(framedir,'%05d' + extn)                
            linkname = os.path.join(framedir,('%05d' % i) + extn)
            os.symlink(os.path.abspath(line),linkname)
            temps.append(linkname)
            i = i + 1

def do(cmdstr):
    if args.dry_run:
        print cmdstr
    else:
        subprocess.call(cmdstr,shell=True)

if args.passes == 2:
    do('ffmpeg -f image2 -r %(framerate)s -i \'%(framespec)s\' -c:v libx264 -r %(framerate)s %(qualstr)s -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -preset slower -tune grain -pass 1 -f mp4 %(numframestr)s -y /dev/null' % vars(args))
    do('ffmpeg -f image2 -r %(framerate)s -i \'%(framespec)s\' -c:v libx264 -r %(framerate)s %(qualstr)s -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -preset slower -tune grain -pass 2 -f mp4 %(numframestr)s -y %(output)s' % vars(args))
else:
    do('ffmpeg -f image2 -r %(framerate)s -i \'%(framespec)s\' -c:v libx264 -r %(framerate)s %(qualstr)s -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -preset slower -tune grain -f mp4 %(numframestr)s -y %(output)s' % vars(args))

if temps:
    sys.stderr.write('INFO: Cleaning up frame symlinks.\n')
    try:
        while temps:
            fn = temps.pop()
            os.unlink(fn)
    except OSError:
        os.rmdir(fn)

if not args.keep_temp:
    for fn in ['ffmpeg2pass-0.log', 'ffmpeg2pass-0.log.mbtree']:
        if os.path.exists(fn):
            os.unlink(fn)
