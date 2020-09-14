import pyaudio
import numpy as np
import struct
import math

SRATE=44100
CHUNK=4410
CNKTIM=0.1
FORMAT=pyaudio.paInt16

pa=pyaudio.PyAudio()

def rms( data ):
    count = len(data)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, data )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768)
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

stream=pa.open(
    format=FORMAT,
    channels=1,
    rate=SRATE,
    output=False,
    input=True,
    input_device_index=2, #Comment out for linux to use the default device, since pyaudio/portaudio doesn't talk direct to pulseaudio
    frames_per_buffer=CHUNK)

stream.start_stream()

while True:
    data = stream.read(CHUNK)
    print(rms(data))
