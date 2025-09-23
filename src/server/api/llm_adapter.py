import os
from dotenv import load_dotenv

load_dotenv()  # Lädt .env Datei

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")

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

    def score_answer(self, user_answer: str, correct_answer: str) -> float:
        """
        Gibt Score zwischen 0.0 (falsch) und 1.0 (perfekt) zurück
        """
        prompt = f"""
        Compare these translations:
        Correct: "{correct_answer}"
        User: "{user_answer}"
        Return only a number between 0 and 1.
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
            score = float(raw)
            return max(0.0, min(1.0, score))
        except:
            return 0.0
