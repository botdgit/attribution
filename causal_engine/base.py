from abc import ABC, abstractmethod
import pandas as pd


class CausalModelBase(ABC):
    def __init__(self, client_id: str, model_params: dict):
        self.client_id = client_id
        self.params = model_params or {}

    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """Loads data from the canonical standard_events table."""
        pass

    @abstractmethod
    def run_analysis(self, data: pd.DataFrame) -> pd.DataFrame:
        """Performs the causal analysis and returns results as a DataFrame."""
        pass

    @abstractmethod
    def write_results(self, results: pd.DataFrame):
        """Writes the results to the appropriate BigQuery result table."""
        pass

    def run(self):
        data = self.load_data()
        results = self.run_analysis(data)
        self.write_results(results)
