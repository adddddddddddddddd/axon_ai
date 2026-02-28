import mne
import numpy as np

import os

if __name__ == "__main__":
    sample_data_folder = mne.datasets.sample.data_path()
    sample_data_raw_file = os.path.join(
        sample_data_folder, "MEG", "sample", "sample_audvis_raw.fif"
    )
    raw = mne.io.read_raw_fif(sample_data_raw_file)
    raw.crop(0, 60).load_data()  # just use a fraction of data for speed here
    raw.plot(n_channels=30, scalings="auto", show_scrollbars=False, title="Raw data", block=True)