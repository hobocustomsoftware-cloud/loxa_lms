# temp_utils.py (VS Code တွင် ပြင်ဆင်ရန်)

def get_oauth2_redirect_url(request, provider): 
    # ... code များ ...
    
    url = request.build_absolute_uri(callback_url) # type: ignore # ⬅️ URL ကို ဖန်တီးတဲ့လိုင်း
    
    # 🚨🚨🚨 ဒီ Log statement ကို အသစ်ထည့်ပါ 🚨🚨🚨
    print("FINAL REDIRECT URI CHECK:", url) 
    
    return url