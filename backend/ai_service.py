import json
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.config import GROQ_API_KEY, GROQ_MODEL

log = logging.getLogger(__name__)


def _fallback(base_recommendations: list[dict]) -> dict:
    """Ответ без модели: пустая сводка — интерфейс оставит шаблонную, model=None."""
    return {"summary": "", "recommendations": base_recommendations, "model": None}


async def generate_ai_recommendations_list(owner: str, name: str, base_recommendations: list[dict]) -> dict:
    """Отправляет факты в ИИ и возвращает JSON со сводкой, рекомендациями и моделью.

    Ключ `model` — имя модели, которая написала текст, либо None: по нему интерфейс
    отличает настоящую генерацию от запасного варианта и не подписывает шаблонную
    сводку чужим авторством.
    """
    if not GROQ_API_KEY:
        log.warning("GROQ_API_KEY не задан (.env или окружение) — ИИ-сводка не генерируется, "
                    "интерфейс покажет базовые рекомендации")
        return _fallback(base_recommendations)

    llm = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0.2)

    prompt = PromptTemplate.from_template(
        """Ты — строгий техлид платформы SourceCraft. 
        Напиши общую сводку и улучши рекомендации для репозитория {owner}/{name}.

        Базовые рекомендации:
        {recommendations}

        Верни СТРОГО валидный JSON-объект с двумя ключами:
        1. "summary": строка (2-3 предложения об общем состоянии проекта, что хорошо, а что плохо).
        2. "recommendations": массив объектов (улучшенные базовые рекомендации с ключами: "category", "priority", "title", "problem", "why", "action", "impact").

        Отвечай только JSON-объектом, без лишнего текста.
        """
    )

    recs_json = json.dumps(base_recommendations, ensure_ascii=False)
    chain = prompt | llm | JsonOutputParser()

    try:
        answer = await chain.ainvoke({"owner": owner, "name": name, "recommendations": recs_json})
    except Exception as exc:
        log.error("Ошибка при генерации ИИ-рекомендаций: %s", exc)
        return _fallback(base_recommendations)

    if not isinstance(answer, dict):
        log.error("Модель вернула не объект: %s", type(answer).__name__)
        return _fallback(base_recommendations)

    summary = str(answer.get("summary") or "").strip()
    recs = answer.get("recommendations")
    if not isinstance(recs, list) or not recs:
        recs = base_recommendations

    # Модель отвечала, но сводки не дала: рекомендации берём, в шапке остаётся шаблон
    return {"summary": summary, "recommendations": recs, "model": GROQ_MODEL}
