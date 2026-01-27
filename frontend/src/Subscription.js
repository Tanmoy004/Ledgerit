import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function Subscription({ user, onBack }) {
  const [plans, setPlans] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/subscription/plans');
      setPlans(response.data.plans);
    } catch (err) {
      setError('Failed to load plans');
    }
  };

  const handleSubscribe = async (planKey) => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:5000/api/subscription/subscribe',
        { plan: planKey },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess(response.data.message);
      setTimeout(() => {
        onBack();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.error || 'Subscription failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button 
              onClick={onBack}
              className="bg-white shadow-lg rounded-full p-3 hover:bg-gray-50 transition"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Choose Your Plan</h1>
          </div>
          <div className="text-sm text-gray-600">
            Welcome, {user?.name}
          </div>
        </div>
      </header>

      <section className="py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-2xl">⚠️</span>
              <h3 className="text-lg font-semibold text-red-800">Page Limit Reached</h3>
            </div>
            <p className="text-red-700 mb-4">
              You've used {user?.stats?.pages_used || 0} out of {user?.stats?.pages_limit || 100} free pages.
              Upgrade to continue processing bank statements.
            </p>
            <div className="bg-red-100 rounded-lg p-4">
              <div className="flex justify-between text-sm text-red-800">
                <span>Pages Used</span>
                <span>{user?.stats?.pages_used || 0} / {user?.stats?.pages_limit || 100}</span>
              </div>
              <div className="w-full bg-red-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-red-600 h-2 rounded-full" 
                  style={{ width: `${Math.min(100, ((user?.stats?.pages_used || 0) / (user?.stats?.pages_limit || 100)) * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Unlock Unlimited Processing</h2>
            <p className="text-xl text-gray-600">Choose the plan that works best for you</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-center">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6 text-center">
              {success}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {Object.entries(plans).map(([key, plan]) => (
              <div key={key} className={`bg-white rounded-2xl shadow-xl p-8 relative ${
                key === 'yearly' ? 'ring-2 ring-blue-500 transform scale-105' : ''
              }`}>
                {key === 'yearly' && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                      Best Value
                    </span>
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="text-4xl font-bold text-blue-600 mb-2">
                    ₹{plan.price}
                  </div>
                  <p className="text-gray-600">
                    {key === 'monthly' && 'per month'}
                    {key === 'quarterly' && 'per 3 months'}
                    {key === 'yearly' && 'per year'}
                  </p>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-3">
                      <span className="text-green-500 text-xl">✓</span>
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSubscribe(key)}
                  disabled={loading}
                  className={`w-full py-3 px-4 rounded-lg font-semibold transition ${
                    key === 'yearly'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  } disabled:opacity-50`}
                >
                  {loading ? 'Processing...' : 'Choose Plan'}
                </button>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-gray-600 mb-4">
              All plans include unlimited PDF processing, support for all banks, and priority customer support.
            </p>
            <p className="text-sm text-gray-500">
              Note: This is a demo. In production, integrate with payment gateways like Razorpay or Stripe.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}