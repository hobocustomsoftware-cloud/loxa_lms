from django.contrib import admin
from .models import*

@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type")          # removed created_at
    search_fields = ("name",)
    list_filter = ("type",)                         # removed created_at
    ordering = ("name",)


@admin.register(OrgMembership)
class OrgMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "user", "role")
    search_fields = ("org", "user", "role")
    list_filter = ("org",)
    ordering = ("org",)




# ---------- Catalog / Program / Level (optional admin) ----------
@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ("id","org","name","code")
    list_filter  = ("org",)
    search_fields = ("name","code")

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("id","catalog","title","code","kind","duration_months")
    list_filter  = ("catalog","kind")
    search_fields = ("title","code")

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("id","program","label","order")
    list_filter  = ("program",)
    ordering     = ("program","order","id")
    search_fields = ("label",)
