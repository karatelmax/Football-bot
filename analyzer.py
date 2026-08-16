from typing import Dict, List, Optional, Tuple
import math


def poisson_probability(lmbda: float, k: int) -> float:
    """P(X = k) для Poisson"""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)


def remaining_goals_probs(current_home: int, current_away: int, 
                          expected_home: float, expected_away: float,
                          minutes_played: int) -> Dict:
    """
    Оценка вероятностей оставшихся голов.
    expected_home/away — ожидаемые голы за весь матч (из статистики команд).
    """
    if minutes_played <= 0:
        minutes_played = 1
    if minutes_played >= 90:
        remaining_factor = 0.05  # добавленное время
    else:
        remaining_factor = (90 - minutes_played) / 90

    lambda_home = expected_home * remaining_factor
    lambda_away = expected_away * remaining_factor

    probs = {
        "over_0_5": 1 - poisson_probability(lambda_home + lambda_away, 0),
        "over_1_5": 1 - (poisson_probability(lambda_home + lambda_away, 0) + 
                         poisson_probability(lambda_home + lambda_away, 1)),
        "btts_yes": (1 - poisson_probability(lambda_home, 0)) * (1 - poisson_probability(lambda_away, 0)),
        "home_scores": 1 - poisson_probability(lambda_home, 0),
        "away_scores": 1 - poisson_probability(lambda_away, 0),
        "lambda_home": round(lambda_home, 2),
        "lambda_away": round(lambda_away, 2),
        "remaining_minutes": max(0, 90 - minutes_played)
    }
    return probs


def analyze_live_match(fixture: Dict, stats: List[Dict] = None) -> str:
    """
    Генерирует текстовый анализ live-матча.
    """
    teams = fixture.get("teams", {})
    goals = fixture.get("goals", {})
    league = fixture.get("league", {})
    status = fixture.get("fixture", {}).get("status", {})

    home_name = teams.get("home", {}).get("name", "Home")
    away_name = teams.get("away", {}).get("name", "Away")
    home_goals = goals.get("home") or 0
    away_goals = goals.get("away") or 0
    elapsed = status.get("elapsed") or 0
    short_status = status.get("short", "")

    text = f"⚽ <b>{home_name} {home_goals}:{away_goals} {away_name}</b>\n"
    text += f"🏆 {league.get('name', '')} ({league.get('country', '')})\n"
    text += f"⏱ {elapsed}' | Статус: {short_status}\n\n"

    total_goals = home_goals + away_goals

    if elapsed < 70:
        if total_goals == 0:
            text += "📊 <b>Анализ:</b>\n"
            text += "• Матч пока без голов. Вероятность хотя бы одного гола до конца высокая.\n"
            text += "• Смотри на Over 1.5 / Over 2.5 и BTTS в зависимости от команд.\n"
        elif total_goals == 1:
            text += "📊 <b>Анализ:</b>\n"
            text += "• Один гол уже есть. Хороший момент смотреть на Over 2.5 и BTTS.\n"
        elif total_goals >= 2:
            text += "📊 <b>Анализ:</b>\n"
            text += "• Уже много голов. Осторожно с тоталами — можно смотреть Under оставшихся.\n"
    else:
        text += "📊 <b>Анализ (конец матча):</b>\n"
        if total_goals <= 1:
            text += "• Мало голов. Возможны поздние голы, но вероятность ниже.\n"
        else:
            text += "• Голы уже были. Фокус на точных рынках (точный счёт, next goal).\n"

    if stats:
        text += "\n📈 <b>Статистика матча:</b>\n"
        for team_stat in stats:
            team_name = team_stat.get("team", {}).get("name", "")
            statistics = team_stat.get("statistics", [])
            shots = next((s["value"] for s in statistics if s["type"] == "Total Shots"), None)
            shots_on = next((s["value"] for s in statistics if s["type"] == "Shots on Goal"), None)
            possession = next((s["value"] for s in statistics if s["type"] == "Ball Possession"), None)
            if shots is not None:
                text += f"• {team_name}: удары {shots}"
                if shots_on is not None:
                    text += f" (в створ {shots_on})"
                if possession:
                    text += f", владение {possession}"
                text += "\n"

    text += "\n⚠️ Это базовая статистическая оценка. Не финансовый совет."
    return text


def simple_value_hint(home_goals: int, away_goals: int
