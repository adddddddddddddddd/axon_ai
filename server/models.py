from sqlmodel import SQLModel, Field
import mne
from sqlalchemy import Column, LargeBinary
import pickle
    
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str
    email: str
    password_hash: str    

class Run(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    eeg_file_id: int = Field(foreign_key="eegfile.id")
    bids_dataset_id: int = Field(foreign_key="bidsdataset.id")
    subject_id: str
    start_time: str
    end_time: str
    pipeline_status: str
    last_opened_at: str
    
    
class Images(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    step_id: int = Field(foreign_key="step.id")
    image_url: str
    image_type: str
    description: str    

#image_type: 'psd', 'topography', 'ica_component', etc.

class Step(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    name: str
    status: str
    started_at: str
    ended_at: str
    raw : mne.io.BaseRaw = Field(sa_column=Column(pickle.dumps(None), type_=LargeBinary))
    ica_components : list = Field(sa_column=Column(pickle.dumps(None), type_=LargeBinary))
    psd : list = Field(sa_column=Column(pickle.dumps(None), type_=LargeBinary))
    sensor_topography : list = Field(sa_column=Column(pickle.dumps(None), type_=LargeBinary))

class BIDSDataset(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    subject_id: str
    session_id: str
    task_id: str
    raw_data_path: str

class Tasks(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str

class EEGFile(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    filename: str
    filepath: str
    upload_time: str
    
class AgentThought(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    thought: str
    action: str
    observation: str
    timestamp: str