import json
import asyncio
from typing import List, Dict, Any, Tuple
from google import genai
from app.core.config import settings


class GeminiService:
    PROMPT_VERSION = "3.1.0"

    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model_priority = [
            "gemini-2.5-flash",  # 1ª Opção: Melhor custo-benefício atual
            "gemini-2.5-flash-lite",  # 2ª Opção: Mais rápido/barato se o principal falhar
            "gemini-2.0-flash",  # 3ª Opção: Versão anterior estável
            "gemini-2.5-pro",  # 4ª Opção: "Tanque de guerra" (mais lento/caro, mas resolve tudo)
        ]

    async def enrich_anomalies_table(
        self, hits: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Recebe a lista de anomalias e preenche explicacao e recomendacao.
        """
        if not self.client or not hits:
            return hits, {
                "status": "skipped",
                "error": "AI client not initialized or no hits",
            }

        system_msg = (
            "Você é um auditor fiscal. Receberá um JSON com anomalias detectadas. "
            "Para cada item, use o campo 'contexto_ia' para escrever:\n"
            "1. 'explicacao': O que aconteceu de errado (máximo 15 palavras).\n"
            "2. 'recomendacao': O que deve ser feito (máximo 15 palavras).\n"
            "Retorne APENAS o JSON atualizado com os campos: ['arquivo', 'anomalia', 'explicacao', 'recomendacao', 'criticidade', 'slug']."
        )

        prompt = f"Enriqueça estas anomalias:\n\n{json.dumps(hits, ensure_ascii=False)}"

        for model_id in self.model_priority:
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config={
                            "system_instruction": system_msg,
                            "response_mime_type": "application/json",
                        },
                    )

                    usage = response.usage_metadata
                    token_info = {
                        "model": model_id,
                        "prompt_tokens": (
                            getattr(usage, "prompt_token_count", 0) if usage else 0
                        ),
                        "candidates_tokens": (
                            getattr(usage, "candidates_token_count", 0) if usage else 0
                        ),
                        "status": "success",
                    }

                    data = json.loads(response.text or "[]")
                    return data, token_info

                except Exception as e:
                    if "429" in str(e) or "503" in str(e):
                        await asyncio.sleep(2)
                        continue
                    break

        return hits, {"status": "failed", "error": "All models failed"}


gemini_service = GeminiService()
