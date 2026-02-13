import os
from datetime import datetime
import glob

MEDIA_ROOT = "media"
TRANSCRIPT_ROOT = "transcript"
TTS_ROOT = "TTS"
RENDER_ROOT = "render"
QUIZ_ROOT = "quiz"

def get_storage_path(root_folder: str, filename: str) -> str:
    """
    Generates a path based on current month/year and creates the directory if needed.
    Structure: root_folder/MM-YYYY/filename
    """
    now = datetime.now()
    subfolder = now.strftime("%m-%Y")
    
    directory = os.path.join(root_folder, subfolder)
    os.makedirs(directory, exist_ok=True)
    
    return os.path.join(directory, filename)
    
def list_transcript_files() -> list:
    """
    Lists all transcript files (excluding timestamped versions) in the transcript directory.
    Returns a list of relative paths.
    """
    files = []
    if os.path.exists(TRANSCRIPT_ROOT):
        for root, dirs, filenames in os.walk(TRANSCRIPT_ROOT):
            for filename in filenames:
                if filename.endswith(".txt") and "_timestamped" not in filename:
                    files.append(os.path.join(root, filename))
    return sorted(files, key=os.path.getmtime, reverse=True)

def list_latex_files() -> list:
    """
    Lists all .tex files in the render directory.
    Returns a list of relative paths.
    """
    files = []
    if os.path.exists(RENDER_ROOT):
        for root, dirs, filenames in os.walk(RENDER_ROOT):
            for filename in filenames:
                if filename.endswith(".tex"):
                    files.append(os.path.join(root, filename))
    return sorted(files, key=os.path.getmtime, reverse=True)

def generate_filename(original_filename: str, suffix: str = "") -> str:
    """
    Generates a filename with current datetime and optional suffix.
    Format: {original_name}_{datetime}{suffix}.{ext}
    """
    name, ext = os.path.splitext(original_filename)
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S")
    
    # Sanitize name slightly to avoid path issues
    clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
    clean_name = clean_name.replace(" ", "_")
    
    return f"{clean_name}_{dt_string}{suffix}{ext}"

def save_uploaded_file(uploaded_file, suffix: str = "") -> str:
    """
    Saves an uploaded Streamlit file to the media directory.
    Returns the absolute path to the saved file.
    """
    new_filename = generate_filename(uploaded_file.name, suffix=suffix)
    save_path = get_storage_path(MEDIA_ROOT, new_filename)
    
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    return save_path

def list_media_files() -> list:
    """
    Lists all files in the media directory recursively.
    Returns a list of relative paths from the current working directory.
    """
    files = []
    # Browse through all subdirectories of MEDIA_ROOT
    if os.path.exists(MEDIA_ROOT):
        for root, dirs, filenames in os.walk(MEDIA_ROOT):
            for filename in filenames:
                files.append(os.path.join(root, filename))
    return sorted(files, key=os.path.getmtime, reverse=True)
