from pydantic import BaseModel
from typing import Optional

class SignupModel(BaseModel):
    mobile: str
    username: str
    password: str
    secret_phrase: str

class LoginModel(BaseModel):
    username: str
    password: str

class OTPSendModel(BaseModel):
    mobile: str

class OTPVerifyModel(BaseModel):
    mobile: str
    otp: str

class VerifyPhraseModel(BaseModel):
    username: str
    secret_phrase: str

class ResetPasswordModel(BaseModel):
    username: str
    secret_phrase: str
    new_password: str

class UpdateProfileModel(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    dob: Optional[str] = None
