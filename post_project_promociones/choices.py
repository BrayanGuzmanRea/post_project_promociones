from django.db import models

class EstadoEntidades(models.IntegerChoices): 
    ACTIVO = 1, "Activo" 
    DE_BAJA = 9, "De baja"