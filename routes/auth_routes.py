from fastapi import APIRouter
from controllers.auth_controller import send_otp, verify_otp, signup, login, verify_phrase, reset_password
from models.user import OTPSendModel, OTPVerifyModel, SignupModel, LoginModel, VerifyPhraseModel, ResetPasswordModel

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/send-otp")
async def api_send_otp(data: OTPSendModel):
    return await send_otp(data)

@router.post("/verify-otp")
async def api_verify_otp(data: OTPVerifyModel):
    return await verify_otp(data)

@router.post("/signup")
async def api_signup(data: SignupModel):
    return await signup(data)

@router.post("/login")
async def api_login(data: LoginModel):
    return await login(data)

@router.post("/verify-phrase")
async def api_verify_phrase(data: VerifyPhraseModel):
    return await verify_phrase(data)

@router.post("/reset-password")
async def api_reset_password(data: ResetPasswordModel):
    return await reset_password(data)
