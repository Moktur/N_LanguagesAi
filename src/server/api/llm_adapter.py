import os
from dotenv import load_dotenv
import json
from google.genai import types


load_dotenv()  # Lädt .env Datei

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
        You are a strict but fair language teacher evaluating translations.
        The source sentence is: "{to_translate}"

        The user provided translations (dictionary JSON format):
        {user_translations}

        Scoring rules: 
        100 points: Perfect translation, correct grammar, meaning, and nuance. 
        80-99 points: Small mistakes, but overall correct and understandable. 
        60-79 points: Some errors, but the main meaning is preserved. 
        40-59 points: Significant errors, but partially correct. 
        20-39 points: Mostly incorrect, meaning hard to understand. 
        0-19 points: Completely wrong, nonsense, or unrelated.
        Important:
        - Minor grammar or word choice issues should still score 70 or above if the meaning is correct.
        - If the translation captures the main meaning, it should never score below 60.
        - Only give very low scores (<40) if the translation is nonsense or completely unrelated.
        Give a score for every translation, add these scores together and divide through the number of translations.
        Return then ONLY this number as single integer between 1 and 100.
        """

        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()

        elif self.provider == "gemini":
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
                    ),
                )
            if response.candidates and response.candidates[0].content.parts:
                raw = response.candidates[0].content.parts[0].text.strip()



        elif self.provider == "local":
            output = self.client(prompt, max_tokens=10)
            raw = output["choices"][0]["text"].strip()

        elif self.provider == "mock":
            raw = "13"  # Simulierter Wert


        # security for getting int as return
        try:
            score = int(raw)
            return max(0, min(100, score))
        except ValueError:
            try:
                # Falls es z. B. "0.8" zurückgibt → in Prozent umrechnen
                score = float(raw) * 100
                return max(0, min(100, int(score)))
            except:
                return 0


# TODO Test entfernen
ladapter = LLMAdapter()
trans = {"translations": [
    {"it": "Vado stadio a vedere una partita di calcio"}, # allo
    {"en": "I'm going to the stadium to watch a football"}]} # match
print(ladapter.score_answer("ich fahre zum stadion fußball schauen ", trans))
