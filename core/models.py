from django.db import models


class ValidatingModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop("_skip_validation", False)
        if not skip_validation:
            self.full_clean()

        return super().save(*args, **kwargs)
