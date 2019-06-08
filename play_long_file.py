#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:05:21 2019

@author: jason
"""

from __future__ import division, print_function
import numpy as np
import argparse
try:
    import queue  # Python 3.x
except ImportError:
    import Queue as queue  # Python 2.x
import sys
import threading

#def int_or_str(text):
#    """Helper function for argument parsing."""
#    try:
#        return int(text)
#    except ValueError:
#        return text

parser = argparse.ArgumentParser(description=__doc__)
filename = 'i_ran_so_far_away-flock_of_seagulls.wav'
device_=16
#parser.add_argument('filename', help='audio file to be played back')
#parser.add_argument('-d', '--device', type=int_or_str,
#                    help='output device (numeric ID or substring)')
parser.add_argument('-b', '--blocksize', type=int, default=4096,
                    help='block size (default: %(default)s)')
parser.add_argument(
    '-q', '--buffersize', type=int, default=5,
    help='number of blocks used for buffering (default: %(default)s)')
args = parser.parse_args()
if args.blocksize == 0:
    parser.error('blocksize must not be zero')
if args.buffersize < 1:
    parser.error('buffersize must be at least 1')

q = queue.Queue(maxsize=args.buffersize)
event = threading.Event()


def callback(outdata,frames, time, status):
#    outdata=np.reshape(outdata,(-1,2)) 
    print('frames',frames)
    print('sizeof outdata',np.shape(outdata))
    assert frames == args.blocksize
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    assert not status
    
    
    try:
        data = q.get_nowait()
    except queue.Empty:
        print('Buffer is empty: increase buffersize?', file=sys.stderr)
        raise sd.CallbackAbort
    if len(data) < len(outdata):
        outdata[:len(data),0] = data
        outdata[len(data):,0] = 0.0* (len(outdata) - len(data))
        outdata[:len(data),1] = 0.0 * (len(outdata) - len(data))
        outdata[len(data):,1] = data
        raise sd.CallbackStop
    else:
        outdata[:,0] = data
        outdata[:,1] = data
    outdata=np.transpose(outdata)
    print(np.shape(data),np.shape(outdata))
      

try:
    import sounddevice as sd
    import soundfile as sf
#    data, samplerate = sf.read('./please.wav',frames=1024)
#    sd.query_devices(device=16, kind=None)
#    sd.default
#    sd.default.device = 14
    with sf.SoundFile(filename) as f:
        for _ in range(args.buffersize):
            data = f.read(frames=args.blocksize, dtype='float32',fill_value=0.0)
            data=data.flatten()
            print ('data size 1: ',len(data))
            if len(data)==0:
                break
            q.put_nowait(data)  # Pre-fill queue

        stream = sd.OutputStream(samplerate=f.samplerate, blocksize=args.blocksize,
                                 device=16, channels=2, 
                                 dtype='float32',
                                 callback=callback, finished_callback=event.set)
        with stream:
            timeout = args.blocksize * args.buffersize / f.samplerate
            while len(data)>0:
                data = f.read(frames=args.blocksize, dtype='float32',fill_value=0.0)
                print('data size 2: ',np.shape(data))
                q.put(data, timeout=timeout)
            event.wait()  # Wait until playback is finished
except KeyboardInterrupt:
    parser.exit('\nInterrupted by user')
except queue.Full:
    # A timeout occured, i.e. there was an error in the callback
    parser.exit(1)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))