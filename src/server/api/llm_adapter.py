import os
from dotenv import load_dotenv
import json

load_dotenv()  # Lädt .env Datei

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

class LLMAdapter:
    def __init__(self):
        if LLM_PROVIDER == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.provider = "openai"

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

    def score_answer(self, to_translate: str, translations: dict) -> int:
        normalized_translations = {
            language_code : translation
            for translation_dict in translations["translations"]
            for language_code, translation in translation_dict.items()
        }
        
        

        user_translations = json.dumps(normalized_translations)
        """
        Gibt Score zwischen 0 (sehr falsch) und 100 (perfekt) zurück
        """
        prompt = f"""
        Compare these translations:
        to translate: "{to_translate}"
        User Translations: "{user_translations}"
        Return only a number between 0 and 100.
        """

        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()

        elif self.provider == "local":
            output = self.client(prompt, max_tokens=10)
            raw = output["choices"][0]["text"].strip()
        
        elif self.provider == "mock":
            # Mock scoring for development
            raw = "0.8"

        try:
            score = int(raw)
            return max(0, min(100, score))
        except:
            return 0.0


# TODO Test entfernen
ladapter = LLMAdapter()
trans = {"translations": [{"it": "vado al lavoro"}, {"en": "fuck"}]}
print(ladapter.score_answer("ich fahre zur Arbeit", trans))
