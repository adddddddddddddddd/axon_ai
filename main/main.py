import logging
import json
import os
from pathlib import Path
from typing import Optional, TypedDict, List, Dict, Any
import mne
from mne_bids import BIDSPath, read_raw_bids
from mne.preprocessing import ICA
import openneuro
from pydantic import BaseModel, Field, field_validator

import argparse

from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
api_key = os.environ["MISTRAL_API_KEY"]
model = "magistral-small-2509"
client = Mistral(api_key=api_key)

SLOW_DRIFT_THRESHOLD = 0.5  # Threshold for deciding if slow drift correction is needed

if not os.path.exists("../datasets/ds004504"):
    openneuro.download(dataset="ds004504", target_dir="../datasets/ds004504")


bids_path = BIDSPath(
    subject="001",  # Replace with subject ID (e.g., '001' to '088')
    task="eyesclosed",
    root="../datasets/ds004504",
    datatype="eeg",
)


class ICAAnalysis(BaseModel):
    ica_channels_to_remove: list = Field(
        description="List of ICA channels to remove based on the analysis"
    )
    justification: str = Field(
        description="A brief explanation of the reasoning behind the selected ICA channels, referencing specific features in the ICA plots such as artifacts, noise, or other relevant observations."
    )


class EEGSlowDriftAnalysis(BaseModel):
    slow_drift_probability: float = Field(
        description="Probability between 0 and 1 indicating whether the EEG data shows signs of slow drifts"
    )

    @field_validator("slow_drift_probability")
    @classmethod
    def validate_probability(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Probability must be between 0 and 1")
        return v

    justification: str = Field(
        description="A brief explanation of the reasoning behind the assigned probability, referencing specific features in the EEG plot such as baseline shifts, trends across channels, or other relevant observations."
    )


class EEGPipelineState(TypedDict):
    """Complete state for the EEG preprocessing pipeline"""

    # Subject identifier
    subject_id: str
    
    # Current processing stage
    current_stage: str

    input_raw: mne.io.Raw
    output_raw: Optional[mne.io.Raw]

    skip_stage: List[str]
    justification: Dict[str, str]

    errors: List[str]

    experiment_metadata: Dict[str, Any]

    bad_channels: List[str]
    
    # Additional fields used by agents
    slow_drift_probability: Optional[float]
    ica_channels_to_remove: Optional[List[int]]
    ica_justification: Optional[str]
    final_qc_assessment: Optional[str]


def create_reasoning_messages(user_prompt: str, image_url: str) -> list:
    """Create message structure for Mistral reasoning mode"""
    return [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "# HOW YOU SHOULD THINK AND ANSWER\n\nFirst draft your thinking process (inner monologue) until you arrive at a response. Format your response using Markdown, and use LaTeX for any mathematical equations. Write both your thoughts and the response in the same language as the input.\n\nYour thinking process must follow the template below:",
                },
                {
                    "type": "thinking",
                    "thinking": [
                        {
                            "type": "text",
                            "text": "Your thoughts or/and draft, like working through an exercise on scratch paper. Be as casual and as long as you want until you are confident to generate the response to the user.",
                        }
                    ],
                },
                {"type": "text", "text": "Here, provide a self-contained response."},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": image_url},
            ],
        },
    ]


raw = read_raw_bids(bids_path=bids_path)

# Create images directory if it doesn't exist
os.makedirs("./images", exist_ok=True)

current_stage = "initial_qc"
state = EEGPipelineState(
    subject_id="001",  # Initialize with subject ID from bids_path
    current_stage=current_stage,
    input_raw=raw,
    output_raw=None,
    skip_stage=[],
    justification={},
    errors=[],
    experiment_metadata={"experiment_context": ""},
    bad_channels=[],
    slow_drift_probability=None,
    ica_channels_to_remove=None,
    ica_justification=None,
    final_qc_assessment=None,
)

pipeline_states = {}  # To store state after each stage for debugging and analysis


