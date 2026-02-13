from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def get_client(provider: str = "Ollama"):
    """
    Returns an OpenAI-compatible client based on the provider.
    """
    if provider == "OpenRouter":
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    else: # Default to Ollama
        return OpenAI(
            base_url='http://localhost:11434/v1',
            api_key='ollama',
        )

def generate_latex_code(transcript_text: str, model_name: str = "qwen3:30b-instruct", summary_mode: str = "concise", provider: str = "Ollama"):
    """
    Sends the transcript to the selected provider to generate LaTeX code.
    Yields chunks of generated text for streaming.
    """
    client = get_client(provider)

    system_prompt = """You are an expert academic assistant and LaTeX specialist.
    Your task is to convert lecture transcripts or content into a comprehensive, high-quality LaTeX document.
    You strictly follow formatting rules, structure requirements, and content documentation rules.
    You explain complex concepts in layman's terms while retaining all technical depth.
    """

    user_prompt_template = f"""
convert this lecture transcript to latex to give me the key highlights while retaining all the necessary information (in layman terms) so that i can have an all-in-one information in a single document. dont use em-dashes in your response.

convert transcript to latex.

structure:
- \\maketitle for title page
- \\section* (unnumbered) for main sections
- \\section (numbered) for sub-sections
- \\subsection* for sub-sub-sections
- \\begin{{itemize}}[label=$\\bullet$] for bullet lists
- \\begin{{enumerate}}[label=\\arabic*.] for numbered lists
- $...$ inline math for all variables
- \\textbf{{}} for emphasis

color boxes:
- blue!5!white with blue!75!black frame for "Key Takeaway"
- green!5!white with green!75!black frame for "Remember"
- yellow!5!white with yellow!75!black frame for "Crucial Insight"
- gray!10!white with black frame for code/structure outlines

content rules:
- explain everything in layman's terms but keep all technical info
- for each component:
  - definition in simple words with analogy
  - technical definition
  - purpose: why it exists
  - why this specific method chosen
  - advantages in this context
  - disadvantages and failure modes
  - role during training vs inference
  - interaction with other components
- for each code function:
  - show exact signature
  - high-level purpose
  - document every parameter
  - line-by-line breakdown with why each line necessary
  - return value and format
  - when to call it
  - common errors
- preserve all formulas, variables, definitions from transcript
- organize chronologically
- use boxes for definitions, distinctions, summaries
- keep language clear, concise, beginner-friendly


diagram specs:
- use tikz with \\begin{{tikzpicture}}[node distance=1.5cm, auto, font=\\small]
- nodes: rectangles for processes/layers, ellipses for start/end, diamonds for decisions
- arrows: -> for data flow, thick colored arrows for weight updates
- each diagram must have title and legend

output:
- only complete latex code
- wrap in code block like ```latex ... ```
- no extra text outside latex
- do not modify transcript code, only document it
- no em-dashes anywhere

special:
- when transcript says "help me rationalise", add yellow box explaining architectural decision
- for each concept:
  - definition
  - purpose
  - why used here
  - advantages
  - disadvantages
  - implementation details
- include "Common Implementation Errors" section at end
- include "Extensions and Advanced Topics" section

for every transcript mention of "why", add yellow box explaining design choice. for every code snippet, add gray box with code then plain text breakdown. use inline math $z_dim$, $hidden_dim$, $im_dim$, $batch_size$, $lr$, etc. keep transcript code exact.

Content Style:
    Retain all technical information but explain in layman's terms
    Preserve key formulas, variables, and definitions
    Organize chronologically/logically while grouping related concepts
    Use boxes to highlight definitions, important distinctions, and summary points
    Keep language clear, concise, and beginner-friendly

Output: Provide only the complete LaTeX code, in the form of code, not plaintext.

to give you the added information benefit, the lecture slides are VERY laymen, it only provides the information i have to know practically, but does NOT go deeper on why certain types are used instead of another method, help me rationalise why certain methods are used, its advantageous and disadvantageous for every single term mentioned that is used for each architecture. help me provide the key concepts of each architecture, how they are trained, i want to know the definitions of each component of each architecture, their purpose.

TRANSCRIPT:
{{transcript}}
"""

    stream = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_template.replace("{transcript}", transcript_text)}
        ],
        stream=True,
        temperature=0.1,
        extra_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Unified Media Parser",
        } if provider == "OpenRouter" else None
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def generate_podcast_script(transcript_text: str, model_name: str = "qwen3:30b-instruct", provider: str = "Ollama"):
    """
    Generates a podcast-style script from the transcript using the selected provider.
    Yields chunks of generated text for streaming.
    """
    client = get_client(provider)

    system_prompt = """You are an expert podcast scriptwriter and educational communicator. 
    Your goal is to transform lecture transcripts into engaging, easy-to-follow, and highly verbose podcast scripts that cover the material comprehensively from start to finish.
    """

    user_prompt = f"""
You are creating a raw audio script for a Text-to-Speech podcast. Your output will be fed DIRECTLY into a TTS system, so follow these rules exactly:

OUTPUT FORMAT REQUIREMENTS:
- Pure plaintext only - absolutely NO markdown formatting (no asterisks, no hashes, no bullets, no tables, no lists)
- NO speaker labels like "Host:" or "Narrator:"
- NO stage directions or sound effect descriptions like "[pause]" or "(laughs)"
- NO em-dashes (—) - use commas or periods instead
- Just continuous flowing text as if someone is speaking naturally

CONTENT REQUIREMENTS:
- BE EXTREMELY VERBOSE AND THOROUGH - aim for at least 2000-3000 words
- Cover EVERY concept, example, and detail from the start to the absolute end of the transcript
- Do not summarize or condense - expand and elaborate on each point
- Use conversational transitions like "Now, let's dive deeper into...", "Here's what's fascinating...", "Think about it this way..."
- Include analogies and real-world examples to explain technical concepts
- Maintain an engaging, enthusiastic tone like a passionate teacher sharing insights

STYLE GUIDELINES:
- Write as if you're an expert having an intimate one-on-one conversation with a curious learner
- Use natural speech patterns with varied sentence lengths
- Ask rhetorical questions to maintain engagement
- Rephrase complex ideas multiple times using different angles
- Build momentum and excitement around key concepts
- Never rush through material - take your time explaining

Remember: The output must be ONLY the words that will be spoken. No formatting, no labels, no structure markers. Just pure conversational text from beginning to end, in English.

TRANSCRIPT TO CONVERT:
    {transcript_text}
    """

    # We use extra_body to pass Ollama-specific parameters like num_ctx
    stream = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=True,
        extra_body={
            "num_ctx": 32768  # Set context limit to 32k
        } if provider == "Ollama" else None,
        extra_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Unified Media Parser",
        } if provider == "OpenRouter" else None
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def generate_conversational_summary(transcript_text: str, model_name: str = "google/gemini-2.5-flash-lite"):
    """
    Generates an in-depth conversational summary from the transcript using OpenRouter (Gemini 2.5 Flash Lite).
    Returns pure plaintext.
    """
    client = get_client("OpenRouter")

    system_prompt = "You are an expert communicator. Your task is to perform an in-depth summary of the provided transcript content and respond in a conversational manner, in complete plaintext. Do not use em-dashes."

    user_prompt = f"""
Perform an in-depth summary of the transcript content and respond in a conversational manner.
Rules:
- Pure plaintext ONLY.
- No markdown, no bullets, no formatting.
- Be conversational and engaging.
- Cover all key points thoroughly.
- No em-dashes.

TRANSCRIPT:
{transcript_text}
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    content = response.choices[0].message.content
    # Strip any potential markdown code blocks if the model ignores instructions
    if "```" in content:
        content = content.replace("```plaintext", "").replace("```", "").strip()
    
    # Final safety check for em-dashes and formatting
    content = content.replace("—", "-").replace("**", "").replace("__", "")
    return content.strip()

def get_tools():
    """Returns the list of tools available for the LLM."""
    return [
        {
            "type": "function",
            "function": {
                "name": "download_youtube",
                "description": "Download audio from a YouTube URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The YouTube video URL"}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "transcribe_file",
                "description": "Transcribe an audio/video file to text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The absolute path to the media file"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_summary_pdf",
                "description": "Generate a LaTeX summary and compile it to PDF from a transcript file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transcript_path": {"type": "string", "description": "The absolute path to the transcript .txt file"},
                        "model_name": {"type": "string", "description": "Model to use for summary generation", "default": "qwen3:30b-instruct"}
                    },
                    "required": ["transcript_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_quiz_from_latex",
                "description": "Generate an interactive quiz from a LaTeX summary file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latex_path": {"type": "string", "description": "The absolute path to the .tex file"},
                        "num_questions": {"type": "integer", "description": "Number of questions to generate", "default": 10}
                    },
                    "required": ["latex_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List available media or transcript files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "folder_type": {
                            "type": "string", 
                            "enum": ["media", "transcripts", "latex", "quiz"],
                            "description": "Type of files to list"
                        }
                    },
                    "required": ["folder_type"]
                }
            }
        }
    ]

def chat_with_tools(messages, model_name="qwen3:30b-instruct", provider="Ollama"):
    """
    Handles a chat conversation with potential tool calling.
    """
    client = get_client(provider)
    tools = get_tools()

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    return response.choices[0].message
