# api/utils_autofill.py
import re, unicodedata
from django.utils.text import slugify

def smart_slug(text: str, maxlen: int = 40) -> str:
    """
    Safer slugify that keeps ascii only but works with Myanmar too by fallback.
    """
    base = slugify(text)
    if not base:
        # fallback: normalize & strip spaces/puncts -> ascii
        t = unicodedata.normalize("NFKD", text)
        t = re.sub(r"[^\w\s-]", "", t).strip().lower()
        base = re.sub(r"[-\s]+", "-", t)
    return base[:maxlen] or "item"

def next_code_for_org(model_cls, org, base: str) -> str:
    """
    Make code unique within (org, code). If 'math-101' exists, returns 'math-101-001', etc.
    """
    base = base.strip("-")
    # exact free?
    exists = model_cls.objects.filter(org=org, code=base).exists()
    if not exists:
        return base
    # find suffix
    i = 1
    while True:
        candidate = f"{base}-{i:03d}"
        if not model_cls.objects.filter(org=org, code=candidate).exists():
            return candidate
        i += 1


