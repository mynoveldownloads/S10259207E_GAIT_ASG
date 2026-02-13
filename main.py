import streamlit as st
import os
from utils_storage import save_uploaded_file, get_storage_path, TRANSCRIPT_ROOT, generate_filename, MEDIA_ROOT, list_media_files, list_transcript_files, TTS_ROOT, RENDER_ROOT, list_latex_files, QUIZ_ROOT
from utils_processing import download_youtube_audio, transcribe_audio, format_timestamped_transcript, convert_to_wav, generate_tts_audio, compile_latex_to_pdf, process_unified_file
from utils_llm import generate_latex_code, generate_podcast_script
from utils_llm_quiz import generate_quiz
from utils_ocr import get_ocr_content

st.set_page_config(page_title="Unified Media & Document Parser", layout="wide")

st.title("🚀 Unified Media & Document Parser")
st.markdown("Upload any file (Video, Audio, PDF, PPTX) or provide a YouTube URL to transcribe or summarize it.")

# Sidebar Configuration for LLM
with st.sidebar:
    st.header("🤖 AI Configuration")
    llm_provider = st.selectbox("Model Provider", ["Ollama", "OpenRouter"], index=0, help="Choose between local Ollama or cloud OpenRouter.")
    
    if llm_provider == "Ollama":
        llm_model = st.text_input("Local Model", value="qwen3:30b-instruct", help="Model name in Ollama (e.g., qwen3:30b-instruct, gpt-oss)")
    else:
        llm_model = st.text_input("Cloud Model", value="google/gemini-2.5-flash-lite", help="OpenRouter model string.")

    st.divider()
    st.header("⚙️ Feature Station")
    
    st.subheader("🗣️ Text-to-Speech (TTS)")
    st.write("Generate audio from your saved transcripts using Kokoro.")
    
    transcripts = list_transcript_files()
    if transcripts:
        selected_transcript_tts = st.selectbox("Select Transcript for TTS", transcripts, key="tts_select")
        
        audio_type = st.selectbox(
            "Audio Type", 
            ["Audio Transcript", "Audio Summary"], 
            help="Transcript: Direct TTS. Summary: Podcast-style run-through via gpt-oss."
        )
        
        if st.button("Generate Audio", key="generate_tts"):
            try:
                with open(selected_transcript_tts, "r", encoding="utf-8") as f:
                    text_content = f.read()
                
                if not text_content.strip():
                    st.warning("Transcript is empty.")
                else:
                    final_tts_text = text_content
                    base_name = os.path.splitext(os.path.basename(selected_transcript_tts))[0]
                    if audio_type == "Audio Summary":
                        st.info(f"Generating Podcast Script... ({llm_provider}: {llm_model})")
                        script_placeholder = st.empty()
                        generated_script = ""
                        with st.container(height=300, border=True):
                            for chunk in generate_podcast_script(text_content, model_name=llm_model, provider=llm_provider):
                                generated_script += chunk
                                script_placeholder.markdown(generated_script)
                        final_tts_text = generated_script
                        st.success("Podcast Script Generated!")
                        tts_filename = f"{base_name}_Podcast_TTS.wav"
                    else:
                        tts_filename = f"{base_name}_TTS.wav"
                    
                    with st.spinner("Generating Speech..."):
                        tts_path = get_storage_path(TTS_ROOT, tts_filename)
                        generate_tts_audio(final_tts_text, tts_path)
                        st.success(f"Audio generated!")
                        st.audio(tts_path)
                        with open(tts_path, "rb") as f:
                                st.download_button("Download Audio", f, file_name=tts_filename)
            except Exception as e:
                st.error(f"TTS Error: {e}")
    else:
        st.info("No transcripts found.")

    st.divider()

    st.subheader("📄 PDF Summary (LaTeX)")
    st.write("Generate a condensed PDF summary using AI.")
    
    if transcripts:
        selected_transcript_pdf = st.selectbox("Select Transcript for PDF", transcripts, key="pdf_select")
        model_name = st.text_input("Model Name", value="gpt-oss:latest")
        
        summary_mode = st.selectbox(
            "Summary Mode",
            options=["Concise Summary", "Detailed Coverage"],
            index=0,
            help="Concise: Key highlights only. Detailed: Comprehensive coverage of all content."
        )
        
        mode_mapping = {
            "Concise Summary": "concise",
            "Detailed Coverage": "detailed"
        }
        selected_mode = mode_mapping[summary_mode]
        
        if st.button("Generate PDF", key="generate_pdf"):
            with st.spinner("Generating LaTeX Code & Compiling PDF..."):
                try:
                    with open(selected_transcript_pdf, "r", encoding="utf-8") as f:
                        transcript_text = f.read()
                        
                    st.info(f"Querying Model... (Mode: {summary_mode})")
                    
                    with st.container(height=400):
                        latex_output_placeholder = st.empty()
                        full_latex_code = ""
                        
                        for chunk in generate_latex_code(transcript_text, model_name=llm_model, summary_mode=selected_mode, provider=llm_provider):
                            full_latex_code += chunk
                            latex_output_placeholder.code(full_latex_code, language="latex")
                        
                    latex_code = full_latex_code
                    
                    if "```latex" in latex_code:
                        latex_code = latex_code.replace("```latex", "").replace("```", "")
                    elif "```" in latex_code:
                        latex_code = latex_code.replace("```", "")
                    latex_code = latex_code.strip()
                    
                    base_name = os.path.splitext(os.path.basename(selected_transcript_pdf))[0]
                    pdf_filename = f"{base_name}_Summary.pdf"
                    tex_filename = f"{base_name}_Summary.tex"
                    
                    target_pdf_path = get_storage_path(RENDER_ROOT, pdf_filename)
                    output_dir = os.path.dirname(target_pdf_path)
                    os.makedirs(output_dir, exist_ok=True)
                    
                    tex_path = os.path.join(output_dir, tex_filename)
                    with open(tex_path, "w", encoding="utf-8") as f:
                        f.write(latex_code)
                    
                    st.success(f"✓ LaTeX file saved: {tex_filename}")
                    st.info("Compiling PDF with pdflatex...")
                    
                    try:
                        final_pdf = compile_latex_to_pdf(tex_path, cleanup=True, output_dir=output_dir)
                        if final_pdf:
                            st.success("✓ PDF Generated Successfully!")
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(final_pdf, "rb") as f:
                                    st.download_button("Download PDF Summary", f, file_name=pdf_filename)
                            with col2:
                                with open(tex_path, "rb") as f:
                                    st.download_button("Download Source (.tex)", f, file_name=tex_filename)
                        else:
                            st.error("PDF compilation failed.")
                            with open(tex_path, "rb") as f:
                                st.download_button("Download Source (.tex)", f, file_name=tex_filename)
                    except Exception as e:
                        st.error(f"PDF Compilation Error: {str(e)}")
                        if os.path.exists(tex_path):
                            with open(tex_path, "rb") as f:
                                st.download_button("Download Source (.tex)", f, file_name=tex_filename)
                except Exception as e:
                    st.error(f"Generation Error: {e}")
    else:
        st.info("No transcripts available.")
    
    st.divider()
    st.subheader("📝 Quiz Generator")
    latex_files = list_latex_files()
    if latex_files:
        selected_latex = st.selectbox("Select LaTeX Summary", latex_files, key="quiz_latex_select")
        quiz_model = st.text_input("Model for Quiz", value="gpt-oss:latest", key="quiz_model")
        num_questions = st.slider("Number of Questions", min_value=5, max_value=30, value=10, step=5)
        
        if st.button("Generate Quiz", key="generate_quiz_btn"):
            with st.spinner(f"Generating {num_questions} quiz questions..."):
                try:
                    with open(selected_latex, "r", encoding="utf-8") as f:
                        latex_content = f.read()
                    
                    st.info(f"Analyzing content...")
                    json_response = generate_quiz(latex_content, model_name=llm_model, num_questions=num_questions, provider=llm_provider)
                    
                    try:
                        import json
                        quiz_data = json.loads(json_response)
                        st.session_state['quiz_data'] = quiz_data
                        st.session_state['quiz_answers'] = {}
                        st.session_state['quiz_submitted'] = False
                        
                        base_name = os.path.splitext(os.path.basename(selected_latex))[0]
                        quiz_path = get_storage_path(QUIZ_ROOT, f"{base_name}_Quiz.json")
                        with open(quiz_path, "w", encoding="utf-8") as f:
                            json.dump(quiz_data, f, indent=2)
                        st.success(f"✓ Generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to parse quiz JSON: {e}")
                        st.code(json_response, language="json")
                except Exception as e:
                    st.error(f"Quiz Generation Error: {e}")
    else:
        st.info("No LaTeX summaries available.")

