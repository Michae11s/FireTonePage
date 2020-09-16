# just dicking around with py audio, hopefully we can get a working FF

#imports
import os
import sys
import pyaudio
import wave
import numpy as np
import scipy.fftpack as sf
import struct
import math
import xml.etree.ElementTree as ET
import smtplib
import ssl
import email

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydub import AudioSegment as ast
from pydub.utils import which
from datetime import datetime as dt

#make sure ffmpeg is accessible, since I don't care for the user case w/o ffmpeg its mandatory
if not(which("ffmpeg")):
    print("FFMPEG NOT FOUND! EXITING...")
    exit()

pa=pyaudio.PyAudio() #create the pyaudio class

#should give us a chunk every .1sec IMPORTANT TO DURATION CALCS DON"T CHANGE
SRATE=44100
CHUNK=4410
CNKTIM=0.1

#CHANGABLE GLOBAL VARS
SQUELCH=0.02 #RMS valued squelch
TLRNC = .01 #tone tolerance, percentage was a tone can be and still be recognized

#NON EDITABLE GLOBAL VARS
FORMAT=pyaudio.paInt16

#EMAIL VARS
#### TODO, IMPORT THEM #####
#Import Email settings (basically setup for ssl gmail)
tee=ET.parse("config.xml")
root=tee.getroot()
email=root.find("Email")
SERVER=email.find("server").text
PORT=email.find("server").get("port")
ADDR=email.find("account").text
PWORD=email.find("pword").text
context = ssl.create_default_context()

