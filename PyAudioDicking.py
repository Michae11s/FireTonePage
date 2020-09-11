# just dicking around with py audio, hopefully we can get a working FFT

#imports
import os
import sys
import pyaudio
import wave
import numpy as np
import scipy.fftpack as sf
import struct
import math


pa=pyaudio.PyAudio()

CHUNK=2*2048
DEVICE=7
SRATE=44100

dtones = [[1100,440],[1200,330],[880,750]]
tolerance = .01
detect=0

stream=pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=SRATE,
    output=False,
    input=True,
    # input_device_index=DEVICE,
    frames_per_buffer=CHUNK)

def rms( data ):
    count = len(data)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, data )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768)
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

def maxFrequency(X, F_sample):

        M = X.size # let M be the length of the time series
        S = sf.rfft(X, n=M)
        freqs = sf.rfftfreq(len(S))
        idx=np.argmax(np.abs(S))
        freq = freqs[idx]
        freqHz = abs(freq*F_sample)
        return freqHz

stream.start_stream()

while True:
    data = stream.read(CHUNK)
    indata = np.frombuffer(data, dtype=np.int16)
    # intensity = abs(sp.fft(indata))[:CHUNK/2]
    # frequencies= np.linspace(0.0, float(SRATE)/2, num=CHUNK/2)


    # for i in range(0,32):
    #     a0 = np.fromstring(data,dtype=np.int16)[i::6]
    #     a = a0.tostring()
    if (rms(data) > .05): #make sure we have a signal
        # print (rms(data))
        rnFreq=maxFrequency(indata, SRATE)
        print (rnFreq)
        if (np.isclose(rnFreq, dtones[0], tolerance)):
            print("tone detected")

    # print(maxFrequency(indata, FREQUENCY))
    # print(rms(a))
