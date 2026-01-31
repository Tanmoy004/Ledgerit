import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function Signup({ onLogin, switchToLogin }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: ''
  });
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [countdown]);

  const sendOTP = async () => {
    if (!formData.email) {
      setError('Please enter email address');
      return;
    }

    setLoading(true);
    try {
      await axios.post('http://localhost:5000/api/auth/send-otp', { email: formData.email });
      setOtpSent(true);
      setCountdown(300);
      setError('');
    } catch (err) {
      if (err.code === 'ECONNREFUSED' || err.message === 'Network Error') {
        setError('Service temporarily unavailable. Please try again in a moment.');
      } else {
        setError(err.response?.data?.error || 'Failed to send OTP. Please try again.');
      }
    }
    setLoading(false);
  };

  const verifyOTP = async () => {
    if (!otp) {
      setError('Please enter OTP');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await axios.post('http://localhost:5000/api/auth/verify-otp', { 
        email: formData.email, 
        otp: otp 
      });
      setEmailVerified(true);
      setError('');
    } catch (err) {
      if (err.code === 'ECONNREFUSED' || err.message === 'Network Error') {
        setError('Service temporarily unavailable. Please try again in a moment.');
      } else {
        setError(err.response?.data?.error || 'Invalid OTP. Please try again.');
      }
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!emailVerified) {
      setError('Please verify your email address first');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!formData.phone) {
      setError('WhatsApp number is required');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/auth/signup', {
        ...formData,
        email_verified: emailVerified
      });
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      onLogin(response.data.user);
    } catch (err) {
      if (err.code === 'ECONNREFUSED' || err.message === 'Network Error') {
        setError('Service temporarily unavailable. Please try again in a moment.');
      } else {
        setError(err.response?.data?.error || 'Signup failed. Please try again.');
      }
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Create Account</h2>
            <p className="text-gray-600 mt-2">Get started with 100 free pages</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Name
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email ID
              </label>
              <div className="flex gap-2">
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  disabled={emailVerified}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  placeholder="Enter your email"
                />
                {!emailVerified && (
                  <button 
                    type="button" 
                    onClick={sendOTP}
                    disabled={loading || !formData.email || countdown > 0}
                    className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {countdown > 0 ? `${Math.floor(countdown/60)}:${(countdown%60).toString().padStart(2,'0')}` : (otpSent ? 'Resend' : 'Send OTP')}
                  </button>
                )}
                {emailVerified && (
                  <span className="px-4 py-3 text-green-600 font-semibold">✓ Verified</span>
                )}
              </div>
            </div>

            {otpSent && !emailVerified && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter OTP
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    maxLength="6"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter 6-digit OTP"
                  />
                  <button 
                    type="button" 
                    onClick={verifyOTP}
                    disabled={loading || !otp}
                    className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    Verify
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-1 flex flex-col sm:flex-row sm:items-center sm:gap-1">
                  <span>Check your email for the verification code</span>
                  {countdown > 0 && (
                    <span className="text-red-500 font-medium sm:font-normal sm:ml-1">
                      (Expires in {Math.floor(countdown / 60)}:
                      {(countdown % 60).toString().padStart(2, '0')})
                    </span>
                  )}
                </p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Whatsapp Number *
              </label>
              <input
                type="tel"
                required
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your whatsapp number"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Create Password
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Create your password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                required
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Confirm your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !emailVerified}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 transition"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <button
                onClick={switchToLogin}
                className="text-blue-600 hover:text-blue-700 font-semibold"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}