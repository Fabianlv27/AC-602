from http.client import HTTPException
import json
from groq import AsyncGroq, RateLimitError
from dotenv import load_dotenv
import os
import random

load_dotenv()

# --- 1. GESTIÓN DE MÚLTIPLES CLAVES (ROTACIÓN) ---
# Cargamos todas las claves y limpiamos espacios
keys_string = os.getenv("GROQ_API_KEYS", "")
API_KEYS = [k.strip() for k in keys_string.split(",") if k.strip()]

if not API_KEYS:
    print("❌ ERROR: No se encontraron claves en GROQ_API_KEYS")
    API_KEYS = ["dummy_key"] # Para evitar crash inmediato, fallará luego

async def get_groq_completion(messages, system_instruction, model="llama-3.1-8b-instant"):
    """
    Intenta realizar la petición rotando claves si encuentra un error 429.
    """
    # Intentamos con cada clave disponible
    for i, api_key in enumerate(API_KEYS):
        try:
            # Instanciamos el cliente con la clave actual
            client = AsyncGroq(api_key=api_key)
            
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    # Si messages ya tiene estructura, úsala, si no, adáptalo
                ],
                model=model,
                temperature=0.1,
                response_format={"type": "json_object"}, 
                max_completion_tokens=1500,
            )
            return chat_completion.choices[0].message.content

        except RateLimitError:
            print(f"⚠️ Clave {i+1}/{len(API_KEYS)} agotada (429). Cambiando a la siguiente...")
            continue # Salta a la siguiente clave en el bucle
            
        except Exception as e:
            # Si el error contiene "429" en el mensaje (a veces Groq lo lanza como APIError genérico)
            if "429" in str(e):
                print(f"⚠️ Clave {i+1}/{len(API_KEYS)} agotada (Error genérico 429). Rotando...")
                continue
            
            # Si es otro error, lo lanzamos
            print(f"❌ Error en cliente Groq (Clave {i+1}): {e}")
            raise e
            
    # Si salimos del bucle, es que todas fallaron
    raise Exception("Rate limit reached on ALL available API keys.")

# --- CARGA DE DATOS (Igual que antes) ---
def load_constraints():
    try:
        with open("Data/Etiquetas.json", "r", encoding="utf-8") as f:
            tags_list = json.load(f)
        with open("Data/Niveles.json", "r", encoding="utf-8") as f:
            levels_list = json.load(f)
        with open("Data/Tipos.json", "r", encoding="utf-8") as f: 
            types_list = json.load(f)
        return tags_list, levels_list, types_list
    except FileNotFoundError:
        return [], [], []

# --- EL PROMPT (Igual que antes) ---
def GetPrompt(transcript_text, tags, levels, types):
    tags_str = ", ".join([f'"{t}"' for t in tags]) if tags else "Technology, Business"
    levels_str = ", ".join([f'"{l}"' for l in levels]) if levels else "B1, B2"
    types_str = ", ".join([f'"{t}"' for t in types]) if types else "General"
    
    json_structure = {
        "summary": "Concise summary in 2 lines (ENGLISH).",
        "transcript_summary": "Detailed summary (max 500 chars) (ENGLISH).",
        "level": "One value from list.",
        "topics": ["Tag1", "Tag2", "Tag3"],
        "accents": ["US", "British"],
        "content_types": ["Type1"],
        "wpm_estimate": 150,
        "vocabulary": [{ "term": "Word", "definition": "Short definition in English." }],
        "grammar_stats": { "subjunctive": "Low", "past_tense": "Medium", "future_tense": "Low", "connectors": "High" },
        "functional_use": "E.g.: To learn business negotiation."
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

# --- GENERACIÓN PRINCIPAL ---
async def generate_response(transcript_text) -> dict:
    try:
        tags, levels, types = load_constraints()
        system_instruction = GetPrompt(transcript_text, tags, levels, types)
        
        # LLAMADA CON ROTACIÓN
        try:
            text_resp = await get_groq_completion([], system_instruction)
        except Exception as e:
            return {"error": f"Todas las claves fallaron: {str(e)}"}
        
        try:
            parsed = json.loads(text_resp)
            return parsed
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response"}

    except Exception as e:
        return {"error": f"Error General IA: {str(e)}"}