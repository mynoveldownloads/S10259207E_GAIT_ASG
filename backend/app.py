"""
Flask Backend API for Video Transcription App
Provides REST API endpoints for the React frontend
"""

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import sys
import json
from werkzeug.utils import secure_filename

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils_storage import (
    save_uploaded_file, get_storage_path, TRANSCRIPT_ROOT, 
    generate_filename, MEDIA_ROOT, list_media_files, 
    list_transcript_files, TTS_ROOT, RENDER_ROOT, 
    list_latex_files, QUIZ_ROOT
)
from utils_processing import (
    download_youtube_audio, transcribe_audio, 
    format_timestamped_transcript, convert_to_wav, 
    generate_tts_audio, compile_latex_to_pdf, process_unified_file
)
from utils_llm import generate_latex_code, chat_with_tools, generate_conversational_summary
from utils_llm_quiz import generate_quiz

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
ALLOWED_EXTENSIONS = {
    'mp4', 'avi', 'mov', 'mp3', 'wav', 'm4a', 'mkv', 'webm', 'flv', 'ogg',
    'pdf', 'pptx', 'docx', 'png', 'jpg', 'jpeg', 'webp'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Backend is running'})

# ============================================================================
# MEDIA MANAGEMENT
# ============================================================================

@app.route('/api/media/list', methods=['GET'])
def list_media():
    """List all uploaded media files"""
    try:
        files = list_media_files()
        file_list = [
            {
                'path': f,
                'name': os.path.basename(f),
                'size': os.path.getsize(f)
            }
            for f in files
        ]
        return jsonify({'success': True, 'files': file_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/media/upload', methods=['POST'])
def upload_media():
    """Upload a media file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Save file using existing utility
        filename = secure_filename(file.filename)
        temp_path = os.path.join(MEDIA_ROOT, filename)
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        file.save(temp_path)
        
        # Generate proper filename with timestamp
        final_name = generate_filename(os.path.splitext(filename)[0], os.path.splitext(filename)[1])
        final_path = get_storage_path(MEDIA_ROOT, final_name)
        os.rename(temp_path, final_path)
        
        return jsonify({
            'success': True,
            'path': final_path,
            'filename': final_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/media/youtube', methods=['POST'])
def download_youtube():
    """Download audio from YouTube URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # Generate filename
        temp_name = generate_filename("youtube_download", suffix="")
        temp_base = os.path.splitext(temp_name)[0]
        save_path_template = get_storage_path(MEDIA_ROOT, temp_base)
        
        # Download
        source_path = download_youtube_audio(url, save_path_template)
        
        return jsonify({
            'success': True,
            'path': source_path,
            'filename': os.path.basename(source_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# TRANSCRIPTION
# ============================================================================

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio/video file"""
    try:
        data = request.get_json()
        source_path = data.get('path')
        
        if not source_path or not os.path.exists(source_path):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        
        # Route to unified processor
        result = process_unified_file(source_path)
        
        if result["type"] == "media":
            transcript_text = result["text"]
            segments = result["segments"]
            
            # Save transcripts
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            transcript_filename = f"{base_name}_transcript.txt"
            timestamped_filename = f"{base_name}_transcript_timestamped.txt"
            
            transcript_path = get_storage_path(TRANSCRIPT_ROOT, transcript_filename)
            timestamped_path = get_storage_path(TRANSCRIPT_ROOT, timestamped_filename)
            
            # Save plain text
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            
            # Save timestamped
            timestamped_text = format_timestamped_transcript(segments)
            with open(timestamped_path, "w", encoding="utf-8") as f:
                f.write(timestamped_text)
            
            return jsonify({
                'success': True,
                'type': 'media',
                'transcript': transcript_text,
                'timestamped': timestamped_text,
                'transcript_path': transcript_path,
                'timestamped_path': timestamped_path
            })
        else:
            # Document OCR result
            content = result["content"]
            
            # Save as a transcript file as well for downstream features
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            transcript_filename = f"{base_name}_ocr.txt"
            transcript_path = get_storage_path(TRANSCRIPT_ROOT, transcript_filename)
            
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return jsonify({
                'success': True,
                'type': 'document',
                'transcript': content,
                'transcript_path': transcript_path
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transcripts/list', methods=['GET'])
def list_transcripts():
    """List all transcripts"""
    try:
        files = list_transcript_files()
        transcript_list = [
            {
                'path': f,
                'name': os.path.basename(f),
                'size': os.path.getsize(f)
            }
            for f in files
        ]
        return jsonify({'success': True, 'transcripts': transcript_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transcripts/content', methods=['POST'])
def get_transcript_content():
    """Get content of a specific transcript"""
    try:
        data = request.get_json()
        path = data.get('path')
        
        if not path or not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# TEXT-TO-SPEECH
# ============================================================================

@app.route('/api/tts/generate', methods=['POST'])
def generate_tts():
    """Generate TTS audio from transcript"""
    try:
        data = request.get_json()
        transcript_path = data.get('transcript_path')
        
        if not transcript_path or not os.path.exists(transcript_path):
            return jsonify({'success': False, 'error': 'Invalid transcript path'}), 400
        
        # Read transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        if not text_content.strip():
            return jsonify({'success': False, 'error': 'Transcript is empty'}), 400
        
        tts_mode = data.get('tts_mode', 'transcript')
        print(f"Generating TTS in mode: {tts_mode}")
        
        if tts_mode == 'summary':
            # Generate conversational summary using Gemini Flash
            print("Requesting conversational summary...")
            text_content = generate_conversational_summary(text_content)
            print("Summary generated successfully.")
            base_name = os.path.splitext(os.path.basename(transcript_path))[0]
            tts_filename = f"{base_name}_Summary_TTS.wav"
        else:
            base_name = os.path.splitext(os.path.basename(transcript_path))[0]
            tts_filename = f"{base_name}_TTS.wav"
            
        # Generate TTS
        tts_path = get_storage_path(TTS_ROOT, tts_filename)
        print(f"Saving TTS to: {tts_path}")
        
        generate_tts_audio(text_content, tts_path)
        print("TTS audio file created.")
        
        # Return filename and a relative URL for the frontend
        return jsonify({
            'success': True,
            'audio_path': tts_path,
            'filename': tts_filename,
            'audio_url': f"/api/tts/download/{tts_filename}"
        })
    except Exception as e:
        print(f"Error in TTS generation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tts/download/<filename>', methods=['GET'])
def download_tts(filename):
    """Download generated TTS audio"""
    try:
        path = get_storage_path(TTS_ROOT, filename)
        if not os.path.exists(path):
            return "File not found", 404
        return send_file(path, mimetype="audio/wav")
    except Exception as e:
        return str(e), 500

# ============================================================================
# PDF GENERATION
# ============================================================================

@app.route('/api/pdf/stream_latex', methods=['POST'])
def stream_latex():
    """Stream LaTeX code generation"""
    try:
        data = request.get_json()
        transcript_path = data.get('transcript_path')
        model_name = data.get('model_name', 'openai/gpt-oss-120b')
        summary_mode = data.get('summary_mode', 'concise')
        provider = data.get('provider', 'OpenRouter')
        
        if not transcript_path or not os.path.exists(transcript_path):
            return jsonify({'success': False, 'error': 'Invalid transcript path'}), 400
            
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
            
        def generate():
            for chunk in generate_latex_code(transcript_text, model_name=model_name, summary_mode=summary_mode, provider=provider):
                yield chunk
                
        return Response(generate(), mimetype='text/plain')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pdf/generate', methods=['POST'])
def generate_pdf():
    """Generate PDF summary from transcript or provided LaTeX code"""
    try:
        data = request.get_json()
        transcript_path = data.get('transcript_path')
        model_name = data.get('model_name', 'openai/gpt-oss-120b')
        summary_mode = data.get('summary_mode', 'concise')
        provider = data.get('provider', 'Ollama')
        provided_latex = data.get('latex_code')
        
        if not transcript_path or not os.path.exists(transcript_path):
            return jsonify({'success': False, 'error': 'Invalid transcript path'}), 400
        
        if provided_latex:
            latex_code = provided_latex
        else:
            # Read transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Generate LaTeX (collect all chunks)
            latex_code = ""
            for chunk in generate_latex_code(transcript_text, model_name=model_name, summary_mode=summary_mode, provider=provider):
                latex_code += chunk
        
        # Clean up markdown markers
        if "```latex" in latex_code:
            latex_code = latex_code.replace("```latex", "").replace("```", "")
        elif "```" in latex_code:
            latex_code = latex_code.replace("```", "")
        latex_code = latex_code.strip()
        
        # Save .tex file
        base_name = os.path.splitext(os.path.basename(transcript_path))[0]
        pdf_filename = f"{base_name}_Summary.pdf"
        tex_filename = f"{base_name}_Summary.tex"
        
        target_pdf_path = get_storage_path(RENDER_ROOT, pdf_filename)
        output_dir = os.path.dirname(target_pdf_path)
        os.makedirs(output_dir, exist_ok=True)
        
        tex_path = os.path.join(output_dir, tex_filename)
        
        # Write .tex file
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        
        # Compile PDF
        try:
            final_pdf = compile_latex_to_pdf(tex_path, cleanup=True, output_dir=output_dir)
            
            return jsonify({
                'success': True,
                'pdf_path': final_pdf,
                'tex_path': tex_path,
                'pdf_filename': pdf_filename,
                'tex_filename': tex_filename
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'PDF compilation failed: {str(e)}',
                'tex_path': tex_path,
                'tex_filename': tex_filename
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/latex/list', methods=['GET'])
def list_latex():
    """List all LaTeX files"""
    try:
        files = list_latex_files()
        latex_list = [
            {
                'path': f,
                'name': os.path.basename(f),
                'size': os.path.getsize(f)
            }
            for f in files
        ]
        return jsonify({'success': True, 'files': latex_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# QUIZ GENERATION
# ============================================================================

@app.route('/api/quiz/generate', methods=['POST'])
def generate_quiz_endpoint():
    """Generate quiz from LaTeX summary"""
    try:
        data = request.get_json()
        latex_path = data.get('latex_path')
        model_name = data.get('model_name', 'gpt-oss:latest')
        num_questions = data.get('num_questions', 10)
        
        if not latex_path or not os.path.exists(latex_path):
            return jsonify({'success': False, 'error': 'Invalid LaTeX path'}), 400
        
        # Read LaTeX content
        with open(latex_path, 'r', encoding='utf-8') as f:
            latex_content = f.read()
        
        # Generate quiz
        json_response = generate_quiz(latex_content, model_name=model_name, num_questions=num_questions)
        
        # Parse JSON
        quiz_data = json.loads(json_response)
        
        # Save quiz to file
        base_name = os.path.splitext(os.path.basename(latex_path))[0]
        quiz_filename = f"{base_name}_Quiz.json"
        quiz_path = get_storage_path(QUIZ_ROOT, quiz_filename)
        
        with open(quiz_path, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'quiz_data': quiz_data,
            'quiz_path': quiz_path,
            'quiz_filename': quiz_filename
        })
    except json.JSONDecodeError as e:
        return jsonify({'success': False, 'error': f'Failed to parse quiz JSON: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# FILE DOWNLOAD
# ============================================================================

@app.route('/api/download', methods=['POST'])
def download_file():
    """Download a file"""
    try:
        data = request.get_json()
        file_path = data.get('path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CHATBOT
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Chatbot with tool calling"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        model_name = data.get('model_name', 'qwen3:30b-instruct')
        provider = data.get('provider', 'Ollama')

        # First call to get model response and potential tool calls
        response_message = chat_with_tools(messages, model_name, provider)
        
        # If there are no tool calls, just return the message
        if not response_message.tool_calls:
            return jsonify({
                'success': True, 
                'message': response_message.content,
                'tool_calls': []
            })

        # Process tool calls
        tool_results = []
        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"🛠️ Executing tool: {function_name} with {function_args}")
            
            result = None
            if function_name == "download_youtube":
                url = function_args.get("url")
                temp_name = generate_filename("youtube_download", suffix="")
                temp_base = os.path.splitext(temp_name)[0]
                save_path_template = get_storage_path(MEDIA_ROOT, temp_base)
                source_path = download_youtube_audio(url, save_path_template)
                result = {"status": "success", "path": source_path, "filename": os.path.basename(source_path)}
            
            elif function_name == "transcribe_file":
                path = function_args.get("path")
                
                # Use unified processing
                transcription_result = process_unified_file(path)
                
                # Save results based on type
                base_name = os.path.splitext(os.path.basename(path))[0]
                if transcription_result["type"] == "media":
                    transcript_path = get_storage_path(TRANSCRIPT_ROOT, f"{base_name}_transcript.txt")
                    content = transcription_result["text"]
                else:
                    transcript_path = get_storage_path(TRANSCRIPT_ROOT, f"{base_name}_ocr.txt")
                    content = transcription_result["content"]
                    
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                result = {
                    "status": "success", 
                    "type": transcription_result["type"],
                    "transcript_path": transcript_path, 
                    "text_preview": content[:200] + "..."
                }
            
            elif function_name == "generate_summary_pdf":
                t_path = function_args.get("transcript_path")
                m_name = function_args.get("model_name", "gpt-oss:latest")
                
                with open(t_path, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                
                latex_code = ""
                for chunk in generate_latex_code(transcript_text, model_name=m_name):
                    latex_code += chunk
                
                if "```latex" in latex_code:
                    latex_code = latex_code.replace("```latex", "").replace("```", "")
                elif "```" in latex_code:
                    latex_code = latex_code.replace("```", "")
                latex_code = latex_code.strip()
                
                base_name = os.path.splitext(os.path.basename(t_path))[0]
                pdf_filename = f"{base_name}_Summary.pdf"
                target_pdf_path = get_storage_path(RENDER_ROOT, pdf_filename)
                output_dir = os.path.dirname(target_pdf_path)
                os.makedirs(output_dir, exist_ok=True)
                
                tex_path = os.path.join(output_dir, f"{base_name}_Summary.tex")
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_code)
                
                final_pdf = compile_latex_to_pdf(tex_path, cleanup=True, output_dir=output_dir)
                result = {"status": "success", "pdf_path": final_pdf, "tex_path": tex_path}
            
            elif function_name == "generate_quiz_from_latex":
                l_path = function_args.get("latex_path")
                num_q = function_args.get("num_questions", 10)
                
                with open(l_path, 'r', encoding='utf-8') as f:
                    latex_content = f.read()
                
                json_response = generate_quiz(latex_content, num_questions=num_q)
                quiz_data = json.loads(json_response)
                
                base_name = os.path.splitext(os.path.basename(l_path))[0]
                quiz_path = get_storage_path(QUIZ_ROOT, f"{base_name}_Quiz.json")
                with open(quiz_path, 'w', encoding='utf-8') as f:
                    json.dump(quiz_data, f, indent=2)
                
                result = {"status": "success", "quiz_path": quiz_path}
            
            elif function_name == "list_files":
                f_type = function_args.get("folder_type")
                file_list = []
                if f_type == "media":
                    file_list = [os.path.basename(f) for f in list_media_files()]
                elif f_type == "transcripts":
                    file_list = [os.path.basename(f) for f in list_transcript_files()]
                elif f_type == "latex":
                    file_list = [os.path.basename(f) for f in list_latex_files()]
                elif f_type == "quiz":
                    files = []
                    if os.path.exists(QUIZ_ROOT):
                        files = [os.path.join(QUIZ_ROOT, f) for f in os.listdir(QUIZ_ROOT) if f.endswith('.json')]
                    file_list = [os.path.basename(f) for f in files]
                
                result = {"status": "success", "files": file_list}

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result),
            })
            tool_results.append({"tool": function_name, "result": result})

        # Second call to get final response after tool execution
        final_response = chat_with_tools(messages, model_name, provider)
        
        return jsonify({
            'success': True,
            'message': final_response.content,
            'tool_results': tool_results
        })

    except Exception as e:
        print(f"❌ Chat Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'File too large (max 500MB)'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(TRANSCRIPT_ROOT, exist_ok=True)
    os.makedirs(TTS_ROOT, exist_ok=True)
    os.makedirs(RENDER_ROOT, exist_ok=True)
    os.makedirs(QUIZ_ROOT, exist_ok=True)
    
    print("🚀 Starting Flask Backend Server...")
    print("📡 API will be available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