class InitialQCResult(BaseModel):
    skip_stages: List[str]
    justification: Dict[str, str]


def initial_qc_agent(state: EEGPipelineState) -> EEGPipelineState:
    """
    [TBC] Initial quality control agent.
    Determines which pipeline stages are necessary based on initial data assessment.
    """
    logging.info(f"[INITIAL QC] Processing subject {state['subject_id']}")

    input_timeseries_fig = state["input_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    input_timeseries_fig.savefig("./images/raw_timeseries.jpg")

    input_psd_fig = state["input_raw"].plot_psd(
        fmax=50
    )  # Generate PSD plot without displaying
    input_psd_fig.savefig("./images/psd_plot.jpg")

    input_sensors_fig = state["input_raw"].plot_sensors(
        show_names=True
    )  # Generate sensor layout plot without displaying
    input_sensors_fig.savefig("./images/sensors.jpg")

    try:
        prompt = """You are a helpful assistant for EEG data analysis. I will give you an image of raw EEG data. Based on the visual analysis of the plot, determine which preprocessing steps are necessary for this data. Consider the following:
        Looking at raw plot, expert looks at:
            if recording looks fairly continuous and biologically plausible.
            If there are blatantly dead/flat channels.
            If there are channels with huge persistent amplitude dominating everything.
            If there is slow drift / low-frequency fluctuation across many channels.
            If there is some frontal activity that could be eye-related. 
            If there is line noise
            Psd shape: i/f trend, any peaks, line noise
            Do the traces look generally like EEG
        - Notch filtering: Look for signs of line noise (strong peaks at 50Hz or 60Hz in the power spectrum).
        - Slow drift correction: Look for gradual upward or downward shifts in the signal baseline across channels.
        - ICA: Look for common artifacts such as eye movements, heartbeats, or muscle activity that would require ICA for removal.
        Respond by listing the necessary preprocessing steps for this data (notch filtering, slow drift correction, ICA) and provide a brief justification for each step based on specific features observed in the plot."""
        messages = create_reasoning_messages(
            user_prompt=prompt, image_url="./images/raw_timeseries.jpg"
        )  # TODO - Add current eeg plot url
        ## Ajout du psd plot pour le notch filtering
        messages += create_reasoning_messages(
            user_prompt="Here is the power spectrum of the data. Does it show signs of line noise or other issues that would inform preprocessing decisions?",
            image_url="./images/psd_plot.jpg",
        )
        chat_response = client.chat.parse(
            model="magistral-small-2509",
            messages=messages,
            prompt_mode="reasoning",
            response_format=InitialQCResult,
            temperature=0.1,
        )
        result = chat_response.choices[0].message.parsed
        state.skip_stage = result.skip_stages
        state.justification["initial_qc"] = result.justification

    except Exception as e:
        logging.error(f"Error in initial QC: {e}")
        state["errors"].append(f"Initial QC failed: {str(e)}")
        state.skip_stage = []

    state["current_stage"] = "bandpass_filtering"

    logging.info("[INITIAL QC] Placeholder: proceeding with all stages")
    return state


def bandpass_filter(
    raw: mne.io.Raw, l_freq: float = 0.5, h_freq: float = 45.0
) -> mne.io.Raw:
    return raw.filter(l_freq=l_freq, h_freq=h_freq)


names_to_functions = {
    "bandpass_filter": bandpass_filter,
}
bandpass_filtering_agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "bandpass_filter",
            "description": "Apply bandpass filter to the data with specified low and high cutoff frequencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "l_freq": {
                        "type": "number",
                        "description": "Low cutoff frequency in Hz. Example: 0.5.",
                    },
                    "h_freq": {
                        "type": "number",
                        "description": "High cutoff frequency in Hz. Example: 45.0.",
                    },
                },
                "required": ["l_freq", "h_freq"],
            },
        },
    }
]


