"""
If executing this script returns an 'Address already in use' error
make sure there are no processes running on the ports already.
To do that run 'sudo lsof -i:9997' 'sudo lsof -i:9998'
(9997 and 9998 are the default ports used here, so adjust accordingly
if using different ports) This commands brings up list of processes using these ports,
and gives their PID. For each process type, 'kill XXXX' where XXXX is PID.
Also, make sure the pure data patch is disconnected when you do this, otherwise
it will show up in the list and killing the process will quit the patch.
"""


import argparse
import sys
import pickle
import numpy as np
from sklearn.decomposition import sparse_encode
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client
import mido
from utilities_globals import *


NONZERO_COEFS = 6 # corresponds to maximum possible notes at once
current_note_fft = []


def on_handler(*args):
    global current_note_fft
    print("on") # just for sanity checking
    current_note_fft = []
    return


def off_handler(*args):
    """
    Send midi off messages to all active notes when we detect guitar string
    is no longer playing sound
    """
    midiout.reset()


def get_relevant_pitches(pitches, c):
    """
    TODO: Make this method more robust
    This method takes the maximum coefficients of
    a sparse encoding and determines which coefficients correspond to real notes"""
    print(pitches)
    print(c)
    pitches = pitches[::-1]
    midi = note_to_midi(pitches)
    c = c[::-1]
    rel = [pitches[0]]
    for i in range(1, len(pitches)):
        if c[i] > .1:
            pass
        else:
            break
        if np.any(np.abs([(midi[i]-m) for m in midi[:i]]) < 2):
            continue
        rel += [pitches[i]]
    return rel


def sendMIDI_out(data):
    print('sending notes:', data)
    midi = [int(m) for m in note_to_midi(data)]
    for m in midi:
        midiout.send(mido.Message('note_on', note=m, velocity=100))

"""
def sendOSC_for_PD_synth(comps):
    n = 1
    topones = []
    ampsum = 0
    for i in indices[:3]:
        freq = comps[i]
        freqi = np.argsort(freq)
        topamp = np.max(freq)
        topfreq = freqs[freqi[-1]]
        topones += [(topfreq, topamp)]
        ampsum += topamp
    print("Top 3 freq/amp outputs")
    for i, (freq,amp) in enumerate(topones):
        msgf = '/freq'+str(i+1)
        msga = '/amp'+str(i+1)
        print(msgf)
        print(freq, amp)
        print(pitch(freq))
        client.send_message(msgf, freq)
        client.send_message(msga, amp)
"""

def fft_handler(*args):
    global current_note_fft
    print(len(current_note_fft))
    fft = args[1].split()
    fft = np.array([float(i) for i in fft])
    n = normalize_vector(fft.reshape(1, -1))[0]
    if n is None:
        return
    current_note_fft += [n]
    if len(current_note_fft) == 10:
        s = sparse_encode(n.reshape(1, -1), data_per_fret, algorithm='lars',
            n_nonzero_coefs=NONZERO_COEFS)
        s = s[0]
        a = np.argsort(s)
        coeffs = [s[i] for i in a[-NONZERO_COEFS:]]
        coeffs = normalize_vector(np.array(coeffs))[0]
        pitches = [guitar_notes[i] for i in a[-NONZERO_COEFS:]]
        print(pitches)
        print(coeffs)
        d = get_relevant_pitches(pitches, coeffs)
        sendMIDI_out(d)

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--serverport",
        type=int, default=9997, help="The port for server listen on")
    parser.add_argument("--clientport",
        type=int, default=9996, help="The client port")
    parser.add_argument("--datafile", default="fretdata.p",
        help="File to write data to (extension should be '.p')")
    parser.add_argument("--max_notes_per_chord", type=int, default=6)
    parser.add_argument("--midi_port", default='IAC Driver Bus 1')
    args = parser.parse_args()
    try:
        midiout = mido.open_output(args.midi_port)
    except:
        print("The midi port {} could not be found".format(args.midi_port))
        print("To run with a different midi port, rerun this program with the command line"+
            "argument '--midi_port 'port name goes here' ")
        print("Where 'port name goes here' corresponds to one of the following recognized midi ports:")
        print(mido.get_output_names())
        sys.exit()

    guitar_notes = create_notebins(min_note='E2', max_note='C#6')
    NONZERO_COEFS = args.max_notes_per_chord
    datafilename = args.datafile
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/fftmag", fft_handler)
    dispatcher.map("/on", on_handler)
    dispatcher.map("/off", off_handler)

    try:
        data_per_fret = pickle.load(open(datafilename, "rb"))
    except:
        print("file {} not found".format(datafilename))
        sys.exit()
    data_per_fret = data_to_dict_matrix(data_per_fret)
    client = udp_client.SimpleUDPClient(args.ip, args.clientport)
    print(data_per_fret.shape)
    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.serverport), dispatcher)
    print("Serving on {}".format(server.server_address))
    print("Ctrl+C to quit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        midiout.close();
        sys.exit()
