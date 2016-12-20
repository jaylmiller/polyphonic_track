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
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client
from utilities_globals import *

cnote = -1
data_per_note = None


def monophonic_handler(*args):
    global cnote
    m = int(np.round(float(args[1])))
    m -= min_note_midi
    print(m)
    cnote = m


def fft_handler(*args):
    global data_per_note
    if cnote >= 0 and cnote < len(data_per_note):
        print("updating data for note:", pitches_per_index[cnote])
        fft = args[1].split()
        fft = np.array([float(i) for i in fft])
        fft = normalize_vector(fft.reshape(1,-1))
        data_per_note[cnote] += [fft]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--serverport",
        type=int, default=9997, help="The port for server listen on")
    parser.add_argument("--clientport",
        type=int, default=9996, help="The client port")
    parser.add_argument("--datafile", default="fretdata.p",
        help="File to write data to (extension should be '.p')")
    parser.add_argument("--minnote", default="E2")
    parser.add_argument("--maxnote", default="C#6")
    args = parser.parse_args()
    pitches_per_index = create_notebins(min_note=args.minnote,
                                        max_note=args.maxnote)
    min_note_midi = note_to_midi(args.minnote)
    max_note_midi = note_to_midi(args.maxnote)
    data_per_note = [[] for i in pitches_per_index]

    datafilename = args.datafile
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/fftmag", fft_handler)
    dispatcher.map("/monophonic_signal", monophonic_handler)

    client = udp_client.SimpleUDPClient(args.ip, args.clientport)
    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.serverport), dispatcher)

    print("Serving on {}".format(server.server_address))
    print("Ctrl+C to quit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        save = input("Save? (y/n)")
        overwrite = None
        if save != 'y':
            sys.exit()
        try:
            old_data = pickle.load(open(datafilename, "rb"))
        except:
            pickle.dump(data_per_note, open(datafilename, "wb"))
            sys.exit()
        overwrite = input("Data file with same name already exists."
                          + "Overwrite data file or merge it? (o/m)")
        if overwrite == 'm':
            print("Merging data")
            data_per_note = old_data+data_per_note
        else:
            print("Overwriting previous data")
        pickle.dump(data_per_note, open(datafilename, "wb"))