def bandpass_filtering_agent(state: EEGPipelineState) -> EEGPipelineState:
    """
    [TBC] Bandpass filtering agent.
    Applies bandpass filter to the data if not skipped.
    """
    logging.info(f"[BANDPASS FILTERING] Processing subject {state['subject_id']}")

    if "bandpass_filtering" in state.skip_stage:
        logging.info(
            "[BANDPASS FILTERING] Skipping bandpass filtering based on initial QC."
        )
        state["justification"][
            "bandpass_filtering"
        ] = "Skipped based on initial QC assessment."
        return state

    state["input_raw"] = state["output_raw"]
    state["output_raw"] = None  # Reset output raw for this stage

    experiment_context = state["experiment_metadata"]["experiment_context"]

    try:
        prompt = f"""Here is the context of the experiment: {experiment_context}. Based on this context, determine the optimal bandpass filter settings (low and high cutoff frequencies) for preprocessing EEG data. Consider factors such as the expected frequency range of neural signals of interest, potential artifacts, and the overall quality of the recording. Provide specific cutoff frequencies and a brief justification for your choices based on the experiment context."""
        messages = [
            {
                "role": "system",
                "content": "you are a helpful assistant for EEG data analysis.Based on the experiment context, determine the optimal bandpass filter settings (low and high cutoff frequencies) for preprocessing EEG data. Call the tools after you have determined the optimal settings and always provide a justification for your choices based on the experiment context.",
            },
            {"role": "user", "content": prompt},
        ]
        chat_response = client.chat.complete(
            model="mistral-large-2512",
            messages=messages,
            tools=bandpass_filtering_agent_tools,
        )
        
        # Check if tool_calls is available
        if not chat_response.choices[0].message.tool_calls:
            logging.error("No tool calls returned from the model")
            state["errors"].append("Bandpass filtering failed: No tool calls from model")
            return state
            
        # while chat_response.choices[0].message.tool_calls:
        if chat_response.choices[0].message.content:
            logging.info(f"Model response: {chat_response.choices[0].message.content}")
        tool_call = chat_response.choices[0].message.tool_calls[0]
        function_name = tool_call.name
        function_to_call = names_to_functions[function_name]
        arguments = tool_call.arguments
        raw_filtered = function_to_call(raw=state["input_raw"], **arguments)

        # chat_response = client.chat.complete(
        #     model="mistral-large-2512",
        #     messages=messages,
        #     tools=bandpass_filtering_agent_tools,
        #     tool_results=[{"name": function_name, "result": str(raw_filtered)}],
        # )
        # messages.append({"role": "tool", "content": {"name": function_name, "result": str(raw_filtered)}})
        justification = chat_response.choices[0].message.content
        state["output_raw"] = (
            raw_filtered  # Assuming the function result is the filtered raw data
        )
        state["justification"]["bandpass_filtering"] = justification
        return state

    except Exception as e:
        logging.error(f"Error in bandpass filtering: {e}")
        state["errors"].append(f"Bandpass filtering failed: {str(e)}")
        return state


class BadChannelAnalysis(BaseModel):
    bad_channels_to_remove: list = Field(
        description="List of bad channels to remove based on the analysis"
    )
    justification: str = Field(
        description="A brief explanation of the reasoning behind the selected bad channels"
    )


