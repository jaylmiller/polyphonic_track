import numpy as np
from sklearn.preprocessing import normalize
import re

SR = 44100
TOTAL_SIZE = 4096
CROP_SIZE = 256
NONZERO_COEFS = 6

freqs = np.fft.rfftfreq(TOTAL_SIZE, 1/SR)
freqs = freqs[:CROP_SIZE]

A4 = 440
C0 = A4*np.power(2, -4.75)

notenames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
pitch_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
acc_map = {'#': 1, '': 0, 'b': -1, '!': -1}
note_map = ['C', 'C#', 'D', 'D#',
            'E', 'F', 'F#', 'G',
            'G#', 'A', 'A#', 'B']

def pitch(freq):
    try:
        h = round(12*np.log2(freq/C0))
        octave = h // 12
        n = h % 12
        return notenames[int(n)] + str(int(octave))
    except:
        print("Could not compute pitch of:", freq)


def normalize_vector(b):
    try:
        b = normalize(b)
        return b
    except:
        return None


def create_notebins(min_note='C0', max_note='E7'):
    note_bins = [min_note]
    last_note = min_note
    idx = notenames.index(last_note[0])
    octave = int(min_note[1])
    while last_note != max_note:
        idx += 1
        last_note = notenames[idx % 12]+str(octave)
        note_bins += [last_note]
        if idx % 12 == 11:
            octave += 1
    return note_bins


def note_to_midi(note, round_midi=True):
    if not isinstance(note, str):
        return np.array([note_to_midi(n, round_midi=round_midi) for n in note])


    match = re.match(r'^(?P<note>[A-Ga-g])'
                     r'(?P<accidental>[#b!]*)'
                     r'(?P<octave>[+-]?\d+)?'
                     r'(?P<cents>[+-]\d+)?$',
                     note)
    if not match:
        print("Improper input {} to note_to_midi function".format(note))

    pitch = match.group('note').upper()
    offset = np.sum([acc_map[o] for o in match.group('accidental')])
    octave = match.group('octave')
    cents = match.group('cents')

    if not octave:
        octave = 0
    else:
        octave = int(octave)

    if not cents:
        cents = 0
    else:
        cents = int(cents) * 1e-2

    note_value = 12 * (octave + 1) + pitch_map[pitch] + offset + cents

    if round_midi:
        note_value = int(np.round(note_value))

    return note_value


def midi_to_note(midi):
    if not np.isscalar(midi):
        return [midi_to_note(x) for x in midi]

    note_num = int(np.round(midi))
    note_cents = int(100 * np.around(midi - note_num, 2))

    note = note_map[note_num % 12]

    if octave:
        note = '{:s}{:0d}'.format(note, int(note_num / 12) - 1)
    if cents:
        note = '{:s}{:+02d}'.format(note, note_cents)

    return note



def data_to_dict_matrix(data):
    dict_matrix = [np.average(np.array(i), axis=0) for i in data]
    dict_matrix = np.array([normalize_vector(i) for i in dict_matrix])
    return np.squeeze(dict_matrix)
