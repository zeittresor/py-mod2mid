import tkinter as tk
from tkinter import filedialog, messagebox
from mido import Message, MidiFile, MidiTrack, MetaMessage
import math
import os

# Known ProTracker note periods (PAL) for one octave, extended for multiple octaves.
# We'll use a reference table and find the closest note for a given period.
# Reference standard periods from a common ProTracker note table (C-1 to B-3):
PROTRACKER_NOTES = [
    ("C-1", 856), ("C#1", 808), ("D-1", 762), ("D#1", 720), ("E-1", 678), ("F-1", 640), ("F#1", 604), ("G-1", 570), ("G#1", 538), ("A-1", 508), ("A#1", 480), ("B-1", 453),
    ("C-2", 428), ("C#2", 404), ("D-2", 381), ("D#2", 360), ("E-2", 340), ("F-2", 320), ("F#2", 302), ("G-2", 285), ("G#2", 269), ("A-2", 254), ("A#2", 240), ("B-2", 226),
    ("C-3", 214), ("C#3", 202), ("D-3", 190), ("D#3", 180), ("E-3", 170), ("F-3", 160), ("F#3", 151), ("G-3", 143), ("G#3", 135), ("A-3", 127), ("A#3", 120), ("B-3", 113)
]

# Map ProTracker notes to MIDI notes. We'll assume C-1 = MIDI note 24 as a baseline.
# C-1 ~ 856 period → Let's define C-1 as MIDI 24, then each semitone up adds 1.
BASE_MIDI = 24
PT_NOTE_TO_MIDI = {}
for i, (nname, period) in enumerate(PROTRACKER_NOTES):
    PT_NOTE_TO_MIDI[period] = BASE_MIDI + i

# For periods not exactly matching, find nearest period in table
def period_to_midi_note(period):
    if period is None:
        return None
    closest_period = None
    closest_diff = 999999
    closest_midi = None
    for p in PT_NOTE_TO_MIDI:
        diff = abs(p - period)
        if diff < closest_diff:
            closest_diff = diff
            closest_period = p
            closest_midi = PT_NOTE_TO_MIDI[p]
    return closest_midi

