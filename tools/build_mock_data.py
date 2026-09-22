#!/usr/bin/env python3
"""
Готовит mock-данные для фронтенда SourceCraft Repo Health из сырой выгрузки
repo_health_report.csv.

ВАЖНО: скоринг здесь — ДЕМОНСТРАЦИОННЫЙ. Он нужен только для того, чтобы фронт
можно было показать без поднятого бэкенда. Боевые значения приходят из витрины
команды (score_security, score_docs, ..., total_health_score) через API.
Формы JSON в точности повторяют контракт API (docs/api-contract.md), поэтому
переключение фронта на реальный бэк = смена одного флага в .env.

Запуск:
    python3 tools/build_mock_data.py --csv ~/Downloads/repo_health_report.csv \
        --out frontend/public/mock
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

csv.field_size_limit(10 ** 9)

NOW = datetime(2026, 9, 22, tzinfo=timezone.utc)
FORMULA_VERSION = "demo-0.3.0"

WEIGHTS = {
    "security": 0.20,
    "code_health": 0.20,
    "activity": 0.15,
    "documentation": 0.15,
    "cicd": 0.15,
    "issues": 0.15,
}

TITLES = {
    "security": "Security",
    "code_health": "Состояние кода",
    "activity": "Активность",
    "documentation": "Документация",
    "cicd": "CI/CD",
    "issues": "Issues",
}


# --------------------------------------------------------------------------- utils
def f(row, key):
    """float или None"""
    v = (row.get(key) or "").strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def b(row, key):
    v = (row.get(key) or "").strip().lower()
    if v in ("true", "1"):
        return True
    if v in ("false", "0"):
        return False
    return None


def s(row, key):
    return (row.get(key) or "").strip() or None


def jlist(row, key):
    raw = (row.get(key) or "").strip()
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except Exception:
        return []


def days_since(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (NOW - dt).total_seconds() / 86400


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def metric(key, label, value, display, status="ok", hint=None, source=None):
    return {
        "key": key,
        "label": label,
        "value": value,
        "display": display,
        "status": status,
        "hint": hint,
        "source": source,
    }


def human_days(d):
    if d is None:
        return "—"
    d = int(round(d))
    if d <= 0:
        return "сегодня"
    if d == 1:
        return "1 день назад"
    if d < 5:
        return f"{d} дня назад"
    if d < 31:
        return f"{d} дней назад"
    months = d // 30
    if months < 12:
        return f"{months} мес. назад"
    return f"{months // 12} г. назад"


# --------------------------------------------------------------------------- категории
def score_documentation(row):
    status_raw = s(row, "collection.category_status.documentation")
    if status_raw == "unavailable":
        return {
            "score": None,
            "status": "no_data",
            "no_data_reason": "Репозиторий не удалось склонировать, файлы документации не проверены.",
            "signal_coverage": 0.0,
            "metrics": [],
            "strengths": [],
            "weaknesses": [],
            "summary": "Нет данных: рабочая копия недоступна.",
        }

    has_readme = b(row, "documentation.has_readme")
    length = f(row, "documentation.readme_length_chars") or 0
    sections = jlist(row, "documentation.readme_has_sections")
    has_license = b(row, "documentation.has_license")
    license_type = s(row, "documentation.license_type")
    contributing = b(row, "documentation.has_contributing")
    coc = b(row, "documentation.has_code_of_conduct")
    changelog = b(row, "documentation.has_changelog")
    docs_dir = b(row, "documentation.has_docs_dir")
    docs_files = f(row, "documentation.docs_file_count") or 0
    issue_tpl = b(row, "documentation.has_issue_templates")
    pr_tpl = b(row, "documentation.has_pr_template")

    pts = 0.0
    pts += 25 if has_readme else 0
    if has_readme:
        pts += 15 if length >= 2000 else (8 if length >= 500 else 2)
        pts += 10 if len(sections) >= 3 else (5 if sections else 0)
    pts += 15 if has_license else 0
    pts += 10 if contributing else 0
    pts += 5 if coc else 0
    pts += 5 if changelog else 0
    pts += 10 if (docs_dir or docs_files > 0) else 0
    pts += 5 if issue_tpl else 0
    pts += 5 if pr_tpl else 0

    metrics = [
        metric("readme", "README", has_readme,
               f"есть, {int(length)} символов" if has_readme else "отсутствует",
               "ok" if has_readme else "ok", "Первое, что видит новый разработчик.", "git_clone"),
        metric("readme_sections", "Разделы README", sections,
               ", ".join(sections) if sections else "разделы не распознаны",
               "ok", "Инструкция локального запуска, сборка, тесты.", "git_clone"),
        metric("license", "Лицензия", has_license,
               license_type or ("есть" if has_license else "отсутствует"),
               "ok", "Без лицензии проект нельзя легально использовать.", "git_clone"),
        metric("contributing", "CONTRIBUTING", contributing, "есть" if contributing else "нет", "ok", None, "git_clone"),
        metric("code_of_conduct", "CODE_OF_CONDUCT", coc, "есть" if coc else "нет", "ok", None, "git_clone"),
        metric("changelog", "CHANGELOG", changelog, "есть" if changelog else "нет", "ok", None, "git_clone"),
        metric("docs_dir", "Каталог docs/", docs_dir,
               f"{int(docs_files)} файлов" if docs_files else ("есть" if docs_dir else "нет"), "ok", None, "git_clone"),
        metric("templates", "Шаблоны issue/PR", bool(issue_tpl or pr_tpl),
               ", ".join([x for x in ["issue" if issue_tpl else None, "PR" if pr_tpl else None] if x]) or "нет",
               "ok", None, "git_clone"),
    ]

    strengths, weaknesses = [], []
    if has_readme and length >= 2000:
        strengths.append("Подробный README (%d символов)" % length)
    if has_license:
        strengths.append(f"Лицензия {license_type or 'указана'}")
    if contributing:
        strengths.append("Есть инструкция для контрибьюторов")
    if docs_dir or docs_files:
        strengths.append("Отдельный каталог документации")
    if not has_readme:
        weaknesses.append("README отсутствует")
    elif length < 500:
        weaknesses.append("README короче 500 символов")
    if not has_license:
        weaknesses.append("Нет файла лицензии")
    if not sections:
        weaknesses.append("В README не найдено инструкции локального запуска")
    if not contributing:
        weaknesses.append("Нет CONTRIBUTING")

    score = clamp(pts)
    summary = (
        f"{score:.0f}/100: " +
        ("README отсутствует" if not has_readme
         else ("нет инструкции локального запуска" if not sections
               else ("нет лицензии" if not has_license else "документация покрывает основные разделы")))
    )
    return {
        "score": score, "status": "ok" if has_readme is not None else "partial",
        "signal_coverage": 1.0, "metrics": metrics,
        "strengths": strengths, "weaknesses": weaknesses, "summary": summary,
        "no_data_reason": None,
    }


def score_cicd(row):
    status_raw = s(row, "collection.category_status.cicd")
    if status_raw == "unavailable":
        return {"score": None, "status": "no_data",
                "no_data_reason": "Конфигурация и история пайплайнов недоступны.",
                "signal_coverage": 0.0, "metrics": [], "strengths": [], "weaknesses": [],
                "summary": "Нет данных о CI/CD."}

    has_ci = b(row, "cicd.has_ci_config")
    path = s(row, "cicd.ci_config_path")
    test_stage = b(row, "cicd.has_test_stage")
    lint_stage = b(row, "cicd.has_lint_or_security_stage")
    deploy_stage = b(row, "cicd.has_deploy_stage")
    stages = f(row, "cicd.declared_stage_count")
    history = b(row, "cicd.pipeline_history_available")
    runs = f(row, "cicd.runs_30d")
    success = f(row, "cicd.success_rate_30d")
    duration = f(row, "cicd.median_duration_seconds")
    last_status = s(row, "cicd.last_run_status")

    config_pts = 0.0
    config_pts += 45 if has_ci else 0
    config_pts += 25 if test_stage else 0
    config_pts += 18 if lint_stage else 0
    config_pts += 12 if deploy_stage else 0
    config_part = clamp(config_pts)

    metrics = [
        metric("ci_config", "Конфигурация CI", has_ci, path or ("есть" if has_ci else "не найдена"),
               "ok", "Без CI изменения не проверяются автоматически.", "git_clone"),
        metric("test_stage", "Стадия тестов", test_stage, "есть" if test_stage else "нет", "ok", None, "git_clone"),
        metric("lint_stage", "Линт/секьюрити-стадия", lint_stage, "есть" if lint_stage else "нет", "ok", None, "git_clone"),
        metric("deploy_stage", "Стадия деплоя", deploy_stage, "есть" if deploy_stage else "нет", "ok", None, "git_clone"),
        metric("stages", "Объявлено стадий", stages, f"{int(stages)}" if stages is not None else "—", "ok", None, "git_clone"),
    ]

    if history:
        run_pts = 0.0
        run_pts += (success or 0) * 60
        run_pts += 25 if (runs or 0) >= 10 else (15 if (runs or 0) >= 3 else 5)
        run_pts += 15 if (duration or 0) and duration <= 900 else 7
        score = clamp(config_part * 0.5 + clamp(run_pts) * 0.5)
        coverage = 1.0
        cat_status = "ok"
        metrics += [
            metric("runs_30d", "Прогонов за 30 дней", runs, f"{int(runs or 0)}", "ok", None, "platform_api"),
            metric("success_rate", "Доля успешных прогонов", success,
                   f"{(success or 0) * 100:.0f}%", "ok", "Нестабильный CI блокирует поставку.", "platform_api"),
            metric("median_duration", "Медианная длительность", duration,
                   f"{int(duration or 0)} с", "ok", None, "platform_api"),
            metric("last_run", "Последний прогон", last_status, last_status or "—", "ok", None, "platform_api"),
        ]
        summary_tail = f"{(1 - (success or 0)) * 100:.0f}% последних прогонов завершились неуспешно"
    else:
        score = config_part
        coverage = 0.5
        cat_status = "partial"
        metrics += [
            metric("runs_30d", "Прогонов за 30 дней", None, "нет данных", "no_data",
                   "Платформа вернула 403 на историю пайплайнов.", "platform_api"),
            metric("success_rate", "Доля успешных прогонов", None, "нет данных", "no_data", None, "platform_api"),
        ]
        summary_tail = "история прогонов недоступна, оценка только по конфигурации"

    strengths, weaknesses = [], []
    if has_ci:
        strengths.append(f"CI настроен ({path or 'конфигурация найдена'})")
    else:
        weaknesses.append("Конфигурация CI не найдена")
    if test_stage:
        strengths.append("В пайплайне есть стадия тестов")
    else:
        weaknesses.append("В пайплайне нет стадии тестов")
    if not lint_stage:
        weaknesses.append("Нет стадии линта или проверки безопасности")

    if not has_ci:
        summary_tail = "конфигурация CI не найдена в репозитории"

    return {"score": score, "status": cat_status,
            "no_data_reason": None if history else "История прогонов пайплайнов недоступна через API платформы.",
            "signal_coverage": coverage, "metrics": metrics,
            "strengths": strengths, "weaknesses": weaknesses,
            "summary": f"{score:.0f}/100: {summary_tail}"}


def score_security(row):
    available = b(row, "security.appsec_available")
    policy = b(row, "security.has_security_policy")
    open_total = f(row, "security.open_defect_groups_total")
    oldest = f(row, "security.oldest_open_defect_group_age_days")
    scan_status = s(row, "security.latest_scan.status")
    scan_type = s(row, "security.latest_scan.scan_type")
    scan_at = s(row, "security.latest_scan.finished_at")

    policy_metric = metric(
        "security_policy", "SECURITY-политика", policy,
        "есть" if policy else "нет", "ok",
        "Справочный признак, в Score не входит: категория считается только по данным AppSec.",
        "git_clone")

    if not available:
        return {"score": None, "status": "no_data",
                "no_data_reason": "AppSec SourceCraft вернул 403: результаты SAST/SCA/secret scanning "
                                  "не выдаются без прав на репозиторий.",
                "signal_coverage": 0.0,
                "metrics": [
                    metric("appsec", "Данные AppSec", False, "недоступны", "no_data",
                           "Security считается только по фактическим результатам AppSec SourceCraft.", "appsec_api"),
                    policy_metric,
                ],
                "strengths": [], "weaknesses": [],
                "summary": "Нет данных: результаты AppSec недоступны."}

    severity = {}
    try:
        severity = json.loads(row.get("security.defect_groups_by_severity") or "{}") or {}
    except Exception:
        severity = {}
    crit = float(severity.get("CRITICAL", severity.get("critical", 0)) or 0)
    high = float(severity.get("HIGH", severity.get("high", 0)) or 0)
    med = float(severity.get("MEDIUM", severity.get("medium", 0)) or 0)
    low = float(severity.get("LOW", severity.get("low", 0)) or 0)

    penalty = crit * 25 + high * 12 + med * 4 + low * 1
    age_penalty = 0
    if oldest:
        age_penalty = 10 if oldest > 180 else (5 if oldest > 90 else 0)
    score = clamp(100 - penalty - age_penalty)

    metrics = [
        metric("scan", "Последнее сканирование", scan_at,
               f"{scan_type or 'scan'}, {scan_status or 'ok'}, {human_days(days_since(scan_at))}", "ok", None, "appsec_api"),
        metric("critical", "Критические дефекты", crit, f"{int(crit)}", "ok", None, "appsec_api"),
        metric("high", "Высокие дефекты", high, f"{int(high)}", "ok", None, "appsec_api"),
        metric("medium", "Средние дефекты", med, f"{int(med)}", "ok", None, "appsec_api"),
        metric("open_total", "Открытых групп дефектов", open_total, f"{int(open_total or 0)}", "ok", None, "appsec_api"),
        metric("oldest_open", "Возраст старейшей проблемы", oldest, human_days(oldest), "ok", None, "appsec_api"),
        policy_metric,
    ]
    strengths, weaknesses = [], []
    if crit == 0 and high == 0:
        strengths.append("Критических и высоких уязвимостей не обнаружено")
    if crit:
        weaknesses.append(f"{int(crit)} критических уязвимостей")
    if high:
        weaknesses.append(f"{int(high)} уязвимостей высокого уровня")
    if oldest and oldest > 90:
        weaknesses.append(f"Старейшая открытая проблема не исправлена {human_days(oldest)}")

    return {"score": score, "status": "ok", "no_data_reason": None, "signal_coverage": 1.0,
            "metrics": metrics, "strengths": strengths, "weaknesses": weaknesses,
            "summary": f"{score:.0f}/100: " + (
                f"обнаружено {int(crit)} критических и {int(high)} высоких уязвимостей"
                if (crit or high) else "открытых критических проблем нет")}


def score_activity(row):
    status_raw = s(row, "collection.category_status.activity")
    if status_raw == "unavailable":
        return {"score": None, "status": "no_data",
                "no_data_reason": "Git-история недоступна: рабочая копия не получена.",
                "signal_coverage": 0.0, "metrics": [], "strengths": [], "weaknesses": [],
                "summary": "Нет данных о Git-активности."}

    c30 = f(row, "activity.commits_30d") or 0
    c90 = f(row, "activity.commits_90d") or 0
    c365 = f(row, "activity.commits_365d") or 0
    last = s(row, "activity.last_commit_at")
    age = days_since(last)
    contributors = f(row, "activity.contributors_365d") or 0
    bus = f(row, "activity.bus_factor_top1_share_365d")
    tags = f(row, "activity.tag_count") or 0
    releases = f(row, "activity.releases.count") or 0
    prs_open = f(row, "activity.pull_requests.open") or 0
    prs_merged = f(row, "activity.pull_requests.merged_90d") or 0
    prs_stale = f(row, "activity.pull_requests.stale_open_count") or 0

    pts = 0.0
    if age is None:
        pts += 0
    elif age <= 7:
        pts += 30
    elif age <= 30:
        pts += 25
    elif age <= 90:
        pts += 18
    elif age <= 180:
        pts += 10
    elif age <= 365:
        pts += 5

    pts += 25 if c90 > 60 else (18 if c90 > 20 else (12 if c90 > 5 else (6 if c90 > 0 else 0)))
    pts += 20 if contributors >= 10 else (14 if contributors >= 4 else (8 if contributors >= 2 else (3 if contributors >= 1 else 0)))

    if contributors >= 2 and bus is not None:
        pts += 15 if bus <= 0.4 else (10 if bus <= 0.6 else (5 if bus <= 0.8 else 0))
    elif contributors >= 2:
        pts += 5
    pts += 10 if (tags > 0 or releases > 0) else 0

    metrics = [
        metric("last_commit", "Последний коммит", last, human_days(age) if age is not None else "—", "ok", None, "git_clone"),
        metric("commits_30d", "Коммитов за 30 дней", c30, f"{int(c30)}", "ok", None, "git_clone"),
        metric("commits_90d", "Коммитов за 90 дней", c90, f"{int(c90)}", "ok", None, "git_clone"),
        metric("commits_365d", "Коммитов за год", c365, f"{int(c365)}", "ok", None, "git_clone"),
        metric("contributors", "Контрибьюторов за год", contributors, f"{int(contributors)}", "ok", None, "git_clone"),
        metric("bus_factor", "Доля топ-1 автора", bus,
               f"{bus * 100:.0f}%" if bus is not None else "нет данных",
               "ok" if bus is not None else "no_data",
               "Чем выше доля одного автора, тем ниже bus factor.", "git_clone"),
        metric("tags", "Тегов", tags, f"{int(tags)}", "ok", None, "git_clone"),
        metric("releases", "Релизов", releases, f"{int(releases)}", "ok", None, "platform_api"),
        metric("prs_open", "Открытых merge request", prs_open, f"{int(prs_open)}", "ok", None, "platform_api"),
        metric("prs_merged_90d", "Влито MR за 90 дней", prs_merged, f"{int(prs_merged)}", "ok", None, "platform_api"),
        metric("prs_stale", "Зависших MR", prs_stale, f"{int(prs_stale)}", "ok", None, "platform_api"),
    ]
    strengths, weaknesses = [], []
    if age is not None and age <= 30:
        strengths.append("Проект активно развивается: коммиты за последние 30 дней")
    if contributors >= 10:
        strengths.append(f"{int(contributors)} контрибьюторов за год")
    if bus is not None and bus <= 0.4 and contributors >= 3:
        strengths.append("Работа распределена между несколькими авторами")
    if age is not None and age > 180:
        weaknesses.append(f"Последний коммит {human_days(age)}")
    if contributors <= 1:
        weaknesses.append("Весь код за год написан одним автором (bus factor = 1)")
    elif bus is not None and bus > 0.8:
        weaknesses.append(f"{bus * 100:.0f}% коммитов сделал один автор")
    if prs_stale > 0:
        weaknesses.append(f"{int(prs_stale)} merge request зависли")
    if tags == 0 and releases == 0:
        weaknesses.append("Нет тегов и релизов")

    score = clamp(pts)
    return {"score": score, "status": "ok", "no_data_reason": None, "signal_coverage": 1.0,
            "metrics": metrics, "strengths": strengths, "weaknesses": weaknesses,
            "summary": f"{score:.0f}/100: " + (
                "проект активно развивается" if age is not None and age <= 30
                else (f"последний коммит {human_days(age)}" if age is not None else "активность не определена"))}


def score_issues(row):
    status_raw = s(row, "collection.category_status.issues")
    if status_raw == "unavailable":
        return {"score": None, "status": "no_data",
                "no_data_reason": "API трекера задач недоступно.",
                "signal_coverage": 0.0, "metrics": [], "strengths": [], "weaknesses": [],
                "summary": "Нет данных об issues."}

    open_count = f(row, "issues.open_count") or 0
    opened = f(row, "issues.opened_90d") or 0
    closed = f(row, "issues.closed_90d") or 0
    first_resp = f(row, "issues.avg_time_to_first_response_hours")
    to_close = f(row, "issues.avg_time_to_close_hours")
    stale = f(row, "issues.stale_open_count") or 0
    unanswered = f(row, "issues.unanswered_open_count") or 0
    labels = jlist(row, "issues.labels_in_use")

    if open_count == 0 and opened == 0 and closed == 0:
        return {"score": None, "status": "not_applicable",
                "no_data_reason": "В трекере репозитория нет ни одной задачи — оценивать нечего. "
                                  "Категория исключена из расчёта, а не засчитана как плохой результат.",
                "signal_coverage": 0.0,
                "metrics": [metric("open_count", "Открытых задач", 0, "0", "ok", None, "platform_api")],
                "strengths": [], "weaknesses": [],
                "summary": "Не применимо: трекер не используется."}

    pts = 0.0
    ratio = closed / opened if opened else (1.0 if closed else 0.5)
    pts += 35 if ratio >= 0.8 else (25 if ratio >= 0.5 else (15 if ratio >= 0.2 else 5))
    stale_share = stale / open_count if open_count else 0
    pts += 25 if stale_share == 0 else (18 if stale_share <= 0.2 else (10 if stale_share <= 0.5 else 2))
    unans_share = unanswered / open_count if open_count else 0
    pts += 20 if unans_share == 0 else (14 if unans_share <= 0.2 else (7 if unans_share <= 0.5 else 2))
    if first_resp is not None:
        pts += 20 if first_resp <= 24 else (14 if first_resp <= 72 else (8 if first_resp <= 168 else 3))
        coverage = 1.0
    else:
        pts = pts / 80 * 100
        coverage = 0.8

    metrics = [
        metric("open_count", "Открытых задач", open_count, f"{int(open_count)}", "ok", None, "platform_api"),
        metric("opened_90d", "Заведено за 90 дней", opened, f"{int(opened)}", "ok", None, "platform_api"),
        metric("closed_90d", "Закрыто за 90 дней", closed, f"{int(closed)}", "ok", None, "platform_api"),
        metric("first_response", "Среднее время до первого ответа", first_resp,
               f"{first_resp:.1f} ч" if first_resp is not None else "нет данных",
               "ok" if first_resp is not None else "no_data", None, "platform_api"),
        metric("time_to_close", "Среднее время до закрытия", to_close,
               f"{to_close / 24:.1f} дн." if to_close else "нет данных",
               "ok" if to_close else "no_data", None, "platform_api"),
        metric("stale", "Зависших задач", stale, f"{int(stale)}", "ok",
               "Открыты и не обновлялись более 30 дней.", "platform_api"),
        metric("unanswered", "Без ответа", unanswered, f"{int(unanswered)}", "ok", None, "platform_api"),
        metric("labels", "Используемых меток", len(labels), f"{len(labels)}", "ok", None, "platform_api"),
    ]
    strengths, weaknesses = [], []
    if ratio >= 0.8:
        strengths.append("Задачи закрываются быстрее, чем заводятся")
    if stale == 0 and open_count:
        strengths.append("Зависших задач нет")
    if stale:
        weaknesses.append(f"{int(stale)} задач не обновлялись более 30 дней")
    if unanswered:
        weaknesses.append(f"{int(unanswered)} открытых задач без ответа")
    if first_resp is not None and first_resp > 72:
        weaknesses.append(f"Первый ответ в среднем через {first_resp:.0f} ч")

    score = clamp(pts)
    return {"score": score, "status": "ok" if coverage == 1.0 else "partial",
            "no_data_reason": None if coverage == 1.0 else "Время первого ответа платформа не отдаёт.",
            "signal_coverage": coverage, "metrics": metrics,
            "strengths": strengths, "weaknesses": weaknesses,
            "summary": f"{score:.0f}/100: " + (
                f"{int(stale)} открытых задач не обновлялись более 30 дней" if stale
                else "поток задач обрабатывается")}


def score_code_health(row):
    status_raw = s(row, "collection.category_status.code_health")
    if status_raw == "unavailable":
        return {"score": None, "status": "no_data",
                "no_data_reason": "Рабочая копия недоступна, код не проанализирован.",
                "signal_coverage": 0.0, "metrics": [], "strengths": [], "weaknesses": [],
                "summary": "Нет данных о состоянии кода."}

    files = f(row, "code_health.file_count") or 0
    loc = f(row, "code_health.lines_of_code_estimate") or 0
    todo = f(row, "code_health.todo_count") or 0
    fixme = f(row, "code_health.fixme_count") or 0
    hack = f(row, "code_health.hack_count") or 0
    density = f(row, "code_health.todo_density_per_kloc")
    oldest = f(row, "code_health.oldest_todo_age_days")
    largest = f(row, "code_health.largest_file_lines") or 0

    if loc < 200:
        return {"score": None, "status": "not_applicable",
                "no_data_reason": f"В репозитории {int(loc)} строк кода — выборка слишком мала "
                                  "для воспроизводимой оценки технического долга.",
                "signal_coverage": 0.0,
                "metrics": [metric("loc", "Строк кода", loc, f"{int(loc)}", "ok", None, "git_clone")],
                "strengths": [], "weaknesses": [],
                "summary": "Не применимо: слишком мало кода."}

    d = density if density is not None else 0
    pts = 0.0
    pts += 30 if d == 0 else (25 if d <= 1 else (18 if d <= 3 else (10 if d <= 8 else 3)))
    if oldest is None:
        pts += 20
    else:
        pts += 18 if oldest <= 90 else (12 if oldest <= 180 else (7 if oldest <= 365 else 3))
    pts += 25 if largest <= 1000 else (18 if largest <= 3000 else (10 if largest <= 6000 else 4))
    avg = loc / files if files else 0
    pts += 25 if avg <= 300 else (18 if avg <= 600 else (10 if avg <= 1000 else 5))

    metrics = [
        metric("files", "Файлов под контролем версий", files, f"{int(files)}", "ok", None, "git_clone"),
        metric("loc", "Строк кода (оценка)", loc, f"{int(loc):,}".replace(",", " "), "ok", None, "git_clone"),
        metric("todo", "TODO", todo, f"{int(todo)}", "ok", None, "git_clone"),
        metric("fixme", "FIXME", fixme, f"{int(fixme)}", "ok", None, "git_clone"),
        metric("hack", "HACK", hack, f"{int(hack)}", "ok", None, "git_clone"),
        metric("todo_density", "Плотность TODO на 1000 строк", density,
               f"{d:.2f}", "ok", "Сопоставимо между проектами разного размера.", "git_clone"),
        metric("oldest_todo", "Возраст старейшего TODO", oldest, human_days(oldest), "ok",
               "Считается по дате строки в Git-истории.", "git_clone"),
        metric("largest_file", "Самый большой файл", largest, f"{int(largest)} строк", "ok", None, "git_clone"),
        metric("avg_file", "Средний размер файла", avg, f"{avg:.0f} строк", "ok", None, "git_clone"),
    ]
    strengths, weaknesses = [], []
    total_marks = int(todo + fixme + hack)
    if d <= 1:
        strengths.append("Низкая плотность TODO/FIXME")
    if largest <= 1000:
        strengths.append("Нет файлов-гигантов")
    if total_marks:
        weaknesses.append(f"{total_marks} пометок TODO/FIXME/HACK в коде")
    if oldest and oldest > 180:
        weaknesses.append(f"Старейший TODO висит {human_days(oldest)}")
    if largest > 3000:
        weaknesses.append(f"Файл на {int(largest)} строк сложно сопровождать")

    score = clamp(pts)
    oldest_note = ""
    if oldest and oldest > 180 and total_marks:
        oldest_note = f", старейшему {human_days(oldest)}"
    return {"score": score, "status": "ok", "no_data_reason": None, "signal_coverage": 1.0,
            "metrics": metrics, "strengths": strengths, "weaknesses": weaknesses,
            "summary": f"{score:.0f}/100: найдено {total_marks} TODO/FIXME/HACK{oldest_note}"}


SCORERS = {
    "documentation": score_documentation,
    "cicd": score_cicd,
    "security": score_security,
    "activity": score_activity,
    "issues": score_issues,
    "code_health": score_code_health,
}


def grade(total):
    if total is None:
        return "—"
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 55:
        return "C"
    if total >= 40:
        return "D"
    return "E"


# --------------------------------------------------------------------------- рекомендации
def build_recommendations(cats, row, total):
    """Правила -> приоритизированный список. expected_gain считается как
    (целевой балл - текущий) * эффективный вес категории."""
    by_key = {c["key"]: c for c in cats}
    recs = []

    def gain(key, delta_points):
        """delta_points — сколько баллов внутри категории вернёт исправление
        по той же формуле, что считает Score. Переводим их в баллы итогового Score."""
        c = by_key[key]
        if c["score"] is None:
            return 0.0
        headroom = max(0.0, 100.0 - c["score"])
        return round(min(delta_points, headroom) * c["effective_weight"], 1)

    def add(key, priority, title, problem, why, action, evidence, delta_points):
        recs.append({
            "id": f"{key}.{len(recs) + 1}",
            "category": key,
            "priority": priority,
            "title": title,
            "problem": problem,
            "why": why,
            "action": action,
            "evidence": evidence,
            "expected_gain": gain(key, delta_points),
        })

    url = s(row, "repo.url") or ""

    # security
    sec = by_key["security"]
    if sec["score"] is not None:
        crit = next((m["value"] for m in sec["metrics"] if m["key"] == "critical"), 0) or 0
        high = next((m["value"] for m in sec["metrics"] if m["key"] == "high"), 0) or 0
        if crit:
            add("security", "critical", "Устраните критические уязвимости",
                f"AppSec SourceCraft нашёл {int(crit)} критических групп дефектов.",
                "Критические уязвимости эксплуатируются в первую очередь и блокируют использование проекта в проде.",
                "Обновите затронутые зависимости до безопасных версий и перезапустите сканирование.",
                [{"label": "Критических групп дефектов", "value": str(int(crit)), "url": url}], crit * 25)
        elif high:
            add("security", "high", "Разберите уязвимости высокого уровня",
                f"Открыто {int(high)} групп дефектов уровня HIGH.",
                "Накопленные HIGH-дефекты со временем становятся входной точкой для атак.",
                "Назначьте владельцев на группы дефектов и закройте их в ближайшем спринте.",
                [{"label": "HIGH-дефектов", "value": str(int(high)), "url": url}], high * 12)

    # documentation
    doc = by_key["documentation"]
    if doc["score"] is not None:
        has_readme = next((m["value"] for m in doc["metrics"] if m["key"] == "readme"), None)
        sections = next((m["value"] for m in doc["metrics"] if m["key"] == "readme_sections"), []) or []
        has_license = next((m["value"] for m in doc["metrics"] if m["key"] == "license"), None)
        if not has_readme:
            add("documentation", "high", "Добавьте README",
                "В корне репозитория нет README.",
                "Без README новый разработчик не понимает, что делает проект и как его запустить.",
                "Опишите назначение проекта, требования, установку, запуск и тесты.",
                [{"label": "README", "value": "отсутствует", "url": url}], 50)
        elif not sections:
            add("documentation", "medium", "Опишите локальный запуск в README",
                "В README не найдено раздела с установкой или запуском.",
                "Инструкция локального запуска — главный барьер входа для контрибьютора.",
                "Добавьте разделы Installation / Quick start / Tests с рабочими командами.",
                [{"label": "Разделы README", "value": "не распознаны", "url": url}], 10)
        if not has_license:
            add("documentation", "high", "Добавьте файл лицензии",
                "Файл лицензии не найден.",
                "Без лицензии код формально нельзя использовать в других проектах: это отсекает пользователей.",
                "Выберите лицензию (Apache-2.0 или MIT) и добавьте LICENSE в корень.",
                [{"label": "LICENSE", "value": "отсутствует", "url": url}], 15)

    # cicd
    ci = by_key["cicd"]
    if ci["score"] is not None:
        has_ci = next((m["value"] for m in ci["metrics"] if m["key"] == "ci_config"), None)
        test_stage = next((m["value"] for m in ci["metrics"] if m["key"] == "test_stage"), None)
        if not has_ci:
            add("cicd", "high", "Настройте CI",
                "Конфигурация CI в репозитории не найдена.",
                "Без CI регрессии обнаруживаются только вручную и попадают в основную ветку.",
                "Добавьте .sourcecraft/ci.yaml со стадиями сборки, тестов и линта.",
                [{"label": "Конфигурация CI", "value": "не найдена", "url": url}], 45)
        elif not test_stage:
            add("cicd", "medium", "Добавьте стадию тестов в пайплайн",
                "В конфигурации CI нет стадии запуска тестов.",
                "Пайплайн без тестов подтверждает только то, что проект собирается.",
                "Добавьте job с прогоном тестов и сделайте его блокирующим для merge request.",
                [{"label": "Стадия тестов", "value": "нет", "url": url}], 25)

    # activity
    act = by_key["activity"]
    if act["score"] is not None:
        bus = next((m["value"] for m in act["metrics"] if m["key"] == "bus_factor"), None)
        contributors = next((m["value"] for m in act["metrics"] if m["key"] == "contributors"), 0) or 0
        last = next((m for m in act["metrics"] if m["key"] == "last_commit"), None)
        stale_pr = next((m["value"] for m in act["metrics"] if m["key"] == "prs_stale"), 0) or 0
        age = days_since(last["value"]) if last and last["value"] else None
        if contributors <= 1:
            add("activity", "high", "Снизьте зависимость от одного разработчика",
                "За последний год коммиты делал один автор — bus factor равен 1.",
                "Уход единственного разработчика останавливает проект.",
                "Подключите второго мейнтейнера, введите обязательный review и опишите онбординг.",
                [{"label": "Контрибьюторов за год", "value": f"{int(contributors)}", "url": url}], 20)
        elif bus is not None and bus > 0.8:
            add("activity", "medium", "Распределите нагрузку между авторами",
                f"{bus * 100:.0f}% коммитов за год сделал один автор.",
                "Концентрация знаний у одного человека — риск сопровождения.",
                "Разделите зоны ответственности и добавьте CODEOWNERS на ключевые каталоги.",
                [{"label": "Доля топ-1 автора", "value": f"{bus * 100:.0f}%", "url": url}], 15)
        if age is not None and age > 180:
            add("activity", "medium", "Обновите проект или пометьте его архивным",
                f"Последний коммит был {human_days(age)}.",
                "Пользователи не могут отличить стабильный проект от заброшенного.",
                "Опубликуйте план развития или переведите репозиторий в архив.",
                [{"label": "Последний коммит", "value": human_days(age), "url": url}], 25)
        if stale_pr:
            add("activity", "medium", "Разберите зависшие merge request",
                f"{int(stale_pr)} merge request остаются открытыми более 30 дней.",
                "Зависшие MR демотивируют контрибьюторов и копят конфликты слияния.",
                "Назначьте ревьюеров и закройте или влейте зависшие MR.",
                [{"label": "Зависших MR", "value": f"{int(stale_pr)}", "url": url}], 0)

    # issues
    iss = by_key["issues"]
    if iss["score"] is not None:
        stale = next((m["value"] for m in iss["metrics"] if m["key"] == "stale"), 0) or 0
        unanswered = next((m["value"] for m in iss["metrics"] if m["key"] == "unanswered"), 0) or 0
        if stale:
            add("issues", "medium", "Разберите зависшие задачи",
                f"{int(stale)} открытых задач не обновлялись более 30 дней.",
                "Зависшие задачи создают у пользователей ощущение, что проект не поддерживают.",
                "Проведите груминг: закройте неактуальное, остальному назначьте владельцев.",
                [{"label": "Зависших задач", "value": f"{int(stale)}", "url": url}], 25)
        if unanswered:
            add("issues", "low", "Отвечайте на новые issues",
                f"{int(unanswered)} открытых задач без единого ответа.",
                "Время до первого ответа — ключевой сигнал живого сообщества.",
                "Договоритесь о SLA на первый ответ (например, 48 часов) и заведите дежурство.",
                [{"label": "Задач без ответа", "value": f"{int(unanswered)}", "url": url}], 20)

    # code health
    ch = by_key["code_health"]
    if ch["score"] is not None:
        density = next((m["value"] for m in ch["metrics"] if m["key"] == "todo_density"), 0) or 0
        oldest = next((m["value"] for m in ch["metrics"] if m["key"] == "oldest_todo"), None)
        largest = next((m["value"] for m in ch["metrics"] if m["key"] == "largest_file"), 0) or 0
        todo = next((m["value"] for m in ch["metrics"] if m["key"] == "todo"), 0) or 0
        fixme = next((m["value"] for m in ch["metrics"] if m["key"] == "fixme"), 0) or 0
        if density > 3:
            add("code_health", "medium", "Сократите технический долг в коде",
                f"Плотность пометок — {density:.1f} TODO/FIXME на 1000 строк "
                f"({int(todo)} TODO и {int(fixme)} FIXME).",
                "Высокая плотность пометок означает отложенные решения, которые всплывают при доработках.",
                "Заведите задачи на самые старые пометки и удаляйте их вместе с исправлением.",
                [{"label": "TODO/FIXME на 1000 строк", "value": f"{density:.1f}", "url": url}], 20)
        if oldest and oldest > 365:
            add("code_health", "low", "Закройте застарелые TODO",
                f"Старейшая пометка живёт в коде {human_days(oldest)}.",
                "TODO старше года почти всегда означают потерянный контекст.",
                "Просмотрите старые пометки: либо исправьте, либо удалите как неактуальные.",
                [{"label": "Возраст старейшего TODO", "value": human_days(oldest), "url": url}], 15)
        if largest > 3000:
            add("code_health", "low", "Разбейте самый большой файл",
                f"Самый большой файл содержит {int(largest)} строк.",
                "Файлы такого размера трудно ревьюить и тестировать.",
                "Выделите независимые части в отдельные модули.",
                [{"label": "Самый большой файл", "value": f"{int(largest)} строк", "url": url}], 15)

    # нет данных -> действие, а не штраф
    for key, c in by_key.items():
        if c["score"] is None and key in ("security", "cicd"):
            recs.append({
                "id": f"{key}.nodata",
                "category": key,
                "priority": "info",
                "title": f"Откройте данные категории «{TITLES[key]}»",
                "problem": c["no_data_reason"] or "Данные категории недоступны.",
                "why": "Категория исключена из расчёта: Score посчитан по остальным категориям, "
                       "но оценка остаётся неполной.",
                "action": "Авторизуйтесь через Я ID и запустите анализ своего репозитория — "
                          "сервис запросит данные от вашего имени." if key == "security"
                          else "Выдайте сервису доступ к истории пайплайнов или запустите анализ "
                               "из личного кабинета после авторизации.",
                "evidence": [{"label": "Статус категории", "value": "нет данных", "url": None}],
                "expected_gain": 0.0,
            })

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    recs.sort(key=lambda r: (order[r["priority"]], -r["expected_gain"]))
    return recs


# --------------------------------------------------------------------------- сборка отчёта
def build_report(row):
    cats = []
    for key, scorer in SCORERS.items():
        res = scorer(row)
        cats.append({
            "key": key,
            "title": TITLES[key],
            "weight": WEIGHTS[key],
            "effective_weight": 0.0,
            **res,
        })

    covered = sum(c["weight"] for c in cats if c["score"] is not None)
    for c in cats:
        c["effective_weight"] = round(c["weight"] / covered, 4) if (covered and c["score"] is not None) else 0.0

    if covered == 0:
        total = None
    else:
        total = round(sum(c["score"] * c["weight"] for c in cats if c["score"] is not None) / covered, 1)

    order = ["security", "code_health", "activity", "documentation", "cicd", "issues"]
    cats.sort(key=lambda c: order.index(c["key"]))

    recs = build_recommendations(cats, row, total)

    errors = []
    try:
        for e in json.loads(row.get("collection.errors") or "[]"):
            errors.append({
                "category": e.get("category"),
                "source": e.get("source"),
                "code": e.get("code"),
                "message": (e.get("message") or "")[:400],
            })
    except Exception:
        pass

    strengths, risks = [], []
    for c in cats:
        for x in c["strengths"][:2]:
            strengths.append({"category": c["key"], "text": x})
        for x in c["weaknesses"][:2]:
            risks.append({"category": c["key"], "text": x})

    analyzed_at = s(row, "collection.collected_at") or NOW.isoformat()
    likes = f(row, "activity.likes.value") or 0
    no_data = [c["key"] for c in cats if c["score"] is None]

    summary_parts = []
    if total is not None:
        summary_parts.append(
            f"Repo Health Score {total:.0f} из 100 (оценка {grade(total)}), посчитан по "
            f"{len([c for c in cats if c['score'] is not None])} из 6 категорий "
            f"({covered * 100:.0f}% веса методики)."
        )
    best = max((c for c in cats if c["score"] is not None), key=lambda c: c["score"], default=None)
    worst = min((c for c in cats if c["score"] is not None), key=lambda c: c["score"], default=None)
    if best:
        summary_parts.append(f"Сильнее всего категория «{best['title']}» — {best['score']:.0f}/100.")
    if worst and worst is not best:
        summary_parts.append(f"Слабее всего «{worst['title']}» — {worst['score']:.0f}/100: {worst['summary'].split(': ', 1)[-1]}.")
    missing = [c for c in cats if c["status"] == "no_data"]
    na = [c for c in cats if c["status"] == "not_applicable"]
    if missing:
        summary_parts.append(
            "Нет данных: " + ", ".join(c["title"] for c in missing) +
            " — категории исключены из расчёта и не ухудшают Score."
        )
    if na:
        summary_parts.append("Не применимо: " + ", ".join(c["title"] for c in na) + ".")
    crit_rec = next((r for r in recs if r["priority"] in ("critical", "high")), None)
    if crit_rec:
        summary_parts.append(f"Первоочередное действие: {crit_rec['title']}.")

    return {
        "id": s(row, "repo.platform_id"),
        "full_path": s(row, "repo.full_path"),
        "owner": s(row, "repo.owner"),
        "name": s(row, "repo.name"),
        "url": s(row, "repo.url"),
        "description": s(row, "repo.description"),
        "visibility": s(row, "repo.visibility") or "public",
        "default_branch": s(row, "repo.default_branch"),
        "primary_language": s(row, "repo.primary_language"),
        "likes": likes,
        "likes_percentile": f(row, "activity.likes.percentile"),
        "last_activity_at": s(row, "activity.last_commit_at"),
        "analyzed_at": analyzed_at,
        "score": {
            "total": total,
            "grade": grade(total),
            "coverage": round(covered, 4),
            "formula_version": FORMULA_VERSION,
            "weights": WEIGHTS,
        },
        "categories": cats,
        "recommendations": recs,
        "strengths": strengths,
        "risks": risks,
        "no_data_categories": [c["key"] for c in cats if c["status"] == "no_data"],
        "not_applicable_categories": [c["key"] for c in cats if c["status"] == "not_applicable"],
        "summary": " ".join(summary_parts),
        "collection": {
            "collected_at": analyzed_at,
            "duration_ms": f(row, "collection.duration_ms"),
            "collector_version": s(row, "collection.collector_version"),
            "sources_used": {
                "git_clone": b(row, "collection.sources_used.git_clone"),
                "platform_api": b(row, "collection.sources_used.platform_api"),
                "platform_cli": b(row, "collection.sources_used.platform_cli"),
                "appsec_api": b(row, "collection.sources_used.appsec_api"),
            },
            "errors": errors,
        },
        "history": [{"analyzed_at": analyzed_at, "total": total}],
    }


def summarize(report, rank=None):
    return {
        "id": report["id"],
        "full_path": report["full_path"],
        "owner": report["owner"],
        "name": report["name"],
        "url": report["url"],
        "description": report["description"],
        "primary_language": report["primary_language"],
        "likes": report["likes"],
        "last_activity_at": report["last_activity_at"],
        "analyzed_at": report["analyzed_at"],
        "total_score": report["score"]["total"],
        "grade": report["score"]["grade"],
        "coverage": report["score"]["coverage"],
        "categories": {c["key"]: c["score"] for c in report["categories"]},
        "no_data_categories": report["no_data_categories"],
        "not_applicable_categories": report["not_applicable_categories"],
        "has_ci": next((m["value"] for c in report["categories"] if c["key"] == "cicd"
                        for m in c["metrics"] if m["key"] == "ci_config"), None) or False,
        "security_status": next(c["status"] for c in report["categories"] if c["key"] == "security"),
        "rank": rank,
    }


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=1500,
                    help="сколько репозиториев положить в mock-рейтинг")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    random.seed(20260922)
    featured = {"userver/userver", "annetutil/annet", "gravity-ui/aikit",
                "datalens/datalens", "datalens/datalens-us"}
    picked, others = [], []

    with open(args.csv, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            path = (row.get("repo.full_path") or "").strip()
            likes = f(row, "activity.likes.value") or 0
            if path in featured or likes > 0:
                picked.append(row)
            else:
                others.append(row)

    random.shuffle(others)
    rows = picked + others[: max(0, args.limit - len(picked))]
    print(f"строим отчёты: {len(rows)} репозиториев (из них с лайками/featured: {len(picked)})")

    reports = {}
    for row in rows:
        try:
            rep = build_report(row)
        except Exception as exc:  # noqa: BLE001
            print("skip", row.get("repo.full_path"), exc, file=sys.stderr)
            continue
        reports[rep["full_path"]] = rep

    ranked = sorted(
        (r for r in reports.values() if r["score"]["total"] is not None),
        key=lambda r: (-r["score"]["total"], -(r["likes"] or 0)),
    )
    summaries = []
    for i, rep in enumerate(ranked, start=1):
        summaries.append(summarize(rep, rank=i))
    for rep in reports.values():
        if rep["score"]["total"] is None:
            summaries.append(summarize(rep, rank=None))

    langs = {}
    for it in summaries:
        langs[it["primary_language"] or "—"] = langs.get(it["primary_language"] or "—", 0) + 1

    (out / "repos.json").write_text(json.dumps({
        "items": summaries,
        "total": len(summaries),
        "generated_at": NOW.isoformat(),
        "source": "repo_health_report.csv",
        "formula_version": FORMULA_VERSION,
    }, ensure_ascii=False), encoding="utf-8")

    # отчёты кладём по файлу на репозиторий: мок-клиент тянет только запрошенный
    rep_dir = out / "reports"
    if rep_dir.exists():
        for f_old in rep_dir.glob("*.json"):
            f_old.unlink()
    rep_dir.mkdir(parents=True, exist_ok=True)
    for path, rep in reports.items():
        fname = path.replace("/", "__") + ".json"
        (rep_dir / fname).write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")

    (out / "languages.json").write_text(json.dumps(
        [{"language": k, "count": v} for k, v in sorted(langs.items(), key=lambda kv: -kv[1])],
        ensure_ascii=False), encoding="utf-8")

    # витрина личного кабинета: профили разного качества
    def pick(pred, n):
        res = []
        for it in summaries:
            if pred(it) and it["full_path"] not in featured:
                res.append(it["full_path"])
            if len(res) >= n:
                break
        return res

    my = ["userver/userver", "annetutil/annet"]
    my += pick(lambda it: it["total_score"] is not None and it["total_score"] >= 60, 1)
    my += pick(lambda it: it["total_score"] is not None and 40 <= it["total_score"] < 55, 2)
    my += pick(lambda it: it["total_score"] is None, 1)
    my = [p for p in dict.fromkeys(my) if p in reports][:6]

    (out / "me.json").write_text(json.dumps({
        "user": {
            "id": "demo-user-1",
            "login": "demo-user",
            "display_name": "Demo User",
            "email": "demo-user@example.com",
            "avatar_url": None,
            "provider": "yandex_id",
        },
        "repos": [
            {**summarize(reports[p]),
             "role": "maintainer" if i % 2 == 0 else "owner",
             "visibility": reports[p]["visibility"],
             "last_analysis_at": reports[p]["analyzed_at"]}
            for i, p in enumerate(my)
        ],
    }, ensure_ascii=False), encoding="utf-8")

    stats = {
        "repos_total": len(summaries),
        "repos_scored": len(ranked),
        "median_score": round(sorted(r["score"]["total"] for r in ranked)[len(ranked) // 2], 1) if ranked else None,
        "no_data_security": sum(1 for it in summaries if it["security_status"] == "no_data"),
        "with_ci": sum(1 for it in summaries if it["has_ci"]),
        "last_run_at": NOW.isoformat(),
        "next_run_at": NOW.replace(hour=3, minute=0, second=0, microsecond=0).isoformat(),
        "schedule": "0 3 * * *",
    }
    (out / "stats.json").write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")

    for name in ("repos.json", "languages.json", "me.json", "stats.json"):
        size = (out / name).stat().st_size / 1024
        print(f"  {name}: {size:.0f} KB")
    print(f"  reports/: {len(reports)} файлов")
    print("готово:", out)


if __name__ == "__main__":
    main()
