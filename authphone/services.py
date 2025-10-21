# authphone/services.py
import os, random
from dataclasses import dataclass

@dataclass
class SMSResult:
    ok: bool
    provider: str
    detail: str = ""

class SMSBackendBase:
    def send(self, phone: str, message: str) -> SMSResult: raise NotImplementedError

class DebugBackend(SMSBackendBase):
    def send(self, phone, message) -> SMSResult:
        print(f"[DEBUG SMS] to={phone} :: {message}")
        return SMSResult(True, "DEBUG")

class HTTPBackend(SMSBackendBase):
    # Generic aggregator via HTTP
    def __init__(self, url: str, headers: dict[str,str]):
        self.url, self.headers = url, headers
    def send(self, phone, message) -> SMSResult:
        # requests.post(...)  # (prod: implement)
        return SMSResult(True, "HTTP", "mocked")

def get_sms_backend() -> SMSBackendBase:
    mode = os.getenv("SMS_BACKEND", "DEBUG").upper()
    if mode == "HTTP":
        return HTTPBackend(
            url=os.getenv("SMS_HTTP_URL", ""),
            headers={ os.getenv("SMS_HTTP_KEY1",""): os.getenv("SMS_HTTP_VAL1","") }
        )
    return DebugBackend()

def generate_otp(n=6) -> str:
    return f"{random.randint(0, 10**n-1):0{n}d}"
