from typing import Tuple, Optional
import cv2
import numpy as np
from dotenv import load_dotenv
from config import thresholds, instructions

def is_low_contrast(img: np.ndarray, thresh: float = thresholds.min_contrast) -> bool:
    """
    Check if the image has low contrast.
    Args:
        img: Input image as numpy array
        thresh: Contrast threshold
    Returns:
        True if low contrast, False otherwise.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    std_val = float(np.std(gray))
    return std_val < thresh #, std_val

def is_low_resolution(img: np.ndarray, 
                      min_width: int = thresholds.min_width,
                      min_height: int = thresholds.min_height) -> bool:
    """
    Check if image resolution is too low.
    Args:
        img: Input image as numpy array
        min_width: Minimum width
        min_height: Minimum height
    Returns:
        True if resolution is too low, False otherwise.
    """
    h, w = img.shape[:2]
    is_low = w < min_width or h < min_height
    return is_low #, (w, h)

def is_low_edge_density(img: np.ndarray,
                        thresh: float = thresholds.min_edge_density) -> bool:
    """
    Check if image has sufficient edge information (sharpness indicator).
    Args:
        img: Input image as numpy array
        thresh: Edge density threshold
    Returns:
        True if edge density is low, False otherwise.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    return edge_density < thresh #, edge_density

def is_blurry(img: np.ndarray, threshold: float = thresholds.blur_threshold) -> bool:
    """
    Check if an image is blurry using Laplacian variance.
    Args:
        img: Input image as numpy array
        threshold: Blur threshold (lower = more strict)
    Returns:
        True if blurry, False otherwise.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold #, variance


def has_glare(img: np.ndarray, threshold: float = thresholds.glare_threshold, bright_threshold: int = thresholds.glare_brightness) -> bool:
    """
    Check if an image has glare by detecting very bright pixels.
    Args:
        img: Input image as numpy array
        threshold: Percentage threshold for glare detection
        bright_threshold: Brightness threshold for pixel classification
    Returns:
        True if glare is present, False otherwise.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bright_mask = cv2.threshold(gray, bright_threshold, 255, cv2.THRESH_BINARY)
    glare_ratio = np.sum(bright_mask == 255) / (img.shape[0] * img.shape[1])
    return glare_ratio > threshold #, glare_ratio


def is_dark(img: np.ndarray, threshold: int = thresholds.darkness_threshold) -> bool:
    """
    Check if an image is too dark.
    Args:
        img: Input image as numpy array
        threshold: Mean brightness threshold
    Returns:
        True if image is too dark, False otherwise.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))
    return mean_brightness < threshold #, mean_brightness

def has_contours(img: np.ndarray) -> np.ndarray | None:
    """
    Find the largest 4-point contour (document outline) and return it if found.
    Args:
        img: Input image as numpy array
    Returns:
        The largest 4-point contour as a numpy array if found, else None.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Enhanced preprocessing for better contour detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Morphological operations to close gaps
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    image_area = img.shape[0] * img.shape[1]
    
    for c in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
        # Calculate area ratio
        area_ratio = cv2.contourArea(c) / image_area
        
        # Skip very small contours
        if area_ratio < 0.1:
            continue
            
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4:
            return approx #, area_ratio
    
    return None #, 0

def deskew_image(img: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """
    Deskew a document to a top-down view using perspective transform.
    Args:
        img: Input image as numpy array
        contour: 4-point document contour
    Returns:
        Deskewed image as numpy array.
    """
    # Reshape contour to 4x2 array
    points = contour.reshape(4, 2).astype("float32")
    
    # Sort points: top-left, top-right, bottom-right, bottom-left
    sum_coords = points.sum(axis=1)
    diff_coords = np.diff(points, axis=1)
    
    rect = np.array([
        points[np.argmin(sum_coords)],      # top-left
        points[np.argmin(diff_coords)],     # top-right
        points[np.argmax(sum_coords)],      # bottom-right
        points[np.argmax(diff_coords)]      # bottom-left
    ])
    
    # Calculate dimensions
    width = int(max(
        np.linalg.norm(rect[2] - rect[3]),  # bottom-right to bottom-left
        np.linalg.norm(rect[1] - rect[0])   # top-right to top-left
    ))
    height = int(max(
        np.linalg.norm(rect[1] - rect[2]),  # top-right to bottom-right
        np.linalg.norm(rect[0] - rect[3])   # top-left to bottom-left
    ))
    
    # Define destination rectangle
    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")
    
    # Apply perspective transform
    transform_matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, transform_matrix, (width, height))


def image_preops(image_path: str):
    """
    Run all pre-processing checks and deskewing on the image at the given path.
    Args:
        image_path: Path to the image file
    Returns:
        Tuple of (JPEG bytes if successful, error message if failed)
    """
    image_object = cv2.imread(image_path)
    if image_object is not None:
        if not is_blurry(image_object):
            if not is_low_resolution(image_object):
                if not is_low_contrast(image_object):
                    if not has_glare(image_object):
                        if not is_dark(image_object):
                            if not is_low_edge_density(image_object):
                                contour = has_contours(image_object)
                                if contour is not None:
                                    deskewed = deskew_image(image_object, contour)
                                    success, jpg_bytes = cv2.imencode('.jpg', deskewed)
                                    if success:
                                        return (jpg_bytes.tobytes(), "")
                                    else:
                                        return (None, "Failed to encode image as JPEG!")
                                return (None, "No Edges Found!" + instructions)
                            return (None, "Image has low edges!" + instructions)
                        return (None, "Image Too Dark!" + instructions)
                    return (None, "Image too Bright!" + instructions)
                return (None, "Image Contrast too Low!" + instructions)
            return (None, "Image resolution too low!" + instructions)
        return (None, "Image too Blurry!" + instructions)
    return (None, "Cannot read image!" + instructions)
