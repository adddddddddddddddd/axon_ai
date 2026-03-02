# Axon, the EEG Preprocessing AI Agent

The main goal of this project is to limit the time spent on the EEG preprocessing pipeline to let experts focus on the actual analysis of the results.

We are also implementing an ui to make interact with Axon easier. MCP could also be a thing.

A huge thanks for the work behind mne sdk. This is actually what powers the models capabilities and it is a wonderful package.

# How to use

## Setup
```
#Clone the repository
git clone git@github.com:adddddddddddddddd/axon_ai.git

# Go in the file you just created by cloning it
cd axon_ai

# Install dependencies and create virtual environment
uv sync

# Run the main file to preprocess the data for openneuro ds004504 of subject 001
cd main
uv run main.py

```
## Modifying the input data
### Change dataset

You can specify which dataset you want to access by changing its import


```python
# axon_ai/main/main.py line 34
if not os.path.exists("../datasets/ds004504"):
    openneuro.download(dataset="ds004504", target_dir="../datasets/ds004504")
```

### Change subject

You can specify which subject you want to preprocess by changing the subject id in the BIDSPath object

```python
# axon_ai/main/main.py line 42
bids_path = BIDSPath(
    subject="sub-001",
    session="ses-01",
    task="rest",
    datatype="eeg",
    root="../datasets/ds004504"
)
```

## Output
The preprocessed data will be stored in the `images` folder. You can change this by modifying the `OUTPUT_DIR` variable in `main.py`.

# Architecture

## Pipeline Flow

```
Initial QC Agent - Planning Agent
    ↓
[Conditional] Notch Filtering Agent ← ─ ─ ┐
    ↓                                     │ (Agent loop)
[Validation by plot analysis] ─ ─ ─ ─ ─ ─ ┘
    ↓
Bad Channel Identifier Agent
    ↓
Optional Notch Filtering Agent 
    ↓
Slow Drift Detector Agent
    ↓
Slow Drift Corrector (if needed)
    ↓
ICA Application Agent
    ↓                                      
Bad ICA Detector Agent (if needed)   
    ↓
Interpolation Agent (if Bad Channel Handoff to him)
    ↓
Final result
```

## Key Features and leveraged features from Magistral

- **Sequential Processing**: Agents execute in a defined order with conditional branches thanks to the Planner
- **Retry Mechanisms**: The Agent is fed the results of his tool usage again to see whether or not it might be necessary to reapply one of his tools before handoff.
- **Conditional Execution**: Stages can be skipped based on Initial QC assessment and "_Detector_" agents
- **State Management**: Complete pipeline state passed between agents
- **Visual Analysis**: Agents analyze EEG plots via image URLs
- **Structured Outputs**: Pydantic models ensure consistent agent responses 
- **Mistral native tool usage and Reasoning**

## File Structure

```
├── pyproject.toml                   # Dependencies
├── README.md                        # This file
├── drafts/                          # Pipeline implementation (work in progress)
│   ├── main.py                      # Main orchestrator and CLI
│   ├── pipeline_state.py            # State schema definitions
│   ├── pipeline_graph.py            # LangGraph workflow definition
│   ├── agents.py                    # All agent implementations
│   ├── bad_channel_detector.py      # Original bad channel agent (standalone)
│   ├── slow_drift_analysis_agent.py # Original slow drift agent (standalone)
│   ├── ica_discrimination_agent.py  # Original ICA agent (standalone)
│   ├── eeg_utils.py                 # EEG utility functions
│   └── pytest.ini                   # Test configuration
├── main/                            # Main application entry point
│   ├── __init__.py
│   ├── main.py                      # Production main file
│   └── images/                      # Generated images
├── frontend/                        # Next.js web interface
│   ├── app/                         # Next.js app directory
│   ├── components/                  # React components
│   └── lib/                         # Frontend utilities
└── server/                          # Backend server
    ├── main.py                      # FastAPI server
    ├── database.py                  # Database configuration
    ├── models.py                    # Data models
    └── alembic/                     # Database migrations
```



## Agent Details

### Implemented Agents (✓)

These agents use Mistral's multimodal reasoning models to analyze EEG plots and make preprocessing decisions:

#### 1. Initial QC Agent
- **Model**: `magistral-small-2509` (reasoning mode)
- **Input**: Raw EEG timeseries plot, PSD plot, and sensor layout
- **Output**: List of pipeline stages to skip with justifications
- **Logic**: Analyzes initial data quality to determine which preprocessing steps are necessary (bandpass filtering, notch filtering, bad channel identification, slow drift correction, ICA)
- **Response Format**: `InitialQCResult` (structured Pydantic model)