INSTRUMENT_KEYWORDS = [
    (["piano", "pian", "keys", "grand", "klav"], 0),
    (["brightpiano", "bright"], 1),
    (["electricpiano", "elecpian", "epian", "epno"], 4),
    (["honky", "honkytonk"], 2),
    (["rhodes", "e-piano2", "fender"], 5),
    (["harpsi", "harp", "cembalo"], 6),
    (["clav", "clavi"], 7),
    (["celesta", "celeste"], 8),
    (["glocken", "glockenspiel", "bell", "chime"], 9),
    (["musicbox", "box"], 10),
    (["vibra", "vibraphone"], 11),
    (["marimba", "marimb"], 12),
    (["xylophone", "xylo"], 13),
    (["tubebell", "tubular", "carillon"], 14),
    (["dulcimer", "cymbalom"], 15),
    (["organ", "hammond", "church", "orgel"], 16),
    (["reed", "accord", "harmon", "bandoneon"], 21),
    (["guitar", "guit", "gtar"], 24),
    (["jazzguitar", "jazzguit"], 26),
    (["clean", "cleanguitar"], 27),
    (["mutedguitar", "mtdguit"], 28),
    (["overdrive", "odguit", "distorted"], 29),
    (["harmguitar", "harmonicsguit"], 30),
    (["bass", "bazz", "lowend", "tbass"], 32),
    (["fretless", "frtlbass"], 35),
    (["slapbass", "slpbas"], 36),
    (["synthbass", "synbass", "sbass"], 38),
    (["violin", "cello", "viol", "vl", "strings"], 40),
    (["pizz", "pizzicato"], 45),
    (["harp", "harfe", "harpisch"], 46),
    (["timpani", "timp"], 47),
    (["ensemble", "stringensemble"], 48),
    (["synthstrings", "synstrings"], 50),
    (["choir", "vox", "voice", "ahh", "ohh"], 52),
    (["orchestra", "orch"], 48),
    (["trumpet", "tromp"], 56),
    (["trombone", "tromb"], 57),
    (["tuba"], 58),
    (["mutedtrumpet", "mutetrump"], 59),
    (["horn", "frenchhorn"], 60),
    (["brass", "brs", "brassens"], 61),
    (["sax", "saxophone"], 64),
    (["oboe", "obo"], 68),
    (["englishhorn", "enghorn"], 69),
    (["bassoon", "fagott"], 70),
    (["clarinet", "klarin"], 71),
    (["piccolo"], 72),
    (["flute", "flut", "flöte"], 73),
    (["recorder", "blockflöte"], 74),
    (["panflute", "pan"], 75),
    (["bottle", "bottleneck", "blowbottle"], 76),
    (["shakuhachi"], 77),
    (["whistle", "pfiff"], 78),
    (["ocarina"], 79),
    (["squar", "square"], 80),
    (["saw", "sawtooth"], 81),
    (["calliope"], 82),
    (["chiff"], 83),
    (["charang"], 84),
    (["voicelead", "solo vox", "leadvox"], 85),
    (["fifths", "fifth"], 86),
    (["basslead"], 87),
    (["newage", "new age", "pad"], 88),
    (["warm", "warm pad"], 89),
    (["polysynth", "poly"], 90),
    (["choirpad", "choir pad"], 91),
    (["bowed", "bowedglass"], 92),
    (["metalpad"], 93),
    (["halopad"], 94),
    (["sweeper"], 95),
    (["rain"], 96),
    (["soundtrack"], 97),
    (["crystal"], 98),
    (["atmos", "atmosphere"], 99),
    (["brightness", "brightpad"], 100),
    (["goblins"], 101),
    (["echoes", "echo"], 102),
    (["sci-fi", "scifi"], 103),
    (["sitar"], 104),
    (["banjo"], 105),
    (["shamisen"], 106),
    (["koto"], 107),
    (["kalimba"], 108),
    (["bagpipe"], 109),
    (["fiddle"], 110),
    (["shanai"], 111),
    (["tinkle bell"], 112),
    (["agogo"], 113),
    (["steel drums"], 114),
    (["woodblock"], 115),
    (["taiko", "taikodrum"], 116),
    (["melodictom"], 117),
    (["synthdrum", "drum synth"], 118),
    (["reverse cymbal"], 119),
    (["guitarfretnoise"], 120),
    (["breathnoise", "breath"], 121),
    (["seashore"], 122),
    (["birdtweet", "bird", "tweet"], 123),
    (["telephone", "phone"], 124),
    (["helicopter"], 125),
    (["applause", "clap"], 126),
    (["gunshot"], 127)
]

DRUM_KEYWORDS = ["drum", "kick", "snare", "hihat", "hat", "cymbal", "tom", "perc", "808", "909", "crash", "ride", "shaker", "tambo", "rimshot", "tambourine"]
DRUM_CHANNEL = 9

def guess_instrument(sample_name):
    s = sample_name.strip().lower()
    for dk in DRUM_KEYWORDS:
        if dk in s:
            return ("drum", None)
    best_prog = None
    best_len = 0
    for kw_list, prog_num in INSTRUMENT_KEYWORDS:
        for kw in kw_list:
            if kw in s and len(kw) > best_len:
                best_len = len(kw)
                best_prog = prog_num
    return ("melodic", best_prog)

