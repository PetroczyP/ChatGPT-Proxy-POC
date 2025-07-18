from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from openai import OpenAI, AsyncOpenAI
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List
import os
import jwt
import json
import uuid
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', '').split(',') if os.environ.get('ADMIN_EMAILS') else []
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://2e51ad72-7b0f-492c-a172-3771d8f293ac.preview.emergentagent.com')

# Initialize FastAPI app
app = FastAPI(title="ChatGPT Proxy POC Application", version="1.0.0")

# Configure CORS for production
if ENVIRONMENT == 'production':
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://*.run.app",  # Cloud Run domains
            "https://*.yourdomain.com",  # Your custom domain
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")

# Initialize OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Database setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
users_collection = db.users
chats_collection = db.chats
admin_collection = db.admin
messages_collection = db.messages

# Security
security = HTTPBearer()

# Pydantic models
class ChatMessage(BaseModel):
    message: str

class AdminConfig(BaseModel):
    openai_key: str
    user_email: Optional[str] = None

class UserProfile(BaseModel):
    email: str
    name: str
    picture: str
    is_admin: bool = False

# Helper functions
def create_jwt_token(user_data: dict):
    """Create JWT token for user"""
    payload = {
        'user_id': user_data['user_id'],
        'email': user_data['email'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, 'secret-key', algorithm='HS256')

def verify_jwt_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, 'secret-key', algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from token"""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user = users_collection.find_one({"user_id": payload['user_id']})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_user_api_key(user_id: str):
    """Get user's assigned API key"""
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get('api_key'):
        return {'key': user['api_key'], 'source': 'user_specific'}
    
    # Check for default admin key
    admin_config = admin_collection.find_one({"type": "default"})
    if admin_config and admin_config.get('api_key'):
        return {'key': admin_config.get('api_key'), 'source': 'default_admin'}
    
    # Fallback to environment variable
    if OPENAI_API_KEY:
        return {'key': OPENAI_API_KEY, 'source': 'environment'}
    
    return None  # No API key available

# Routes
@app.get("/")
async def root():
    return {"message": "ChatGPT Proxy POC Application API"}

@app.get("/api/login/google")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    try:
        # Use the frontend URL as the redirect URI
        redirect_uri = f"{FRONTEND_URL}/auth/google"
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/auth/google")
async def google_auth(request: Request):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_id = str(uuid.uuid4())
        user_data = {
            'user_id': user_id,
            'email': user_info['email'],
            'name': user_info['name'],
            'picture': user_info['picture'],
            'is_admin': user_info['email'].lower() in [email.lower().strip() for email in ADMIN_EMAILS],
            'created_at': datetime.utcnow(),
            'last_login': datetime.utcnow()
        }
        
        # Check if user exists
        existing_user = users_collection.find_one({"email": user_info['email']})
        if existing_user:
            # Update last login
            users_collection.update_one(
                {"email": user_info['email']},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            user_data['user_id'] = existing_user['user_id']
        else:
            # Create new user
            users_collection.insert_one(user_data)
        
        # Create JWT token
        jwt_token = create_jwt_token(user_data)
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{FRONTEND_URL}?token={jwt_token}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "user_id": current_user['user_id'],
        "email": current_user['email'],
        "name": current_user['name'],
        "picture": current_user['picture'],
        "is_admin": current_user.get('is_admin', False)
    }

@app.post("/api/chat")
async def send_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """Send message to ChatGPT"""
    try:
        user_id = current_user['user_id']
        
        # Get user's API key
        api_key_info = get_user_api_key(user_id)
        if not api_key_info:
            raise HTTPException(
                status_code=400, 
                detail="No ChatGPT API key configured for your account. Please contact your administrator to configure an API key."
            )
        
        api_key = api_key_info['key']
        
        # Create chat session
        session_id = f"chat_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        client = AsyncOpenAI(api_key=api_key)
        
        # Send message
        chat_completion = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message.message}
            ]
        )
        response = chat_completion.choices[0].message.content
        
        # Store chat history
        chat_record = {
            "chat_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "user_message": message.message,
            "assistant_response": response,
            "timestamp": datetime.utcnow(),
            "api_key_source": api_key_info['source']
        }
        chats_collection.insert_one(chat_record)
        
        return {
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "api_key_source": api_key_info['source']
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        if "No ChatGPT API key configured" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/api/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    """Get user's chat history"""
    try:
        user_id = current_user['user_id']
        chats = list(chats_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(50))
        
        return {"chats": chats}
        
    except Exception as e:
        logger.error(f"Chat history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

# Admin routes
@app.post("/api/admin/configure")
async def configure_api_key(
    config: AdminConfig,
    current_user: dict = Depends(get_current_user)
):
    """Configure API key for user (admin only)"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        if config.user_email:
            # Configure for specific user
            users_collection.update_one(
                {"email": config.user_email},
                {"$set": {"api_key": config.openai_key}},
                upsert=True
            )
        else:
            # Configure default key
            admin_collection.update_one(
                {"type": "default"},
                {"$set": {"api_key": config.openai_key, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        
        return {"message": "API key configured successfully"}
        
    except Exception as e:
        logger.error(f"Admin config error: {str(e)}")
        raise HTTPException(status_code=500, detail="Configuration failed")

@app.get("/api/admin/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Get all users with API key status (admin only)"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        users = list(users_collection.find({}, {"_id": 0}))
        
        # Add API key status to each user
        for user in users:
            api_key_info = get_user_api_key(user['user_id'])
            user['has_api_key'] = api_key_info is not None
            user['api_key_source'] = api_key_info['source'] if api_key_info else None
            user['has_personal_key'] = bool(user.get('api_key'))
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get users")

@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    """Get admin statistics"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        total_users = users_collection.count_documents({})
        total_chats = chats_collection.count_documents({})
        
        return {
            "total_users": total_users,
            "total_chats": total_chats,
            "admin_email": current_user['email']
        }
        
    except Exception as e:
        logger.error(f"Admin stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.post("/api/admin/user-api-key")
async def manage_user_api_key(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Assign, update, or remove API key for a specific user (admin only)"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        email = request.get('email')
        api_key = request.get('api_key')  # Can be empty string to remove
        action = request.get('action', 'set')  # 'set' or 'remove'
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Find user by email
        user = users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if action == 'remove' or not api_key:
            # Remove API key
            users_collection.update_one(
                {"email": email},
                {"$unset": {"api_key": ""}}
            )
            message = f"API key removed for {email}"
        else:
            # Set/update API key
            users_collection.update_one(
                {"email": email},
                {"$set": {"api_key": api_key}}
            )
            message = f"API key updated for {email}"
        
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Manage user API key error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to manage user API key")

@app.get("/api/user/api-key-status")
async def get_user_api_key_status(current_user: dict = Depends(get_current_user)):
    """Get current user's API key status"""
    try:
        user_id = current_user['user_id']
        api_key_info = get_user_api_key(user_id)
        
        return {
            "has_api_key": api_key_info is not None,
            "api_key_source": api_key_info['source'] if api_key_info else None,
            "has_personal_key": bool(current_user.get('api_key'))
        }
        
    except Exception as e:
        logger.error(f"Get API key status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API key status")

@app.post("/api/admin/manage-admin")
async def manage_admin_access(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Add or remove admin access for a user (super admin only)"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        email = request.get('email')
        action = request.get('action')  # 'add' or 'remove'
        
        if not email or action not in ['add', 'remove']:
            raise HTTPException(status_code=400, detail="Invalid email or action")
        
        # Update user in database
        if action == 'add':
            users_collection.update_one(
                {"email": email},
                {"$set": {"is_admin": True}},
                upsert=False
            )
            message = f"Admin access granted to {email}"
        else:
            users_collection.update_one(
                {"email": email},
                {"$set": {"is_admin": False}},
                upsert=False
            )
            message = f"Admin access removed from {email}"
        
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Manage admin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to manage admin access")

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Cloud Run compatibility
    port = int(os.environ.get('PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)