# Interactive Quiz Display
if 'quiz_data' in st.session_state and st.session_state['quiz_data']:
    st.divider()
    st.header("📝 Interactive Quiz")
    quiz_data = st.session_state['quiz_data']
    st.subheader(quiz_data.get('quiz_title', 'Quiz'))
    
    for q in quiz_data['questions']:
        q_id = q['id']
        with st.container():
            st.markdown(f"### Question {q_id}")
            st.markdown(f"**{q['question']}**")
            options_list = [f"{key}: {value}" for key, value in q['options'].items()]
            selected = st.radio("Select your answer:", options=options_list, key=f"q_{q_id}", index=None, disabled=st.session_state.get('quiz_submitted', False))
            if selected: st.session_state['quiz_answers'][q_id] = selected[0]
            if st.session_state.get('quiz_submitted', False):
                user_answer = st.session_state['quiz_answers'].get(q_id, None)
                correct_answer = q['correct_answer']
                if user_answer == correct_answer: st.success(f"✅ Correct!")
                elif user_answer: st.error(f"❌ Incorrect. Correct: {correct_answer}")
                else: st.warning(f"⚠️ Not answered. Correct: {correct_answer}")
                with st.expander("📖 Explanation"): st.write(q['explanation'])
            st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if not st.session_state.get('quiz_submitted', False) and st.button("Submit Quiz", type="primary"):
            st.session_state['quiz_submitted'] = True
            st.rerun()
    with col2:
        if st.button("Reset Quiz"):
            st.session_state['quiz_answers'] = {}
            st.session_state['quiz_submitted'] = False
            st.rerun()
    if st.session_state.get('quiz_submitted', False):
        correct_count = sum(1 for q in quiz_data['questions'] if st.session_state['quiz_answers'].get(q['id']) == q['correct_answer'])
        total = len(quiz_data['questions'])
        percentage = (correct_count / total) * 100
        st.markdown("---")
        st.subheader(f"📊 Score: {correct_count}/{total} ({percentage:.1f}%)")
        with col3:
            import json
            results = {"quiz_title": quiz_data.get('quiz_title', 'Quiz'), "score": f"{correct_count}/{total}", "percentage": f"{percentage:.1f}%", "answers": st.session_state['quiz_answers'], "questions": quiz_data['questions']}
            st.download_button("Download Results (JSON)", json.dumps(results, indent=2), file_name="quiz_results.json", mime="application/json")

