import os
import yt_dlp
import whisper
import subprocess
from datetime import datetime
import soundfile as sf
import numpy as np

try:
    from kokoro import KPipeline
except ImportError:
    KPipeline = None

def download_youtube_audio(url: str, output_path_template: str) -> str:
    """
    Downloads audio from a YouTube URL using yt-dlp and saves it to the specified path template.
    output_path_template should be a full path without extension.
    We force conversion to wav (best compatibility).
    Returns the path to the downloaded file.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path_template,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    # yt-dlp appends extension
    return output_path_template + ".wav"

def transcribe_audio(file_path: str):
    """
    Transcribes audio using Whisper base model.
    Returns a dictionary with 'text' and 'segments'.
    """
    model = whisper.load_model("base")
    # Force English as requested
    result = model.transcribe(file_path, language="en")
    return result

def format_timestamped_transcript(segments) -> str:
    """
    Formats the segments into a timestamped string.
    """
    output = ""
    for segment in segments:
        start = segment['start']
        end = segment['end']
        text = segment['text']
        # Format seconds to HH:MM:SS
        start_str = format_seconds(start)
        end_str = format_seconds(end)
        output += f"[{start_str} --> {end_str}] {text}\n"
    return output

def format_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def convert_to_wav(input_path: str, output_path: str):
    """
    Converts any media file to WAV using ffmpeg (pcm_s16le).
    This codec is built-in to even minimal ffmpeg installations.
    """
    # Ensure absolute paths to avoid any subprocess path resolution issues
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-vn',  # Disable video recording
            '-acodec', 'pcm_s16le',  # Standard wav pcm
            '-ar', '16000',  # 16kHz is optimal for Whisper
            '-ac', '1',  # Mono is enough for transcription and saves space
            '-y',  # Overwrite output files
            output_path
        ]
        # Run command
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "No stderr output"
        print(f"FFmpeg Error: {error_message}")
        raise RuntimeError(f"FFmpeg failed with exit code {e.returncode}. Stderr: {error_message}") from e

def generate_tts_audio(text: str, output_path: str):
    """
    Generates TTS audio using Kokoro and saves it to output_path as a WAV file.
    """
    if KPipeline is None:
        raise ImportError("Kokoro library not installed. Please install 'kokoro' and 'soundfile'.")

    # Initialize Pipeline (English)
    # This might download weights on first run
    pipeline = KPipeline(lang_code='a')  # 'a' for American English

    # Generate audio
    # voice='af_bella' is a common default, or we could expose this
    # speed=1 is default
    generator = pipeline(text, voice='af_bella', speed=1)

    # Collect all audio chunks
    all_audio = []
    for _, _, audio in generator:
        all_audio.append(audio)

    if all_audio:
        # Concatenate audio chunks
        final_audio = np.concatenate(all_audio)
        # Save to file
        # Kokoro uses 24000 Hz by default
        sf.write(output_path, final_audio, 24000)
        return True
    else:
        return False

def compile_latex_to_pdf(tex_filepath, cleanup=True, output_dir=None):
    """
    Compile a .tex file to PDF using pdflatex.
    
    Args:
        tex_filepath: Full path to the .tex file
        cleanup: Whether to delete auxiliary files after compilation
        output_dir: Optional output directory for the PDF (if None, uses same dir as tex file)
    
    Returns:
        Path to the generated PDF if successful, None otherwise
    """
    # Ensure we have absolute path
    tex_filepath = os.path.abspath(tex_filepath)
    
    # Get base name without extension
    base_name = os.path.splitext(tex_filepath)[0]
    tex_dir = os.path.dirname(tex_filepath)
    
    # Check if .tex file exists
    if not os.path.exists(tex_filepath):
        print(f"Error: {tex_filepath} not found!")
        return None
    
    print(f"Compiling {tex_filepath}...")
    
    # Determine pdflatex command
    pdflatex_cmd = "pdflatex"
    common_paths = [
        r"C:\Users\mynov\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Users\mynov\Documents\MiKTeX\miktex\bin\x64\pdflatex.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"),
        r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64\pdflatex.exe"
    ]
    
    # Check for pdflatex in PATH
    has_pdflatex = False
    try:
        subprocess.run([pdflatex_cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        has_pdflatex = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Check common Windows MiKTeX paths
        for p in common_paths:
            if os.path.exists(p):
                pdflatex_cmd = p
                has_pdflatex = True
                print(f"Found pdflatex at: {p}")
                break
    
    if not has_pdflatex:
        print("Error: pdflatex not found! Make sure MiKTeX is installed and in PATH.")
        return None
    
    # Build pdflatex command
    # Use output directory if specified, otherwise use tex file's directory
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        cmd = [pdflatex_cmd, '-interaction=nonstopmode', f'-output-directory={output_dir}', tex_filepath]
        pdf_file = os.path.join(output_dir, os.path.basename(base_name) + '.pdf')
        log_file = os.path.join(output_dir, os.path.basename(base_name) + '.log')
    else:
        cmd = [pdflatex_cmd, '-interaction=nonstopmode', tex_filepath]
        pdf_file = base_name + '.pdf'
        log_file = base_name + '.log'
    
    try:
        # Run pdflatex (Pass 1)
        print("Running first pass...")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check if PDF was created (even if there were warnings)
        # LaTeX often returns non-zero for warnings (overfull boxes, etc.) but still creates the PDF
        if not os.path.exists(pdf_file):
            print(f"Error during compilation!")
            print(f"Return code: {result.returncode}")
            
            # Check log file for detailed errors
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    # Print last 50 lines of log
                    print("\nLast 50 lines of log file:")
                    log_excerpt = '\n'.join(log_content.split('\n')[-50:])
                    print(log_excerpt)
            return None
        
        # Run second pass for cross-references (even if there were warnings)
        print("Running second pass...")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if os.path.exists(pdf_file):
            print(f"✓ PDF created successfully: {pdf_file}")
            
            # Show warnings if any (but don't fail)
            if result.returncode != 0:
                print(f"Note: LaTeX returned warnings (code {result.returncode}), but PDF was created successfully.")
            
            # Cleanup auxiliary files
            if cleanup:
                aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot']
                for ext in aux_extensions:
                    if output_dir:
                        aux_file = os.path.join(output_dir, os.path.basename(base_name) + ext)
                    else:
                        aux_file = base_name + ext
                    if os.path.exists(aux_file):
                        try:
                            os.remove(aux_file)
                            print(f"Removed {aux_file}")
                        except:
                            pass
            
            return pdf_file
        else:
            print("Error: PDF file not created!")
            return None
            
    except FileNotFoundError:
        print("Error: pdflatex not found! Make sure MiKTeX is installed and in PATH.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
def process_unified_file(file_path: str, model_name: str = "gpt-oss:latest"):
    """
    Routes a file to the appropriate processing pipeline based on its extension.
    - Video/Audio: Transcription
    - PDF/PPTX: OCR & Summary
    Returns a dictionary with processing results.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.mp4', '.avi', '.mov', '.mp3', '.wav', '.m4a', '.mkv', '.webm', '.flv', '.ogg']:
        # 1. Ensure WAV for whisper
        working_p = file_path
        if not file_path.endswith(".wav"):
            wav_path = os.path.splitext(file_path)[0] + ".wav"
            convert_to_wav(file_path, wav_path)
            working_p = wav_path
        
        # 2. Transcribe
        result = transcribe_audio(working_p)
        return {
            "type": "media",
            "text": result["text"],
            "segments": result["segments"],
            "source_path": working_p
        }
        
    elif ext in ['.pdf', '.pptx', '.docx', '.png', '.jpg', '.jpeg', '.webp']:
        from utils_ocr import get_ocr_content
        content = get_ocr_content(file_path)
        return {
            "type": "document",
            "content": content
        }
    else:
        raise ValueError(f"Unsupported file format: {ext}")