class toneSet(object):
    def __init__(self, name="default", tonesA=[1100,.6], tonesB=[440,.8], amrEmails=["6032192080@vzwpix.com","kk9michaels@gmail.com"], txtEmails=[], mp3Emails=["kk9michaels@gmail.com"], rDelay=0.0, DeadSpace=5.0):
        #Vals from arguments
        self.name=name                      # tone set name, things such as Chichester Fire, Tritown Ambulance, etc
        self.tones=[tonesA, tonesB]         # list of tone lists, tones will be in format [freq, duration]
        self.amr=amrEmails                  # list of emails to recieve AMR files, (phone numbers)
        self.txt=txtEmails                  # list of emails to revieve pre-alert messages
        self.mp3=mp3Emails                  # list of emails to recieve MP3 files
        self.rDelay=rDelay                  # recording delay
        self.maxDeadSpace=DeadSpace         # maximum amount of deadspace after which we stop recording

        #Preset Vals
        self.recording=False                # var to hold current recording state
        self.toneA=False                    # Holds whether we've recognized tone A yet or not
        self.clen=[0.0,0.0,0.0]             # Holds in order, amount of time recognized A, time recognized B, time w/no recognition
        self.toneto=0.5                     # amount of time after which we reset if no tones have be recognized, correlates w/ clen[2]
        self.recording=False                # state var to hold whether we are recording
        self.frames=[]                      # hold recording of current audio frames to write out to wav
        self.timeZ=dt.utcfromtimestamp(0)   # reference datetime to use as null comparison
        self.rDeadSpace=self.timeZ     # ammount of DeadSpace we have seen so far

    #### INTERNAL METHODS ####
    # Return a fileName with a givene extension in a certain directory
    def fileName(self, type="wav"):
        return (type.upper() + "/" + self.name + "_" + self.rstart.strftime("%m%d%y-%H%M%S") + "." + type)

    # Reset the detection variables
    def reset(self):
        self.clen=[0.0,0.0,0.0]
        self.toneA=False

    def check(self, freq): #pass the current fft freq, return true if this creates a total match meaning we have detected a tone
        if np.isclose(freq, self.tones[0][0], TLRNC): #are we matching tone A?
                #print("ToneA recognized")
                self.clen[0] += CNKTIM
                # print(self.clen[0])
                if(self.clen[0] >= self.tones[0][1]): #toneA detected successfully, met required time
                    self.toneA=True
                    self.clen[2]=0.0
                    # print("detected A successfully")
        elif self.toneA: #we have already verified A tone
            if np.isclose(freq, self.tones[1][0], TLRNC): #is the current freq B tone
                self.clen[1]+=CNKTIM
                self.clen[2]=0.0
                if (self.clen[1] >= self.tones[1][1]): #have we met the time length, detect the tone
                    print("Tone Detected: " + self.name)
                    self.reset()
                    return True
            elif np.isclose(freq, self.tones[0][0], TLRNC): #still toneA lets do nothing
                return False
            else: #not tone A and not tone B, lets start timing out
                self.clen[2]+=CNKTIM
                if(self.clen[2] >= self.toneto): #we have timed out, reset for new detection
                    self.reset()
        else:
            if not(self.clen[0]==0.0): #its not tone A or not looking for B yet, if we are in the process of timing out lets continue to count
                self.clen[2]+=CNKTIM
                if(self.clen[2]>=self.toneto): #timed out
                    self.reset()
        # if we made it to here we failed to fully detect a tone so exit without a recognition
        return False

    def sendEmails(self, type): #type can be "pre" "mp3" "amr"
        #Setup the email
        subject= "[TONE] " + self.name
        body= "Page recieved for: " + self.name + "\n at " + self.rstart.strftime("%H:%M:%S on %m/%d/%y")
        message = MIMEMultipart()
        message["From"] = ADDR
        message["To"] = ADDR
        message["Subject"] = subject
        message.attach(MIMEText(body, 'plain'))

        #differentiate base on type
        if (type=="pre"):
            elist=self.txt
        else:
            if(type=="mp3"):
                elist=self.mp3
                fname=self.fileName("mp3")
            else:
                elist=self.amr
                fname=self.fileName("amr")
            with open(fname, 'rb') as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {fname[4:]}",
            )
            message.attach(part)

        #send the emails
        with smtplib.SMTP_SSL(SERVER, PORT, context=context) as server:
            server.login(ADDR, PWORD)
            for recipient in elist:
                message["Bcc"] = recipient
                text=message.as_string()
                server.sendmail(ADDR, recipient, text)

        print("EMAILS SENT:" + type.upper())
        #SEND EMAILS HERE

    def startRecord(self):
        self.frames=[] #make sure our buffer is empty, nothing left over
        self.recording=True #flip the flag
        self.rstart=dt.now() #hold the time we started recording, so we can delay when we actually start recording
        #self.fileName= self.name + "-" + self.rstart.strftime("%m%d%y-%H%M%S")
        print("recording started:" + self.fileName())
        self.sendEmails("pre") #lets send out the pre alert

    def record(self, data):
        now=dt.now()
        if ((now-self.rstart).total_seconds() > self.rDelay): #have we passed the recording delay
            self.frames.append(data) #reccord current chunk
            if (rms(data) > SQUELCH): #if this chunk is above the squelch, reset deadspace timer
                self.rDeadSpace=self.timeZ
            elif (self.rDeadSpace==self.timeZ): #no audio and we aren't already keeping track of rDeadSpace
                self.rDeadSpace=now
            elif((now-self.rDeadSpace).total_seconds() > self.maxDeadSpace): #see if current time is max deadspace then stop recording
                self.stopRecord()

    def stopRecord(self):
        self.recording=False #change the recording flag
        self.frames = self.frames[:-(int((self.maxDeadSpace*10)-30))] #lets subtract the deadspace, which is time*(frames/sec==10)
        print("Stopped Recording: " + self.fileName("wav"))

        #lets actually writeout the file
        wf = wave.open(self.fileName("wav"), 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(SRATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        #now lets convert the wav into something useful
        hold=ast.from_wav(self.fileName("wav"))
        hold.export(self.fileName("mp3"), format="mp3")
        print("MP3 generated:" + self.fileName("mp3"))
        self.sendEmails("mp3")
        hold.export(self.fileName("amr"), format="amr", parameters=["-ar", "8000", "-ab", "12.2k"])
        print("AMR generated:" + self.fileName("amr"))
        self.sendEmails("amr")

        #clear out our recording buffer
        self.frames=[]

    #### Methods to be called externally ####

    """
    If we aren't recording try to detect tones,
    if we are recording lets do that
    """
    def eval(self, freq, data):
        if not(self.recording):
            if self.check(freq): #just matched for the first time
                self.startRecord()
                self.record(data)
        else:
            self.record(data)

class holdTones():
    def __init__(self, Fname="tones.xml"):
        self.Fname=Fname
        self.lastChecked=dt.now()
        self.tones=self.ImportTones()

    def ImportTones(self):
        tones=[toneSet()]
        if os.path.exists(self.Fname):
            try:
                tree=ET.parse(self.Fname) #tones.xml exists, lets import
            except:
                print("tones.xml import fails")
                return tones
            root=tree.getroot()
            for d in root:
                _nam=d.get("name")
                _toneA=[int(d.find("ToneA")[0].text),float(d.find("ToneA")[1].text)]
                _toneB=[int(d.find("ToneB")[0].text),float(d.find("ToneB")[1].text)]
                _rDelay=float(d.find("recordDelay").text)
                _mDS=float(d.find("maxDeadSpace").text)
                _txtEmail=[]
                _mp3Email=[]
                _amrEmail=[]
                for email in d.find("txtEmails"):
                    _txtEmail.append(email.text)
                for email in d.find("mp3Emails"):
                    _mp3Email.append(email.text)
                for email in d.find("amrEmails"):
                    _amrEmail.append(email.text)

                tones.append(toneSet(
                    _nam,
                    _toneA,
                    _toneB,
                    _amrEmail,
                    _txtEmail,
                    _mp3Email,
                    _rDelay,
                    _mDS))
        return tones

    def toneSets(self):
        return self.tones

    def update(self):
        if (float(dt.now().strftime("%S.%f")) < 0.1):
            if os.path.exists(self.Fname):
                if (dt.fromtimestamp(os.path.getmtime(self.Fname)) > self.lastChecked):
                    print("reimporting departments")
                    self.lastChecked = dt.now()
                    self.tones=self.ImportTones()

#calculate the rms of the chunk, used for squelching operations
def rms( data ):
    count = len(data)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, data )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768)
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

