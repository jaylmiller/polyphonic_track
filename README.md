# polyphonic_track
Polyphonic pitch tracking in real time using Python and Pure Data. Note tracking data is converted to MIDI and can be sent to DAWs, midi-capable hardware, etc. via a virtual MIDI bus (has only been testing using OSX's IAC midi driver).

# Description
Real time polyphonic pitch tracking translating raw audio (of isolated instruments) to polyphonic midi data using Pure Data and Python. Pure Data is used as the audio engine for receiving audio input, synthesizing audio (not fully implemented, only midi is currently), and as a signal processor, detecting note onsets/ends, and computing fast Fourier transforms. This data is sent to a Python script (sending OSC messages over a UDP connection), which uses the machine learning library Scikit-Learn to perform dimensionality reduction on short time Fourier transforms to obtain the set of notes comprising the signal--this is not computationally expensive because only one FFT block (4096 samples) is analyzed per note onset. The maximum number of notes that can be detected is specified when running the Python script.
### Demo
https://www.youtube.com/watch?v=GwEdOo7iPuA&t=1s

# Installation

Download this repository to your local machine, and then install the following required software.

## Requirements

Pure data extended version and Python 3 need to be installed on your machine. 
- Download PD extended at https://puredata.info/downloads/pd-extended
- If you are not a Python user, I recommend downloading this Python 3 distribution: http://conda.pydata.org/miniconda.html (make you to download Python 3.5 not 2.7)

This Pure Data external compressor: https://github.com/twobigears/tb_peakcomp/releases must be installed (download it and put into your PD path).


Several Python libraries are required. To install each, open up terminal and enter the command following each library
  - Numpy (scientific computing)
  
    ```
    pip install numpy
    ```
    
  - Scikit-Learn (machine learning)
  
  
    ```
    pip install scikit-learn
    ```
    
  - Python-osc (Python OSC implementations)
  
    
    ```
    pip install python-osc
    ```
    
  - Mido (Python MIDI implementations)
  
    
    ```
    pip install mido
    ```


# Usage
- The pure data patch must always be running (audio_engine.pd) with DSP turned on, make sure audio settings are set up so that your instrument's audio is routed into pure data.

### Learning
- Before you can track notes, the program must 'learn' how each note on your instrument sounds. To do this, open up a terminal in this directory (i.e. the one containing this README) and run the 'learning server' by typing in

```
python learning_server.py --minnote E2 --maxnote C#6 
```

- These input parameters are for a 21 fret guitar in standard tuning, so change them according to your instrument. For example for an 88-key piano you would do

```
python learning_server.py --minnote A0 --maxnote C8
```

- Now the server should start running (assuming all installation went correctly). Next start the Pure Data OSC server by pressing the 'connect 127.0.0.1 9997' button (it's in the red box). Now start playing single, monophonic, notes on your instrument. If Python and Pure Data are communicating correctly, you should see output being printed to standard out. When learning server is running, the program is learning how individual notes sound on the instrument (so it can then in the future extrapolate this information to groups of notes), for best results make sure every note on your instrument is played atleast once (in the demo video, I trained the program by playing every note exactly twice, although playing each note the same amount of times is not necessary). You do not need to restart if you make any mistakes (e.g. on guitar if you misfret a note or hit an open string by accident), the program accounts for this. When your done hit ctrl+c and then say 'y' when it asks you to save.

- The data collected will be saved to a default filename. If you only want to create data for tracking 1 instrument, you can just use this. If you want to create a new data file without overwriting your old one, add the argument 'datafile' followed by the name you want (end it with '.p') when starting the learning server. For example 


```
python learning_server.py --minnote E2 --maxnote C#6 --datafile 'newdata.p'
```

- (Optional) if you want to check and make sure the learning went correctly, you can run 

```
python graph.py
```
note that this requires another python library which you can install in the same way as before

```
pip install matplotlib
```

this will output a graph of harmonics learned for each note, here's mine:

![alt text](https://github.com/jaym910/polyphonic_track/raw/master/datapic.png "Graph example")

You should see nice logarithmic curves like in the example above (the Y axis corresponds to each note learned on the instrument--in order--which is why we see the logarithmic curve). Note if you used a non-default name for the data file you have to go into the graph.py script and change the line DATAFILE accordingly.

### Tracking

- Now run the tracking server (you often have to disconnect pure data and reconnect pure data from OSC--click disconnect right below connect in the redbox of the PD patch and then click connect again)

```
python tracking_server.py
```

- By default the MIDI bus is selected to be IAC Bus Driver 1, so make sure this is running. Alternatively you can specify a different MIDI port with the command line arg --midiport, also if you are using a nondefault data file name, specify it in the same way as before. So for example:

 ```
 python tracking_server.py --datafilename 'altdata.p' --midiport 'Daemon Output 0'
 ```
 
If your not sure what name the midi port should be entered as, you can simply run the tracking_server and it will fail and output a message that contains all the midi ports on your computer as they should be entered as a commandline arg. Something like this should be printed:
 
 ```
To run with a different midi port, rerun this program with the command lineargument '--midi_port 'port name goes here'

Where 'port name goes here' corresponds to one of the following recognized midi ports:

['Daemon Output 0', 'Daemon Output 1', 'Daemon Output 2', 'Daemon Output 3', 'Daemon Output 4', 'Daemon Output 5', 'Daemon Output 6', 'Daemon Output 7', 'IAC Driver Bus 1', 'IAC Driver IAC Bus 2']
 ```
 
 - One last command line argument that can be entered here is 'max_notes_per_chord', this defaults to 6. Setting it as a higher number can produce interesting results as it can often sway the algorithm into guessing notes that aren't actually there, yet these notes almost always harmonically make sense with the true notes being played (see the ending bit of the demo video for an example).
 
 ```
python tracking_server.py --max_notes_per_chord 15
```

# Notes
This is an ongoing project and is by no means perfect. There is minor latency, and the pitch tracking is not always completely accurate (although as mentioned before, the notes guessed always make sense harmoincally with the real notes, so this could still be used in music production/performance scenarios). Other features that I would like to implement include adding an online machine learning routine so that the algorithm can learn even during the tracking server phase and get better and better over time.

A full list of command line args and info on them can be found by running
 
 ```
python tracking_server.py --help
```

 ```
python tracking_server.py --help
```

arguments here that were not discussed in the instructions are only necessary for more advanced usage (for example changing which ports to send OSC over), and in general should be ignored.
