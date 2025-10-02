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

    def score_answer(
    self, 
    to_translate: str, 
    translations: dict, 
    native_language: str = None
        ) -> dict:
        """
        Bewertet Übersetzungen und gibt structured output zurück.

        Parameters
        ----------
        to_translate : str
            Der Originalsatz.
        translations : dict
            User-Übersetzungen im Format:
            {"translations": [{"en": "..."}, {"it": "..."}]}
        native_language : str, optional
            Muttersprache des Users.

        Returns
        -------
        dict
            {
            "overall_score": int,
            "evaluations": {
                "en": {
                    "score": int,
                    "correct_translation": str,
                    "explanation": str
                },
                "it": {
                    "score": int,
                    "correct_translation": str,
                    "explanation": str
                }
            }
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

        Source sentence: "{to_translate}"
        User's native language: "{native_language}"

        User provided translations (JSON format):
        {user_translations}

        For each translation:
        - Give a score between 0 and 100
        - Provide the correct (ideal) translation
        - Give a short explanation why you scored it this way

        Scoring rules:
        - 100 points: Perfect translation, correct grammar, meaning, and nuance.
        - 80-99 points: Small mistakes, but overall correct and understandable.
        - 60-79 points: Some errors, but the main meaning is preserved.
        - 40-59 points: Significant errors, but partially correct.
        - 20-39 points: Mostly incorrect, meaning hard to understand.
        - 0-19 points: Completely wrong, nonsense, or unrelated.

        Return your response strictly as valid JSON in the following format
        and in the users native language:

        {{
        "overall_score": <int>,
        "evaluations": {{
            "<language_code>": {{
            "score": <int>,
            "correct_translation": "<string>",
            "explanation": "<string>"
            }},
            ...
        }}
        }}
        """

        raw = None
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}  # Structured output erzwingen
            )
            raw = response.choices[0].message.content.strip()

        elif self.provider == "gemini":
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                ),
            )
            if response.candidates and response.candidates[0].content.parts:
                raw = response.candidates[0].content.parts[0].text.strip()

        elif self.provider == "local":
            output = self.client(prompt, max_tokens=500)
            raw = output["choices"][0]["text"].strip()

        elif self.provider == "mock":
            raw = json.dumps({
                "overall_score": 75,
                "evaluations": {
                    "en": {
                        "score": 80,
                        "correct_translation": "I am going to work",
                        "explanation": "Minor grammar mistake, but understandable"
                    },
                    "it": {
                        "score": 70,
                        "correct_translation": "Vado al lavoro",
                        "explanation": "Article usage is slightly off, but meaning preserved"
                    }
                }
            })

        try:
            result = json.loads(raw)
            # Sicherheit: Clampen der Scores
            result["overall_score"] = max(0, min(100, int(result.get("overall_score", 0))))
            for lang, eval_data in result.get("evaluations", {}).items():
                eval_data["score"] = max(0, min(100, int(eval_data.get("score", 0))))
            return result
        except Exception as e:
            print(f"Parsing error: {e}, raw={raw}")
            return {"overall_score": 0, "evaluations": {}}



# --- Test ---
if __name__ == "__main__":
    ladapter = LLMAdapter()
    trans = {"translations": [{"de": "ich fahre zur Arbeit"}, {"en": "I go to work"}]}
    result = ladapter.score_answer("vado al lavoro", trans, native_language="it")
    print(json.dumps(result, indent=2, ensure_ascii=False))