#### 2. Bandpass Filtering Agent
- **Model**: `mistral-large-2512` (tool usage)
- **Input**: Experiment context metadata
- **Output**: Optimal bandpass filter settings (low and high cutoff frequencies)
- **Tools**: `bandpass_filter(l_freq, h_freq)`
- **Logic**: Determines appropriate frequency band based on experiment type (default: 0.5-45 Hz for Alzheimer's EEG analysis)
- **Behavior**: Iterative tool calling until filter is properly applied

#### 3. Bad Channel Identifier Agent
- **Model**: `magistral-small-2509` (reasoning mode)
- **Input**: EEG timeseries plot URL
- **Output**: List of bad channels to remove with justification
- **Logic**: Identifies channels with flat lines or near-zero activity across the entire recording
- **Response Format**: `BadChannelAnalysis` (structured Pydantic model)

#### 4. Notch Filtering Agent
- **Model**: `magistral-small-2509` (reasoning mode + tool usage)
- **Input**: PSD plot URL, list of available channels
- **Output**: Decision on whether notch filtering is needed, frequencies to filter, and channels to apply to
- **Tools**: `notch_filter(freqs, picks)`
- **Logic**: 
  - Analyzes PSD for narrow 50/60 Hz line noise peaks
  - Only applies notch if clear narrow peak exists within analysis band
  - Selects specific frequencies (50 or 60 Hz + harmonics if clearly present)
  - Targets specific channels carrying line noise or applies to all if widespread
- **Behavior**: May skip notch filtering if no clear line noise is detected

#### 5. Slow Drift Analysis Agent
- **Model**: `magistral-small-2509` (reasoning mode)
- **Input**: EEG timeseries plot URL
- **Output**: Probability (0-1) of slow drift presence with justification
- **Logic**: 
  - Detects gradual baseline shifts across channels
  - Applies high-pass filter (0.5 Hz) to correct drifts if probability > 0.5 threshold
- **Response Format**: `EEGSlowDriftAnalysis` (structured Pydantic model with validated probability)

#### 6. Resampling Processor
- **Type**: Processing function (non-AI agent)
- **Input**: Raw EEG data
- **Output**: Resampled data at 250 Hz
- **Logic**: Uses polyphase method for anti-aliasing resampling before ICA
- **Purpose**: Reduces computational cost for ICA while preserving signal quality

#### 7. ICA Preparation Processor
- **Type**: Processing function (non-AI agent)
- **Input**: Resampled EEG data
- **Output**: High-pass filtered copy for ICA (1.0-45 Hz)
- **Logic**: Creates dedicated copy with stronger high-pass filter (1.0 Hz) to improve ICA decomposition
- **Purpose**: Removes slow drifts that can interfere with ICA component separation

#### 8. ICA Application Processor
- **Type**: Processing function (non-AI agent)
- **Input**: Prepared EEG data
- **Output**: Fitted ICA object
- **Logic**: Fits ICA with n_components = min(n_channels - 1, 20)
- **Method**: Uses MNE's default FastICA algorithm

#### 9. ICA Discrimination Agent
- **Model**: `magistral-small-2509` (reasoning mode)
- **Input**: ICA components topography plot, ICA source timeseries plot
- **Output**: List of ICA component indices to remove with justification
- **Logic**: Identifies artifact components based on:
  - **Blinks**: Vertical eye movement patterns in frontal components
  - **Eye movements**: Horizontal step functions in frontal/temporal components
  - **ECG**: QRS complex patterns (sharp peak + inverted peak)
  - **Muscle artifacts**: High-frequency bursts, localized to face/neck
  - **Line noise**: Strong 50/60 Hz peaks in component spectrum
  - **EOG correlation**: Components resembling EOG signal patterns
- **Response Format**: `ICAAnalysis` (structured Pydantic model)
- **Constraint**: Returns validated list of components (asserted non-empty list)

#### 10. ICA Correction Processor
- **Type**: Processing function (non-AI agent)
- **Input**: Original raw data, ICA object, components to remove
- **Output**: Artifact-corrected EEG data
- **Logic**: 
  - Converts component labels (e.g., "ICA001") to zero-indexed integers
  - Sets ICA.exclude list
  - Applies ICA inverse transform with excluded components

#### 11. Bad Channel Interpolation Processor
- **Type**: Processing function (non-AI agent)
- **Input**: EEG data with annotated bad channels
- **Output**: Data with interpolated bad channels
- **Logic**: Uses spherical spline interpolation to estimate signal at bad channel locations from neighboring good channels
- **Purpose**: Restores complete channel montage for downstream analysis

## Why Magistral Small 2509 ?

Axon is based on Magistral Small (2509 for the moment), which is a proprietary model from Mistral. Axon architecture leverages both vision and reasoning of the model and works very well on openneuro ds004504 cleaning. To be fair, Mistral's API has a generous free API plan.
Making it available through free, self-hosted models is a thing we could aim for.


## TODOs

- Implement frontend backend interaction with signal storage and retrieval

## Mistral docs

https://docs.mistral.ai/