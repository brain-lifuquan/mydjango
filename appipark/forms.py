from django.forms import ModelForm

from . import models


class ScaleTypeForm(ModelForm):
    class Meta:
        model = models.ScaleType
        fields = '__all__'


class ProgramForm(ModelForm):
    class Meta:
        model = models.Program
        fields = ['name', 'scale_type']


class EquipmentForm(ModelForm):
    class Meta:
        model = models.Equipment
        fields = '__all__'
