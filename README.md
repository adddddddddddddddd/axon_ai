# Axon, the EEG Preprocessing AI Agent

The main goal of this project is to limit the time spent on the EEG preprocessing pipeline to let experts focus on the actual analysis of the results.

We are also implementing an ui to make interact with Axon easier. MCP could also be a thing.

A huge thanks for the work behind mne sdk. This is actually what powers the models capabilities and it is a wonderful package.

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

## Change dataset

You can specify which dataset you want to access by changing its import


```python
# axon_ai/main/main.py line 34
if not os.path.exists("../datasets/ds004504"):
    openneuro.download(dataset="ds004504", target_dir="../datasets/ds004504")
```

## Architecture

### Pipeline Flow

```
Initial QC Agent
    ↓
[Conditional] Notch Filtering Agent ← ─ ─ ┐
    ↓                                     │
Validation Agent                          │ (retry loop,
    ↓                                     │  max 3 times)
[Retry Check] ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
    ↓
Bad Channel Identifier Agent (✓ Implemented)
    ↓
Optional Notch Filtering Agent ← ─ ─ ┐
    ↓                                 │
Validation Agent                      │ (retry loop,
    ↓                                 │  max 3 times)
[Retry Check] ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
    ↓
Slow Drift Detector Agent (✓ Implemented)
    ↓
[Conditional] Slow Drift Corrector ← ─ ─ ┐
    ↓                                     │
Validation Agent                          │ (retry loop,
    ↓                                     │  max 3 times)
[Retry Check] ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
    ↓
[Conditional] ICA Application Agent ← ─ ─ ┐
    ↓                                      │
Bad ICA Detector Agent (✓ Implemented)    │
    ↓                                      │ (retry loop,
Stage QC Agent                             │  max 3 times)
    ↓                                      │
[Retry Check] ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
    ↓
Interpolation Agent
    ↓
Final QC Agent
```

### Key Features

- **Sequential Processing**: Agents execute in a defined order with conditional branches
- **Retry Mechanisms**: Failed validation triggers retry (max 3 attempts per stage)
- **Conditional Execution**: Stages can be skipped based on Initial QC assessment
- **State Management**: Complete pipeline state passed between agents
- **Visual Analysis**: Agents analyze EEG plots via image URLs
- **Structured Outputs**: Pydantic models ensure consistent agent responses

## File Structure

```
├── main.py                          # Main orchestrator and CLI
├── pipeline_state.py                # State schema definitions
├── pipeline_graph.py                # LangGraph workflow definition
├── agents.py                        # All agent implementations
├── bad_channel_detector.py          # Original bad channel agent (standalone)
├── slow_drift_analysis_agent.py    # Original slow drift agent (standalone)
├── ica_discrimination_agent.py     # Original ICA agent (standalone)
└── pyproject.toml                   # Dependencies
```


## Why Magistral Small 2509 ?

Axon is based on Magistral Small (2509 for the moment), which is a proprietary model from Mistral. Axon architecture leverages both vision and reasoning of the model and works very well on openneuro ds004504 cleaning. To be fair, Mistral's API has a generous free API plan.
Making it available through free, self-hosted models is a thing we could aim for.

