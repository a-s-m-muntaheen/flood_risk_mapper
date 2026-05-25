"""
LLM service using Ollama (local, free).
Answers natural language questions about flood risk
using real data from PostGIS as context.
"""
import requests
import json
from django.db.models import Avg, Count
from flood_zones.models import FloodZone, RainfallRecord

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

def get_area_context(area_name: str) -> dict:
    """
    Build a context dict from PostGIS for a given area name.
    Used to ground the LLM answer in real data.
    """
    # Try matching zone names containing the area
    matching_zones = FloodZone.objects.filter(
        name__icontains=area_name
    ).exclude(risk_score=0.0)

    if not matching_zones.exists():
        # Fallback — use all zones and mention no match
        matching_zones = FloodZone.objects.exclude(
            risk_score=0.0
        ).order_by('-risk_score')[:20]
        matched = False
    else:
        matched = True

    stats = matching_zones.aggregate(
        avg_score    = Avg('risk_score'),
        avg_elev     = Avg('avg_elevation_m'),
        avg_rain     = Avg('avg_rainfall_mm'),
        total_zones  = Count('id'),
    )

    level_counts = dict(
        matching_zones
        .values('risk_level')
        .annotate(c=Count('id'))
        .values_list('risk_level', 'c')
    )

    # Get peak monsoon rainfall near this area
    rain_records = RainfallRecord.objects.filter(
        month__in=[6, 7, 8, 9],
        station_name__icontains=area_name,
    )
    if not rain_records.exists():
        rain_records = RainfallRecord.objects.filter(
            month__in=[6, 7, 8, 9]
        )
    rain_avg = rain_records.aggregate(
        avg=Avg('rainfall_mm')
    )['avg'] or 0

    return {
        'area_name':     area_name,
        'matched':       matched,
        'total_zones':   stats['total_zones'] or 0,
        'avg_risk':      round(stats['avg_score']   or 0, 3),
        'avg_elevation': round(stats['avg_elev']    or 0, 1),
        'avg_rainfall':  round(stats['avg_rain']    or 0, 1),
        'monsoon_rain':  round(rain_avg, 1),
        'high_zones':    level_counts.get('high',   0),
        'medium_zones':  level_counts.get('medium', 0),
        'low_zones':     level_counts.get('low',    0),
    }


def build_system_prompt() -> str:
    return """You are a flood risk analyst for Bangladesh.
You have access to real spatial data from a PostGIS database
covering elevation, rainfall, and AI-computed flood risk scores
across the entire country.

Your role:
- Answer questions about flood risk clearly and concisely
- Always ground your answers in the provided data context
- Give practical safety advice when relevant
- Mention specific numbers from the context when available
- Keep answers under 120 words
- Never make up data not in the context

Bangladesh context you must know:
- Monsoon season: June to September
- Most flood-prone: coastal areas, river deltas, low-elevation zones
- Risk levels: low (0-35%), medium (35-65%), high (65-100%)
- Major rivers: Padma, Meghna, Jamuna, Brahmaputra
- Dhaka elevation: ~4-8m above sea level"""


def build_user_prompt(question: str, context: dict) -> str:
    matched_str = (
        f"Data found for '{context['area_name']}'"
        if context['matched']
        else f"No exact match for '{context['area_name']}' — using national average"
    )

    return f"""Question: {question}

Spatial data context ({matched_str}):
- Area: {context['area_name']}
- Zones analysed: {context['total_zones']}
- Average flood risk score: {context['avg_risk'] * 100:.1f}%
- Average elevation: {context['avg_elevation']}m
- Average monsoon rainfall: {context['monsoon_rain']}mm/month
- Risk breakdown: {context['high_zones']} high-risk, {context['medium_zones']} medium-risk, {context['low_zones']} low-risk zones

Answer the question using this data. Be specific and practical."""


def ask_flood_question(question: str) -> dict:
    """
    Main entry point — takes a natural language question,
    extracts area name, fetches PostGIS context,
    calls Ollama, returns structured response.
    """
    # Simple area extraction — look for known BD place names
    BD_PLACES = [
        'dhaka', 'mirpur', 'chittagong', 'sylhet', 'rajshahi',
        'khulna', 'barishal', 'mymensingh', 'comilla', 'rangpur',
        'jessore', 'faridpur', 'tangail', 'bogra', 'dinajpur',
        'cox\'s bazar', 'noakhali', 'narsingdi', 'gazipur',
    ]
    question_lower = question.lower()
    detected_area  = 'Bangladesh'
    for place in BD_PLACES:
        if place in question_lower:
            detected_area = place.title()
            break

    context = get_area_context(detected_area)
    system  = build_system_prompt()
    prompt  = build_user_prompt(question, context)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model':  OLLAMA_MODEL,
                'prompt': prompt,
                'system': system,
                'stream': False,
                'options': {
                    'temperature': 0.3,
                    'num_predict': 200,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        answer = response.json().get('response', '').strip()

    except requests.exceptions.ConnectionError:
        answer = (
            "Ollama is not running. Start it with: ollama serve\n"
            f"Based on database data: {detected_area} has an average "
            f"flood risk of {context['avg_risk']*100:.1f}% with "
            f"{context['high_zones']} high-risk zones."
        )
    except Exception as e:
        answer = f"Error contacting LLM: {str(e)}"

    return {
        'question':      question,
        'answer':        answer,
        'area_detected': detected_area,
        'context':       context,
        'model':         OLLAMA_MODEL,
    }