from abc import ABC, abstractmethod
from typing import List, Dict, Any

class RankingModelInterface(ABC):
    """
    Abstract interface for workforce ranking models.
    
    Any machine learning model (Random Forest, XGBoost, LightGBM, Custom Ranker)
    must implement this interface so it can be swapped into the Django platform
    seamlessly without changing backend business logic.
    """

    @abstractmethod
    def rank_candidates(self, candidates_features: List[Dict[str, Any]]) -> List[float]:
        """
        Takes a list of structured candidate feature dictionaries and returns
        a list of float suitability scores in range [0.0, 1.0], matching the order
        of candidates.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Returns a string identifier of the active ranking model / version.
        """
        pass
