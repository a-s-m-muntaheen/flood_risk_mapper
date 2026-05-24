from rest_framework import serializers
from flood_zones.models import FloodZone


class FloodZoneSerializer(serializers.ModelSerializer):
    geometry = serializers.SerializerMethodField()

    class Meta:
        model  = FloodZone
        fields = [
            'id', 'name', 'geometry',
            'risk_score', 'risk_level',
            'avg_elevation_m', 'avg_slope_degrees',
            'avg_rainfall_mm', 'distance_to_river_m',
            'land_use_code',
        ]

    def get_geometry(self, obj):
        import json
        return json.loads(obj.geometry.geojson)


class FloodZoneGeoSerializer(serializers.ModelSerializer):
    """
    Returns full GeoJSON Feature format —
    ready to drop into Leaflet directly.
    """
    class Meta:
        model  = FloodZone
        fields = ['id', 'name', 'risk_score', 'risk_level']