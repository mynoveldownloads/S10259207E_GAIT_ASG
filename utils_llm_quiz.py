from openai import OpenAI
import json
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

def generate_quiz(latex_content: str, model_name: str = "qwen3:30b-instruct", num_questions: int = 10, provider: str = "Ollama"):
    """
    Generates quiz questions and answers from LaTeX content in JSON format.
    Returns the complete JSON string (non-streaming for reliable JSON parsing).
    """
    client = get_client(provider)

    system_prompt = """You are an expert educational assessment creator. You generate high-quality quiz questions in valid JSON format."""

    user_prompt = f"""
    Based on the following LaTeX educational content, generate {num_questions} multiple-choice quiz questions.

    CRITICAL: Your response must be ONLY valid JSON, nothing else. No markdown, no explanations, just pure JSON.

    Requirements:
    1. Each question must have:
       - A clear, specific question
       - Exactly 4 options (A, B, C, D)
       - One correct answer (letter only: A, B, C, or D)
       - A detailed explanation of why the answer is correct
    
    2. Question quality:
       - Test UNDERSTANDING, not just memorization
       - Include questions at different difficulty levels
       - Focus on key concepts, definitions, and applications
       - Include "why" and "how" questions, not just "what"
    
    3. Coverage:
       - Ensure questions cover different topics from the material
       - Include both foundational and advanced concepts
    
    4. JSON Structure (EXACT FORMAT):
    {{
        "quiz_title": "Quiz on [Topic Name]",
        "total_questions": {num_questions},
        "questions": [
            {{
                "id": 1,
                "question": "What is the main purpose of X?",
                "options": {{
                    "A": "First option text",
                    "B": "Second option text",
                    "C": "Third option text",
                    "D": "Fourth option text"
                }},
                "correct_answer": "B",
                "explanation": "Detailed explanation of why B is correct and why others are wrong.",
                "difficulty": "easy"
            }},
            {{
                "id": 2,
                "question": "How does Y work?",
                "options": {{
                    "A": "First option",
                    "B": "Second option",
                    "C": "Third option",
                    "D": "Fourth option"
                }},
                "correct_answer": "C",
                "explanation": "Detailed explanation here.",
                "difficulty": "medium"
            }}
        ]
    }}

    LATEX CONTENT:
    {latex_content[:4000]}

    Remember: Output ONLY valid JSON. No markdown code blocks, no extra text, just the JSON object.
    """

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=False,  # Non-streaming for reliable JSON
        extra_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Unified Media Parser",
        } if provider == "OpenRouter" else None
    )

    json_response = response.choices[0].message.content.strip()
    
    # Clean up any markdown code blocks if present
    if json_response.startswith("```json"):
        json_response = json_response.replace("```json", "").replace("```", "").strip()
    elif json_response.startswith("```"):
        json_response = json_response.replace("```", "").strip()
    
    return json_response
