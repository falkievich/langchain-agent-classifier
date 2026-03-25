"""
classes/custom_llm_classes.py
──────────────────────────────
Clases LLM personalizadas.

  · CustomOpenWebLLM  → cliente HTTP genérico (Open WebUI / Ollama) — mantenido por compatibilidad
  · OpenAILLM         → cliente oficial de OpenAI con:
        - Caché del system prompt (cached_content vía prompt caching de OpenAI)
        - Conteo de tokens y requests con prints detallados
        - Modelo configurable desde .env con variable OPENAI_MODEL
        - Parámetros de eficiencia (temperatura baja, max_tokens limitado)
"""

import os
import requests
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM

# ── Intentar importar openai y tiktoken ────────────────────────
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    print("[custom_llm_classes] ⚠ 'openai' no está instalado. Ejecuta: pip install openai tiktoken")

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False

# Cargar variables de entorno
load_dotenv()

BASE_URL  = os.getenv("BASE_URL")
API_KEY   = os.getenv("API_KEY")
MODEL_ID  = os.getenv("MODEL_ID")

# ── Variables OpenAI ────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# ▼▼▼  CAMBIA EL MODELO AQUÍ (o en el .env con OPENAI_MODEL)  ▼▼▼
# Opciones: gpt-4.1-nano | gpt-4.1-mini | gpt-4o-mini | gpt-4o | gpt-4.1 | o4-mini
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
# ▲▲▲────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════
#  Contador global de uso (requests + tokens)
# ═══════════════════════════════════════════════════════════════

class _UsageTracker:
    """
    Acumula estadísticas de uso de la API de OpenAI a lo largo de la sesión.

    Precios de referencia gpt-4.1-nano (por 1 000 tokens, USD):
      · Input normal   : $0.000100  (0.1 $/1k)
      · Input cacheado : $0.000025  (0.025 $/1k)  ← ~75 % más barato
      · Output         : $0.000400  (0.4 $/1k)
    """

    # ── Precios por 1 000 tokens (ajustá si cambias de modelo) ──
    PRICE_INPUT_PER_1K        = 0.000100   # USD / 1k tokens — input normal
    PRICE_INPUT_CACHED_PER_1K = 0.000025   # USD / 1k tokens — input cacheado
    PRICE_OUTPUT_PER_1K       = 0.000400   # USD / 1k tokens — output

    def __init__(self):
        self.total_requests: int = 0
        self.total_input_tokens: int = 0        # todos los input (incluye cacheados)
        self.total_cached_tokens: int = 0       # subconjunto de input servido desde caché
        self.total_output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def _cost(self, input_tokens: int, output_tokens: int, cached_tokens: int) -> float:
        """Calcula costo estimado en USD para una llamada."""
        normal_input = input_tokens - cached_tokens
        return (
            normal_input   / 1000 * self.PRICE_INPUT_PER_1K
            + cached_tokens / 1000 * self.PRICE_INPUT_CACHED_PER_1K
            + output_tokens / 1000 * self.PRICE_OUTPUT_PER_1K
        )

    def record(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0):
        self.total_requests += 1
        self.total_input_tokens  += input_tokens
        self.total_cached_tokens += cached_tokens
        self.total_output_tokens += output_tokens

    def print_last(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0):
        """Print detallado de la última llamada + acumulado de sesión."""
        normal_input = input_tokens - cached_tokens
        call_cost    = self._cost(input_tokens, output_tokens, cached_tokens)
        session_cost = self._cost(self.total_input_tokens, self.total_output_tokens, self.total_cached_tokens)

        cache_pct = f"{cached_tokens / input_tokens * 100:.0f}%" if input_tokens > 0 else "0%"

        print(
            f"\n{'─'*64}\n"
            f"  📤 OpenAI  |  request #{self.total_requests}\n"
            f"  │\n"
            f"  ├─ INPUT  tokens      : {input_tokens:>7,}\n"
            f"  │    ├─ normal        : {normal_input:>7,}   → ~${normal_input  / 1000 * self.PRICE_INPUT_PER_1K:.6f}\n"
            f"  │    └─ cacheados     : {cached_tokens:>7,}   → ~${cached_tokens / 1000 * self.PRICE_INPUT_CACHED_PER_1K:.6f}  ({cache_pct} del input)\n"
            f"  ├─ OUTPUT tokens      : {output_tokens:>7,}   → ~${output_tokens / 1000 * self.PRICE_OUTPUT_PER_1K:.6f}\n"
            f"  ├─ COSTO esta llamada : ~${call_cost:.6f} USD\n"
            f"  │\n"
            f"  └─ SESIÓN ACUMULADA\n"
            f"       input  : {self.total_input_tokens:>7,}  (cacheados: {self.total_cached_tokens:,})\n"
            f"       output : {self.total_output_tokens:>7,}\n"
            f"       total  : {self.total_tokens:>7,} tokens  en {self.total_requests} request(s)\n"
            f"       costo  : ~${session_cost:.6f} USD\n"
            f"{'─'*64}\n"
        )

