import React from 'react';

export default function Features() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-6xl font-bold mb-4">Features</h1>
          <p className="text-xl opacity-90">Powerful tools to streamline your bank statement processing</p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            {/* Multi-Bank Support */}
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🏦</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Multi-Bank Support</h3>
              <p className="text-gray-600">Supports all major banks including SBI, HDFC, ICICI, Axis Bank, JK Bank, Indian Bank, and more.</p>
            </div>

            {/* OCR Technology */}
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🔍</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Advanced OCR</h3>
              <p className="text-gray-600">Powered by PaddleOCR for accurate text extraction from both bordered and borderless tables.</p>
            </div>

            {/* Multiple Formats */}
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">📄</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Export Options</h3>
              <p className="text-gray-600">Export to CSV, XML, or Tally-compatible formats for seamless integration.</p>
            </div>

            {/* Password Protection */}
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">🔒</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Password Protected PDFs</h3>
              <p className="text-gray-600">Handles password-protected bank statements with secure processing.</p>
            </div>

            {/* Real-time Processing */}
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Fast Processing</h3>
              <p className="text-gray-600">Quick extraction with real-time progress tracking and optimized algorithms.</p>
            </div>

            {/* Balance Calculation */}
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-2xl">💰</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Auto Balance Calculation</h3>
              <p className="text-gray-600">Automatically calculates opening and closing balances from transaction data.</p>
            </div>

          </div>
        </div>
      </section>

      {/* Technical Features */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Technical Capabilities</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <span>Supports both bordered and borderless table formats</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <span>Custom parsers for specific bank formats</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <span>Multi-line transaction merging</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <span>Automatic bank detection and classification</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <span>Column order preservation from original PDFs</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <span>Special character cleaning for clean exports</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8">
              <h3 className="text-xl font-semibold mb-4">Supported File Types</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>PDF Bank Statements</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span>Password Protected PDFs</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                  <span>Multi-page Documents</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl opacity-90 mb-8">Upload your bank statement and see the magic happen</p>
          <a 
            href="/" 
            className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
          >
            Try Now
          </a>
        </div>
      </section>
    </div>
  );
}