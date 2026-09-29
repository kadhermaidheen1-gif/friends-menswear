import os
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import AsyncGroq
from supabase import create_client, Client

load_dotenv()

# ---------- Read config.txt ----------
def read_config():
    config = {}
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.txt")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    return config

CFG = read_config()

STORE_NAME = CFG.get("STORE_NAME", "Friends Menswear")
STORE_TAGLINE = CFG.get("STORE_TAGLINE", "Group Shirts & T-Shirts Available")
STORE_PHONE = CFG.get("STORE_PHONE", "+91 90927 17474")
STORE_WHATSAPP = CFG.get("STORE_WHATSAPP", "+91 90927 17474")
STORE_ADDRESS = CFG.get("STORE_ADDRESS", "Thidal South Street, 8GW8+CH6, Muthukulathur, Tamil Nadu 623704, India")
STORE_HOURS = CFG.get("STORE_HOURS", "Mon-Thu & Sat: 09:00 - 21:00 | Fri: 09:00 - 12:00, 14:30 - 21:00")
OWNER_NAME = CFG.get("OWNER_NAME", "Sikkandhar Ubaidullah")
STORE_CITY = CFG.get("STORE_CITY", "Mudukulathur")

GROQ_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

groq_client = AsyncGroq(api_key=GROQ_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

app = FastAPI(title=f"{STORE_NAME} API")

# ---------- System Prompts ----------
SYSTEM_PROMPT_EN = f"""You are the friendly virtual assistant for {STORE_NAME}, a menswear shop in Mudukulathur.

Your role:
- Answer customer questions warmly, clearly, and briefly (2-4 short sentences max).
- Help customers with sizing, product availability, pricing, and exchange policies.
- Never invent prices or stock. If unsure, ask the customer for their phone number so staff can call back.

Store information (source of truth):
- Name: {STORE_NAME}
- Tagline: {STORE_TAGLINE}
- Address: {STORE_ADDRESS}
- Phone: {STORE_PHONE}
- Hours: {STORE_HOURS}
- Owner: {OWNER_NAME}

What we sell:
- Formal shirts (cotton, linen)
- Casual shirts and t-shirts
- Formal trousers and chinos
- Jeans
- Ethnic wear (kurta, dhoti)
- Wedding and party wear
- Perfumes
- Group orders for weddings, corporates, and events

What we offer:
- Group and bulk orders welcome
- 7-day exchange policy on unused items with tags
- WhatsApp ordering available

Tone:
- Warm, professional, respectful. Never pushy.
- Use "Sir" or "Ma'am" when appropriate.
- Keep replies short — this is a chat, not an email.

Rules:
- Do NOT make up information.
- Do NOT discuss competitor shops.
- If asked about a specific product or price you don't know, ask for their phone number so staff can call back.
- Do NOT claim we offer products or services that are NOT explicitly listed above.
- If a customer asks for something we don't sell (blazers, suits, custom stitching, home delivery), politely say "I'm sorry Sir, we don't offer that" — do NOT offer to call them back just to seem helpful.
"""

SYSTEM_PROMPT_TA = f"""நீங்கள் {STORE_NAME} என்ற கோயம்புத்தூரில் உள்ள ஆண்கள் ஆடைக் கடையின் நட்பான மெய்நிகர் உதவியாளர்.

உங்கள் பணி:
- வாடிக்கையாளர் கேள்விகளுக்கு அன்பாக, தெளிவாக, சுருக்கமாக (2-4 வாக்கியங்கள்) பதில் சொல்லுங்கள்.
- அளவு, பொருள் கிடைக்கும் தன்மை, விலை, டெலிவரி, மாற்று கொள்கை ஆகியவற்றில் உதவுங்கள்.
- விலை அல்லது ஸ்டாக் பற்றி தெரியாதபோது கற்பனை செய்யாதீர்கள். வாடிக்கையாளரின் தொலைபேசி எண்ணைக் கேளுங்கள், ஊழியர்கள் திரும்ப அழைப்பார்கள்.

கடை தகவல்:
- பெயர்: {STORE_NAME}
- குறிக்கோள்: {STORE_TAGLINE}
- முகவரி: {STORE_ADDRESS}
- தொலைபேசி: {STORE_PHONE}
- நேரம்: {STORE_HOURS}
- உரிமையாளர்: {OWNER_NAME}

நாங்கள் விற்பனை செய்வது:
- முறையான சட்டைகள் (பருத்தி, லினன்)
- சாதாரண சட்டைகள், டி-ஷர்ட்கள்
- முறையான பேண்ட்கள், சினோஸ்
- ஜீன்ஸ்
- இன மரபு ஆடைகள் (குர்தா, வேட்டி)
- திருமண மற்றும் விருந்து ஆடைகள்
- குழு ஆர்டர்கள் — திருமணம், கார்ப்பரேட், நிகழ்வுகள்

நாங்கள் வழங்குவது:
- குழு மற்றும் மொத்த ஆர்டர்கள் வரவேற்கப்படுகின்றன
- 7 நாள் மாற்று கொள்கை (டேக் உள்ள பயன்படுத்தாத பொருட்கள்)
- வாட்ஸ்அப் ஆர்டர் வசதி

தொனி:
- அன்பான, மரியாதையான, தொழில்முறை.
- "ஐயா" அல்லது "அம்மா" என்று அழைக்கவும்.
- சுருக்கமாக பதில் சொல்லுங்கள்.

விதிகள்:
- தகவல் கற்பனை செய்யாதீர்கள்.
- போட்டி கடைகளைப் பற்றி பேசாதீர்கள்.
- தெரியாத பொருள்/விலை பற்றி கேட்டால், தொலைபேசி எண் கேளுங்கள்.
"""

# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str
    history: list = []
    lang: str = "en"  # "en" or "ta"

# ---------- Helpers ----------
def save_lead(name: str, phone: str, interest: str = "", lang: str = "en") -> bool:
    if supabase is None:
        return False
    try:
        supabase.table("menswear_leads").insert({
            "name": name,
            "phone": phone,
            "interest": interest,
            "lang": lang,
        }).execute()
        return True
    except Exception as e:
        print(f"[LEAD SAVE ERROR] {e}")
        return False

def extract_lead(text: str):
    t = text.lower()
    booking_words = ("book", "order", "buy", "interested", "call me", "visit",
                     "appointment", "தொடர்பு", "ஆர்டர்", "வாங்க")
    if not any(w in t for w in booking_words):
        return None

    phone_match = re.search(r"(\+?\d[\d\s\-]{8,14}\d)", text)
    phone = phone_match.group(1).strip() if phone_match else None

    name_match = re.search(
        r"(?:my name is|i am|this is|i'm|என் பெயர்|நான்)\s+([A-Za-z\u0B80-\u0BFF]+(?:\s+[A-Za-z\u0B80-\u0BFF]+)?)",
        text,
    )
    name = name_match.group(1).strip() if name_match else None

    if phone and name:
        return {"name": name, "phone": phone, "interest": "product inquiry"}
    return None

# ---------- API ----------
@app.post("/api/chat")
async def chat(req: ChatRequest):
    lang = req.lang if req.lang in ("en", "ta") else "en"
    system_prompt = SYSTEM_PROMPT_TA if lang == "ta" else SYSTEM_PROMPT_EN

    history = req.history or []
    if not history or history[0].get("role") != "system":
        history = [{"role": "system", "content": system_prompt}] + history
    else:
        # Replace system prompt to match current lang
        history[0] = {"role": "system", "content": system_prompt}

    history.append({"role": "user", "content": req.message})

    lead = extract_lead(req.message)
    if lead:
        saved = save_lead(lead["name"], lead["phone"], lead["interest"], lang)
        if saved:
            if lang == "ta":
                reply = (f"நன்றி {lead['name']}! உங்கள் விவரங்களை பதிவு செய்துவிட்டேன். "
                         f"எங்கள் குழு {lead['phone']} என்ற எண்ணுக்கு விரைவில் அழைக்கும்.")
            else:
                reply = (f"Thank you, {lead['name']}! I've noted your details. "
                         f"Our team will call you at {lead['phone']} shortly.")
            history.append({"role": "assistant", "content": reply})
            return {"reply": reply, "history": history[-10:], "lead_captured": True}

    try:
        response = await groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=history,
            temperature=0.7,
            max_tokens=400,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GROQ ERROR] {e}")
        if lang == "ta":
            reply = f"சிறிய தொழில்நுட்ப பிரச்சனை. {STORE_PHONE} என்ற எண்ணுக்கு அழைக்கவும்."
        else:
            reply = f"I'm having a small issue right now. Please call {STORE_PHONE}."

    history.append({"role": "assistant", "content": reply})
    return {"reply": reply, "history": history[-10:], "lead_captured": False}

@app.get("/api/info")
async def info():
    return {
        "store_name": STORE_NAME,
        "tagline": STORE_TAGLINE,
        "phone": STORE_PHONE,
        "whatsapp": STORE_WHATSAPP,
        "address": STORE_ADDRESS,
        "hours": STORE_HOURS,
        "owner": OWNER_NAME,
    }

# ---------- Serve frontend ----------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/style.css")
async def style_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"), media_type="text/css")

@app.get("/widget.js")
async def widget_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "widget.js"), media_type="application/javascript")

@app.get("/logo.png")
async def logo():
    return FileResponse(os.path.join(FRONTEND_DIR, "logo.png"), media_type="image/png")