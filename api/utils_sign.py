from django.core import signing
SIGNER = signing.TimestampSigner(salt="asset-sign")

def sign_path(path:str, max_age_seconds:int=3600):
    # caller keeps the signed value, ProtectedMedia will check TTL
    return SIGNER.sign(path)
