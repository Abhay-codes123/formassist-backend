from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv
from middleware.auth import verify_token

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

router = APIRouter(prefix="/ai", tags=["AI"])

# Models
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"

class CVRequest(BaseModel):
    name: str
    role: str
    mobile: str
    email: Optional[str] = ""
    city: Optional[str] = ""
    about: Optional[str] = ""
    education: Optional[str] = ""
    skills: Optional[str] = ""
    experience: Optional[str] = ""
    projects: Optional[str] = ""
    template: Optional[str] = "classic"

class LetterRequest(BaseModel):
    type: str
    name: str
    to: str
    place: Optional[str] = ""
    details: Optional[str] = ""
    language: Optional[str] = "en"

class DocumentRequest(BaseModel):
    image_base64: str
    filename: Optional[str] = ""

class FormAuditRequest(BaseModel):
    url: Optional[str] = ""
    name: Optional[str] = ""
    mobile: Optional[str] = ""
    aadhar: Optional[str] = ""
    pan: Optional[str] = ""

class FormAnalyzeRequest(BaseModel):
    url: str
    user_profile: Optional[dict] = {}

def get_lang_name(lang):
    return {"en": "English", "hi": "Hindi", "mr": "Marathi"}.get(lang, "English")

# AI CHAT
@router.post("/chat")
async def ai_chat(req: ChatRequest):
    try:
        if not GEMINI_API_KEY:
            return get_fallback_chat(req.message, req.language)
        
        lang = get_lang_name(req.language)
        prompt = f"""You are FormAssist AI, an expert assistant for Indian government forms, 
        schemes, documents, CV building, and application letters.
        Answer in {lang} language. Be helpful, concise, and accurate.
        Focus on Indian government services, schemes like PM Kisan, Ayushman Bharat, 
        passport, Aadhar, PAN, scholarships, and job applications.
        
        User question: {req.message}"""
        
        response = model.generate_content(prompt)
        return {"success": True, "reply": response.text}
    except Exception as e:
        return get_fallback_chat(req.message, req.language)

def get_fallback_chat(message, lang):
    msg = message.lower()
    replies = {
        "passport": "For Passport: Visit passportindia.gov.in. Documents needed: Aadhar, PAN, Address proof, DOB certificate. Fee: Normal ₹1500, Tatkal ₹3500.",
        "kisan": "PM Kisan Samman Nidhi: ₹6,000/year for farmers in 3 installments. Apply at pmkisan.gov.in with Aadhar, land records, bank passbook.",
        "ayushman": "Ayushman Bharat: Free health cover up to ₹5 Lakh/year. Check eligibility at pmjay.gov.in. Helpline: 14555.",
        "aadhar": "Aadhar: Apply/Update at uidai.gov.in or nearest Aadhar center. Helpline: 1947.",
        "pan": "PAN Card: Apply at tin-nsdl.com or utiitsl.com. Documents: Aadhar, DOB proof, photo. Fee: ₹107.",
    }
    for key, reply in replies.items():
        if key in msg:
            return {"success": True, "reply": reply}
    return {"success": True, "reply": "I can help with passport, Aadhar, PAN, PM Kisan, Ayushman Bharat, scholarships, and more. What do you need help with?"}

# CV GENERATOR
@router.post("/generate-cv")
async def generate_cv(req: CVRequest):
    try:
        if not GEMINI_API_KEY:
            return generate_cv_fallback(req)
        
        prompt = f"""Create a professional CV in HTML format for:
        Name: {req.name}
        Role: {req.role}
        Mobile: {req.mobile}
        Email: {req.email}
        City: {req.city}
        About: {req.about}
        Education: {req.education}
        Skills: {req.skills}
        Experience: {req.experience}
        Projects: {req.projects}
        Template: {req.template}
        
        Return ONLY clean HTML for the CV content (no full page HTML, just the CV sections).
        Use inline CSS for styling. Make it professional and clean.
        Include sections: Header, About, Skills, Education, Experience/Projects."""
        
        response = model.generate_content(prompt)
        return {"success": True, "cv_html": response.text}
    except Exception as e:
        return generate_cv_fallback(req)

