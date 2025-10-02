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

    def score_answer(self, to_translate: str, translations: dict, native_language: str = "en") -> dict:
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
        - Provide a short explanation (max 2 sentences) written in the user's native language: {native_language}.

        Return JSON strictly in this format:
        {{
          "results": [
            {{
              "language": "<lang_code>",
              "score": <int>,
              "corrected": "<corrected sentence>",
              "explanation": "<short explanation in {native_language}>"
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
                        "explanation": f"(Mock) Explanation in {native_language}"
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
    result = ladapter.score_answer("ich fahre zur Arbeit", trans, native_language="de")
    print(json.dumps(result, indent=2, ensure_ascii=False))
