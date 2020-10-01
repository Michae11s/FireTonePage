import pyaudio
import numpy as np
import scipy.fftpack as sf
import struct
import math

pa=pyaudio.PyAudio()

SQUELCH=.0001

SRATE=44100
#CHUNK=4410
CHUNK=8820
CNKTIM=CHUNK/SRATE
FORMAT=pyaudio.paInt16

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
    input_device_index=8, #Comment out for Windows to use the default device (use python -m sounddevice to find this index number)
    frames_per_buffer=CHUNK)

stream.start_stream()

while True:
    try:
        #loop time
        # ntime=dt.now()
        # logging.debug((ntime-ltime).total_seconds())

        data = stream.read(CHUNK, exception_on_overflow=False) # read from our buffer
        # ltime=dt.now()
        level=rms(data)
        if level>SQUELCH:
            print(level)

        #need this to run every chunk, as this handles both detection and recording for the tones
    except KeyboardInterrupt:
        print("=====Keyboard Interupt::Exiting Cleanly=====")
        stream.close()
        pa.terminate()
        quit()
    except OSError as err:
        print("OS error: {0}".format(err))
        print("==== Exiting =====")
        stream.close()
        pa.terminate()
        quit()
