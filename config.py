from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

QUALITY_STRICTNESS = os.getenv('QUALITY_STRICTNESS', 'medium').lower()

@dataclass
class QualityThresholds:
    """Configurable quality thresholds for different quality levels"""
    blur_threshold: float
    glare_threshold: float
    glare_brightness: int
    darkness_threshold: int
    min_contrast: float
    min_width: int
    min_height: int
    min_doc_area_ratio: float
    min_edge_density: float

# Easy (lenient) - UPDATED to match reference code "lenient" settings
easy_thresholds = QualityThresholds(
    blur_threshold=20.0,      # Very lenient (was 150.0)
    glare_threshold=0.15,     # 15% glare allowed (was 0.01)
    glare_brightness=250,     # Higher threshold (was 220)
    darkness_threshold=15,    # Very dark allowed (was 70)
    min_contrast=3.0,         # Almost no contrast needed (was 20.0)
    min_width=150,           # Very small images allowed (was 600)
    min_height=100,          # Very small images allowed (was 400)
    min_doc_area_ratio=0.03, # Only 3% area needed (was 0.2)
    min_edge_density=0.001   # Almost no sharpness needed (was 0.015)
)

# Medium (default) - UPDATED to match reference code "standard" settings  
medium_thresholds = QualityThresholds(
    blur_threshold=30.0,      # Very lenient (was 200.0)
    glare_threshold=0.10,     # 10% glare allowed (was 0.005)
    glare_brightness=245,     # Higher threshold (was 240)
    darkness_threshold=25,    # Very dark allowed (was 100)
    min_contrast=5.0,         # Very low contrast allowed (was 30.0)
    min_width=200,           # Very small images allowed (was 800)
    min_height=150,          # Very small images allowed (was 600)
    min_doc_area_ratio=0.05, # Only 5% area needed (was 0.3)
    min_edge_density=0.003   # Very low sharpness allowed (was 0.02)
)

# Hard (strict) - UPDATED to match reference code "strict" settings
hard_thresholds = QualityThresholds(
    blur_threshold=80.0,      # More lenient than old standard (was 300.0)
    glare_threshold=0.05,     # 5% glare allowed (was 0.003)
    glare_brightness=235,     # Lower than lenient (was 250)
    darkness_threshold=40,    # More lenient (was 120)
    min_contrast=12.0,        # More lenient (was 40.0)
    min_width=300,           # More lenient (was 1000)
    min_height=250,          # More lenient (was 800)
    min_doc_area_ratio=0.1,  # 10% area needed (was 0.4)
    min_edge_density=0.008   # More lenient (was 0.025)
)

if QUALITY_STRICTNESS == 'easy':
    thresholds = easy_thresholds
elif QUALITY_STRICTNESS == 'hard':
    thresholds = hard_thresholds
else:
    thresholds = medium_thresholds

instructions = """
Ensure good lighting without harsh shadows or glare
Hold camera steady and ensure the image is in focus 
Make sure the document fills most of the frame
Take photo straight-on to avoid perspective distortion
"""