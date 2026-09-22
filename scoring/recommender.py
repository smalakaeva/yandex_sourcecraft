class SourceCraftRecommendationEngine:
    def __init__(self):
        # Приоритизированный список: от Critical до Low
        self.rules = [
            # ================= 1. SECURITY =================
            {
                "category": "Security",
                "priority": "Критический",
                "condition": lambda r: str(r.get('security.defect_groups_by_severity', '')).upper() in ['CRITICAL',
                                                                                                        'HIGH'],
                "problem": "AppSec SourceCraft обнаружил уязвимости со статусом CRITICAL или HIGH.",
                "importance": "Уязвимости в коде или зависимостях ведут к прямому риску взлома.",
                "action": "Срочно изучите отчет AppSec и обновите уязвимые пакеты.",
                "impact": "Устранение критических дефектов вернет основные баллы в категории Security."
            },
            {
                "category": "Security",
                "priority": "Высокий",
                "condition": lambda r: r.get('security.oldest_open_defect_group_age_days', 0) > 30,
                "problem": "Обнаружены открытые дефекты безопасности старше 30 дней.",
                "importance": "Игнорирование уязвимостей увеличивает окно возможностей для атак.",
                "action": "Проведите триаж старых уязвимостей: закройте их или отметьте как ложные срабатывания (RESOLVED_FP).",
                "impact": "Снизит штраф за возраст открытых дефектов."
            },
            {
                "category": "Security",
                "priority": "Средний",
                "condition": lambda r: r.get('security.has_security_policy', False) == False,
                "problem": "Отсутствует файл политики безопасности (SECURITY.md).",
                "importance": "Пользователи не знают, как безопасно сообщить вам о найденных багах.",
                "action": "Добавьте SECURITY.md с инструкцией по репорту уязвимостей.",
                "impact": "Повысит оценку применения практик безопасной разработки."
            },

            # ================= 2. CI/CD =================
            {
                "category": "CI/CD",
                "priority": "Высокий",
                "condition": lambda r: r.get('cicd.has_ci_config', False) == False,
                "problem": "В проекте отсутствует конфигурация CI-пайплайна.",
                "importance": "Без настроенного CI невозможно автоматизировать сборку и тестирование.",
                "action": "Добавьте конфигурационный файл пайплайна (например, .gitlab-ci.yml).",
                "impact": "Разблокирует категорию CI/CD для начисления баллов."
            },
            {
                "category": "CI/CD",
                "priority": "Высокий",
                "condition": lambda r: r.get('cicd.branch_protection_enabled', False) == False,
                "problem": "Защита основных веток (Branch Protection) отключена.",
                "importance": "Любой разработчик может запушить сломанный код напрямую в default-ветку.",
                "action": "Включите защиту веток в настройках репозитория (требование code review).",
                "impact": "Существенно улучшит оценку надежности CI/CD."
            },
            {
                "category": "CI/CD",
                "priority": "Средний",
                "condition": lambda r: r.get('cicd.success_rate_30d', 1.0) != -1.0 and r.get('cicd.success_rate_30d',
                                                                                             1.0) < 0.8,
                "problem": "Доля успешных пайплайнов за последние 30 дней ниже 80%.",
                "importance": "Нестабильные сборки (flaky tests, ошибки среды) блокируют доставку новых фичей.",
                "action": "Стабилизируйте падающие шаги пайплайна и исправьте нестабильные тесты.",
                "impact": "Напрямую повысит метрику cicd.success_rate_30d_score."
            },
            {
                "category": "CI/CD",
                "priority": "Средний",
                "condition": lambda r: r.get('cicd.has_test_stage', False) == False and r.get('cicd.has_ci_config',
                                                                                              False) == True,
                "problem": "В CI-пайплайне не настроен этап тестирования (test stage).",
                "importance": "Сборка кода без прогона автотестов не гарантирует его работоспособность.",
                "action": "Добавьте шаг запуска unit/интеграционных тестов в ваш CI-конфиг.",
                "impact": "Повысит балл за полноту конвейера."
            },

            # ================= 3. DOCUMENTATION =================
            {
                "category": "Documentation",
                "priority": "Высокий",
                "condition": lambda r: r.get('documentation.has_readme', False) == False,
                "problem": "Отсутствует файл README.",
                "importance": "README — точка входа для понимания архитектуры, локального запуска и сборки проекта.",
                "action": "Создайте README.md с подробным описанием.",
                "impact": "Значительно повысит оценку в категории документации."
            },
            {
                "category": "Documentation",
                "priority": "Низкий",
                "condition": lambda r: r.get('documentation.has_readme', False) == True and r.get(
                    'documentation.readme_length_chars', 1000) < 300,
                "problem": "Файл README слишком короткий (менее 300 символов).",
                "importance": "Короткий README обычно не содержит инструкций по сборке и запуску.",
                "action": "Дополните README разделами 'Getting Started', 'Prerequisites' и 'Installation'.",
                "impact": "Повысит качество оценки документации."
            },
            {
                "category": "Documentation",
                "priority": "Высокий",
                "condition": lambda r: r.get('documentation.has_license', False) == False,
                "problem": "В проекте не указана лицензия.",
                "importance": "Без явной лицензии открытый код не может легально использоваться другими командами.",
                "action": "Добавьте файл LICENSE (например, Apache-2.0 или MIT).",
                "impact": "Улучшит показатель применения лучших практик (Best Practices)."
            },
            {
                "category": "Documentation",
                "priority": "Средний",
                "condition": lambda r: r.get('documentation.has_contributing', False) == False,
                "problem": "Отсутствует файл CONTRIBUTING.",
                "importance": "Потенциальные контрибьюторы не знают ваших правил написания кода и создания PR.",
                "action": "Добавьте файл CONTRIBUTING.md с правилами работы над проектом.",
                "impact": "Улучшит скоринг по стандартам Open Source."
            },

            # ================= 4. ISSUES =================
            {
                "category": "Issues",
                "priority": "Высокий",
                "condition": lambda r: r.get('issues.unanswered_open_count', 0) > 3,
                "problem": "Обнаружены открытые задачи (issues) без ответов мейнтейнеров.",
                "importance": "Игнорирование баг-репортов демотивирует комьюнити и снижает активность.",
                "action": "Проведите первичный триаж: ответьте пользователям, запросите логи или закройте тикеты.",
                "impact": "Улучшит метрики скорости реакции мейнтейнеров."
            },
            {
                "category": "Issues",
                "priority": "Средний",
                "condition": lambda r: r.get('issues.avg_time_to_first_response_hours', 0) > 72,
                "problem": "Среднее время первого ответа на Issue превышает 3 дня (72 часа).",
                "importance": "Медленная реакция замедляет цикл исправления багов.",
                "action": "Настройте систему уведомлений для оперативной реакции на новые Issues.",
                "impact": "Снизит штраф за задержки в обработке багов."
            },
            {
                "category": "Issues",
                "priority": "Низкий",
                "condition": lambda r: r.get('issues.stale_open_count', 0) > 5,
                "problem": "Скопилось много зависших (stale) открытых задач.",
                "importance": "Накопление старых тикетов превращает бэклог в свалку.",
                "action": "Закройте неактуальные задачи или переведите их в статус 'Отложено'.",
                "impact": "Очистит метрику 'stale issues' и повысит Health Score."
            },

            # ================= 5. ACTIVITY =================
            {
                "category": "Activity",
                "priority": "Высокий",
                "condition": lambda r: r.get('activity.bus_factor_top1_share_365d', 0) > 0.85,
                "problem": "Риск Bus Factor: один разработчик вносит более 85% коммитов за год.",
                "importance": "Если ключевой мейнтейнер покинет проект, поддержка полностью остановится.",
                "action": "Распределяйте задачи между участниками команды, привлекайте новых контрибьюторов.",
                "impact": "Улучшит баланс активности и повысит устойчивость репозитория."
            },
            {
                "category": "Activity",
                "priority": "Средний",
                "condition": lambda r: r.get('activity.last_commit_at_days_ago', 0) > 90,
                "problem": "Проект не обновлялся более 3 месяцев.",
                "importance": "Отсутствие активности сигнализирует пользователям о том, что проект заброшен.",
                "action": "Смержите накопившиеся PR или выпустите техническое обновление зависимостей.",
                "impact": "Повысит Health Score активности репозитория."
            },

            # ================= 6. CODE HEALTH =================
            {
                "category": "Code Health",
                "priority": "Средний",
                "condition": lambda r: r.get('code_health.largest_file_lines', 0) > 1500,
                "problem": "В проекте обнаружены огромные монолитные файлы (более 1500 строк).",
                "importance": "Такие файлы крайне тяжело ревьюить, тестировать и поддерживать.",
                "action": "Разбейте логику крупного файла на мелкие модули/классы.",
                "impact": "Снизит штраф за технический долг и сложность."
            },
            {
                "category": "Code Health",
                "priority": "Низкий",
                "condition": lambda r: r.get('code_health.oldest_todo_age_days', 0) > 180,
                "problem": "В коде присутствуют комментарии TODO/FIXME старше полугода.",
                "importance": "Забытые TODO свидетельствуют о неконтролируемом росте технического долга.",
                "action": "Удалите неактуальные TODO, а требующие внимания перенесите в трекер задач.",
                "impact": "Улучшит метрики чистоты кода (Maintainability)."
            },
            {
                "category": "Code Health",
                "priority": "Высокий",
                "condition": lambda r: r.get('code_health.hack_count', 0) > 0,
                "problem": "В коде обнаружены маркеры костылей (HACK).",
                "importance": "HACK-решения хрупкие и часто ломаются при обновлениях.",
                "action": "Проведите рефакторинг участков кода, отмеченных как HACK.",
                "impact": "Повысит оценку надежности кодовой базы."
            }
        ]

    def generate_recommendations(self, row_data):
        active_recs = []
        for rule in self.rules:
            try:
                if rule["condition"](row_data):
                    clean_rule = {
                        "category": rule["category"],
                        "priority": rule["priority"],
                        "problem": rule["problem"],
                        "importance": rule["importance"],
                        "action": rule["action"],
                        "impact": rule["impact"]
                    }

                    # Динамическая подстановка значений
                    if "зависших (stale)" in clean_rule["problem"] and 'issues.stale_open_count' in row_data:
                        clean_rule[
                            "problem"] = f"Обнаружено {int(row_data['issues.stale_open_count'])} зависших (stale) открытых задач."

                    if "без ответов" in clean_rule["problem"] and 'issues.unanswered_open_count' in row_data:
                        clean_rule[
                            "problem"] = f"Обнаружено {int(row_data['issues.unanswered_open_count'])} открытых задач без ответов мейнтейнеров."

                    if "Bus Factor" in clean_rule["problem"] and 'activity.bus_factor_top1_share_365d' in row_data:
                        share = round(row_data['activity.bus_factor_top1_share_365d'] * 100)
                        clean_rule["problem"] = f"Риск Bus Factor: один разработчик вносит {share}% коммитов за год."

                    active_recs.append(clean_rule)
            except Exception:
                pass

        return active_recs