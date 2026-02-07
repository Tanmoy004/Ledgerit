import React, { useState } from 'react';
import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || `http://${window.location.hostname}:5000`;

export default function Login({ onLogin, switchToSignup, onBack }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [key, setKey] = useState(Date.now());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Force form reset on component mount
  React.useEffect(() => {
    setKey(Date.now());
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, formData);
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      onLogin(response.data.user);
    } catch (err) {
      if (err.code === 'ECONNREFUSED' || err.message === 'Network Error') {
        setError('Service temporarily unavailable. Please try again in a moment.');
      } else {
        setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      {onBack && (
        <button
  onClick={onBack}
  className="fixed top-4 left-4 z-50 h-11 w-11 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-700 hover:bg-gray-100 hover:scale-105 transition"
  aria-label="Go back"
>
  ←
</button>
      )}
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Welcome Back</h2>
            <p className="text-gray-600 mt-2">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" autoComplete="off" key={key}>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                autoComplete="nope"
                name="email-new"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                autoComplete="nope"
                name="password-new"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 transition"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <button
                onClick={switchToSignup}
                className="text-blue-600 hover:text-blue-700 font-semibold"
              >
                Sign up
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}