# method to calculate the FFT of the chunk and return the peak, lets us detect a tone in the chunk and return it
def toneDetect(data, F_sample):
    X = np.frombuffer(data, dtype=np.int16)
    if (rms(data) > SQUELCH): #SQUELCH
        M = X.size                  # let M be the length of the time series
        S = sf.rfft(X, n=M)         # FFT
        freqs = sf.rfftfreq(len(S)) # grab the freqs associated
        idx=np.argmax(np.abs(S))    # find the x postion of the peak frequency
        freq = freqs[idx]           # identify that frequency
        freqHz = abs(freq*F_sample) # convert back to Hz
        return freqHz
    else:
        return 0.0 #if we failed the squelch return zero

# define listening port, this is the output of the audio streamed from the radio/sdr
stream=pa.open(
    format=FORMAT,
    channels=1,
    rate=SRATE,
    output=False,
    input=True,
    input_device_index=2, #Comment out for linux to use the default device, since pyaudio/portaudio doesn't talk direct to pulseaudio
    frames_per_buffer=CHUNK)

# start listening
stream.start_stream()
print("stream started, Running...")

# CREATE TONE SETS
departments=holdTones()

while True:
    global toneSets
    global tonesChecked
    data = stream.read(CHUNK) # read from our buffer
    rnFreq=toneDetect(data, SRATE) # run the fft to get the peak frequency
    if not(rnFreq==0.0): #lets print to terminal if something broke the squelch
        print(rnFreq)

    #need this to run every chunk, as this handles both detection and recording for the tones
    for department in departments.toneSets():
        department.eval(rnFreq, data)

    departments.update()

#exit cleanly
stream.close()
pa.terminate()