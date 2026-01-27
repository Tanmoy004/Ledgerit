import React from 'react';

export default function Support() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-6xl font-bold mb-4">Support</h1>
          <p className="text-xl opacity-90">Get help with your bank statement processing</p>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            
            {/* Contact Info */}
            <div>
              <h2 className="text-3xl font-bold mb-8">Get in Touch</h2>
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📧</span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Email Support</h3>
                    <p className="text-gray-600">support@ledgerit.com</p>
                    <p className="text-sm text-gray-500">Response within 24 hours</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📞</span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Phone Support</h3>
                    <p className="text-gray-600">+91 8777654651</p>
                    <p className="text-sm text-gray-500">Mon-Fri, 9 AM - 6 PM IST</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">💬</span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Live Chat</h3>
                    <p className="text-gray-600">Available on website</p>
                    <p className="text-sm text-gray-500">Instant support during business hours</p>
                  </div>
                </div>
              </div>
            </div>

            {/* FAQ */}
            <div>
              <h2 className="text-3xl font-bold mb-8">Frequently Asked Questions</h2>
              <div className="space-y-4">
                
                <div className="bg-white rounded-lg p-6 shadow-sm">
                  <h3 className="font-semibold mb-2">Which banks are supported?</h3>
                  <p className="text-gray-600 text-sm">We support all major Indian banks including SBI, HDFC, ICICI, Axis Bank, JK Bank, Indian Bank, and many more.</p>
                </div>

                <div className="bg-white rounded-lg p-6 shadow-sm">
                  <h3 className="font-semibold mb-2">What file formats can I upload?</h3>
                  <p className="text-gray-600 text-sm">Currently, we support PDF bank statements. Both password-protected and regular PDFs are accepted.</p>
                </div>

                <div className="bg-white rounded-lg p-6 shadow-sm">
                  <h3 className="font-semibold mb-2">Is my data secure?</h3>
                  <p className="text-gray-600 text-sm">Yes, all data is processed locally and securely. We don't store your bank statements on our servers.</p>
                </div>

                <div className="bg-white rounded-lg p-6 shadow-sm">
                  <h3 className="font-semibold mb-2">What export formats are available?</h3>
                  <p className="text-gray-600 text-sm">You can export your data as CSV, XML, or Tally-compatible formats for easy integration.</p>
                </div>

                <div className="bg-white rounded-lg p-6 shadow-sm">
                  <h3 className="font-semibold mb-2">Why is processing taking too long?</h3>
                  <p className="text-gray-600 text-sm">Large PDF files may take 2-3 minutes to process. Ensure your internet connection is stable and the Flask server is running.</p>
                </div>

              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Troubleshooting */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Troubleshooting</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">⚠️</span>
              </div>
              <h3 className="font-semibold mb-2">Network Error</h3>
              <p className="text-gray-600 text-sm">Ensure Flask server is running: <code className="bg-gray-100 px-2 py-1 rounded">python flask_app.py</code></p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🔒</span>
              </div>
              <h3 className="font-semibold mb-2">Password Protected PDF</h3>
              <p className="text-gray-600 text-sm">Enter the PDF password when prompted. Contact your bank if you don't know the password.</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📄</span>
              </div>
              <h3 className="font-semibold mb-2">No Transactions Found</h3>
              <p className="text-gray-600 text-sm">Ensure the PDF contains transaction tables. Some summary pages may not have extractable data.</p>
            </div>

          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Still Need Help?</h2>
            <p className="text-xl opacity-90">Send us a message and we'll get back to you</p>
          </div>
          
          <div className="bg-white rounded-2xl p-8 text-gray-900">
            <form className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Name</label>
                  <input type="text" className="w-full border rounded-lg px-4 py-3" placeholder="Your name" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
                  <input type="email" className="w-full border rounded-lg px-4 py-3" placeholder="your@email.com" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Subject</label>
                <input type="text" className="w-full border rounded-lg px-4 py-3" placeholder="How can we help?" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Message</label>
                <textarea rows="4" className="w-full border rounded-lg px-4 py-3" placeholder="Describe your issue or question..."></textarea>
              </div>
              <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
                Send Message
              </button>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
}