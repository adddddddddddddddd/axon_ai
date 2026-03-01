from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio, json
from mne_bids import read_raw_bids, BIDSPath

from models import User, Run, Step, BIDSDataset, Tasks, EEGFile, AgentThought
from database import engine
from sqlmodel import Session, select


from pathlib import Path
import os

from utils import (
    upload_image_to_catbox,
    ICAAnalysis,
    EEGSlowDriftAnalysis,
    EEGPipelineState,
    create_reasoning_messages,
    InitialQCResult,
    initial_qc_agent,
    bandpass_filter,
    BandpassFilterSettings,
    bandpass_filtering_agent,
    BadChannelAnalysis,
    bad_channel_identifier_agent,
    annotate_bad_channels,
    notch_filter,
    notch_filtering_agent,
    apply_slow_drift_correction,
    slow_drift_analysis_agent,
    resampling,
    prepare_ica_copy,
    apply_ica,
    ica_discrimination_agent,
    apply_ica_correction,
    interpolate_bad_channels,
    bids_path,
    ALZEIMER_EXPERIMENT_CONTEXT,
    attach_websocket_to_logger,
    detach_websocket_handler,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/signals/{run_id}/step/{step_id}/timeseries")
def get_timeseries(run_id: int, step_id: int):
    with Session(engine) as session:
        step = session.exec(select(Step).where(Step.id == step_id, Step.run_id == run_id)).first()
        if not step:
            return {"error": "Step not found"}
    raw = step.raw
    data, times = raw.get_data(return_times=True)
    
    # Downsample pour le web (IMPORTANT)
    data = data[:, ::10]
    times = times[::10]

    return {
        "channels": raw.ch_names,
        "data": data.tolist(),
        "times": times.tolist()
    }

@app.get("/signals/{run_id}/step/{step_id}/psd")
def get_psd(run_id: int, step_id: int):
    with Session(engine) as session:
        step = session.exec(select(Step).where(Step.id == step_id, Step.run_id == run_id)).first()
        if not step:
            return {"error": "Step not found"}
    psd = step.psd
    freqs = psd[0]  # Assuming freqs are stored in the first element
    psd_values = psd[1]  # Assuming PSD values are stored in the second element

    return {
        "freqs": freqs,
        "psd_values": psd_values
    }
    
@app.get("/signals/{run_id}/step/{step_id}/sensors")
def get_sensors(run_id: int, step_id: int):
    with Session(engine) as session:
        step = session.exec(select(Step).where(Step.id == step_id, Step.run_id == run_id)).first()
        if not step:
            return {"error": "Step not found"}
    sensor_topography = step.sensor_topography
    return {
        "sensor_topography": sensor_topography
    }
    
@app.get("/runs/{run_id}/step/{step_id}/ica_components")
def get_ica_components(run_id: int, step_id: int):
    with Session(engine) as session:
        step = session.exec(select(Step).where(Step.id == step_id, Step.run_id == run_id)).first()
        if not step:
            return {"error": "Step not found"}
    ica_components = step.ica_components
    return {
        "ica_components": ica_components
    }

@app.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket):
    await websocket.accept()
    ws_handler = attach_websocket_to_logger(websocket)

    # Tu appelles ton pipeline ici, et tu envoies des messages au fur et à mesure
    raw = read_raw_bids(bids_path=bids_path)
    raw.pick("all").load_data()
    websocket.send_text(json.dumps({"type": "pipeline", "step": 1}))
    current_stage = "initial_qc"
    state = EEGPipelineState(
        subject_id="001",  # Initialize with subject ID from bids_path
        current_stage=current_stage,
        input_raw=raw,
        output_raw=None,
        skip_stage=[],
        justification={},
        errors=[],
        experiment_metadata={"experiment_context": ALZEIMER_EXPERIMENT_CONTEXT},
        bad_channels=[],
        slow_drift_probability=None,
        ica_channels_to_remove=None,
        ica_justification=None,
        final_qc_assessment=None,
    )

    pipeline_states = {}  # To store state after each stage for debugging and analysis

    # state = initial_qc_agent(state)
    SKIP_STAGE = state["skip_stage"]
    websocket.send_text(json.dumps({"type": "log" , "text": f"Initial QC completed. Stages to skip: {SKIP_STAGE}"}))
    if SKIP_STAGE:
        websocket.send_text(json.dumps({"type": "log" , "text": f"Skipping stages: {SKIP_STAGE}"}))
    else:
        websocket.send_text(json.dumps({"type": "log" , "text": "No stages to skip. Proceeding with full pipeline."}))
    websocket.send_text(json.dumps({"type": "pipeline", "step": 2}))

    if "bandpass_filtering" not in SKIP_STAGE:
        # state = bandpass_filtering_agent(state)
        pass
    websocket.send_text(json.dumps({"type": "log" ,"text": f"Bandpass filtering completed. Justification: {state['justification'].get('bandpass_filtering', 'No justification provided.')}"}))
    websocket.send_text(json.dumps({"type": "pipeline", "step": 3}))

    if "bad_channel_identification" not in SKIP_STAGE:
        # state = bad_channel_identifier_agent(state)
        pass
    websocket.send_text(json.dumps({"type": "log" , "text": f"Bad channel identification completed. Justification: {state['justification'].get('bad_channel_identification', 'No justification provided.')}"}))
    state["output_raw"] = annotate_bad_channels(
        state["input_raw"], state["bad_channels"]
    )
    websocket.send_text(json.dumps({"type": "pipeline", "step": 4}))

    if "notch_filtering" not in SKIP_STAGE:
        # state = notch_filtering_agent(state)
        pass
    websocket.send_text(json.dumps({"type": "log" , "text": f"Notch filtering decision completed. Justification: {state['justification'].get('notch_filtering', 'No justification provided.')}"}))
    
    websocket.send_text(json.dumps({"type": "pipeline", "step": 5}))
    
    if "ica" not in state["skip_stage"]:
        state = resampling(state)
        state = prepare_ica_copy(state)
        ica = apply_ica(state)
        # state = ica_discrimination_agent(state, ica)
        state = apply_ica_correction(state, ica)
    websocket.send_text(json.dumps({"type": "log" , "text": f"ICA correction completed. Justification: {state.get('ica_justification', 'No justification provided.')}"}))

    websocket.send_text(json.dumps({"type": "pipeline", "step": 6}))


    if state["bad_channels"]:
        state["output_raw"] = interpolate_bad_channels(state["output_raw"])
    timeseries_fig = state["output_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    timeseries_fig.savefig("./images/final_timeseries.jpg")
    psd_fig = state["output_raw"].plot_psd(
        fmax=50
    )  # Generate PSD plot without displaying
    psd_fig.savefig("./images/final_psd.jpg")
    sensors_fig = state["output_raw"].plot_sensors(
        show_names=True
    )  # Generate sensor layout plot without displaying
    sensors_fig.savefig("./images/final_sensors.jpg")
            
    detach_websocket_handler(ws_handler)
    
    await websocket.close()
