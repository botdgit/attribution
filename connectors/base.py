from __future__ import annotations
import abc
import json
import logging
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger("connectors")


class Connector(abc.ABC):
    """Base connector interface.

    Implementations should be idempotent, manage state, and emit rows in the canonical schema.
    """

    def __init__(self, state_store: Optional[str] = None):
        # state_store can be a path or a cloud location; implementations decide
        self.state_store = state_store
        self.state: Dict[str, Any] = {}

    def load_state(self) -> None:
        try:
            if self.state_store:
                with open(self.state_store, "r") as fh:
                    self.state = json.load(fh)
        except FileNotFoundError:
            self.state = {}

    def save_state(self) -> None:
        if self.state_store:
            with open(self.state_store, "w") as fh:
                json.dump(self.state, fh)

    def run(self) -> Iterable[Dict[str, Any]]:
        """Run the connector: fetch, transform, and yield canonical rows."""
        self.load_state()
        for item in self.fetch():
            row = self.transform(item)
            yield row
        self.save_state()

    @abc.abstractmethod
    def fetch(self) -> Iterable[Any]:
        """Fetch raw items from source."""

    @abc.abstractmethod
    def transform(self, raw: Any) -> Dict[str, Any]:
        """Transform a raw item into the canonical CFAP row."""
