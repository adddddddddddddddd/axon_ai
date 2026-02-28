import mne
import numpy as np

import os

if __name__ == "__main__":

    root = mne.datasets.sample.data_path() / "MEG" / "sample"
    raw_file = root / "sample_audvis_filt-0-40_raw.fif"
    raw = mne.io.read_raw_fif(raw_file, preload=False)

    events_file = root / "sample_audvis_filt-0-40_raw-eve.fif"
    events = mne.read_events(events_file)

    raw.crop(tmax=90)  # in seconds (happens in-place)
    # discard events >90 seconds (not strictly neces
    events = events[events[:, 0] <= raw.last_samp]
    raw.pick(["eeg", "eog"]).load_data()
    raw.plot(duration=5, n_channels=1, scalings="auto", show_scrollbars=False, block=True)