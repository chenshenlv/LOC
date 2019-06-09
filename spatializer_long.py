#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 16:23:04 2019

@author: jason
"""
import scipy
from scipy.io import loadmat
import math
import numpy as np
import random
import sys
import matplotlib.pyplot as plt
#import time as time
import sounddevice as sd
import soundfile as sf
import queue  # Python 3.x
import threading
#a= np.array([[1, 2, 3], [3, 4, 5], [1, 2, 3]])
#a[1:,0]=0
azimuths = [-80, -65, -55, -45, -40, -35, -30, -25, -20,
                -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 55, 65, 80]

# 50 elevation degrees
elevations = [-45+5.625*e for e in range(50)]
HRTF_data = loadmat('./CIPIC_58_HRTF.mat')
filename = 'i_ran_so_far_away-flock_of_seagulls.wav'   
block_size = 12288 #frames size Sampling frequency in Hertz (= frames per second).
buffer_size = 2 #number of blocks used for buffering    
q = queue.Queue(maxsize=buffer_size)
event = threading.Event()

def spatialization(azimuths,HRTF_data,routine):
#    for i in range(1,np.size(azimuths)): 
    aIndex=routine
#    aIndex=2
    eIndex=8;
    left = np.squeeze(HRTF_data['hrir_l'][aIndex, eIndex, :])  # 200*1
    right = np.squeeze(HRTF_data['hrir_r'][aIndex, eIndex, :])  # 200*1
    delay = HRTF_data['ITD'][aIndex, eIndex]  # float
    hrir_zeros = np.zeros(math.floor(abs(delay)))

    if aIndex < 12:
        left = np.append(left, hrir_zeros)
        right = np.append(hrir_zeros, right)
    else:
        left = np.append(hrir_zeros, left)
        right = np.append(right, hrir_zeros)
        
    data_left = np.convolve(left, data,mode='same')
    data_right = np.convolve(right, data,mode='same')
    buffer = np.vstack((data_left,data_right))
    buffer = np.transpose(buffer)
#        print('buffer size',len(buffer))
    return buffer
    
def callback(outdata, frames, time, status):
#    outdata=np.reshape(outdata,(-1,2))
    print('frames',frames)
    print('sizeof outdata',np.shape(outdata))
    assert frames == block_size
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    assert not status
    try:
        data = q.get_nowait()
        print('len of data',len(data[:,0]))
#        data=data.astype('float64')
    except queue.Empty:
        print('Buffer is empty: increase buffersize?', file=sys.stderr)
        raise sd.CallbackAbort
    if len(data[:,0]) < len(outdata[:,0]):
        outdata[:len(data[:,0]),0] = data[:,0]
        outdata[len(data[:,0]):,0] = 0 * (len(outdata[:,0]) - len(data[:,0]))
        outdata[:len(data[:,0]),1] = data[:,1]
        outdata[len(data[:,0]):,1] = 0 * (len(outdata[:,0]) - len(data[:,0]))
        raise sd.CallbackStop
    else:
       
        outdata[:,0] = data[:,0]
        outdata[:,1] = data[:,1]
        
try:

    with sf.SoundFile(filename) as f:
#        sd.query_devices(device=9, kind=None)
#        sd.default
        routine=0
        for _ in range(buffer_size):
            data = f.read(frames=block_size, dtype='float32',fill_value=0.0)
            data=data.flatten()
            if len(data)==0:
                break
            
            buffer=spatialization(azimuths,HRTF_data,routine)
            routine=routine+1
            q.put_nowait(buffer)  # Pre-fill queue

        stream = sd.OutputStream(
            samplerate=f.samplerate, blocksize=block_size,
            device=16, channels=2, dtype='float32',
            callback=callback, finished_callback=event.set)
        with stream:
            timeout = (block_size * buffer_size-2) / f.samplerate
            while len(data)>0:
                data = f.read(frames=block_size, dtype='float32',fill_value=0.0)
                routine=routine+1
                buffer=spatialization(azimuths,HRTF_data,routine)
                if routine==24:
                    routine=0
                q.put(buffer, timeout=timeout)
            event.wait()  # Wait until playback is finished
except queue.Full:
    print('timeout')
    exit
           