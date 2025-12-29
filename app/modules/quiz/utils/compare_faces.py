import os
import tempfile
from PIL import Image
import face_recognition
from fastapi import UploadFile
from urllib.parse import urlparse
from core.config import settings


async def compare_faces(img1: str, img2_file: UploadFile) -> bool:
    """
    Compare two faces using face_recognition library.
    
    Args:
        img1: URL or local path to first image
        img2_file: Uploaded image file
        
    Returns:
        bool: True if faces match, False otherwise
    """
    
    # Convert URL to local path
    if img1.startswith(("http://", "https://")):
        parsed = urlparse(img1)
        img1_path = os.path.join(
            settings.file_url.upload_dir,
            parsed.path.replace("/uploads/", "").lstrip("/")
        )
    else:
        img1_path = img1
    
    if not os.path.exists(img1_path):
        raise FileNotFoundError(f"Image not found: {img1_path}")
    
    # Save uploaded image to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await img2_file.read())
        tmp_path = tmp.name
    
    try:
        # Load first image and get face encoding
        image1 = face_recognition.load_image_file(img1_path)
        face_encodings1 = face_recognition.face_encodings(image1)
        
        if not face_encodings1:
            raise ValueError(f"No face detected in image: {img1_path}")
        
        # Load second image and get face encoding
        image2 = face_recognition.load_image_file(tmp_path)
        face_encodings2 = face_recognition.face_encodings(image2)
        
        if not face_encodings2:
            raise ValueError(f"No face detected in uploaded image")
        
        # Compare face encodings
        # tolerance: how much distance is allowed (lower = stricter)
        # Default is 0.6, you can adjust based on your needs
        results = face_recognition.compare_faces(
            [face_encodings1[0]], 
            face_encodings2[0], 
            tolerance=0.6
        )
        
        return results[0]
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)