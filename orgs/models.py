from django.conf import settings
from django.db import models
from django.utils.text import slugify

class Org(models.Model):
    TYPE = [("KG","KG"),("UNI","University"),("CERT","Certification")]
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE, default="KG")
    def __str__(self): return f"{self.name} ({self.type})"

class OrgMembership(models.Model):
    ROLE = [("ORG_ADMIN","ORG_ADMIN"),("TEACHER","TEACHER"),
            ("STUDENT","STUDENT"),("PARENT","PARENT"),("MODERATOR","MODERATOR")]
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE)
    class Meta:
        unique_together = [("org","user","role")]




class Catalog(models.Model):
    org  = models.ForeignKey("orgs.Org", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, blank=True, default="")
    class Meta:
        unique_together = [("org","name")]
    def save(self, *a, **kw):
        if not self.code:
            self.code = slugify(self.name)[:50] or "catalog"
        return super().save(*a, **kw)
    def __str__(self): return f"{self.org} / {self.name}"

class Program(models.Model):
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE, related_name="programs")
    title   = models.CharField(max_length=200)
    code    = models.CharField(max_length=50, blank=True, default="")
    kind    = models.CharField(max_length=30, blank=True)     # cert/degree/basic...
    duration_months = models.PositiveIntegerField(default=0)  # for certs
    class Meta:
        unique_together = [("catalog","code")]
    def save(self, *a, **kw):
        if not self.code:
            self.code = slugify(self.title)[:50] or "program"
        return super().save(*a, **kw)
    def __str__(self): return f"{self.catalog} / {self.title}"

class Level(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="levels")
    label   = models.CharField(max_length=50)     # Year-1, Grade-1, Month-1, Sem-1...
    order   = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = [("program","label")]
        ordering = ["order","id"]
    def __str__(self): return f"{self.program} / {self.label}"