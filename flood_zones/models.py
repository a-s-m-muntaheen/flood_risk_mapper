from django.contrib.gis.db import models as gis_models
from django.db import models


class District(models.Model):
    """
    Administrative boundary — upazila level.
    Loaded from the HUMDATA shapefile.
    """
    name        = models.CharField(max_length=100)
    district    = models.CharField(max_length=100)
    division    = models.CharField(max_length=100)
    area_sqkm   = models.FloatField(null=True, blank=True)
    geometry    = gis_models.MultiPolygonField(srid=4326)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.district}"


class ElevationPoint(models.Model):
    """
    Sampled elevation points from SRTM DEM.
    We store a grid of points rather than the full raster.
    """
    location        = gis_models.PointField(srid=4326)
    elevation_m     = models.FloatField()
    slope_degrees   = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            gis_models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"Elev {self.elevation_m}m at {self.location}"


class RainfallRecord(models.Model):
    """
    Historical rainfall records per location and month.
    """
    MONTHS = [(i, m) for i, m in enumerate(
        ['Jan','Feb','Mar','Apr','May','Jun',
         'Jul','Aug','Sep','Oct','Nov','Dec'], 1)]

    location        = gis_models.PointField(srid=4326)
    month           = models.IntegerField(choices=MONTHS)
    year            = models.IntegerField()
    rainfall_mm     = models.FloatField()
    station_name    = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['year', 'month']

    def __str__(self):
        return f"{self.station_name} {self.year}-{self.month}: {self.rainfall_mm}mm"


class FloodZone(models.Model):
    """
    Core model — a geographic zone with its computed flood risk score.
    This is what the AI model writes to and the React map reads from.
    """
    RISK_LEVELS = [
        ('low',    'Low risk'),
        ('medium', 'Medium risk'),
        ('high',   'High risk'),
    ]

    name            = models.CharField(max_length=200)
    geometry        = gis_models.PolygonField(srid=4326)
    risk_score      = models.FloatField(default=0.0)   # 0.0 to 1.0
    risk_level      = models.CharField(
                        max_length=10,
                        choices=RISK_LEVELS,
                        default='low')

    # Features used by the AI model
    avg_elevation_m     = models.FloatField(null=True, blank=True)
    avg_slope_degrees   = models.FloatField(null=True, blank=True)
    avg_rainfall_mm     = models.FloatField(null=True, blank=True)
    distance_to_river_m = models.FloatField(null=True, blank=True)
    land_use_code       = models.IntegerField(null=True, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-risk_score']

    def __str__(self):
        return f"{self.name} — {self.risk_level} ({self.risk_score:.2f})"


class RiverNetwork(models.Model):
    """
    Major rivers in Bangladesh from OSM.
    Used to compute distance-to-river feature.
    """
    name        = models.CharField(max_length=200, blank=True)
    geometry    = gis_models.LineStringField(srid=4326)

    def __str__(self):
        return self.name or "Unnamed river"