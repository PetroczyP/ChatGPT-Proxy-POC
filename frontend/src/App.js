import React, { useState, useEffect } from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [users, setUsers] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [isManagingAdmin, setIsManagingAdmin] = useState(false);
  const [userApiKeyEmail, setUserApiKeyEmail] = useState('');
  const [userApiKey, setUserApiKey] = useState('');
  const [isManagingApiKey, setIsManagingApiKey] = useState(false);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
      localStorage.setItem('authToken', token);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      fetchUserProfile(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUserProfile = async (token) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/user/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setUser(response.data);
      setIsAdmin(response.data.is_admin);
      
      if (response.data.is_admin) {
        fetchAdminStats(token);
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      localStorage.removeItem('authToken');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAdminStats = async (token) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/stats`, {
        headers: {
          'Authorization': `Bearer ${token || localStorage.getItem('authToken')}`
        }
      });
      setAdminStats(response.data);
    } catch (error) {
      console.error('Failed to fetch admin stats:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/users`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      setUsers(response.data.users);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE_URL}/api/login/google`;
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    setMessages([]);
    setIsAdmin(false);
    setShowAdminPanel(false);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isSending) return;

    setIsSending(true);
    const userMessage = inputMessage.trim();
    setInputMessage('');

    // Add user message to chat
    setMessages(prev => [...prev, { 
      type: 'user', 
      content: userMessage, 
      timestamp: new Date().toISOString() 
    }]);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/chat`,
        { message: userMessage },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Add assistant response to chat
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp
      }]);

    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        content: 'Sorry, something went wrong. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const configureApiKey = async () => {
    try {
      await axios.post(
        `${API_BASE_URL}/api/admin/configure`,
        { 
          openai_key: apiKey,
          user_email: userEmail || null
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      alert('API key configured successfully!');
      setApiKey('');
      setUserEmail('');
      
    } catch (error) {
      console.error('Failed to configure API key:', error);
      alert('Failed to configure API key.');
    }
  };

  const manageAdminAccess = async (email, action) => {
    setIsManagingAdmin(true);
    try {
      await axios.post(
        `${API_BASE_URL}/api/admin/manage-admin`,
        { 
          email: email,
          action: action
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      alert(`Admin access ${action === 'add' ? 'granted to' : 'removed from'} ${email}`);
      if (action === 'add') {
        setNewAdminEmail('');
      }
      fetchUsers(); // Refresh the user list
      
    } catch (error) {
      console.error('Failed to manage admin access:', error);
      alert('Failed to manage admin access.');
    } finally {
      setIsManagingAdmin(false);
    }
  };

  const handleAddAdmin = () => {
    if (!newAdminEmail.trim()) {
      alert('Please enter a valid email address');
      return;
    }
    manageAdminAccess(newAdminEmail.trim(), 'add');
  };

  const handleRemoveAdmin = (email) => {
    if (window.confirm(`Are you sure you want to remove admin access from ${email}?`)) {
      manageAdminAccess(email, 'remove');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
          <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full mx-4">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-800 mb-2">ChatGPT Web App</h1>
              <p className="text-gray-600">Sign in with Google to start chatting</p>
            </div>
            
            <button
              onClick={handleGoogleLogin}
              className="w-full bg-white border-2 border-gray-300 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-50 hover:border-gray-400 transition-colors flex items-center justify-center space-x-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span>Sign in with Google</span>
            </button>
            
            <div className="mt-6 text-center text-sm text-gray-500">
              <p>Secure authentication powered by Google</p>
            </div>
          </div>
        </div>
      </GoogleOAuthProvider>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-800">ChatGPT Web App</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {isAdmin && (
                <button
                  onClick={() => setShowAdminPanel(!showAdminPanel)}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Admin Panel
                </button>
              )}
              
              <div className="flex items-center space-x-3">
                <img 
                  src={user.picture} 
                  alt={user.name}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-gray-700 font-medium">{user.name}</span>
              </div>
              
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {showAdminPanel && isAdmin && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Admin Panel</h2>
            
            {adminStats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium text-blue-900">Total Users</h3>
                  <p className="text-2xl font-bold text-blue-600">{adminStats.total_users}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium text-green-900">Total Chats</h3>
                  <p className="text-2xl font-bold text-green-600">{adminStats.total_chats}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-medium text-purple-900">Admin Email</h3>
                  <p className="text-sm font-medium text-purple-600">{adminStats.admin_email}</p>
                </div>
              </div>
            )}
            
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-800 mb-4">Configure API Key</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="password"
                  placeholder="OpenAI API Key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <input
                  type="email"
                  placeholder="User Email (optional - for default leave empty)"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={configureApiKey}
                className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Configure API Key
              </button>
            </div>
            
            <div className="border-t pt-6 mt-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-800">Users</h3>
                <button
                  onClick={fetchUsers}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Refresh
                </button>
              </div>
              
              <div className="max-h-60 overflow-y-auto">
                {users.length > 0 ? (
                  <div className="space-y-2">
                    {users.map((user, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <img 
                            src={user.picture} 
                            alt={user.name}
                            className="w-10 h-10 rounded-full"
                          />
                          <div className="flex-1">
                            <p className="font-medium text-gray-800">{user.name}</p>
                            <p className="text-sm text-gray-600">{user.email}</p>
                            {user.is_admin && (
                              <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full mt-1">
                                Admin
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="text-right">
                            <p className="text-sm text-gray-500">
                              {new Date(user.last_login).toLocaleDateString()}
                            </p>
                          </div>
                          {user.is_admin && user.email !== adminStats?.admin_email && (
                            <button
                              onClick={() => handleRemoveAdmin(user.email)}
                              disabled={isManagingAdmin}
                              className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600 transition-colors disabled:opacity-50"
                            >
                              Remove Admin
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">No users found</p>
                )}
              </div>
            </div>

            {/* Add Admin Section */}
            <div className="border-t pt-6 mt-6">
              <h3 className="text-lg font-medium text-gray-800 mb-4">Manage Admin Access</h3>
              <div className="flex space-x-2">
                <input
                  type="email"
                  placeholder="Enter email to grant admin access"
                  value={newAdminEmail}
                  onChange={(e) => setNewAdminEmail(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isManagingAdmin}
                />
                <button
                  onClick={handleAddAdmin}
                  disabled={isManagingAdmin || !newAdminEmail.trim()}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isManagingAdmin ? 'Processing...' : 'Add Admin'}
                </button>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Grant admin access to users by entering their email address. They must have already signed in at least once.
              </p>
            </div>
          </div>
        )}

        {/* Chat Interface */}
        <div className="bg-white rounded-xl shadow-sm h-[600px] flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-800">Chat with GPT-4</h2>
          </div>
          
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <p className="text-gray-500">Start a conversation with ChatGPT</p>
                <p className="text-sm text-gray-400 mt-2">Type your message below to get started</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))
            )}
            
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Message Input */}
          <div className="p-4 border-t">
            <div className="flex space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="1"
                disabled={isSending}
              />
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isSending}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;