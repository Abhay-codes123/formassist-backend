from fastapi import HTTPException
from passlib.context import CryptContext
from config.db import get_db
from middleware.auth import create_token
from models.user import SignupModel, LoginModel, OTPSendModel, OTPVerifyModel, ResetPasswordModel, VerifyPhraseModel
from datetime import datetime, timedelta
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(p): return pwd_context.hash(p)
def verify_pw(plain, hashed): return pwd_context.verify(plain, hashed)

# SEND OTP
async def send_otp(data: OTPSendModel):
    db = get_db()
    mobile = data.mobile.strip()
    if len(mobile) != 10 or not mobile.isdigit():
        raise HTTPException(status_code=400, detail="Enter valid 10-digit mobile number!")
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    await db.otps.update_one(
        {"mobile": mobile},
        {"$set": {"otp": hash_pw(otp), "expires_at": expires_at, "attempts": 0, "verified": False}},
        upsert=True
    )
    print(f"OTP for {mobile}: {otp}")
    return {"success": True, "message": "OTP sent!", "demo_otp": otp}

# VERIFY OTP
async def verify_otp(data: OTPVerifyModel):
    db = get_db()
    record = await db.otps.find_one({"mobile": data.mobile})
    if not record:
        raise HTTPException(status_code=400, detail="Please send OTP first!")
    if record.get("attempts", 0) >= 3:
        raise HTTPException(status_code=429, detail="Too many attempts! Send OTP again.")
    if datetime.utcnow() > record.get("expires_at"):
        raise HTTPException(status_code=400, detail="OTP expired! Send again.")
    if not verify_pw(data.otp, record["otp"]):
        await db.otps.update_one({"mobile": data.mobile}, {"$inc": {"attempts": 1}})
        remaining = 3 - (record.get("attempts", 0) + 1)
        raise HTTPException(status_code=400, detail=f"Wrong OTP! {remaining} attempts left.")
    await db.otps.update_one({"mobile": data.mobile}, {"$set": {"verified": True}})
    return {"success": True, "message": "OTP verified!"}

# SIGNUP
async def signup(data: SignupModel):
    db = get_db()
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters!")
    if data.username.lower() == data.password.lower():
        raise HTTPException(status_code=400, detail="Username and password cannot be same!")
    if len(data.secret_phrase) < 10:
        raise HTTPException(status_code=400, detail="Secret phrase must be at least 10 characters!")
    otp_record = await db.otps.find_one({"mobile": data.mobile, "verified": True})
    if not otp_record:
        raise HTTPException(status_code=400, detail="Mobile not verified! Please verify OTP first.")
    existing = await db.users.find_one({"$or": [{"mobile": data.mobile}, {"username": data.username}]})
    if existing:
        if existing.get("mobile") == data.mobile:
            raise HTTPException(status_code=400, detail="Mobile already registered!")
        raise HTTPException(status_code=400, detail="Username already taken!")
    user = {
        "mobile": data.mobile,
        "username": data.username,
        "password": hash_pw(data.password),
        "secret_phrase": hash_pw(data.secret_phrase),
        "is_blocked": False,
        "failed_attempts": 0,
        "blocked_until": None,
        "profile": {"name": "", "email": "", "address": "", "pincode": "", "dob": ""},
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    result = await db.users.insert_one(user)
    await db.otps.delete_one({"mobile": data.mobile})
    token = create_token({"user_id": str(result.inserted_id), "username": data.username})
    return {"success": True, "message": "Account created!", "token": token, "username": data.username}

# LOGIN
async def login(data: LoginModel):
    db = get_db()
    user = await db.users.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password!")
    if user.get("is_blocked") and user.get("blocked_until"):
        if datetime.utcnow() < user["blocked_until"]:
            mins = int((user["blocked_until"] - datetime.utcnow()).seconds / 60)
            raise HTTPException(status_code=429, detail=f"Account blocked for {mins} minutes!")
        else:
            await db.users.update_one({"username": data.username},
                {"$set": {"is_blocked": False, "failed_attempts": 0, "blocked_until": None}})
    if not verify_pw(data.password, user["password"]):
        failed = user.get("failed_attempts", 0) + 1
        update = {"$set": {"failed_attempts": failed}}
        if failed >= 3:
            update["$set"]["is_blocked"] = True
            update["$set"]["blocked_until"] = datetime.utcnow() + timedelta(minutes=30)
            await db.users.update_one({"username": data.username}, update)
            raise HTTPException(status_code=429, detail="3 wrong attempts! Account blocked for 30 minutes.")
        await db.users.update_one({"username": data.username}, update)
        raise HTTPException(status_code=401, detail=f"Wrong password! {3-failed} attempts left.")
    await db.users.update_one({"username": data.username},
        {"$set": {"failed_attempts": 0, "is_blocked": False, "last_login": datetime.utcnow()}})
    token = create_token({"user_id": str(user["_id"]), "username": user["username"]})
    return {"success": True, "message": "Login successful!", "token": token, "username": user["username"]}

# VERIFY PHRASE
async def verify_phrase(data: VerifyPhraseModel):
    db = get_db()
    user = await db.users.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    if not verify_pw(data.secret_phrase, user["secret_phrase"]):
        raise HTTPException(status_code=401, detail="Wrong secret phrase!")
    return {"success": True, "message": "Phrase verified!"}

# RESET PASSWORD
async def reset_password(data: ResetPasswordModel):
    db = get_db()
    user = await db.users.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    if not verify_pw(data.secret_phrase, user["secret_phrase"]):
        raise HTTPException(status_code=401, detail="Wrong secret phrase!")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters!")
    await db.users.update_one({"username": data.username},
        {"$set": {"password": hash_pw(data.new_password), "failed_attempts": 0, "is_blocked": False}})
    return {"success": True, "message": "Password reset successfully!"}
