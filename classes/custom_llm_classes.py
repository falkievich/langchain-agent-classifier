import os
import requests
from typing import List, Optional

from dotenv import load_dotenv
from langchain.llms.base import LLM

# Cargar variables de entorno
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_ID = os.getenv("MODEL_ID")


class CustomOpenWebLLM(LLM):
    """LLM personalizado para conectarse a la API de Open WebUI"""

    base_url: str = BASE_URL
    api_key: str = API_KEY
    model: str = MODEL_ID

    # --- Método obligatorio de LangChain ---
    @property
    def _llm_type(self) -> str:
        return "custom-openweb-llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """
        Envia el prompt al modelo Open WebUI y devuelve la respuesta como string.
        """
        # Prints esenciales de debugging
        print(f"\n🔍 DEBUG LLM: Usando modelo '{self.model}'")
        print(f"🔍 DEBUG LLM: Prompt length: {len(prompt)} chars")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un asistente experto en expedientes judiciales."},
                {"role": "user", "content": prompt},
            ],
        }

        print(f"🔍 DEBUG LLM: Messages count: {len(payload['messages'])}")

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
        
        print(f"🔍 DEBUG LLM: Status code: {resp.status_code}")
        print(f"🔍 DEBUG LLM: Response length: {len(resp.text)} chars\n")
        
        resp.raise_for_status()

        data = resp.json()
        text = data["choices"][0]["message"]["content"]

        # Respeta stop sequences si las hay
        if stop:
            for s in stop:
                if s in text:
                    text = text.split(s)[0]

        return text.strip()

    @property
    def _identifying_params(self) -> dict:
        """Parámetros para logging/debug."""
        return {"model": self.model, "base_url": self.base_url}