def bad_channel_identifier_agent(state: EEGPipelineState) -> EEGPipelineState:
    """
    Identifies bad EEG channels that should be removed.
    """
    logging.info(f"[BAD CHANNEL IDENTIFIER] Processing subject {state['subject_id']}")

    if "bad_channel_identification" in state.skip_stage:
        logging.info(
            "[BAD CHANNEL IDENTIFIER] Skipping bad channel identification based on initial QC."
        )
        state["justification"][
            "bad_channel_identification"
        ] = "Skipped based on initial QC assessment."
        return state

    state["input_raw"] = state["output_raw"]
    state["output_raw"] = None  # Reset output raw for this stage

    input_timeseries_fig = state["input_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    input_timeseries_fig.savefig("./images/raw_timeseries.jpg")

    input_psd_fig = state["input_raw"].plot_psd(
        fmax=50
    )  # Generate PSD plot without displaying
    input_psd_fig.savefig("./images/psd_plot.jpg")

    input_sensors_fig = state["input_raw"].plot_sensors(
        show_names=True
    )  # Generate sensor layout plot without displaying
    input_sensors_fig.savefig("./images/sensors.jpg")

    try:
        prompt = """You are a helpful assistant for EEG data analysis. I will give you an image of EEG channels. 
        I want you to analyze the plot and identify which channels should be removed. To answer, here are the rules to identify bad channels:
        - Channels with flat line or almost flat line across the entire recording are likely bad channels and should be tagged as removed.
        Also do a brief justification for your answer."""

        messages = create_reasoning_messages(prompt, "./images/raw_timeseries.jpg")

        chat_response = client.chat.parse(
            model="magistral-small-2509",
            messages=messages,
            prompt_mode="reasoning",
            response_format=BadChannelAnalysis,
            temperature=0.1,
        )

        result = chat_response.choices[0].message.parsed
        state["bad_channels"] = result.bad_channels_to_remove

        logging.info(
            f"Identified {len(result.bad_channels_to_remove)} bad channels: {result.bad_channels_to_remove}"
        )

    except Exception as e:
        logging.error(f"Error in bad channel detection: {e}")
        state["errors"].append(f"Bad channel detection failed: {str(e)}")

    state["current_stage"] = "notch_filtering"
    return state


def annotate_bad_channels(raw: mne.io.Raw, bad_channels: List[str]) -> mne.io.Raw:
    """Annotate bad channels in the raw object"""
    raw.info["bads"] = bad_channels
    return raw


def notch_filtering_agent(state: EEGPipelineState) -> EEGPipelineState:
    """
    [TBC] Notch filtering agent.
    Applies notch filter to the data if not skipped.
    """
    logging.info(f"[NOTCH FILTERING] Processing subject {state['subject_id']}")

    if "notch_filtering" in state.skip_stage:
        logging.info("[NOTCH FILTERING] Skipping notch filtering based on initial QC.")
        state["justification"][
            "notch_filtering"
        ] = "Skipped based on initial QC assessment."
        return state

    state["input_raw"] = state["output_raw"]
    state["output_raw"] = None  # Reset output raw for this stage

    input_timeseries_fig = state["input_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    input_timeseries_fig.savefig("./images/raw_timeseries.jpg")

    input_psd_fig = state["input_raw"].plot_psd(
        fmax=50
    )  # Generate PSD plot without displaying
    input_psd_fig.savefig("./images/psd_plot.jpg")

    input_sensors_fig = state["input_raw"].plot_sensors(
        show_names=True
    )  # Generate sensor layout plot without displaying
    input_sensors_fig.savefig("./images/sensors.jpg")

    try:
        prompt = """You are a helpful assistant for EEG data analysis. I will give you an image of the power spectrum of the data. Does it show signs of line noise or other issues that would inform preprocessing decisions? If there are strong peaks at 50Hz or 60Hz, it may indicate line noise and suggest the need for notch filtering. Also consider any other features in the power spectrum that could inform whether notch filtering is necessary."""
        messages = create_reasoning_messages(prompt, "./images/psd_plot.jpg")
        chat_response = client.chat.parse(
            model="magistral-small-2509",
            messages=messages,
            prompt_mode="reasoning",
            response_format=InitialQCResult,
            temperature=0.1,
        )
        result = chat_response.choices[0].message.parsed
        if "notch_filtering" in result.skip_stages:
            state["justification"]["notch_filtering"] = result.justification.get(
                "notch_filtering", "No justification provided."
            )
            logging.info(
                "[NOTCH FILTERING] Skipping notch filtering based on PSD analysis."
            )
            return state
        else:
            logging.info(
                "[NOTCH FILTERING] Applying notch filter based on PSD analysis."
            )
            # Apply notch filter - detect frequency based on location (50Hz for Europe, 60Hz for US)
            # Here we default to 50Hz, but this could be determined from metadata
            freqs_to_notch = [50.0, 100.0]  # 50 Hz and its harmonic
            raw_notched = state["input_raw"].copy().notch_filter(
                freqs=freqs_to_notch, picks="eeg", method="fir", phase="zero"
            )
            state["output_raw"] = raw_notched
            state["justification"]["notch_filtering"] = result.justification.get(
                "notch_filtering", "No justification provided."
            )
            return state
    except Exception as e:
        logging.error(f"Error in notch filtering decision: {e}")
        state["errors"].append(f"Notch filtering decision failed: {str(e)}")
        return state


def apply_slow_drift_correction(raw: mne.io.Raw) -> mne.io.Raw:
    """Apply slow drift correction to the raw data."""
    raw_corrected = raw.copy().filter(
        l_freq=0.5, h_freq=None
    )  # High-pass filter to remove slow drifts
    return raw_corrected


def slow_drift_analysis_agent(state: EEGPipelineState) -> EEGPipelineState:

    state["input_raw"] = state["output_raw"]
    state["output_raw"] = None  # Reset output raw for this stage

    input_timeseries_fig = state["input_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    input_timeseries_fig.savefig("./images/raw_timeseries.jpg")

    try:
        prompt = """You are a helpful assistant for EEG data analysis. I will give you an image of an EEG plot. I want you to analyze the plot and say whether the data shows signs of slow drifts or not. In raw EEG recordings, slow drifts appear as a gradual upward or downward shift in the signal baseline across channels. Respond by giving a probability between 0 and 1. 1 means the data is very likely to show slow drifts, 0 means it is very unlikely. Add a brief justification for your answer."""
        messages = create_reasoning_messages(prompt, "./images/raw_timeseries.jpg")
        chat_response = client.chat.parse(
            model="magistral-small-2509",
            messages=messages,
            prompt_mode="reasoning",
            response_format=EEGSlowDriftAnalysis,
        )
        result = chat_response.choices[0].message.parsed
        state["slow_drift_probability"] = result.slow_drift_probability
        state["justification"]["slow_drift"] = result.justification

        if result.slow_drift_probability > SLOW_DRIFT_THRESHOLD:
            logging.info(
                f"Data shows signs of slow drifts with probability {result.slow_drift_probability}."
            )
            raw_corrected = apply_slow_drift_correction(state["input_raw"])
            state["output_raw"] = raw_corrected
        else:
            logging.info(
                f"Data does not show strong signs of slow drifts (probability {result.slow_drift_probability}). Skipping slow drift correction."
            )
            state["output_raw"] = state["input_raw"]
        state["current_stage"] = "bad_channel_identification"
    except Exception as e:
        logging.error(f"Error in slow drift analysis: {e}")
        state["errors"].append(f"Slow drift analysis failed: {str(e)}")
        return state
    return state


def resampling(state: EEGPipelineState) -> EEGPipelineState:
    """[TBC] Resampling agent."""
    logging.info(f"[RESAMPLING] Processing subject {state['subject_id']}")
    state["input_raw"] = state["output_raw"]
    state["output_raw"] = None  # Reset output raw for this stage
    ### Optional resampling before ICA
    raw_rs = state["input_raw"].copy()
    raw_rs.resample(
        sfreq=250.0,
        method="polyphase",  # study this vs default fft
    )
    state["output_raw"] = raw_rs
    return state


### Make a dedicated ICA copy with stronger high-pass
def prepare_ica_copy(state: EEGPipelineState) -> EEGPipelineState:
    state["input_raw"] = state["output_raw"].copy()
    raw_ica = state["input_raw"].copy()
    raw_ica.filter(
        l_freq=1.0,
        h_freq=45.0,
        picks="eeg",
        method="fir",
        phase="zero",
        fir_design="firwin",
    )
    state["output_raw"] = raw_ica
    return state


def apply_ica(state: EEGPipelineState, n_components: int = 20) -> ICA:

    ica = ICA(n_components=n_components, random_state=97)
    ica.fit(state["output_raw"])
    return ica


def ica_discrimination_agent(
    state: EEGPipelineState, ica: ICA
) -> EEGPipelineState:
    """
    [TBC] ICA discrimination agent.
    Identifies which ICA components to remove based on the analysis of ICA plots.
    """
    logging.info(f"[ICA DISCRIMINATION] Processing subject {state['subject_id']}")
    if "ica" in state.skip_stage:
        logging.info(
            "[ICA DISCRIMINATION] Skipping ICA discrimination based on initial QC."
        )
        state["justification"][
            "ica_discrimination"
        ] = "Skipped based on initial QC assessment."
        return state
    
    # Generate ICA components plot
    input_ica_fig = ica.plot_components(picks=range(min(20, ica.n_components_)), show=False)
    input_ica_fig.savefig("./images/ica_components.jpg")
    try:

        messages = create_reasoning_messages(
            user_prompt="""You are a helpful assistant for EEG data analysis. I will give you an image of ICA plots. I want you to analyze the plot and identify which ICA channels should be removed. To answer, here are some rules to identify bad ICA components:
            - Vertical eye movement components will contain blinks in the data
            - Horizontal eye movement components will look like step functions
            - The pattern generated by the heart is very typical and is known as a QRS complex (it looks like a sharp peak followed by a smaller inverted peak)
            - Muscle artifacts typically have a high-frequency pattern and are often localized to specific channels, especially those near the face and neck. They can appear as bursts of high-frequency activity in the ICA components
            - Strong peak in power spectrum at either 50Hz or 60Hz
            - If an ICA component looks like the EOG signal (which is at the bottom of the plot) it is likely an eye movement artifact and should be removed.
            Respond by providing a list of ICA channels to remove based on the analysis and the rules. I want only to identify the channels associated to these rules.
            Also do a brief justification for your answer.""",
            image_url="./images/ica_components.jpg",
        )

        chat_response = client.chat.parse(
            model=model,
            messages=messages,
            prompt_mode="reasoning",
            response_format=ICAAnalysis,
            temperature=0.1,
        )
        result = chat_response.choices[0].message.parsed
        state["ica_channels_to_remove"] = result.ica_channels_to_remove
        state["ica_justification"] = result.justification
    except Exception as e:
        logging.error(f"Error in ICA discrimination: {e}")
        state["errors"].append(f"ICA discrimination failed: {str(e)}")
        return state


def apply_ica_correction(state: EEGPipelineState, ica: ICA) -> EEGPipelineState:
    """Apply ICA correction by removing identified components"""
    ica.exclude = state["ica_channels_to_remove"]
    raw_corrected = state["input_raw"].copy()
    ica.apply(raw_corrected)
    state["output_raw"] = raw_corrected
    return state


def interpolate_bad_channels(raw: mne.io.Raw) -> mne.io.Raw:
    """Interpolate bad channels in the raw object"""
    raw.interpolate_bads(reset_bads=True)
    return raw


def final_qc_agent(state: EEGPipelineState) -> EEGPipelineState:
    """[TBC] Final quality control agent."""
    logging.info(f"[FINAL QC] Processing subject {state['subject_id']}")

    state["input_raw"] = state["output_raw"]
    state["output_raw"] = None  # Reset output raw for this stage

    timeseries_fig = state["input_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    timeseries_fig.savefig("./images/final_qc_timeseries.jpg")
    psd_fig = state["input_raw"].plot_psd(
        fmax=50
    )  # Generate PSD plot without displaying
    psd_fig.savefig("./images/final_qc_psd.jpg")
    sensors_fig = state["input_raw"].plot_sensors(
        show_names=True
    )  # Generate sensor layout plot without displaying
    sensors_fig.savefig("./images/final_qc_sensors.jpg")

    try:
        prompt = """You are a helpful assistant for EEG data analysis. I will give you an image of the final preprocessed EEG data. Analyze the plot and assess the overall quality of the preprocessing. Consider factors such as the presence of any remaining artifacts, the shape of the power spectrum, and the general appearance of the EEG traces. Provide a brief assessment of the quality of the preprocessing and any recommendations for further improvement if necessary."""
        messages = create_reasoning_messages(prompt, "./images/final_qc_timeseries.jpg")
        messages += [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here is the power spectrum of the final preprocessed data. Analyze it and consider if there are any remaining issues that could be addressed with further preprocessing steps.",
                    },
                    {"type": "image_url", "image_url": "./images/final_qc_psd.jpg"},
                    {"type": "image_url", "image_url": "./images/final_qc_sensors.jpg"},
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here is the initial raw data plots for comparison. Analyze it in conjunction with the final preprocessed data to assess the effectiveness of the preprocessing steps and identify any remaining issues.",
                    },
                    {"type": "image_url", "image_url": "./images/raw_timeseries.jpg"},
                    {"type": "image_url", "image_url": "./images/raw_psd.jpg"},
                    {"type": "image_url", "image_url": "./images/raw_sensors.jpg"},
                ],
            },
        ]
        chat_response = client.chat.parse(
            model=model,
            messages=messages,
            prompt_mode="reasoning",
            response_format=InitialQCResult,
            temperature=0.1,
        )
        state["final_qc_assessment"] = chat_response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in final QC assessment: {e}")
        state["errors"].append(f"Final QC assessment failed: {str(e)}")

    return state


