"""
Shared image utility functions for storyboard generation.
Provides consistent image processing across all renderers.
"""

from PIL import Image


def fit_image_to_box(img, max_width, max_height, maintain_aspect=True):
    """
    Resize image to fit within box while maintaining aspect ratio.
    
    This is the standard 'contain' behavior - the image is scaled to fit
    completely within the box without cropping, maintaining its aspect ratio.
    
    Args:
        img: PIL Image object to resize
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        maintain_aspect: If True, maintains aspect ratio (default: True)
        
    Returns:
        PIL Image object resized to fit within the box
        
    Examples:
        >>> # Landscape image (800x600) in portrait box (400x600)
        >>> # Result: 400x300 (fits width, height adjusted)
        
        >>> # Portrait image (600x800) in landscape box (600x400)
        >>> # Result: 300x400 (fits height, width adjusted)
    """
    if not maintain_aspect:
        return img.resize((max_width, max_height), Image.Resampling.LANCZOS)
    
    src_width, src_height = img.size
    src_aspect = src_width / src_height
    box_aspect = max_width / max_height
    
    if src_aspect > box_aspect:
        # Width constrained - image is wider than box
        new_width = max_width
        new_height = int(max_width / src_aspect)
    else:
        # Height constrained - image is taller than box
        new_height = max_height
        new_width = int(max_height * src_aspect)
    
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def get_centering_offset(image_size, container_size):
    """
    Calculate offset to center an image within a container.
    
    Args:
        image_size: Tuple of (width, height) of the image
        container_size: Tuple of (width, height) of the container
        
    Returns:
        Tuple of (x_offset, y_offset) in pixels
        
    Example:
        >>> get_centering_offset((300, 400), (500, 600))
        (100, 100)  # Centers the 300x400 image in a 500x600 container
    """
    img_w, img_h = image_size
    container_w, container_h = container_size
    
    x_offset = (container_w - img_w) // 2
    y_offset = (container_h - img_h) // 2
    
    return x_offset, y_offset
