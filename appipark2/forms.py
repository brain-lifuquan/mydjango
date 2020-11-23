from django.forms import ModelForm
from . import models


class EquipmentForm(ModelForm):
    class Meta:
        model = models.Equipment
        fields = '__all__'


class VehicleForm(ModelForm):
    class Meta:
        model = models.Vehicle
        fields = '__all__'


class RouteForm(ModelForm):
    class Meta:
        model = models.Route
        fields = '__all__'

class LocationRecordForm(ModelForm):
    class Meta:
        model = models.LocationRecord
        fields = '__all__'