USAGE = _UsageTracker()


# ═══════════════════════════════════════════════════════════════
#  Helper: contar tokens localmente con tiktoken
# ═══════════════════════════════════════════════════════════════

def _count_tokens_local(text: str, model: str) -> int:
    """
    Estima tokens localmente con tiktoken.
    Devuelve -1 si tiktoken no está disponible o si falla la descarga del
    vocabulario (p. ej. por SSL corporativo / proxy sin acceso a internet).
    """
    if not _TIKTOKEN_AVAILABLE:
        return -1
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return -1
    except Exception:
        # Captura SSLError u otros fallos de red al descargar el vocabulario
        return -1
    try:
        return len(enc.encode(text))
    except Exception:
        return -1


# ═══════════════════════════════════════════════════════════════
#  OpenAILLM
# ═══════════════════════════════════════════════════════════════

class OpenAILLM(LLM):
    """
    LLM que usa la API oficial de OpenAI.

    Características:
      · Prompt caching automático (OpenAI cachea el prefijo del system prompt
        cuando supera ~1 024 tokens; los tokens cacheados cuestan ~50 %).
      · Temperatura baja (0.0) para respuestas deterministas y coherentes.
      · max_tokens limitado para reducir consumo.
      · Print detallado de tokens por llamada y acumulado de sesión.
      · Modelo configurable desde .env → OPENAI_MODEL.
    """

    model: str = OPENAI_MODEL
    temperature: float = 0.0       # 0 = más determinista, menos "creatividad" innecesaria
    max_tokens: int = 512          # limitar respuesta a lo estrictamente necesario
    system_prompt: str = ""        # se setea externamente antes de _call

    @property
    def _llm_type(self) -> str:
        return "openai-llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """
        Llama a la API de OpenAI.
        Si self.system_prompt está seteado se envía como rol 'system' para aprovechar
        el prompt caching de OpenAI (el prefijo del system se cachea automáticamente).
        """
        if not _OPENAI_AVAILABLE:
            raise RuntimeError(
                "El paquete 'openai' no está instalado. Ejecuta: pip install openai tiktoken"
            )

        client = OpenAI(api_key=OPENAI_API_KEY)

        # ── Construir mensajes ──────────────────────────────────
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})

        # ── Estimación local previa (opcional, informativa) ─────
        full_text = (self.system_prompt or "") + prompt
        local_estimate = _count_tokens_local(full_text, self.model)
        if local_estimate > 0:
            print(f"  [OpenAI] estimación local de tokens de entrada: ~{local_estimate:,}")
        else:
            print(f"  [OpenAI] estimación local de tokens no disponible (tiktoken sin acceso a internet)")

        # ── Llamada a la API ────────────────────────────────────
        # store=True → OpenAI guarda el prefijo del system prompt en su caché
        # y lo reutiliza en llamadas posteriores con el mismo system prompt + modelo.
        # El ahorro se refleja en cached_tokens (precio ~75 % más barato que input normal).
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            store=True,
        )

        # ── Métricas de uso ─────────────────────────────────────
        usage         = response.usage
        input_tokens  = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        # cached_tokens: subconjunto del input servido desde caché de OpenAI
        cached_tokens = 0
        if hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
            cached_tokens = getattr(usage.prompt_tokens_details, "cached_tokens", 0) or 0

        USAGE.record(input_tokens, output_tokens, cached_tokens)
        USAGE.print_last(input_tokens, output_tokens, cached_tokens)

        text = response.choices[0].message.content or ""

        # ── Stop sequences ──────────────────────────────────────
        if stop:
            for s in stop:
                if s in text:
                    text = text.split(s)[0]

        return text.strip()

    @property
    def _identifying_params(self) -> dict:
        return {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens}


# ═══════════════════════════════════════════════════════════════
#  CustomOpenWebLLM  (mantenido por compatibilidad)
# ═══════════════════════════════════════════════════════════════

class CustomOpenWebLLM(LLM):
    """LLM genérico para conectarse a Open WebUI o Ollama (HTTP directo)."""

    base_url: str = BASE_URL or ""
    api_key: str = API_KEY or ""
    model: str = MODEL_ID or ""

    @property
    def _llm_type(self) -> str:
        return "custom-openweb-llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key.lower() != "ollama":
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un asistente experto en expedientes judiciales."},
                {"role": "user", "content": prompt},
            ],
        }

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]

        if stop:
            for s in stop:
                if s in text:
                    text = text.split(s)[0]

        return text.strip()

    @property
    def _identifying_params(self) -> dict:
        return {"model": self.model, "base_url": self.base_url}
