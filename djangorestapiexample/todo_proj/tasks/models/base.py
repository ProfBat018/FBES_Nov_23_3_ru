from django.db import models

# BaseEntity
class TimeStampedModel(models.Model):
    """Абстрактная модель с временными метками - только схема БД."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
