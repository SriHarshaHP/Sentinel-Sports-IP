import imagehash
import numpy as np
from PIL import Image

def generate_phash(pil_image, hash_size=16):
    """Generate a high-resolution perceptual hash (256-bit)."""
    return str(imagehash.phash(pil_image, hash_size=hash_size))

def generate_dhash(pil_image, hash_size=16):
    """Generate a difference hash — good at detecting structural changes."""
    return str(imagehash.dhash(pil_image, hash_size=hash_size))

def generate_whash(pil_image, hash_size=16):
    """Generate a wavelet hash — robust against compression artifacts."""
    return str(imagehash.whash(pil_image, hash_size=hash_size))

def generate_color_hash(pil_image):
    """Generate a color-layout hash — captures color distribution."""
    return str(imagehash.colorhash(pil_image, binbits=3))

def generate_multi_hash(pil_image):
    """
    Generate multiple hash fingerprints for a single frame.
    Returns a dict of hash_type -> hash_string.
    Using multiple algorithms dramatically improves matching accuracy
    because each is sensitive to different types of transformations.
    """
    return {
        "phash": generate_phash(pil_image),
        "dhash": generate_dhash(pil_image),
        "whash": generate_whash(pil_image),
        "color": generate_color_hash(pil_image),
    }

def hamming_distance(hash1_hex: str, hash2_hex: str) -> int:
    """Compute hamming distance between two hex-encoded hashes."""
    h1 = imagehash.hex_to_hash(hash1_hex)
    h2 = imagehash.hex_to_hash(hash2_hex)
    return h1 - h2
