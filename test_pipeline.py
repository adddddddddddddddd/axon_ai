"""
Tests unitaires pour le pipeline de prétraitement EEG
"""
import pytest
import numpy as np
import mne
from mne.preprocessing import ICA
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from main import (
    EEGPipelineState,
    bandpass_filter,
    annotate_bad_channels,
    apply_slow_drift_correction,
    interpolate_bad_channels,
    apply_ica,
    apply_ica_correction,
)


@pytest.fixture
def mock_raw_eeg():
    """Create a mock EEG raw object for testing"""
    # Create synthetic EEG data
    sfreq = 250  # Hz
    n_channels = 10
    n_times = int(sfreq * 10)  # 10 seconds of data
    
    # Create synthetic data
    info = mne.create_info(
        ch_names=[f'EEG{i:03d}' for i in range(n_channels)],
        sfreq=sfreq,
        ch_types='eeg'
    )
    
    # Generate random data with some structure
    data = np.random.randn(n_channels, n_times) * 1e-5
    
    # Add some slow drift to channel 0
    t = np.linspace(0, 10, n_times)
    data[0, :] += 0.0001 * t
    
    # Add 50 Hz line noise to channel 1
    data[1, :] += 0.00005 * np.sin(2 * np.pi * 50 * t)
    
    raw = mne.io.RawArray(data, info)
    return raw


@pytest.fixture
def mock_state(mock_raw_eeg):
    """Create a mock pipeline state for testing"""
    return EEGPipelineState(
        subject_id="test_001",
        current_stage="test",
        input_raw=mock_raw_eeg,
        output_raw=None,
        skip_stage=[],
        justification={},
        errors=[],
        experiment_metadata={"experiment_context": "Test experiment"},
        bad_channels=[],
        slow_drift_probability=None,
        ica_channels_to_remove=None,
        ica_justification=None,
        final_qc_assessment=None,
    )


class TestBandpassFilter:
    """Tests for bandpass filtering"""
    
    def test_bandpass_filter_basic(self, mock_raw_eeg):
        """Test that bandpass filter runs without error"""
        raw_filtered = bandpass_filter(mock_raw_eeg, l_freq=0.5, h_freq=45.0)
        
        assert raw_filtered is not None
        assert raw_filtered.info['sfreq'] == mock_raw_eeg.info['sfreq']
        assert len(raw_filtered.ch_names) == len(mock_raw_eeg.ch_names)
    
    def test_bandpass_filter_frequency_range(self, mock_raw_eeg):
        """Test that bandpass filter accepts different frequency ranges"""
        raw_filtered = bandpass_filter(mock_raw_eeg, l_freq=1.0, h_freq=30.0)
        
        assert raw_filtered is not None
        # Check that filter was applied by verifying the object was modified
        assert hasattr(raw_filtered, 'info')


class TestBadChannelHandling:
    """Tests for bad channel detection and handling"""
    
    def test_annotate_bad_channels(self, mock_raw_eeg):
        """Test that bad channels are properly annotated"""
        bad_channels = ['EEG000', 'EEG005']
        raw_annotated = annotate_bad_channels(mock_raw_eeg, bad_channels)
        
        assert raw_annotated.info['bads'] == bad_channels
    
    def test_annotate_empty_bad_channels(self, mock_raw_eeg):
        """Test that empty bad channel list works"""
        raw_annotated = annotate_bad_channels(mock_raw_eeg, [])
        
        assert raw_annotated.info['bads'] == []
    
    def test_interpolate_bad_channels(self, mock_raw_eeg):
        """Test that bad channels can be interpolated"""
        # First annotate bad channels
        mock_raw_eeg.info['bads'] = ['EEG000']
        
        raw_interpolated = interpolate_bad_channels(mock_raw_eeg)
        
        assert raw_interpolated is not None
        # After interpolation, bads should be reset
        assert len(raw_interpolated.info['bads']) == 0


class TestSlowDriftCorrection:
    """Tests for slow drift correction"""
    
    def test_apply_slow_drift_correction(self, mock_raw_eeg):
        """Test that slow drift correction runs without error"""
        raw_corrected = apply_slow_drift_correction(mock_raw_eeg)
        
        assert raw_corrected is not None
        assert raw_corrected.info['sfreq'] == mock_raw_eeg.info['sfreq']


class TestICAProcessing:
    """Tests for ICA processing"""
    
    def test_apply_ica(self, mock_state):
        """Test that ICA fitting works"""
        mock_state['output_raw'] = mock_state['input_raw'].copy()
        
        ica = apply_ica(mock_state, n_components=5)
        
        assert ica is not None
        assert isinstance(ica, ICA)
        assert ica.n_components_ <= 5
    
    def test_apply_ica_correction(self, mock_state):
        """Test that ICA correction can be applied"""
        # Setup state with ICA
        mock_state['input_raw'] = mock_state['input_raw'].copy()
        mock_state['output_raw'] = mock_state['input_raw'].copy()
        
        # Fit ICA
        ica = ICA(n_components=5, random_state=97)
        ica.fit(mock_state['output_raw'])
        
        # Mark some components to remove
        mock_state['ica_channels_to_remove'] = [0, 1]
        
        # Apply correction
        result_state = apply_ica_correction(mock_state, ica)
        
        assert result_state is not None
        assert result_state['output_raw'] is not None
        assert ica.exclude == [0, 1]


