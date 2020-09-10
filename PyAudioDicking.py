# just dicking around with py audio, hopefully we can get a working FFT

#imports
import os
import sys
import pyaudio
import wave
import numpy as np
import scipy.fftpack as sf


pa=pyaudio.PyAudio()

CHUNK=2*4096
DEVICE=2
FREQUENCY=44100

stream=pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=FREQUENCY,
    output=False,
    input=True,
    input_device_index=DEVICE,
    frames_per_buffer=CHUNK)

def maxFrequency(X, F_sample, Low_cutoff=300, High_cutoff= 2000):
        """ Searching presence of frequencies on a real signal using FFT
        Inputs
        =======
        X: 1-D numpy array, the real time domain audio signal (single channel time series)
        Low_cutoff: float, frequency components below this frequency will not pass the filter (physical frequency in unit of Hz)
        High_cutoff: float, frequency components above this frequency will not pass the filter (physical frequency in unit of Hz)
        F_sample: float, the sampling frequency of the signal (physical frequency in unit of Hz)
        """

        M = X.size # let M be the length of the time series
        Spectrum = sf.rfft(X, n=M)
        [Low_cutoff, High_cutoff, F_sample] = map(float, [Low_cutoff, High_cutoff, F_sample])

        #Convert cutoff frequencies into points on spectrum
        [Low_point, High_point] = map(lambda F: F/F_sample * M, [Low_cutoff, High_cutoff])

        maximumFrequency = np.where(Spectrum == np.max(Spectrum[Low_point : High_point])) # Calculating which frequency has max power.

        return maximumFrequency

stream.start_stream()

while True:
    data = stream.read(CHUNK)
    indata = np.fromstring(data)

    print(maxFrequency(indata, FREQUENCY))