# Unified Tabs
tab1, tab2, tab3 = st.tabs(["📁 Unified Upload", "🔗 YouTube URL", "📂 Existing Files"])

source_path = None
original_filename = None

with tab1:
    st.write("Upload any file: Video, Audio, PDF, or PPTX.")
    uploaded_file = st.file_uploader("Upload File", type=['mp4', 'avi', 'mov', 'mp3', 'wav', 'm4a', 'mkv', 'webm', 'flv', 'ogg', 'pdf', 'pptx'])
    if uploaded_file:
        if st.button("Process File", key="process_upload"):
            with st.spinner("Saving file..."):
                # Use suffix for docs to keep them separate if needed, or just save
                suffix = "_local_doc" if uploaded_file.name.lower().endswith(('.pdf', '.pptx')) else ""
                source_path = save_uploaded_file(uploaded_file, suffix=suffix)
                original_filename = uploaded_file.name

with tab2:
    youtube_url = st.text_input("Enter YouTube URL")
    if youtube_url:
        if st.button("Process YouTube", key="process_url"):
            with st.spinner("Downloading audio..."):
                try:
                    temp_name = generate_filename("youtube_download", suffix="")
                    temp_base = os.path.splitext(temp_name)[0]
                    save_path_template = get_storage_path(MEDIA_ROOT, temp_base)
                    source_path = download_youtube_audio(youtube_url, save_path_template)
                    original_filename = os.path.basename(source_path)
                    st.success(f"Downloaded: {original_filename}")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab3:
    st.write("Select a previously uploaded file.")
    files = list_media_files()
    if files:
        selected_file = st.selectbox("Select File", files)
        if st.button("Process Selected File", key="process_existing"):
            source_path = selected_file
            original_filename = os.path.basename(selected_file)
    else:
        st.info("No files found.")

