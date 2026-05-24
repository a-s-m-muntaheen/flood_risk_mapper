from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Count, Avg, Min, Max
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json

from flood_zones.models import FloodZone
from risk_engine.model_service import score_vector, get_models, score_all_zones
from risk_engine.feature_pipeline import geometry_to_features
from risk_engine.serializers import FloodZoneSerializer


@api_view(['POST'])
def score_geometry(request):
    """
    POST /api/risk/score/
    Body: { "geometry": <GeoJSON polygon> }

    User draws an area on the React map,
    we return its flood risk score instantly.
    """
    try:
        geometry = request.data.get('geometry')
        if not geometry:
            return Response(
                {'error': 'geometry field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        raw, normalized, vector = geometry_to_features(geometry)
        result = score_vector(vector)

        return Response({
            'status':    'ok',
            'result':    result,
            'features':  raw,
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_zones(request):
    """
    GET /api/risk/zones/?level=high&limit=100

    Returns flood zones as GeoJSON FeatureCollection.
    Filtered by risk level if ?level= param given.
    """
    level  = request.query_params.get('level', None)
    limit  = int(request.query_params.get('limit', 200))
    min_score = float(request.query_params.get('min_score', 0))

    qs = FloodZone.objects.exclude(
        risk_score=0.0
    ).order_by('-risk_score')

    if level:
        qs = qs.filter(risk_level=level)
    if min_score:
        qs = qs.filter(risk_score__gte=min_score)

    qs = qs[:limit]

    features = []
    for zone in qs:
        features.append({
            'type': 'Feature',
            'geometry': json.loads(zone.geometry.geojson),
            'properties': {
                'id':           zone.id,
                'name':         zone.name,
                'risk_score':   round(zone.risk_score, 4),
                'risk_level':   zone.risk_level,
                'elevation_m':  zone.avg_elevation_m,
                'rainfall_mm':  zone.avg_rainfall_mm,
                'slope_deg':    zone.avg_slope_degrees,
            }
        })

    return Response({
        'type':     'FeatureCollection',
        'count':    len(features),
        'features': features,
    })


@api_view(['GET'])
def zone_detail(request, pk):
    """GET /api/risk/zones/<id>/"""
    try:
        zone = FloodZone.objects.get(pk=pk)
        return Response(FloodZoneSerializer(zone).data)
    except FloodZone.DoesNotExist:
        return Response(
            {'error': 'Zone not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def risk_stats(request):
    """
    GET /api/risk/stats/
    Returns summary statistics across all scored zones.
    """
    stats = FloodZone.objects.exclude(
        risk_score=0.0
    ).aggregate(
        total=Count('id'),
        avg_score=Avg('risk_score'),
        min_score=Min('risk_score'),
        max_score=Max('risk_score'),
    )

    level_counts = dict(
        FloodZone.objects.exclude(risk_score=0.0)
        .values('risk_level')
        .annotate(count=Count('id'))
        .values_list('risk_level', 'count')
    )

    return Response({
        'total_zones':   stats['total'],
        'avg_risk':      round(stats['avg_score'] or 0, 4),
        'min_risk':      round(stats['min_score'] or 0, 4),
        'max_risk':      round(stats['max_score'] or 0, 4),
        'by_level': {
            'low':    level_counts.get('low',    0),
            'medium': level_counts.get('medium', 0),
            'high':   level_counts.get('high',   0),
        }
    })


@api_view(['GET'])
def model_info(request):
    """GET /api/risk/model-info/ — returns model metadata."""
    try:
        _, _, meta = get_models()
        return Response(meta)
    except FileNotFoundError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )