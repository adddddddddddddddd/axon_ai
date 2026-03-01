from sqlmodel import Session, select, create_engine
from models import User, Run, Step, BIDSDataset, Tasks, EEGFile, AgentThought

DATABASE_URL = "postgresql://admin:secretsecret@localhost:5432/eeg_pipeline_db"
engine = create_engine(DATABASE_URL)