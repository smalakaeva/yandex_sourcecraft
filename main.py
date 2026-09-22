import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uuid

# Импортируем твои функции из папки scoring
from scoring.normalizer import calculate_health_score
from scoring.data_loader import preprocess_data
from scoring.recommender import SourceCraftRecommendationEngine

app = FastAPI(title="SourceCraft Backend API")
engine = SourceCraftRecommendationEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RepoPayload(BaseModel):
    repository_id: str
    metrics: Dict[str, Any]


def get_grade(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "E"


@app.get("/api/v1/stats")
def get_stats():
    return {
        "repos_total": 1,
        "repos_scored": 1,
        "median_score": 75.0,
        "no_data_security": 0,
        "with_ci": 1,
        "last_run_at": "2026-09-25T00:00:00Z"
    }


@app.get("/api/v1/languages")
def get_languages():
    return [{"language": "Python", "count": 1}]


@app.get("/api/v1/repos")
def get_repos(page: int = 1, page_size: int = 25, sort: str = "score", order: str = "desc", min_coverage: float = 0.0):
    raw_metrics = {
        'collection.category_status.security': 'ok',
        'collection.category_status.cicd': 'ok',
        'security.defect_groups_by_severity': '{"LOW": 2}',
        'cicd.has_ci_config': True,
        'documentation.has_readme': True,
        'activity.commits_30d': 45,
        'code_health.lines_of_code_estimate': 5000,
        'issues.stale_open_count': 2,
        'activity.bus_factor_top1_share_365d': 0.5
    }

    df_clean = pd.DataFrame([raw_metrics])
    result = calculate_health_score(df_clean)

    calculated_repo = {
        "id": "test-repo-victory",
        "full_path": "ruzel/pandas-victory",
        "owner": "ruzel",
        "name": "pandas-victory",  # Новое имя для сброса кэша!
        "url": "https://sourcecraft.dev/ruzel/pandas-victory",
        "description": "Рейтинг рассчитан напрямую через Pandas и NumPy",
        "primary_language": "Python",
        "likes": 42.0,
        "last_activity_at": "2026-09-20T12:00:00Z",
        "analyzed_at": "2026-09-25T00:00:00Z",
        # Для главной страницы структура плоская (как в repos.json)
        "total_score": result["total_health_score"],
        "grade": get_grade(result["total_health_score"]),
        "coverage": 1.0,
        "categories": result["categories"],
        "no_data_categories": [],
        "not_applicable_categories": [],
        "has_ci": True,
        "security_status": "ok",
        "rank": 1
    }

    return {
        "items": [calculated_repo],
        "total": 1,
        "generated_at": "2026-09-25T00:00:00Z"
    }


@app.get("/api/v1/repos/{owner}/{repo_name}")
def get_repo_details(owner: str, repo_name: str):
    raw_metrics = {
        'collection.category_status.security': 'ok',
        'collection.category_status.cicd': 'ok',
        'security.defect_groups_by_severity': '{"LOW": 2}',
        'cicd.has_ci_config': True,
        'documentation.has_readme': True,
        'activity.commits_30d': 45,
        'code_health.lines_of_code_estimate': 5000,
        'issues.stale_open_count': 2,
        'activity.bus_factor_top1_share_365d': 0.5
    }

    df_clean = pd.DataFrame([raw_metrics])
    result = calculate_health_score(df_clean)

    row_dict = df_clean.iloc[0].to_dict()
    raw_recommendations = engine.generate_recommendations(row_dict)

    # Правильная сборка рекомендаций с ключом evidence (массив)
    safe_recommendations = []
    for i, rec in enumerate(raw_recommendations):
        safe_recommendations.append({
            "id": f"rec-{i}",
            "category": rec.get("category", "activity").lower(),
            "priority": "high",
            "title": rec.get("action", "Рекомендация"),
            "problem": rec.get("problem", "Обнаружена проблема"),
            "why": rec.get("importance", "Влияет на Health Score"),
            "action": rec.get("action", "Исправьте проблему"),
            # Ключевое исправление для ошибки reading 'length'
            "evidence": [
                {"label": "Деталь", "value": "Требует внимания", "url": None}
            ],
            "expected_gain": 5.0
        })

    # Сборка структуры категории строго по эталону
    def make_safe_category(key, title, score_val):
        return {
            "key": key,
            "title": title,
            "weight": 0.16,
            "effective_weight": 0.16,
            "score": float(score_val),
            "status": "ok",
            "no_data_reason": None,
            "signal_coverage": 1.0,
            "metrics": [
                {
                    "key": f"{key}_metric",
                    "label": "Текущая оценка",
                    "value": float(score_val),
                    "display": f"{score_val}/100",
                    "status": "ok",
                    "hint": None,
                    "source": "pandas_engine"
                }
            ],
            "strengths": [],
            "weaknesses": [],
            "summary": f"{score_val}/100: метрика рассчитана"
        }

    return {
        "id": f"{owner}-{repo_name}",
        "full_path": f"{owner}/{repo_name}",
        "owner": owner,
        "name": repo_name,
        "url": f"https://sourcecraft.dev/{owner}/{repo_name}",
        "description": "Детальная страница на основе Pandas",
        "visibility": "public",
        "default_branch": "main",
        "primary_language": "Python",
        "likes": 42.0,
        "likes_percentile": 99.0,
        "last_activity_at": "2026-09-20T12:00:00Z",
        "analyzed_at": "2026-09-25T00:00:00Z",

        # Ключевое исправление для ошибки reading 'replace' — вложенный объект score
        "score": {
            "total": result["total_health_score"],
            "grade": get_grade(result["total_health_score"]),
            "coverage": 1.0,
            "formula_version": "pandas-1.0",
            "weights": {
                "security": 0.2, "code_health": 0.2, "activity": 0.15,
                "documentation": 0.15, "cicd": 0.15, "issues": 0.15
            }
        },
        "categories": [
            make_safe_category("security", "Security", result["categories"]["security"]),
            make_safe_category("code_health", "Состояние кода", result["categories"]["code_health"]),
            make_safe_category("activity", "Активность", result["categories"]["activity"]),
            make_safe_category("documentation", "Документация", result["categories"]["documentation"]),
            make_safe_category("cicd", "CI/CD", result["categories"]["cicd"]),
            make_safe_category("issues", "Issues", result["categories"]["issues"])
        ],
        "recommendations": safe_recommendations,
        "strengths": [{"category": "code_health", "text": "Pandas Engine работает!"}],
        "risks": [],
        "no_data_categories": [],
        "not_applicable_categories": [],
        "summary": f"Health Score {result['total_health_score']} из 100. Работает на FastAPI.",
        "collection": {
            "collected_at": "2026-09-25T00:00:00Z",
            "duration_ms": 150.0,
            "collector_version": "1.0",
            "sources_used": {
                "git_clone": True,
                "platform_api": True,
                "platform_cli": False,
                "appsec_api": True
            },
            "errors": []
        },
        "history": [
            {"analyzed_at": "2026-09-25T00:00:00Z", "total": result["total_health_score"]}
        ]
    }


@app.post("/api/v1/score")
def generate_score(payload: RepoPayload):
    raw_data = payload.metrics
    df_clean = preprocess_data(raw_data)
    health_scores = calculate_health_score(df_clean)
    row_dict = df_clean.iloc[0].to_dict()
    recommendations = engine.generate_recommendations(row_dict)

    return {
        "repository_id": payload.repository_id,
        "scores": health_scores,
        "recommendations": recommendations
    }