def read_mod_file(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 1084:
        raise ValueError("Invalid MOD file")
    title = data[0:20].decode('ascii', 'replace').strip('\x00')
    samples = []
    pos = 20
    for i in range(31):
        s_name = data[pos:pos+22].decode('ascii', 'replace').strip('\x00')
        s_length = (data[pos+22] << 8) | data[pos+23]
        finetune = data[pos+24] & 0x0F
        volume = data[pos+25]
        rep_start = (data[pos+26] << 8) | data[pos+27]
        rep_len = (data[pos+28] << 8) | data[pos+29]
        samples.append({
            "name": s_name,
            "length": s_length*2,
            "finetune": finetune,
            "volume": volume,
            "repeat_start": rep_start*2,
            "repeat_length": rep_len*2
        })
        pos += 30
    song_length = data[pos]
    restart_pos = data[pos+1]
    pattern_table = data[pos+2:pos+2+128]
    pos += 130
    highest_pattern = 0
    for p in pattern_table:
        if p > highest_pattern:
            highest_pattern = p
    num_patterns = highest_pattern + 1
    mod_type = data[1080:1084].decode('ascii', 'replace')
    if mod_type not in ["M.K.", "M!K!", "4CHN", "FLT4", "4CH"]:
        channels = 4
        pattern_data_pos = pos
    else:
        channels = 4
        pattern_data_pos = 1084
    patterns = []
    fpos = pattern_data_pos
    pattern_size = 64 * channels * 4
    for pn in range(num_patterns):
        p_data = data[fpos:fpos+pattern_size]
        fpos += pattern_size
        pattern_rows = []
        for row_i in range(64):
            row_channels = []
            for ch in range(channels):
                c_off = (row_i*channels + ch)*4
                d0, d1, d2, d3 = p_data[c_off], p_data[c_off+1], p_data[c_off+2], p_data[c_off+3]
                period = ((d0 & 0x0F) << 8) | d1
                inst_high = (d0 & 0xF0)
                inst_low = (d2 & 0xF0) >>4
                instrument = (inst_high | inst_low)//16
                effect = d2 & 0x0F
                effect_param = d3
                if period == 0:
                    p_val = None
                else:
                    p_val = period
                if instrument == 0:
                    i_val = None
                else:
                    i_val = instrument
                row_channels.append({
                    "period": p_val,
                    "instrument": i_val,
                    "effect": effect,
                    "effect_param": effect_param
                })
            pattern_rows.append(row_channels)
        patterns.append(pattern_rows)
    return {
        "title": title,
        "samples": samples,
        "song_length": song_length,
        "restart_pos": restart_pos,
        "pattern_table": pattern_table[:song_length],
        "patterns": patterns,
        "channels": channels,
        # We will no longer rely on freq_factor. We'll use period_to_midi_note.
        "freq_factor": 7093789 / 2.0
    }

def convert_mod_to_midi(mod_data, force_piano=False):
    mid = MidiFile(type=1)
    track = MidiTrack()
    mid.tracks.append(track)
    title = mod_data.get("title", "MOD Song")
    track.append(MetaMessage('track_name', name=title, time=0))
    samples = mod_data["samples"]
    patterns = mod_data["patterns"]
    pattern_table = mod_data["pattern_table"]
    channels = mod_data["channels"]
    instrument_map = []
    used_non_drum_channels = []
    for i, smp in enumerate(samples):
        t, prog = guess_instrument(smp["name"])
        if force_piano and t == "melodic":
            prog = 0
        if t == "drum":
            instrument_map.append((DRUM_CHANNEL, None))
        else:
            if prog is None:
                prog = 0  # default piano if unknown
            ch_found = False
            for ch_candidate in range(16):
                if ch_candidate == DRUM_CHANNEL:
                    continue
                if ch_candidate not in used_non_drum_channels:
                    used_non_drum_channels.append(ch_candidate)
                    instrument_map.append((ch_candidate, prog))
                    ch_found = True
                    break
            if not ch_found:
                instrument_map.append((0, prog))
    done_program = set()
    for (ch, prog) in instrument_map:
        if ch != DRUM_CHANNEL and prog is not None and (ch, prog) not in done_program:
            track.append(Message('program_change', program=prog, channel=ch, time=0))
            done_program.add((ch, prog))
    bpm = 125
    tempo = int(60000000 / bpm)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    mid.ticks_per_beat = 480
    ticks_per_16th = 120
    channel_current_instrument = [None]*channels
    for pat_index in pattern_table:
        if pat_index >= len(patterns):
            continue
        pattern = patterns[pat_index]
        for row in pattern:
            note_events = []
            for ch_idx, ch_data in enumerate(row):
                period = ch_data["period"]
                instrument = ch_data["instrument"]
                if instrument is not None and instrument > 0 and instrument <= len(samples):
                    channel_current_instrument[ch_idx] = instrument-1
                inst_idx = channel_current_instrument[ch_idx]
                if inst_idx is None or inst_idx < 0 or inst_idx >= len(samples):
                    continue
                smp = samples[inst_idx]
                chan, prog = instrument_map[inst_idx]
                if period is not None:
                    note = period_to_midi_note(period)
                    if note is None:
                        note = 60
                    vol = int((smp["volume"]/64)*127)
                    if vol < 1:
                        vol = 80
                    note_events.append(Message('note_on', note=note, velocity=vol, channel=chan, time=0))
                    note_events.append(Message('note_off', note=note, velocity=0, channel=chan, time=ticks_per_16th))
            if not note_events:
                # advance time anyway
                track.append(MetaMessage('set_tempo', tempo=tempo, time=ticks_per_16th))
            else:
                for msg in note_events:
                    track.append(msg)
    return mid

class ModToMidiGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("MOD to MIDI Converter")
        self.mod_file_path = tk.StringVar()
        self.midi_file_path = tk.StringVar()
        self.force_piano = tk.BooleanVar(value=False)

        self.mod_label = tk.Label(master, text="MOD file:")
        self.mod_label.grid(row=0, column=0, sticky="e")
        self.mod_entry = tk.Entry(master, textvariable=self.mod_file_path, width=50)
        self.mod_entry.grid(row=0, column=1, padx=5, pady=5)
        self.mod_button = tk.Button(master, text="Open...", command=self.select_mod_file)
        self.mod_button.grid(row=0, column=2, padx=5, pady=5)

        self.midi_label = tk.Label(master, text="Save MIDI as:")
        self.midi_label.grid(row=1, column=0, sticky="e")
        self.midi_entry = tk.Entry(master, textvariable=self.midi_file_path, width=50)
        self.midi_entry.grid(row=1, column=1, padx=5, pady=5)
        self.midi_button = tk.Button(master, text="Save as...", command=self.select_midi_file)
        self.midi_button.grid(row=1, column=2, padx=5, pady=5)

        self.force_piano_check = tk.Checkbutton(master, text="Force unknown instruments to piano", variable=self.force_piano)
        self.force_piano_check.grid(row=2, column=0, columnspan=3, pady=5)

        self.convert_button = tk.Button(master, text="Convert", command=self.convert)
        self.convert_button.grid(row=3, column=0, columnspan=3, pady=10)

    def select_mod_file(self):
        path = filedialog.askopenfilename(filetypes=[("MOD Files", "*.mod")])
        if path:
            self.mod_file_path.set(path)

    def select_midi_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI Files", "*.mid")])
        if path:
            self.midi_file_path.set(path)

    def convert(self):
        mod_path = self.mod_file_path.get()
        midi_path = self.midi_file_path.get()
        if not mod_path or not midi_path:
            messagebox.showerror("Error", "Please specify MOD input file and MIDI output file.")
            return
        if not os.path.isfile(mod_path):
            messagebox.showerror("Error", "MOD file does not exist.")
            return
        try:
            mod_data = read_mod_file(mod_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading MOD file:\n{e}")
            return
        try:
            midi_file = convert_mod_to_midi(mod_data, force_piano=self.force_piano.get())
            midi_file.save(midi_path)
            messagebox.showinfo("Success", "File successfully converted!")
        except Exception as e:
            messagebox.showerror("Error", f"Error converting file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModToMidiGUI(root)
    root.mainloop()
