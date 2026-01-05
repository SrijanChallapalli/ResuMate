"""
Sigmoid calibration for premium scoring.
Applies sigmoid transformation to stabilize 0-100 scores after penalties.
"""
import math


def sigmoid_calibrate(score: float, center: float = 50.0, steepness: float = 0.08) -> float:
    """
    Apply sigmoid calibration to score.
    
    Formula: calibrated = 100 / (1 + exp(-steepness * (score - center)))
    
    This transformation:
    - Maps scores around the center (50) to approximately the same value
    - Compresses extreme scores (very low/high) toward the center
    - Makes the 0-100 scale more stable and interpretable
    
    Args:
        score: Raw score (0-100) after cap and penalty
        center: Center point of sigmoid (default 50)
        steepness: Steepness parameter (default 0.08)
                  Higher = more compression, lower = less compression
    
    Returns:
        Calibrated score (0-100)
    """
    # Clamp input to 0-100
    score = max(0.0, min(100.0, score))
    
    # Apply sigmoid: 100 / (1 + exp(-steepness * (score - center)))
    calibrated = 100.0 / (1.0 + math.exp(-steepness * (score - center)))
    
    # Clamp output to 0-100
    return max(0.0, min(100.0, round(calibrated, 1)))
