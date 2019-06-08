import scipy
from scipy.io import wavfile, loadmat
import numpy as np
import math
import sys
import matplotlib.pyplot as plt
import time as time
import playback as pb
import sounddevice as sd
import soundfile as sf


def main():
    # 25 azimuth degrees
    azimuths = [-80, -65, -55, -45, -40, -35, -30, -25, -20,
                -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 55, 65, 80]

    # 50 elevation degrees
    elevations = [-45+5.625*e for e in range(50)]
    x=[i for i in range(200)]
    filename = './please.wav'
    block_size=20000
#     freq, sig_data = wavfile.read('./RiverStreamAdjusted.wav')
#    freq, sig_data = wavfile.read(filename)
#    sig_data = sig_data / 2**15  # from int16(16 bits) scale to -1 to 1
    with sf.SoundFile(filename) as f:
#        sd.query_devices(device=9, kind=None)
#        sd.default
        sig_data = f.read(block_size, dtype='float64')
        freq=f.samplerate
#        sig_data = np.hstack(sig_data[:]).astype(np.int16)
#        sig_data=sig_data/2**15
    print("data size: {},freq: {}".format(len(sig_data), freq))
    right_sig=sig_data[0:block_size,0].flatten()
    left_sig=sig_data[0:block_size,1].flatten()
    HRTF_data = loadmat('./CIPIC_58_HRTF.mat')
    for i in range(1,np.size(azimuths)):
        aIndex = i
        eIndex = 8

        left = np.squeeze(HRTF_data['hrir_l'][aIndex, eIndex, :])  # 200*1
        right = np.squeeze(HRTF_data['hrir_r'][aIndex, eIndex, :])  # 200*1
#        plt.plot (x,left)
        delay = HRTF_data['ITD'][aIndex, eIndex]  # float
        hrir_zeros = np.zeros(math.floor(abs(delay)))

        if aIndex < 12:
            left = np.append(left, hrir_zeros)
            right = np.append(hrir_zeros, right)
        else:
            left = np.append(hrir_zeros, left)
            right = np.append(right, hrir_zeros)
        print('end')
        
        wave_left = np.convolve(left,left_sig)
        wave_right = np.convolve(right,right_sig)
        buffer = np.vstack((wave_left, wave_right))
        buffer = np.transpose(buffer)
        print('buffer size:{}',format(sys.getsizeof(buffer)))
        # choose a playback backend
        player = pb.Playback(pb.Backend.SOUNDDEVICE)
        player.play(freq=freq, buffer=buffer, channel=2)
        time.sleep(5)

if __name__ == "__main__":
    main()