# Unified Processing Logic
if source_path and os.path.exists(source_path):
    st.divider()
    
    with st.status(f"Processing: {os.path.basename(source_path)}", expanded=True) as status:
        try:
            st.write("🔍 Identifying file type and routing to pipeline...")
            result = process_unified_file(source_path)
            
            if result["type"] == "media":
                st.write("🎙️ Transcribing audio/video with Whisper...")
                transcript_text = result["text"]
                segments = result["segments"]
                source_wav = result["source_path"]
                
                base_name = os.path.splitext(os.path.basename(source_path))[0]
                transcript_path = get_storage_path(TRANSCRIPT_ROOT, f"{base_name}_transcript.txt")
                timestamped_path = get_storage_path(TRANSCRIPT_ROOT, f"{base_name}_transcript_timestamped.txt")
                
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(transcript_text)
                timestamped_text = format_timestamped_transcript(segments)
                with open(timestamped_path, "w", encoding="utf-8") as f:
                    f.write(timestamped_text)
                
                status.update(label="✅ Transcription Complete!", state="complete", expanded=False)
                
                st.success("Transcription Complete!")
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Transcript")
                    st.text_area("Plain Text", transcript_text, height=300)
                    st.download_button("Download Transcript", transcript_text, file_name=f"{base_name}_transcript.txt")
                with col2:
                    st.subheader("Timestamped")
                    st.text_area("With Timestamps", timestamped_text, height=300)
                    st.download_button("Download Timestamped", timestamped_text, file_name=f"{base_name}_transcript_timestamped.txt")
                st.audio(source_wav)
                
            elif result["type"] == "document":
                st.write("📄 Extracting text and performing OCR on images...")
                extracted_content = result["content"]
                
                st.write("🤖 Querying local model (gpt-oss:latest) for LaTeX generation...")
                
                # Show generation in a chat-like box with fixed height
                st.subheader("Real-time LaTeX Generation")
                with st.container(height=400, border=True):
                    latex_placeholder = st.empty()
                    full_latex = ""
                    for chunk in generate_latex_code(extracted_content, model_name=llm_model, summary_mode="concise", provider=llm_provider):
                        full_latex += chunk
                        latex_placeholder.code(full_latex, language="latex")
                
                clean_latex = full_latex.strip()
                if clean_latex.startswith("```latex"): clean_latex = clean_latex[8:]
                elif clean_latex.startswith("```"): clean_latex = clean_latex[3:]
                if clean_latex.endswith("```"): clean_latex = clean_latex[:-3]
                clean_latex = clean_latex.strip()
                
                base_name = os.path.splitext(os.path.basename(source_path))[0]
                tex_filename = f"{base_name}_Summary.tex"
                tex_save_path = get_storage_path(RENDER_ROOT, tex_filename)
                with open(tex_save_path, "w", encoding="utf-8") as f:
                    f.write(clean_latex)
                
                st.write(f"💾 Saved LaTeX source: {tex_filename}")
                st.write("🛠️ Compiling PDF with pdflatex...")
                
                pdf_path = compile_latex_to_pdf(tex_save_path, cleanup=True, output_dir=os.path.dirname(tex_save_path))
                
                if pdf_path and os.path.exists(pdf_path):
                    status.update(label="✅ Document Processing Complete!", state="complete", expanded=False)
                    st.success("PDF Generated Successfully!")
                    col1, col2 = st.columns(2)
                    with col1:
                        with open(pdf_path, "rb") as f:
                            st.download_button("Download PDF Summary", f, file_name=os.path.basename(pdf_path))
                    with col2:
                        with open(tex_save_path, "rb") as f:
                            st.download_button("Download LaTeX Source", f, file_name=tex_filename)
                else:
                    status.update(label="⚠️ Processing finished with compilation errors", state="error", expanded=True)
                    st.error("PDF Compilation failed.")
                    with open(tex_save_path, "rb") as f:
                        st.download_button("Download LaTeX Source", f, file_name=tex_filename)
                        
        except Exception as e:
            st.error(f"Processing Error: {e}")
            import traceback
            st.code(traceback.format_exc())