if __name__ == "__main__":
    state = initial_qc_agent(state)
    SKIP_STAGE = state['skip_stage']
    logging.info(f"Initial QC completed. Stages to skip: {SKIP_STAGE}")
    if SKIP_STAGE:
        logging.info(f"Skipping stages: {SKIP_STAGE}")
    else:
        logging.info("No stages to skip. Proceeding with full pipeline.")
    if "bandpass_filtering" not in SKIP_STAGE:
        state = bandpass_filtering_agent(state)
    logging.info(
        f"Bandpass filtering completed. Justification: {state['justification'].get('bandpass_filtering', 'No justification provided.')}"
    )

    if "bad_channel_identification" not in SKIP_STAGE:
        state = bad_channel_identifier_agent(state)
    logging.info(
        f"Bad channel identification completed. Justification: {state['justification'].get('bad_channel_identification', 'No justification provided.')}"
    )
    state["output_raw"] = annotate_bad_channels(
        state["input_raw"], state["bad_channels"]
    )
    if "notch_filtering" not in SKIP_STAGE:
        state = notch_filtering_agent(state)
    logging.info(
        f"Notch filtering decision completed. Justification: {state['justification'].get('notch_filtering', 'No justification provided.')}"
    )
    if "ica" not in SKIP_STAGE:
        state = resampling(state)
        state = prepare_ica_copy(state)
        ica = apply_ica(state)
        state = ica_discrimination_agent(state, ica)
        state = apply_ica_correction(state, ica)
    logging.info(
        f"ICA correction completed. Justification: {state.get('ica_justification', 'No justification provided.')}"
    )

    if state["bad_channels"]:
        state["output_raw"] = interpolate_bad_channels(state["output_raw"])
    timeseries_fig = state["output_raw"].plot(
        duration=5, n_channels=30, scalings="auto", show_scrollbars=False
    )  # Generate raw EEG plot without displaying
    timeseries_fig.savefig("./images/current_eeg_timeseries.jpg")
    psd_fig = state["output_raw"].plot_psd(
        fmax=50
    )  # Generate PSD plot without displaying
    psd_fig.savefig("./images/current_eeg_psd.jpg")
    sensors_fig = state["output_raw"].plot_sensors(
        show_names=True
    )  # Generate sensor layout plot without displaying
    sensors_fig.savefig("./images/current_eeg_sensors.jpg")
