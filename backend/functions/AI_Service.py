from http.client import HTTPException
import json
from groq import AsyncGroq
from dotenv import load_dotenv

import os
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=api_key)

# --- 1. CARGA DE DATOS (Corregido) ---
def load_constraints():
    # Asegúrate de que las rutas y nombres de archivo sean correctos
    try:
        with open("Data/Etiquetas.json", "r", encoding="utf-8") as f:
            tags_list = json.load(f)
        
        with open("Data/Niveles.json", "r", encoding="utf-8") as f:
            levels_list = json.load(f)

        with open("Data/Tipos.json", "r", encoding="utf-8") as f: 
            types_list = json.load(f)
            
        return tags_list, levels_list, types_list
    except FileNotFoundError as e:
        print(f"Error cargando JSONs de configuración: {e}")
        return [], [], [] # Retorno seguro para no romper, pero deberías revisar los archivos

# --- 2. EL PROMPT "ANTI-ALUCINACIONES" ---
def GetPrompt(transcript_text):
    tags, levels, types = load_constraints()
    
    tags_str = ", ".join([f'"{t}"' for t in tags])
    levels_str = ", ".join([f'"{l}"' for l in levels])
    types_str = ", ".join([f'"{t}"' for t in types])
   
    example_json = {
        "level": "B1",
        "topics": [tags[0] if tags else "Technology", tags[1] if len(tags)>1 else "Business", tags[2] if len(tags)>2 else "Life"],
        "accent": "US",
        "type": types[0] if types else "Informal"
    }
    
    prompt = f"""
    Role: You are an expert linguist and video classifier for English learners.
    
    Task: Analyze the provided transcript snippet and extract metadata strictly following the constraints below.
    
    CONSTRAINTS (You MUST chose values ONLY from these lists):
    1. LEVEL: {levels_str}
    2. TOPICS: Choose exactly 3 tags from: [{tags_str}]
    3. ACCENT: Choose one from ["US", "UK", "AUS"] based on spelling (color/colour) and vocabulary.
    4. TYPE: Choose one from: [{types_str}]
    
    OUTPUT FORMAT:
    Return ONLY a raw JSON object. Do not include markdown formatting like ```json ... ```.
    
    EXAMPLE INPUT:
    "Hello guys, today we are gonna grab some coffee and chat about..."
    
    EXAMPLE OUTPUT:
    {json.dumps(example_json)}
    
    REAL TRANSCRIPT TO ANALYZE:
    "{transcript_text[:3500]}..." 
    """
    return prompt

# --- 3. GENERACIÓN Y LIMPIEZA ---
async def generate_response(transcript_text) -> dict:
    try:
        system_instruction = GetPrompt(transcript_text)
        
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_instruction
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}, 
            max_completion_tokens=512,
        )
        
        text_resp = chat_completion.choices[0].message.content
        
        try:
            parsed = json.loads(text_resp)
            print(parsed)
            final_result = {
                "level": parsed.get("level", "Unrated"),
                "topics": parsed.get("topics", []),
                "accent": parsed.get("accent", "Mixed"),
                "type": parsed.get("type", "General")
            }
            
            return final_result
            
        except json.JSONDecodeError:
            print(f"❌ Error parseando JSON de la IA: {text_resp}")
            return {"error": "Failed to parse AI response", "raw": text_resp}

    except Exception as e:
        print(f"❌ Error crítico en GeminiService: {e}")
        raise HTTPException(status_code=503, detail=f"Error IA: {str(e)}")
    