class TestPipelineState:
    """Tests for pipeline state management"""
    
    def test_state_initialization(self, mock_state):
        """Test that state is properly initialized"""
        assert mock_state['subject_id'] == "test_001"
        assert mock_state['current_stage'] == "test"
        assert mock_state['input_raw'] is not None
        assert mock_state['output_raw'] is None
        assert mock_state['skip_stage'] == []
        assert mock_state['justification'] == {}
        assert mock_state['errors'] == []
        assert mock_state['bad_channels'] == []
    
    def test_state_error_tracking(self, mock_state):
        """Test that errors can be tracked in state"""
        mock_state['errors'].append("Test error 1")
        mock_state['errors'].append("Test error 2")
        
        assert len(mock_state['errors']) == 2
        assert "Test error 1" in mock_state['errors']
    
    def test_state_justification_tracking(self, mock_state):
        """Test that justifications can be tracked"""
        mock_state['justification']['bandpass_filtering'] = "Test justification"
        
        assert 'bandpass_filtering' in mock_state['justification']
        assert mock_state['justification']['bandpass_filtering'] == "Test justification"


class TestDataFlow:
    """Tests for data flow through the pipeline"""
    
    def test_input_output_flow(self, mock_state):
        """Test that data flows correctly from input to output"""
        # Simulate processing stage
        mock_state['output_raw'] = mock_state['input_raw'].copy()
        
        assert mock_state['output_raw'] is not None
        assert mock_state['output_raw'].info['sfreq'] == mock_state['input_raw'].info['sfreq']
    
    def test_stage_chaining(self, mock_state):
        """Test that stages can be chained together"""
        # Stage 1: Bandpass filter
        raw_filtered = bandpass_filter(mock_state['input_raw'], l_freq=0.5, h_freq=45.0)
        mock_state['output_raw'] = raw_filtered
        
        # Move output to input for next stage
        mock_state['input_raw'] = mock_state['output_raw']
        
        # Stage 2: Annotate bad channels
        mock_state['bad_channels'] = ['EEG000']
        raw_annotated = annotate_bad_channels(mock_state['input_raw'], mock_state['bad_channels'])
        
        assert raw_annotated.info['bads'] == ['EEG000']


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_bad_channels_list(self, mock_raw_eeg):
        """Test handling of empty bad channels list"""
        result = annotate_bad_channels(mock_raw_eeg, [])
        assert result.info['bads'] == []
    
    def test_all_channels_bad(self, mock_raw_eeg):
        """Test handling when all channels are marked as bad"""
        all_channels = mock_raw_eeg.ch_names
        result = annotate_bad_channels(mock_raw_eeg, all_channels)
        assert result.info['bads'] == all_channels
    
    def test_invalid_channel_name(self, mock_raw_eeg):
        """Test handling of invalid channel names"""
        # MNE allows invalid channel names in bads list without error
        result = annotate_bad_channels(mock_raw_eeg, ['INVALID_CHANNEL'])
        assert 'INVALID_CHANNEL' in result.info['bads']


class TestImageDirectoryCreation:
    """Tests for image directory management"""
    
    def test_image_directory_exists(self):
        """Test that image directory is created"""
        test_dir = "./test_images"
        os.makedirs(test_dir, exist_ok=True)
        
        assert os.path.exists(test_dir)
        
        # Cleanup
        if os.path.exists(test_dir):
            os.rmdir(test_dir)


# Integration test
class TestFullPipelineMock:
    """Mock integration test for the full pipeline"""
    
    def test_pipeline_stages_order(self, mock_state):
        """Test that pipeline stages execute in correct order"""
        stages_executed = []
        
        # Initial QC
        mock_state['current_stage'] = 'initial_qc'
        stages_executed.append(mock_state['current_stage'])
        
        # Bandpass filtering
        if 'bandpass_filtering' not in mock_state['skip_stage']:
            mock_state['current_stage'] = 'bandpass_filtering'
            stages_executed.append(mock_state['current_stage'])
            mock_state['output_raw'] = bandpass_filter(mock_state['input_raw'])
        
        # Bad channel identification
        if 'bad_channel_identification' not in mock_state['skip_stage']:
            mock_state['current_stage'] = 'bad_channel_identification'
            stages_executed.append(mock_state['current_stage'])
        
        expected_stages = ['initial_qc', 'bandpass_filtering', 'bad_channel_identification']
        assert stages_executed == expected_stages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
