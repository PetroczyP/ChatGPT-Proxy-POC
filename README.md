# ChatGPT Proxy POC App

A full-stack web application that provides a ChatGPT interface with Google OAuth authentication and admin functionality for API key management.

![Application Screenshot](https://via.placeholder.com/800x400?text=ChatGPT+Proxy+POC+App)

## Features

### 🔐 **Authentication**
- Google OAuth 2.0 integration
- Secure JWT token-based sessions
- Protected routes and API endpoints

### 💬 **Chat Interface**
- Clean, responsive chat UI
- Real-time messaging with ChatGPT (GPT-4o)
- Chat history storage and retrieval
- Message streaming and error handling

### 👥 **Admin Panel**
- User management and statistics
- API key configuration per user
- Admin access control
- Visual API key status indicators

### 🛠️ **API Key Management**
- Individual user API key assignment
- Default API key configuration
- Multiple API key sources (user-specific, admin default, environment)
- Clear error messages for users without API keys

## Tech Stack

### Frontend
- **React** - Modern UI framework
- **Tailwind CSS** - Utility-first styling
- **Google OAuth** - Authentication
- **Axios** - HTTP client

### Backend
- **FastAPI** - High-performance Python web framework
- **MongoDB** - Document database
- **JWT** - Token-based authentication
- **OpenAI API** - ChatGPT integration

### Infrastructure
- **Google Cloud Run** - Serverless deployment
- **MongoDB Atlas** - Managed database
- **Docker** - Containerization

## Quick Start

### Prerequisites
- Node.js 18+ and Yarn
- Python 3.11+
- MongoDB (local or Atlas)
- Google OAuth credentials
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chatgpt-proxy-poc.git
   cd chatgpt-proxy-poc
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your backend URL and Google Client ID
   ```

4. **Environment Variables**
   
   **Backend (.env):**
   ```
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=chatgpt_app
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   OPENAI_API_KEY=your-openai-api-key
   ADMIN_EMAILS=admin@yourdomain.com
   ```
   
   **Frontend (.env):**
   ```
   REACT_APP_BACKEND_URL=http://localhost:8001
   REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
   ```

5. **Run the Application**
   ```bash
   # Start backend (from backend directory)
   uvicorn server:app --reload --port 8001
   
   # Start frontend (from frontend directory)
   yarn start
   ```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sign-In API
4. Create OAuth 2.0 credentials
5. Add authorized origins and redirect URIs:
   - Origins: `http://localhost:3000`, `https://yourdomain.com`
   - Redirect URIs: `http://localhost:3000/auth/google`, `https://yourdomain.com/auth/google`

## Deployment

### Google Cloud Run

See the complete deployment guide in [`deployment/README.md`](deployment/README.md).

Quick deployment:
```bash
# Update project configuration
nano deployment/deploy.sh

# Deploy to Google Cloud
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## API Documentation

Once running, visit:
- **API Docs**: `http://localhost:8001/docs`
- **Redoc**: `http://localhost:8001/redoc`

### Key Endpoints

- `GET /api/user/profile` - Get current user
- `POST /api/chat` - Send message to ChatGPT
- `GET /api/chat/history` - Get chat history
- `POST /api/admin/configure` - Configure API keys (admin)
- `GET /api/admin/users` - List all users (admin)

## Usage

### For Users
1. Visit the application URL
2. Click "Sign in with Google"
3. Complete OAuth authentication
4. Start chatting with ChatGPT
5. If no API key is configured, contact admin

### For Admins
1. Sign in with admin account
2. Click "Admin Panel" to access management features
3. Configure API keys:
   - Set default API key for all users
   - Assign individual API keys to specific users
   - View user statistics and manage access

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Frontend    │    │     Backend      │    │    Database     │
│     (React)     │───▶│    (FastAPI)     │───▶│   (MongoDB)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Google OAuth   │    │   OpenAI API     │
│     (Auth)      │    │   (ChatGPT)      │
└─────────────────┘    └──────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security Considerations

- JWT tokens with expiration
- Environment variable protection
- CORS configuration
- Input validation and sanitization
- Protected admin endpoints
- Secure API key storage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@yourdomain.com or open an issue on GitHub.

## Acknowledgments

- OpenAI for ChatGPT API
- Google for OAuth 2.0
- FastAPI and React communities