# import os
# from dotenv import load_dotenv
# import json
# from google.genai import types


# load_dotenv()  # Lädt .env Datei

# LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# class LLMAdapter:
#     def __init__(self):
#         if LLM_PROVIDER == "openai":
#             from openai import OpenAI
#             self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#             self.provider = "openai"

#         elif LLM_PROVIDER == "gemini":
#             from google import genai
#             self.client = genai.Client()
#             self.provider = "gemini"
        

#         elif LLM_PROVIDER == "local":
#             try:
#                 from llama_cpp import Llama
#                 model_path = os.getenv("MODEL_PATH", "./models/llama-2-7b.Q4_K_M.gguf")
#                 self.client = Llama(model_path=model_path)
#                 self.provider = "local"
#             except ImportError:
#                 print("Warning: llama-cpp-python not installed. Using mock local provider.")
#                 self.client = None
#                 self.provider = "mock"

#         else:
#             raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


#     def score_answer(self, to_translate: str, translations: dict) -> int:
#         normalized_translations = {
#             language_code : translation
#             for translation_dict in translations["translations"]
#             for language_code, translation in translation_dict.items()
#         }

#         user_translations = json.dumps(normalized_translations)
#         """
#         Gibt Score zwischen 0 (sehr falsch) und 100 (perfekt) zurück
#         """
#         prompt = f"""
#         You are a strict but fair language teacher evaluating translations.
#         The source sentence is: "{to_translate}"

#         The user provided translations (dictionary JSON format):
#         {user_translations}

#         Scoring rules: 
#         100 points: Perfect translation, correct grammar, meaning, and nuance. 
#         80-99 points: Small mistakes, but overall correct and understandable. 
#         60-79 points: Some errors, but the main meaning is preserved. 
#         40-59 points: Significant errors, but partially correct. 
#         20-39 points: Mostly incorrect, meaning hard to understand. 
#         0-19 points: Completely wrong, nonsense, or unrelated.
#         Important:
#         - Minor grammar or word choice issues should still score 70 or above if the meaning is correct.
#         - If the translation captures the main meaning, it should never score below 60.
#         - Only give very low scores (<40) if the translation is nonsense or completely unrelated.
#         Give a score for every translation, add these scores together and divide through the number of translations.
#         Return then ONLY this number as single integer between 1 and 100.
#         """

#         if self.provider == "openai":
#             response = self.client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[{"role": "user", "content": prompt}]
#             )
#             raw = response.choices[0].message.content.strip()

#         elif self.provider == "gemini":
#             response = self.client.models.generate_content(
#                 model="gemini-2.5-flash",
#                 contents=prompt,
#                 config=types.GenerateContentConfig(
#                 thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
#                     ),
#                 )
#             if response.candidates and response.candidates[0].content.parts:
#                 raw = response.candidates[0].content.parts[0].text.strip()



#         elif self.provider == "local":
#             output = self.client(prompt, max_tokens=10)
#             raw = output["choices"][0]["text"].strip()

#         elif self.provider == "mock":
#             raw = "13"  # Simulierter Wert


#         # security for getting int as return
#         try:
#             score = int(raw)
#             return max(0, min(100, score))
#         except ValueError:
#             try:
#                 # Falls es z. B. "0.8" zurückgibt → in Prozent umrechnen
#                 score = float(raw) * 100
#                 return max(0, min(100, int(score)))
#             except:
#                 return 0


# # TODO Test entfernen
# ladapter = LLMAdapter()
# trans = {"translations": [
#     {"it": "Vado allo stadio a vedere una partita di calcio"}, # allo
#     {"en": "I'm going to the stadium to watch a football match"}]} # match
# print(ladapter.score_answer("ich fahre zum stadion um fußball zu schauen ", trans))
import os
import json
from dotenv import load_dotenv

from google.genai import types

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")


class LLMAdapter:
    def __init__(self):
        if LLM_PROVIDER == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.provider = "openai"

        elif LLM_PROVIDER == "gemini":
            from google import genai
            self.client = genai.Client()
            self.provider = "gemini"

        elif LLM_PROVIDER == "local":
            try:
                from llama_cpp import Llama
                model_path = os.getenv("MODEL_PATH", "./models/llama-2-7b.Q4_K_M.gguf")
                self.client = Llama(model_path=model_path)
                self.provider = "local"
            except ImportError:
                print("Warning: llama-cpp-python not installed. Using mock local provider.")
                self.client = None
                self.provider = "mock"

        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

    def score_answer(self, to_translate: str, translations: dict) -> dict:
        """
        Bewertet Übersetzungen in mehreren Sprachen.
        Gibt ein Dict zurück:
        {
            "results": [
                {
                    "language": "en",
                    "score": 75,
                    "corrected": "...",
                    "explanation": "..."
                },
                ...
            ],
            "overall_score": 85
        }
        """
        normalized_translations = {
            language_code: translation
            for translation_dict in translations["translations"]
            for language_code, translation in translation_dict.items()
        }

        user_translations = json.dumps(normalized_translations, ensure_ascii=False)

        prompt = f"""
        You are a strict but fair language teacher evaluating translations.
        The source sentence is: "{to_translate}"

        The user provided translations (JSON dict):
        {user_translations}

        For each language:
        - Give a score between 0 (very wrong) and 100 (perfect).
        - Suggest the corrected ideal translation in that language.
        - Provide a short explanation (max 2 sentences).

        Return JSON strictly in this format:
        {{
          "results": [
            {{
              "language": "<lang_code>",
              "score": <int>,
              "corrected": "<corrected sentence>",
              "explanation": "<short explanation>"
            }},
            ...
          ],
          "overall_score": <int>
        }}
        """

        raw = None

        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "translation_evaluation",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "results": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "language": {"type": "string"},
                                            "score": {"type": "integer"},
                                            "corrected": {"type": "string"},
                                            "explanation": {"type": "string"}
                                        },
                                        "required": ["language", "score", "corrected", "explanation"]
                                    }
                                },
                                "overall_score": {"type": "integer"}
                            },
                            "required": ["results", "overall_score"]
                        }
                    }
                }
            )
            raw = response.choices[0].message.content

        elif self.provider == "gemini":
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "results": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "language": {"type": "string"},
                                        "score": {"type": "integer"},
                                        "corrected": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    },
                                    "required": ["language", "score", "corrected", "explanation"]
                                }
                            },
                            "overall_score": {"type": "integer"}
                        },
                        "required": ["results", "overall_score"]
                    }
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                raw = response.candidates[0].content.parts[0].text

        elif self.provider == "local":
            output = self.client(prompt, max_tokens=500)
            raw = output["choices"][0]["text"]

        elif self.provider == "mock":
            return {
                "results": [
                    {
                        "language": "en",
                        "score": 50,
                        "corrected": "I'm going to work",
                        "explanation": "Missing verb 'go'."
                    }
                ],
                "overall_score": 50
            }

        # Parsing JSON
        try:
            return json.loads(raw)
        except Exception:
            return {
                "results": [],
                "overall_score": 0,
                "error": f"Could not parse model output: {raw}"
            }


# --- Test ---
if __name__ == "__main__":
    ladapter = LLMAdapter()
    trans = {"translations": [{"it": "vado al lavoro"}, {"en": "I go to work"}]}
    result = ladapter.score_answer("ich fahre zur Arbeit", trans)
    print(json.dumps(result, indent=2, ensure_ascii=False))
