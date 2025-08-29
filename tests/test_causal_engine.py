"""Tests for causal engine functionality."""
import unittest
import pandas as pd
import sys
import os
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from causal_engine.base import CausalModelBase, model_registry
from causal_engine.models.did import DifferenceInDifferencesModel


class MockCausalModel(CausalModelBase):
    """Mock model for testing base functionality."""
    
    def __init__(self, client_id: str, model_params: dict):
        # Manually set attributes to avoid BigQuery initialization
        self.client_id = client_id
        self.params = model_params or {}
        self.model_name = self.__class__.__name__.lower().replace('model', '')
        
        # Core settings
        self.project = self.params.get("project", "test-project")
        self.dataset = self.params.get("dataset", "test_dataset")
        self.table = self.params.get("table", "standard_events")
        
        # Mock BigQuery client
        self.bq_client = Mock()
        
        # Generate unique analysis ID for reproducibility
        import uuid
        from datetime import datetime
        self.analysis_id = str(uuid.uuid4())
        self.analysis_timestamp = datetime.utcnow().isoformat()
    
    def load_data(self) -> pd.DataFrame:
        """Mock data loading."""
        return pd.DataFrame({
            'event_id': ['e1', 'e2', 'e3', 'e4'],
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-15', '2024-01-16'],
            'event_type': ['conversion', 'conversion', 'conversion', 'conversion'],
            'revenue_usd': [10.0, 15.0, 20.0, 25.0],
            'marketing_channel': ['paid_search', None, 'paid_search', None],
            'campaign_id': ['test_campaign'] * 4,
            'user_anonymous_id': ['u1', 'u2', 'u3', 'u4']
        })
    
    def run_analysis(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mock analysis."""
        return pd.DataFrame([{
            'effect_size': 0.15,
            'confidence_interval_lower': 0.05,
            'confidence_interval_upper': 0.25,
            'p_value': 0.03,
            'standard_error': 0.05
        }])


class TestCausalEngineBase(unittest.TestCase):
    """Test the base causal engine functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client_id = "test_client"
        self.params = {
            "project": "test-project",
            "dataset": "test_dataset",
            "campaign_id": "test_campaign"
        }
    
    @patch('causal_engine.base.bigquery.Client')
    def test_model_initialization(self, mock_bigquery):
        """Test model initialization."""
        mock_bigquery.return_value = Mock()
        
        model = MockCausalModel(self.client_id, self.params)
        
        self.assertEqual(model.client_id, self.client_id)
        self.assertEqual(model.params, self.params)
        self.assertEqual(model.project, "test-project")
        self.assertEqual(model.dataset, "test_dataset")
        self.assertIsNotNone(model.analysis_id)
        self.assertIsNotNone(model.analysis_timestamp)
    
    @patch('causal_engine.base.bigquery.Client')
    def test_data_loading(self, mock_bigquery):
        """Test data loading functionality."""
        mock_bigquery.return_value = Mock()
        
        model = MockCausalModel(self.client_id, self.params)
        data = model.load_data()
        
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), 4)
        self.assertIn('event_id', data.columns)
        self.assertIn('campaign_id', data.columns)
    
    @patch('causal_engine.base.bigquery.Client')
    def test_analysis_execution(self, mock_bigquery):
        """Test analysis execution."""
        mock_bigquery.return_value = Mock()
        
        model = MockCausalModel(self.client_id, self.params)
        data = model.load_data()
        results = model.run_analysis(data)
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertEqual(len(results), 1)
        self.assertIn('effect_size', results.columns)
        self.assertIn('p_value', results.columns)
    
    @patch('causal_engine.base.bigquery.Client')
    def test_data_hash(self, mock_bigquery):
        """Test data hashing for reproducibility."""
        mock_bigquery.return_value = Mock()
        
        model = MockCausalModel(self.client_id, self.params)
        data = model.load_data()
        hash1 = model.get_data_hash(data)
        hash2 = model.get_data_hash(data)
        
        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA256 hash length


class TestModelRegistry(unittest.TestCase):
    """Test the model registry functionality."""
    
    def test_model_registration(self):
        """Test model registration."""
        # Check that DID model is registered
        self.assertIn('did', model_registry.list_models())
        
        # Test getting model
        did_model_class = model_registry.get_model('did')
        self.assertIsNotNone(did_model_class)
        self.assertEqual(did_model_class, DifferenceInDifferencesModel)
    
    def test_unknown_model(self):
        """Test handling of unknown models."""
        unknown_model = model_registry.get_model('unknown_model')
        self.assertIsNone(unknown_model)


class TestDIDModel(unittest.TestCase):
    """Test the Difference-in-Differences model."""
    
    def setUp(self):
        """Set up test environment."""
        self.client_id = "test_client"
        self.params = {
            "project": "test-project",
            "dataset": "test_dataset",
            "campaign_id": "test_campaign",
            "split_date": "2024-01-10",
            "treatment_channel": "paid_search"
        }
    
    @patch('causal_engine.models.did.bigquery.Client')
    def test_did_initialization(self, mock_bigquery):
        """Test DID model initialization."""
        mock_bigquery.return_value = Mock()
        
        model = DifferenceInDifferencesModel(self.client_id, self.params)
        
        self.assertEqual(model.campaign_id, "test_campaign")
        self.assertEqual(model.split_date, "2024-01-10")
        self.assertEqual(model.treatment_channel, "paid_search")
    
    def test_did_missing_campaign_id(self):
        """Test DID model without campaign_id."""
        params = self.params.copy()
        del params["campaign_id"]
        
        with self.assertRaises(ValueError):
            with patch('causal_engine.models.did.bigquery.Client'):
                DifferenceInDifferencesModel(self.client_id, params)
    
    @patch('causal_engine.models.did.bigquery.Client')
    def test_did_data_preparation(self, mock_bigquery):
        """Test DID data preparation logic."""
        mock_bigquery.return_value = Mock()
        
        model = DifferenceInDifferencesModel(self.client_id, self.params)
        
        # Create mock data
        data = pd.DataFrame({
            'event_id': ['e1', 'e2', 'e3', 'e4'],
            'timestamp': ['2024-01-01', '2024-01-05', '2024-01-15', '2024-01-20'],
            'event_type': ['conversion', 'conversion', 'conversion', 'conversion'],
            'revenue_usd': [10.0, 15.0, 20.0, 25.0],
            'marketing_channel': ['paid_search', None, 'paid_search', None],
            'campaign_id': ['test_campaign'] * 4,
            'user_anonymous_id': ['u1', 'u2', 'u3', 'u4']
        })
        
        prepared_data = model._prepare_did_data(data)
        
        # Check treatment flag
        self.assertTrue(prepared_data.iloc[0]['is_treatment'])  # paid_search
        self.assertFalse(prepared_data.iloc[1]['is_treatment'])  # None
        
        # Check post flag (split_date = 2024-01-10)
        self.assertFalse(prepared_data.iloc[0]['is_post'])  # 2024-01-01
        self.assertFalse(prepared_data.iloc[1]['is_post'])  # 2024-01-05
        self.assertTrue(prepared_data.iloc[2]['is_post'])   # 2024-01-15
        self.assertTrue(prepared_data.iloc[3]['is_post'])   # 2024-01-20
        
        # Check outcome variable
        self.assertIn('outcome', prepared_data.columns)


if __name__ == '__main__':
    unittest.main()