"""Shared paths for generated Stage 4.3 C images and software references."""
import os

C_IMAGE_DIR = 'c_hex'
C_REFERENCE_DIR = 'c_iss'
C_IMAGE_SUFFIX = '.hex'
C_REFERENCE_SUFFIX = '.trace'

def c_image_path(output_dir, name):
    return os.path.join(output_dir, C_IMAGE_DIR, name + C_IMAGE_SUFFIX)

def c_reference_path(output_dir, name):
    return os.path.join(output_dir, C_REFERENCE_DIR, name + C_REFERENCE_SUFFIX)
