import os
import firebase_admin
from firebase_admin import credentials

def get_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()
    cred_path = os.getenv("FIREBASE_CREDENTIALS_JSON_PATH")
    if not cred_path:
        raise RuntimeError("FIREBASE_CREDENTIALS_JSON_PATH not set")
    cred = credentials.Certificate(cred_path)
    return firebase_admin.initialize_app(cred)