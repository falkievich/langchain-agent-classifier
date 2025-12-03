import os
import requests
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM

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
        Envia el prompt al modelo Open WebUI o Ollama y devuelve la respuesta como string.
        """
        # Prints esenciales de debugging
        print(f"\n DEBUG LLM: Base URL: {self.base_url}")
        print(f" DEBUG LLM: Usando modelo '{self.model}'")
        print(f" DEBUG LLM: Prompt length: {len(prompt)} chars")
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Solo agregar Authorization si la API key no es "ollama" (conexión directa a Ollama)
        if self.api_key and self.api_key.lower() != "ollama":
            headers["Authorization"] = f"Bearer {self.api_key}"


        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un asistente experto en expedientes judiciales."},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
            
            print(f" DEBUG LLM: Status code: {resp.status_code}")
            print(f" DEBUG LLM: Response length: {len(resp.text)} chars\n")
            
            resp.raise_for_status()

            data = resp.json()
            text = data["choices"][0]["message"]["content"]

            # Respeta stop sequences si las hay
            if stop:
                for s in stop:
                    if s in text:
                        text = text.split(s)[0]

            return text.strip()
        except requests.exceptions.RequestException as e:
            print(f" ERROR LLM: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f" Response body: {e.response.text}")
            raise

    @property
    def _identifying_params(self) -> dict:
        """Parámetros para logging/debug."""
        return {"model": self.model, "base_url": self.base_url}
