from http.client import HTTPException
import json
from groq import AsyncGroq, RateLimitError
from dotenv import load_dotenv
import os
import random

load_dotenv()

# --- GESTIÓN DE MÚLTIPLES CLAVES ---
keys_string = os.getenv("GROQ_API_KEYS", "")
API_KEYS = [k.strip() for k in keys_string.split(",") if k.strip()]

if not API_KEYS:
    print("❌ ERROR: No se encontraron claves en GROQ_API_KEYS")
    API_KEYS = ["dummy_key"]

async def get_groq_completion(messages, system_instruction, model="llama-3.1-8b-instant"):
    for i, api_key in enumerate(API_KEYS):
        try:
            client = AsyncGroq(api_key=api_key)
            chat_completion = await client.chat.completions.create(
                messages=[{"role": "system", "content": system_instruction}],
                model=model,
                temperature=0.1,
                response_format={"type": "json_object"}, 
                max_completion_tokens=1500,
            )
            return chat_completion.choices[0].message.content
        except RateLimitError:
            print(f"⚠️ Clave {i+1} agotada (429). Rotando...")
            continue
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Clave {i+1} agotada (Error 429). Rotando...")
                continue
            print(f"❌ Error en cliente Groq (Clave {i+1}): {e}")
            raise e
    raise Exception("Rate limit reached on ALL keys.")

def load_constraints():
    try:
        with open("Data/Etiquetas.json", "r", encoding="utf-8") as f: tags = json.load(f)
        with open("Data/Niveles.json", "r", encoding="utf-8") as f: levels = json.load(f)
        with open("Data/Tipos.json", "r", encoding="utf-8") as f: types = json.load(f)
        return tags, levels, types
    except: return [], [], []

def GetPrompt(transcript_text, tags, levels, types):
    tags_str = ", ".join([f'"{t}"' for t in tags]) if tags else "Technology, Business"
    levels_str = ", ".join([f'"{l}"' for l in levels]) if levels else "B1, B2"
    types_str = ", ".join([f'"{t}"' for t in types]) if types else "General"
    
    # --- JSON ESTRUCTURA SIMPLIFICADA (SIN summary NI functional_use) ---
    json_structure = {
        "transcript_summary": "Detailed summary (max 500 chars) (ENGLISH).",
        "level": "One value from list.",
        "topics": ["Tag1", "Tag2", "Tag3"],
        "accents": ["US", "British"],
        "content_types": ["Type1"],
        "wpm_estimate": 150,
        "vocabulary": [{ "term": "Word", "definition": "Short definition in English." }],
        "grammar_stats": { "subjunctive": "Low", "past_tense": "Medium", "future_tense": "Low", "connectors": "High" }
    }

    prompt = f"""
    Role: Expert English linguist.
    Task: Extract metadata. ALL OUTPUT MUST BE IN ENGLISH.
    
    CONSTRAINTS:
    1. LEVEL: [{levels_str}]
    2. TOPICS: Choose 3 from [{tags_str}]
    3. CONTENT_TYPES: Choose from [{types_str}]
    4. ACCENTS: Infer list based on context.

    OUTPUT JSON STRUCTURE:
    {json.dumps(json_structure)}
    
    TRANSCRIPT:
    "{transcript_text[:6000]}" 
    """
    return prompt

async def generate_response(transcript_text) -> dict:
    try:
        tags, levels, types = load_constraints()
        system_instruction = GetPrompt(transcript_text, tags, levels, types)
        
        try:
            text_resp = await get_groq_completion([], system_instruction)
        except Exception as e:
            return {"error": f"Todas las claves fallaron: {str(e)}"}
        
        try:
            return json.loads(text_resp)
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response"}

    except Exception as e:
        return {"error": f"Error General IA: {str(e)}"}