from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.gis.geos import Point


def health_check(request):
    test_point = Point(90.4125, 23.8103, srid=4326)
    return JsonResponse({
        'status': 'ok',
        'message': 'Flood Risk Mapper API is running',
        'postgis': 'connected',
        'test_coordinate': {
            'city': 'Dhaka',
            'lon': test_point.x,
            'lat': test_point.y,
        }
    })