def generate_cv_fallback(req):
    cv_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;">
        <div style="background:linear-gradient(135deg,#1A6FA8,#1A2340);color:white;padding:24px;border-radius:12px;text-align:center;margin-bottom:20px;">
            <h1 style="margin:0;font-size:28px;">{req.name}</h1>
            <p style="margin:8px 0;opacity:0.9;">{req.role}</p>
            <p style="margin:4px 0;font-size:13px;opacity:0.8;">{req.mobile} | {req.email} | {req.city}</p>
        </div>
        {f'<div style="margin-bottom:16px;"><h2 style="color:#1A6FA8;border-bottom:2px solid #ADD8E6;padding-bottom:6px;">About</h2><p>{req.about}</p></div>' if req.about else ''}
        {f'<div style="margin-bottom:16px;"><h2 style="color:#1A6FA8;border-bottom:2px solid #ADD8E6;padding-bottom:6px;">Skills</h2><p>{req.skills}</p></div>' if req.skills else ''}
        {f'<div style="margin-bottom:16px;"><h2 style="color:#1A6FA8;border-bottom:2px solid #ADD8E6;padding-bottom:6px;">Education</h2><p>{req.education}</p></div>' if req.education else ''}
        {f'<div style="margin-bottom:16px;"><h2 style="color:#1A6FA8;border-bottom:2px solid #ADD8E6;padding-bottom:6px;">Experience</h2><p>{req.experience}</p></div>' if req.experience else ''}
        {f'<div style="margin-bottom:16px;"><h2 style="color:#1A6FA8;border-bottom:2px solid #ADD8E6;padding-bottom:6px;">Projects</h2><p>{req.projects}</p></div>' if req.projects else ''}
    </div>"""
    return {"success": True, "cv_html": cv_html}

# LETTER GENERATOR
@router.post("/generate-letter")
async def generate_letter(req: LetterRequest):
    try:
        if not GEMINI_API_KEY:
            return generate_letter_fallback(req)
        
        lang = get_lang_name(req.language)
        prompt = f"""Write a formal {req.type} letter in {lang} for:
        From: {req.name}
        To: {req.to}
        Organization: {req.place}
        Details: {req.details}
        
        Format: Include Date, Address, Subject, Body, Closing.
        Make it professional and appropriate for Indian context.
        Return the complete letter text."""
        
        response = model.generate_content(prompt)
        return {"success": True, "letter": response.text}
    except Exception as e:
        return generate_letter_fallback(req)

def generate_letter_fallback(req):
    from datetime import datetime
    today = datetime.now().strftime("%d %B %Y")
    
    templates = {
        "leave": f"Subject: Application for Leave\n\nRespected Sir/Madam,\n\nI am {req.name} and I am writing to request a leave of absence due to {req.details or 'personal reasons'}.\n\nKindly grant me the leave. I assure you all pending work will be completed.\n\nYours sincerely,\n{req.name}",
        "job": f"Subject: Job Application\n\nRespected Sir/Madam,\n\nI, {req.name}, am writing to apply for a suitable position at {req.place}. I am a dedicated professional eager to contribute to your organization.\n\n{req.details or ''}\n\nI request an opportunity for an interview.\n\nYours sincerely,\n{req.name}",
        "complaint": f"Subject: Complaint\n\nRespected Sir/Madam,\n\nI, {req.name}, am writing to bring to your attention: {req.details or 'an important matter'}.\n\nKindly look into this at the earliest.\n\nYours sincerely,\n{req.name}",
    }
    letter = templates.get(req.type, templates["leave"])
    return {"success": True, "letter": f"Date: {today}\n\nTo,\nThe {req.to}\n{req.place}\n\n{letter}"}

# DOCUMENT ANALYSIS
@router.post("/analyze-document")
async def analyze_document(req: DocumentRequest):
    try:
        if not GEMINI_API_KEY:
            return analyze_fallback(req.filename)
        
        import base64
        image_data = req.image_base64.split(',')[-1]
        image_bytes = base64.b64decode(image_data)
        
        vision_model = genai.GenerativeModel('gemini-1.5-flash')
        response = vision_model.generate_content([
            "Analyze this Indian government document image. Identify: 1) Document type 2) Key information visible 3) Required supporting documents 4) Important dates/numbers. Be concise and helpful.",
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        return {"success": True, "analysis": response.text, "doc_type": "Government Document"}
    except Exception as e:
        return analyze_fallback(req.filename)

def analyze_fallback(filename):
    fname = (filename or "").lower()
    if "passport" in fname: doc = "Passport Application Form"
    elif "aadhar" in fname or "aadhaar" in fname: doc = "Aadhar Card"
    elif "pan" in fname: doc = "PAN Card"
    elif "kisan" in fname: doc = "PM Kisan Form"
    else: doc = "Government Document"
    return {"success": True, "doc_type": doc, "analysis": f"Document identified as {doc}. Please ensure you have Aadhar Card, PAN Card, and address proof ready."}

# FORM AUDIT
@router.post("/audit-form")
async def audit_form(req: FormAuditRequest):
    results = []
    errors = 0
    warnings = 0
    passed = 0
    
    # Link check
    if req.url:
        if ".gov.in" in req.url:
            results.append({"type": "ok", "title": "Verified Government Link", "desc": "This is a legitimate government portal."})
            passed += 1
        elif req.url.startswith("http"):
            results.append({"type": "warn", "title": "Unverified Link", "desc": "Not a known government portal. Verify before submitting."})
            warnings += 1
        else:
            results.append({"type": "err", "title": "Invalid Link", "desc": "This does not look like a valid URL."})
            errors += 1
    
    # Name check
    if req.name:
        import re
        if re.search(r'\d', req.name):
            results.append({"type": "err", "title": "Name Contains Numbers!", "desc": "Names cannot have numbers."})
            errors += 1
        else:
            results.append({"type": "ok", "title": "Name Format Correct", "desc": "Name format is valid."})
            passed += 1
    
    # Mobile check
    if req.mobile:
        if len(req.mobile) == 10 and req.mobile[0] in ['6','7','8','9']:
            results.append({"type": "ok", "title": "Mobile Valid", "desc": "Valid 10-digit Indian mobile."})
            passed += 1
        else:
            results.append({"type": "err", "title": "Invalid Mobile!", "desc": "Enter valid 10-digit mobile starting with 6/7/8/9."})
            errors += 1
    
    # Aadhar check
    if req.aadhar:
        if len(req.aadhar) == 12 and req.aadhar[0] not in ['0','1']:
            results.append({"type": "ok", "title": "Aadhar Valid", "desc": "12-digit Aadhar format correct."})
            passed += 1
        else:
            results.append({"type": "err", "title": "Invalid Aadhar!", "desc": "Enter valid 12-digit Aadhar."})
            errors += 1
    
    # PAN check
    if req.pan:
        import re
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', req.pan.upper()):
            results.append({"type": "ok", "title": "PAN Valid", "desc": "PAN format is correct."})
            passed += 1
        else:
            results.append({"type": "err", "title": "Invalid PAN!", "desc": "PAN format: ABCDE1234F"})
            errors += 1
    
    total = errors + warnings + passed
    score = round((passed / total) * 100) if total > 0 else 0
    if errors > 0: score = min(score, 60)
    
    return {
        "success": True,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "results": results,
        "verdict": "Safe to Submit!" if errors == 0 else f"Fix {errors} error(s) before submitting!"
    }

# FORM ANALYZE (Smart Search)
@router.post("/analyze-form-url")
async def analyze_form_url(req: FormAnalyzeRequest):
    url = req.url.lower()
    
    forms = {
        "passport": {"name": "Passport Application", "icon": "📘", "fields": ["Full Name", "DOB", "Address", "Mobile", "Aadhar"], "docs": ["Aadhar Card", "PAN Card", "Address Proof", "10th Certificate", "Passport Photo"]},
        "kisan": {"name": "PM Kisan Registration", "icon": "🌾", "fields": ["Full Name", "Mobile", "Aadhar", "Bank Account", "Land Records"], "docs": ["Aadhar Card", "Land Records (7/12)", "Bank Passbook"]},
        "pmjay": {"name": "Ayushman Bharat Card", "icon": "🏥", "fields": ["Full Name", "DOB", "Mobile", "Aadhar"], "docs": ["Aadhar Card", "Ration Card", "Income Certificate"]},
        "scholarship": {"name": "National Scholarship", "icon": "🎓", "fields": ["Full Name", "Mobile", "Aadhar", "DOB", "Address"], "docs": ["Aadhar Card", "Income Certificate", "Marksheet", "Caste Certificate", "Bank Passbook"]},
        "incometax": {"name": "Income Tax Return", "icon": "💰", "fields": ["Full Name", "PAN", "Aadhar", "Email"], "docs": ["PAN Card", "Aadhar Card", "Form 16", "Bank Statement"]},
    }
    
    detected = None
    for key, form in forms.items():
        if key in url:
            detected = form
            break
    
    if not detected:
        detected = {"name": "Government Form", "icon": "📋", "fields": ["Full Name", "Mobile", "Aadhar", "DOB", "Address"], "docs": ["Aadhar Card", "PAN Card", "Address Proof", "Passport Photo"]}
    
    # Map user profile to fields
    profile = req.user_profile or {}
    filled = {}
    field_map = {"Full Name": "name", "Mobile": "mobile", "DOB": "dob", "Address": "address", "Aadhar": "aadhar", "PAN": "pan", "Email": "email"}
    
    for field in detected["fields"]:
        key = field_map.get(field, "")
        if key and profile.get(key):
            filled[field] = profile[key]
    
    return {
        "success": True,
        "form_name": detected["name"],
        "icon": detected["icon"],
        "fields": detected["fields"],
        "filled": filled,
        "docs_required": detected["docs"],
        "fill_count": len(filled),
        "total_fields": len(detected["fields"])
    }
