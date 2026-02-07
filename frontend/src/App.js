import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Features from './Features';
import Support from './Support';
import Login from './Login';
import Signup from './Signup';
import Subscription from './Subscription';

// API Configuration - Dynamic base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || `http://${window.location.hostname}:5000`;

// Fully responsive version with mobile-first layout, collapsible navigation, and responsive table/cards

export default function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [authMode, setAuthMode] = useState(null); // null, 'login' or 'signup'
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showXmlModal, setShowXmlModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [csvFileName, setCsvFileName] = useState('transactions');
  const [xmlConfig, setXmlConfig] = useState({
    ledgerName: '',
    fromDate: '',
    endDate: '',
    fileName: 'transactions'
  });
  const [filteredCount, setFilteredCount] = useState(0);
  const [file, setFile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [columns, setColumns] = useState([]);
  const [metadata, setMetadata] = useState({});
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [password, setPassword] = useState('');
  const [showPasswordPrompt, setShowPasswordPrompt] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteIndex, setDeleteIndex] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [addPosition, setAddPosition] = useState('above');
  const [addIndex, setAddIndex] = useState(null);
  const [editIndex, setEditIndex] = useState(null);
  const [formData, setFormData] = useState({});
  const [toast, setToast] = useState({ show: false, message: '', type: 'error' });


  // Helper function to determine if column should be hidden on mobile
  const isColumnHiddenOnMobile = (columnName) => {
    const hiddenColumns = ['balance', 'remarks', 'reference', 'ref', 'cheque', 'instrument'];
    return hiddenColumns.some(hidden => 
      columnName.toLowerCase().includes(hidden.toLowerCase())
    );
  };

  const addAboveTransaction = (index) => {
    setAddIndex(index);
    setAddPosition('above');
    setFormData(columns.reduce((acc, col) => ({ ...acc, [col]: '' }), {}));
    setShowAddModal(true);
    setOpenDropdown(null);
  };

  const addBelowTransaction = (index) => {
    setAddIndex(index);
    setAddPosition('below');
    setFormData(columns.reduce((acc, col) => ({ ...acc, [col]: '' }), {}));
    setShowAddModal(true);
    setOpenDropdown(null);
  };

  const editTransaction = (index, row) => {
    setEditIndex(index);
    setFormData(columns.reduce((acc, col, i) => ({ ...acc, [col]: row[i] || '' }), {}));
    setShowEditModal(true);
    setOpenDropdown(null);
  };

  const handleAddSubmit = () => {
    const newRow = columns.map(col => formData[col] || '');
    const newTransactions = [...transactions];
    const insertIndex = addPosition === 'above' ? addIndex : addIndex + 1;
    newTransactions.splice(insertIndex, 0, newRow);
    setTransactions(newTransactions);
    setShowAddModal(false);
    setFormData({});
  };

  const handleEditSubmit = () => {
    const updatedRow = columns.map(col => formData[col] || '');
    const newTransactions = [...transactions];
    newTransactions[editIndex] = updatedRow;
    setTransactions(newTransactions);
    setShowEditModal(false);
    setFormData({});
  };

  const closeModals = () => {
    setShowAddModal(false);
    setShowEditModal(false);
    setFormData({});
  };

  const deleteTransaction = (index) => {
    setDeleteIndex(index);
    setShowDeleteModal(true);
    setOpenDropdown(null);
  };

  const confirmDelete = () => {
    const newTransactions = transactions.filter((_, i) => i !== deleteIndex);
    setTransactions(newTransactions);
    setShowDeleteModal(false);
    setDeleteIndex(null);
  };

  const cancelDelete = () => {
    setShowDeleteModal(false);
    setDeleteIndex(null);
  };

  const showToast = (message, type = 'error') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type: 'error' }), 4000);
  };

  const toggleDropdown = (index) => {
    setOpenDropdown(openDropdown === index ? null : index);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => { setIsDragging(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    // Check if user is authenticated before uploading
    if (!isAuthenticated) {
      setAuthMode('login');
      return;
    }
    
    const droppedFile = e.dataTransfer.files[0];
    if (!droppedFile) return;
    const name = droppedFile.name.toLowerCase();
    const isPDF = name.endsWith('.pdf') || droppedFile.type === 'application/pdf';
    if (isPDF) {
      setFile(droppedFile); setError(''); setPassword(''); setShowPasswordPrompt(false);
      // Clear previous data
      setTransactions([]);
      setColumns([]);
      setMetadata({});
      uploadFile(droppedFile);
    }
    else { setError('Please upload a valid PDF file'); }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    // Check if user is authenticated before uploading
    if (!isAuthenticated) {
      setAuthMode('login');
      return;
    }
    
    if (selectedFile.size > 50 * 1024 * 1024) { setError('File size too large. Maximum 50MB allowed.'); return; }
    const name = selectedFile.name.toLowerCase();
    const isPDF = name.endsWith('.pdf') || selectedFile.type === 'application/pdf';
    if (!isPDF) { setError('Please select a valid PDF file.'); return; }
    setFile(selectedFile); setError(''); setPassword(''); setShowPasswordPrompt(false);
    // Clear previous data
    setTransactions([]);
    setColumns([]);
    setMetadata({});
    // Show immediate loading feedback
    setLoading(true);
    setProgress(5); // Start with 5% immediately
    // Auto-upload when file is selected
    uploadFile(selectedFile);
  };

  // Check authentication on app load
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData && userData !== 'undefined') {
      try {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        // Fetch fresh user stats
        fetchUserStats();
      } catch (err) {
        console.error('Error parsing user data:', err);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  }, []);

  const fetchUserStats = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/api/auth/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log('User stats fetched:', response.data.user);
      setUser(response.data.user);
    } catch (err) {
      console.error('Failed to fetch user stats:', err);
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    axios.defaults.headers.common['Authorization'] = `Bearer ${localStorage.getItem('token')}`;
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/auth/logout`);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setIsAuthenticated(false);
      setCurrentPage('home');
    }
  };



  useEffect(() => {
    const getFilteredTransactions = () => {
      if (!xmlConfig.fromDate || !xmlConfig.endDate) return transactions;
      
      const dateColIndex = columns.findIndex(col => 
        col.toLowerCase().includes('date') && !col.toLowerCase().includes('value')
      );
      
      if (dateColIndex === -1) return transactions;

      const parseTransactionDate = (dateStr) => {
        if (!dateStr) return null;

        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
          return new Date(dateStr);
        }

        if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
          const [day, month, year] = dateStr.split('/');
          return new Date(year, month - 1, day);
        }

        if (/^\d{2}\/\d{2}\/\d{2}$/.test(dateStr)) {
          const [day, month, year] = dateStr.split('/');
          const fullYear = parseInt(year) < 50 ? '20' + year : '19' + year;
          return new Date(fullYear, month - 1, day);
        }

        if (/^\d{2}-\d{2}-\d{4}$/.test(dateStr)) {
          const [day, month, year] = dateStr.split('-');
          return new Date(year, month - 1, day);
        }

        if (/^\d{2}-\d{2}-\d{2}$/.test(dateStr)) {
          const [day, month, year] = dateStr.split('-');
          const fullYear = parseInt(year) < 50 ? '20' + year : '19' + year;
          return new Date(fullYear, month - 1, day);
        }

        const monthMap = {
          'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3,
          'May': 4, 'Jun': 5, 'Jul': 6, 'Aug': 7,
          'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };

        const parts = dateStr.split(/[-/]/);
        if (parts.length === 3) {
          let [day, month, year] = parts;

          if (monthMap.hasOwnProperty(month)) {
            month = monthMap[month];
          } else {
            month = parseInt(month) - 1;
          }

          return new Date(year, month, day);
        }
        return null;
      };

      const parseInputDate = (dateStr) => {
        return new Date(dateStr);
      };

      const fromDateObj = parseInputDate(xmlConfig.fromDate);
      const endDateObj = parseInputDate(xmlConfig.endDate);

      if (!fromDateObj || !endDateObj) return transactions;

      fromDateObj.setHours(0, 0, 0, 0);
      endDateObj.setHours(23, 59, 59, 999);

      return transactions.filter(row => {
        const rowDate = row[dateColIndex];
        if (!rowDate) return false;

        const rowDateObj = parseTransactionDate(rowDate);
        if (!rowDateObj) return false;

        rowDateObj.setHours(12, 0, 0, 0);

        return rowDateObj >= fromDateObj && rowDateObj <= endDateObj;
      });
    };

    const filtered = getFilteredTransactions();
    setFilteredCount(filtered.length);
  }, [xmlConfig.fromDate, xmlConfig.endDate, transactions, columns]);

  // Update opening and closing balance when transactions change
  useEffect(() => {
    if (transactions.length > 0 && columns.length > 0) {
      const balanceColIndex = columns.findIndex(col => String(col).toLowerCase().includes('balance'));
      const dateColIndex = columns.findIndex(col => String(col).toLowerCase().includes('date') && !String(col).toLowerCase().includes('value'));
      if (balanceColIndex === -1 || dateColIndex === -1) return;

      // Find all possible transaction amount columns
      const withdrawalColIndex = columns.findIndex(col => String(col).toLowerCase().includes('withdrawal'));
      const depositColIndex = columns.findIndex(col => String(col).toLowerCase().includes('deposit'));
      const debitColIndex = columns.findIndex(col => String(col).toLowerCase().includes('debit') && !String(col).toLowerCase().includes('card'));
      const creditColIndex = columns.findIndex(col => String(col).toLowerCase().includes('credit') && !String(col).toLowerCase().includes('card'));
      const drCrColIndex = columns.findIndex(col => String(col).toLowerCase().includes('dr/cr') || String(col).toLowerCase().includes('dr / cr'));
      const amountColIndex = columns.findIndex(col => String(col).toLowerCase() === 'amount' || String(col).toLowerCase().includes('amount'));

      // Helper to parse amount with embedded Dr/Cr like "10.00 (Dr)"
      const parseAmountWithDrCr = (str) => {
        if (!str) return { amount: 0, type: null };
        const s = String(str).trim();
        const drMatch = s.match(/([\d,.-]+)\s*\(\s*dr\s*\)/i);
        const crMatch = s.match(/([\d,.-]+)\s*\(\s*cr\s*\)/i);
        if (drMatch) return { amount: parseFloat(drMatch[1].replace(/,/g, '')) || 0, type: 'DR' };
        if (crMatch) return { amount: parseFloat(crMatch[1].replace(/,/g, '')) || 0, type: 'CR' };
        return { amount: parseFloat(s.replace(/[^\d.-]/g, '')) || 0, type: null };
      };

      // Parse dates to find oldest and newest transactions
      const parseDate = (dateStr) => {
        if (!dateStr) return null;
        const str = String(dateStr).trim();
        
        // Handle "DD MMM YYYY" format (space-separated)
        const spaceMatch = str.match(/^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})$/i);
        if (spaceMatch) {
          const [, day, month, year] = spaceMatch;
          const monthMap = { 'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12' };
          return new Date(`${year}-${monthMap[month]}-${day.padStart(2, '0')}`);
        }
        
        const parts = str.split(/[-/\s]/);
        if (parts.length === 3) {
          let [day, month, year] = parts;
          if (year.length === 2) year = '20' + year;
          const monthMap = { 'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12' };
          if (monthMap[month]) month = monthMap[month];
          return new Date(`${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`);
        }
        return null;
      };

      let oldestIndex = 0, newestIndex = 0;
      let oldestDate = parseDate(transactions[0][dateColIndex]);
      let newestDate = oldestDate;

      // First pass: find oldest and newest dates
      transactions.forEach((row, i) => {
        const date = parseDate(row[dateColIndex]);
        if (date) {
          if (date < oldestDate) {
            oldestDate = date;
            oldestIndex = i;
          } else if (date.getTime() === oldestDate.getTime()) {
            oldestIndex = i; // Keep updating to get last occurrence
          }
          
          if (date > newestDate) {
            newestDate = date;
            newestIndex = i;
          } else if (date.getTime() === newestDate.getTime()) {
            newestIndex = i; // Keep updating to get last occurrence
          }
        }
      });

      // Determine if data is chronological or reverse
      const isChronological = oldestIndex < newestIndex;

      // Second pass: for same-date transactions, pick correct one based on order
      transactions.forEach((row, i) => {
        const date = parseDate(row[dateColIndex]);
        if (date) {
          if (date.getTime() === oldestDate.getTime()) {
            const currentBalance = parseFloat(String(row[balanceColIndex]).replace(/[^\d.-]/g, '')) || 0;
            const oldestCurrentBalance = parseFloat(String(transactions[oldestIndex][balanceColIndex]).replace(/[^\d.-]/g, '')) || 0;
            if (isChronological) {
              // Chronological: pick highest balance (after all transactions)
              if (currentBalance > oldestCurrentBalance) oldestIndex = i;
            } else {
              // Reverse: pick lowest balance (first transaction)
              if (currentBalance < oldestCurrentBalance) oldestIndex = i;
            }
          }
          
          if (date.getTime() === newestDate.getTime()) {
            const currentBalance = parseFloat(String(row[balanceColIndex]).replace(/[^\d.-]/g, '')) || 0;
            const newestCurrentBalance = parseFloat(String(transactions[newestIndex][balanceColIndex]).replace(/[^\d.-]/g, '')) || 0;
            if (isChronological) {
              // Chronological: pick lowest balance (before all transactions)
              if (currentBalance < newestCurrentBalance) newestIndex = i;
            } else {
              // Reverse: pick highest balance (last transaction)
              if (currentBalance > newestCurrentBalance) newestIndex = i;
            }
          }
        }
      });

      const oldestBalanceStr = String(transactions[oldestIndex][balanceColIndex]);
      const oldestBalance = parseAmountWithDrCr(oldestBalanceStr).amount || parseFloat(oldestBalanceStr.replace(/[^\d.-]/g, '')) || 0;
      const newestBalance = parseFloat(String(transactions[newestIndex][balanceColIndex]).replace(/[^\d.-]/g, '')) || 0;

      let openingBalance, closingBalance;

      // Try Withdrawal/Deposit columns
      if (withdrawalColIndex !== -1 && depositColIndex !== -1) {
        const withdrawal = parseFloat(String(transactions[oldestIndex][withdrawalColIndex]).replace(/[^\d.-]/g, '')) || 0;
        const deposit = parseFloat(String(transactions[oldestIndex][depositColIndex]).replace(/[^\d.-]/g, '')) || 0;
        
        if (withdrawal === 0 && deposit === 0) {
          openingBalance = oldestBalance;
        } else {
          openingBalance = oldestBalance + withdrawal - deposit;
        }
        closingBalance = newestBalance;
      }
      // Try Debit/Credit columns
      else if (debitColIndex !== -1 && creditColIndex !== -1) {
        const debit = parseFloat(String(transactions[oldestIndex][debitColIndex]).replace(/[^\d.-]/g, '')) || 0;
        const credit = parseFloat(String(transactions[oldestIndex][creditColIndex]).replace(/[^\d.-]/g, '')) || 0;
        
        if (debit === 0 && credit === 0) {
          openingBalance = oldestBalance;
        } else {
          openingBalance = oldestBalance + debit - credit;
        }
        closingBalance = newestBalance;
      }
      // Try Amount + DR/CR columns OR Amount with embedded Dr/Cr
      else if (amountColIndex !== -1) {
        const amountStr = String(transactions[oldestIndex][amountColIndex]);
        const parsed = parseAmountWithDrCr(amountStr);
        
        if (parsed.type) {
          // Amount has embedded Dr/Cr like "10.00 (Dr)"
          if (parsed.amount === 0) {
            openingBalance = oldestBalance;
          } else {
            openingBalance = parsed.type === 'DR' ? oldestBalance + parsed.amount : oldestBalance - parsed.amount;
          }
        } else if (drCrColIndex !== -1) {
          // Separate DR/CR column exists
          const drCr = String(transactions[oldestIndex][drCrColIndex]).trim().toUpperCase();
          if (parsed.amount === 0) {
            openingBalance = oldestBalance;
          } else {
            openingBalance = drCr === 'DR' ? oldestBalance + parsed.amount : oldestBalance - parsed.amount;
          }
        } else {
          openingBalance = oldestBalance;
        }
        closingBalance = newestBalance;
      }
      // Fallback: Calculate from balance difference
      else {
        // Check if data is chronological or reverse
        const isChronological = oldestIndex < newestIndex;
        
        if (isChronological) {
          // For chronological: opening is before first transaction
          // Try to infer from balance progression
          if (oldestIndex > 0) {
            // Use previous row's balance as opening
            openingBalance = parseFloat(String(transactions[oldestIndex - 1][balanceColIndex]).replace(/[^\d.-]/g, '')) || oldestBalance;
          } else {
            openingBalance = oldestBalance;
          }
          closingBalance = newestBalance;
        } else {
          // For reverse chronological: opening is after last transaction
          if (oldestIndex < transactions.length - 1) {
            // Use next row's balance as opening
            openingBalance = parseFloat(String(transactions[oldestIndex + 1][balanceColIndex]).replace(/[^\d.-]/g, '')) || oldestBalance;
          } else {
            openingBalance = oldestBalance;
          }
          closingBalance = newestBalance;
        }
      }

      setMetadata(prev => ({ ...prev, opening_balance: openingBalance, closing_balance: closingBalance }));
    }
  }, [transactions, columns]);

  const uploadFile = async (fileToUpload = file) => {
    if (!fileToUpload) return;
    setLoading(true); setError(''); setProgress(0);
    const formData = new FormData();
    formData.append('file', fileToUpload);
    if (password) formData.append('password', password);
    let progressInterval;

    try {
      // Faster progress simulation for better UX
      progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev < 30) return prev + Math.random() * 15; // Fast initial progress
          if (prev < 70) return prev + Math.random() * 8;  // Medium progress
          return prev < 95 ? prev + Math.random() * 3 : prev; // Slow final progress
        });
      }, 150); // Reduced from 300ms to 150ms

      const res = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        timeout: 120000 // Reduced from 180000 (3min) to 120000 (2min)
      });

      clearInterval(progressInterval);
      setProgress(100);
      setTransactions(res.data.transactions || []);
      setColumns(res.data.columns || []);
      // Don't set metadata here - let frontend calculate it
      setShowPasswordPrompt(false);

      // Update user stats if provided
      if (res.data.user_stats) {
        setUser(prev => ({ ...prev, stats: res.data.user_stats }));
      }
    } catch (err) {
      if (progressInterval) clearInterval(progressInterval);
      setProgress(0);

      // Handle subscription/limit errors
      if (err.response?.status === 403 && err.response?.data?.redirect === '/subscription') {
        setCurrentPage('subscription');
        setError('Page limit reached. Please upgrade your plan.');
        return;
      }

      if (err.response?.status === 401) {
        if (err.response?.data?.error === 'PDF is password protected') {
          // PDF is password protected, show password prompt
          setError('');
          setShowPasswordPrompt(true);
        } else if (err.response?.data?.error === 'Wrong password') {
          // User entered wrong password
          setError('Wrong password. Please enter the correct password.');
          setShowPasswordPrompt(true);
        } else {
          // Authentication error - redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
          setError('Session expired. Please login again.');
        }
      } else if (err.code === 'ECONNABORTED') setError('Request timed out. Please try again.');
      else if (err.code === 'ECONNREFUSED' || err.message === 'Network Error') setError('Service temporarily unavailable. Please try again in a moment.');
      else setError(err.response?.data?.error || 'An error occurred. Please try again.');
      setTransactions([]);
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(0), 500); // Reduced from 1000ms
    }
  };

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // Assume your existing data array is named transactions
  const start = page * pageSize;
  const end = start + pageSize;
  const paginated = transactions.slice(start, end);

  const totalPages = Math.ceil(transactions.length / pageSize);

  const nextPage = () => {
    if (page < totalPages - 1) setPage(page + 1);
  };

  const prevPage = () => {
    if (page > 0) setPage(page - 1);
  };

  const getFilteredTransactions = () => {
    // If no date range specified, return all transactions
    if (!xmlConfig.fromDate || !xmlConfig.endDate) return transactions;
    
    const dateColIndex = columns.findIndex(col => 
      col.toLowerCase().includes('date') && !col.toLowerCase().includes('value')
    );
    
    if (dateColIndex === -1) return transactions;

    const parseTransactionDate = (dateStr) => {
      if (!dateStr) return null;

      // Handle YYYY-MM-DD format (from Canara Bank)
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return new Date(dateStr);
      }

      // Handle DD/MM/YYYY format (from HDFC and other banks)
      if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
        const [day, month, year] = dateStr.split('/');
        return new Date(year, month - 1, day);
      }

      // Handle DD/MM/YY format (2-digit year)
      if (/^\d{2}\/\d{2}\/\d{2}$/.test(dateStr)) {
        const [day, month, year] = dateStr.split('/');
        const fullYear = parseInt(year) < 50 ? '20' + year : '19' + year;
        return new Date(fullYear, month - 1, day);
      }

      // Handle DD-MM-YYYY format
      if (/^\d{2}-\d{2}-\d{4}$/.test(dateStr)) {
        const [day, month, year] = dateStr.split('-');
        return new Date(year, month - 1, day);
      }

      // Handle DD-MM-YY format (2-digit year)
      if (/^\d{2}-\d{2}-\d{2}$/.test(dateStr)) {
        const [day, month, year] = dateStr.split('-');
        const fullYear = parseInt(year) < 50 ? '20' + year : '19' + year;
        return new Date(fullYear, month - 1, day);
      }

      // Handle DD-MMM-YYYY format (from other banks)
      const monthMap = {
        'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3,
        'May': 4, 'Jun': 5, 'Jul': 6, 'Aug': 7,
        'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
      };

      const parts = dateStr.split(/[-/]/);
      if (parts.length === 3) {
        let [day, month, year] = parts;

        // Convert month name to number if needed
        if (monthMap.hasOwnProperty(month)) {
          month = monthMap[month];
        } else {
          month = parseInt(month) - 1; // Convert to 0-based index
        }

        return new Date(year, month, day);
      }
      return null;
    };

    const parseInputDate = (dateStr) => {
      // dateStr is in YYYY-MM-DD format from date input
      return new Date(dateStr);
    };

    const fromDateObj = parseInputDate(xmlConfig.fromDate);
    const endDateObj = parseInputDate(xmlConfig.endDate);

    if (!fromDateObj || !endDateObj) return transactions;

    // Set time to start/end of day for inclusive comparison
    fromDateObj.setHours(0, 0, 0, 0);
    endDateObj.setHours(23, 59, 59, 999);

    return transactions.filter(row => {
      const rowDate = row[dateColIndex];
      if (!rowDate) return false;

      console.log('Processing row date:', rowDate);
      const rowDateObj = parseTransactionDate(rowDate);
      console.log('Parsed to:', rowDateObj);
      if (!rowDateObj) return false;

      rowDateObj.setHours(12, 0, 0, 0); // Set to noon to avoid timezone issues

      const isInRange = rowDateObj >= fromDateObj && rowDateObj <= endDateObj;
      console.log('Date', rowDate, 'is in range:', isInRange);

      return isInRange;
    });
  };

  const handleCsvDownload = () => {
    // Check subscription status before download
    if (!user?.stats?.pages_remaining || user.stats.pages_remaining <= 0) {
      setCurrentPage('subscription');
      setError('Page limit reached. Please upgrade your plan to download files.');
      return;
    }

    const csvRows = [];
    csvRows.push(columns.map(col => `"${col}"`).join(','));
    transactions.forEach(row => {
      const cleanRow = row.map(cell => {
        let cleanCell = String(cell || '')
          .replace(/ï¿¾/g, '')
          .replace(/[\r\n\t]/g, ' ')
          .trim();
        return `"${cleanCell}"`;
      });
      csvRows.push(cleanRow.join(','));
    });
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${csvFileName}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    setShowCsvModal(false);
  };

  const handleXmlDownload = () => {
    // Check subscription status before download
    if (!user?.stats?.pages_remaining || user.stats.pages_remaining <= 0) {
      setCurrentPage('subscription');
      setError('Page limit reached. Please upgrade your plan to download files.');
      return;
    }

    // Validation
    if (!xmlConfig.ledgerName.trim()) {
      showToast('Please enter a Bank Name (As per tally)', 'error');
      return;
    }

    if (!xmlConfig.fromDate) {
      showToast('Please select a From Date', 'error');
      return;
    }

    if (!xmlConfig.endDate) {
      showToast('Please select an End Date', 'error');
      return;
    }

    // Get first transaction date for validation
    const dateColIndex = columns.findIndex(col =>
      col.toLowerCase().includes('date') && !col.toLowerCase().includes('value')
    );

    if (dateColIndex !== -1 && transactions.length > 0) {
      const firstTransactionDate = transactions[0][dateColIndex];

      const convertToDateObj = (dateStr) => {
        if (!dateStr) return null;

        // Handle YYYY-MM-DD format
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
          return new Date(dateStr);
        }

        // Handle DD/MM/YYYY format
        if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
          const [day, month, year] = dateStr.split('/');
          return new Date(year, month - 1, day);
        }

        // Handle DD-MM-YYYY format
        if (/^\d{2}-\d{2}-\d{4}$/.test(dateStr)) {
          const [day, month, year] = dateStr.split('-');
          return new Date(year, month - 1, day);
        }

        // Handle DD-MMM-YYYY format
        const monthMap = {
          'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3,
          'May': 4, 'Jun': 5, 'Jul': 6, 'Aug': 7,
          'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };
        const parts = String(dateStr).split(/[-/]/);
        if (parts.length === 3) {
          let [day, month, year] = parts;
          if (monthMap[month]) {
            month = monthMap[month];
          } else {
            month = parseInt(month) - 1;
          }
          return new Date(year, month, day);
        }
        return null;
      };

      const firstTransactionDateObj = convertToDateObj(firstTransactionDate);
      const fromDateObj = new Date(xmlConfig.fromDate);
      const endDateObj = new Date(xmlConfig.endDate);

      // Check if From Date is less than first transaction date
      if (firstTransactionDateObj && fromDateObj < firstTransactionDateObj) {
        showToast('From Date cannot be earlier than the first transaction date', 'error');
        return;
      }

      // Check if From Date is greater than End Date
      if (fromDateObj > endDateObj) {
        showToast('From Date cannot be greater than End Date', 'error');
        return;
      }
    }

    const filteredTransactions = getFilteredTransactions();

    let xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<ENVELOPE>
<HEADER>
<TALLYREQUEST>Import Data</TALLYREQUEST>
</HEADER>
<BODY>
<IMPORTDATA>
<REQUESTDESC>
<REPORTNAME>Vouchers</REPORTNAME>
</REQUESTDESC>
<REQUESTDATA>
`;

    filteredTransactions.forEach(row => {
      const date = row[0] || ''; // Transaction Date
      const description = row[3] || ''; // Description
      const withdrawal = row[4] || ''; // Withdrawals
      const deposit = row[5] || ''; // Deposits

      // Convert date from DD-MMM-YYYY to YYYYMMDD
      const convertDate = (dateStr) => {
        if (!dateStr) return '';
        const monthMap = {
          'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
          'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
          'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        };
        const parts = dateStr.split(/[-/]/);
        if (parts.length === 3) {
          let [day, month, year] = parts;
          if (monthMap[month]) month = monthMap[month];
          return `${year}${month.padStart(2, '0')}${day.padStart(2, '0')}`;
        }
        return '';
      };

      const formattedDate = convertDate(date);
      const amount = withdrawal || deposit || '0';
      const cleanAmount = amount.replace(/[^0-9.-]/g, '');
      const voucherType = withdrawal ? 'Payment' : 'Receipt';

      const cleanDescription = description
        .replace(/ï¿¾/g, '')
        .replace(/[\r\n\t]/g, ' ')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;')
        .replace(/[\uFFFE\uFFFF]/g, ' ')
        .split('').filter(char => char.charCodeAt(0) >= 32 && char.charCodeAt(0) < 65534).join('')
        .trim();

      xmlContent += `<TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="${voucherType}" ACTION="Create">
<DATE>${formattedDate}</DATE>
<VOUCHERTYPENAME>${voucherType}</VOUCHERTYPENAME>
<NARRATION>${cleanDescription}</NARRATION>
<PARTYLEDGERNAME>${xmlConfig.ledgerName}</PARTYLEDGERNAME>
<ALLLEDGERENTRIES.LIST>
<LEDGERNAME>Suspense</LEDGERNAME>
<ISDEEMEDPOSITIVE>${withdrawal ? 'Yes' : 'No'}</ISDEEMEDPOSITIVE>
<AMOUNT>${withdrawal ? '-' + cleanAmount : cleanAmount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST>
<LEDGERNAME>${xmlConfig.ledgerName}</LEDGERNAME>
<ISDEEMEDPOSITIVE>${withdrawal ? 'No' : 'Yes'}</ISDEEMEDPOSITIVE>
<AMOUNT>${cleanAmount}</AMOUNT>
</ALLLEDGERENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE>
`;
    });

    xmlContent += `</REQUESTDATA>
</IMPORTDATA>
</BODY>
</ENVELOPE>`;

    const blob = new Blob([xmlContent], { type: 'application/xml;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${xmlConfig.ledgerName}.xml`;
    a.click();
    URL.revokeObjectURL(url);
    setShowXmlModal(false);
  };

  if (currentPage === 'features') {
    return (
      <div>
        <button
          onClick={() => setCurrentPage('home')}
          className="fixed top-4 left-4 z-50 bg-white shadow-lg rounded-full p-3 hover:bg-gray-50 transition"
        >
          Back
        </button>
        <Features />
      </div>
    );
  }

  if (currentPage === 'support') {
    return (
      <div>
        <button
          onClick={() => setCurrentPage('home')}
          className="fixed top-4 left-4 z-50 bg-white shadow-lg rounded-full p-3 hover:bg-gray-50 transition"
        >
          Back
        </button>
        <Support />
      </div>
    );
  }

  // Authentication pages
  if (!isAuthenticated && authMode === 'login') {
    return <Login onLogin={handleLogin} switchToSignup={() => setAuthMode('signup')} onBack={() => setAuthMode(null)} />;
  }
  
  if (!isAuthenticated && authMode === 'signup') {
    return <Signup onLogin={handleLogin} switchToLogin={() => setAuthMode('login')} />;
  }

  // Subscription page
  if (currentPage === 'subscription') {
    return <Subscription user={user} onBack={() => setCurrentPage('home')} />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 to-blue-50">

      {/* Header */}
      <header className="bg-white shadow-md sticky top-0 z-50">
        {loading && (
          <div className="fixed top-0 left-0 right-0 z-[999]">
            <div className="h-[3px] w-full bg-blue-100 overflow-hidden">
              <div className="h-full w-1/3 bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-600 animate-shimmer" />
            </div>
          </div>
        )}

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src="/logo.png" alt="Ledgerit Logo" className="w-12 h-12 sm:w-16 sm:h-16" />
            <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Ledgerit</h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <button onClick={() => setCurrentPage('home')} className="text-gray-700 hover:text-blue-600 font-medium">Home</button>
            <button onClick={() => setCurrentPage('features')} className="text-gray-700 hover:text-blue-600 font-medium">Features</button>
            <button onClick={() => setCurrentPage('support')} className="text-gray-700 hover:text-blue-600 font-medium">Support</button>
          </nav>
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-gray-600">Welcome, {user?.name || 'User'}</span>
                <div className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {user?.stats?.pages_used || 0}/{user?.stats?.pages_limit === Infinity ? '∞' : user?.stats?.pages_limit || 100} pages
                </div>
                <button
                  onClick={handleLogout}
                  className="text-gray-700 hover:text-red-600 font-medium"
                >
                  Logout
                </button>
              </>
            ) : (
              <button
                onClick={() => setAuthMode('login')}
                className="text-gray-700 hover:text-blue-600 font-medium"
              >
                Login
              </button>
            )}
          </div>
          <button className="md:hidden p-2" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden border-t">
            <div className="px-4 py-2 flex flex-col space-y-2 bg-white">
              <button onClick={() => { setCurrentPage('home'); setMobileMenuOpen(false); }} className="py-2 text-left">Home</button>
              <button onClick={() => { setCurrentPage('features'); setMobileMenuOpen(false); }} className="py-2 text-left">Features</button>
              <button onClick={() => { setCurrentPage('support'); setMobileMenuOpen(false); }} className="py-2 text-left">Support</button>
              <div className="border-t pt-2">
                {isAuthenticated ? (
                  <>
                    <div className="text-sm text-gray-600 py-1">Welcome, {user?.name || 'User'}</div>
                    <div className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded mb-2 inline-block">
                      {user?.stats?.pages_used || 0}/{user?.stats?.pages_limit === Infinity ? '∞' : user?.stats?.pages_limit || 100} pages
                    </div>
                    <button onClick={handleLogout} className="py-2 text-left text-red-600 w-full">Logout</button>
                  </>
                ) : (
                  <button onClick={() => { setAuthMode('login'); setMobileMenuOpen(false); }} className="py-2 text-left w-full">Login</button>
                )}
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-10 sm:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid lg:grid-cols-2 gap-8 items-center">
          <div className="space-y-4 text-center lg:text-left">
            <h2 className="text-3xl sm:text-5xl font-bold">Convert PDF Bank Statements to Tally XML</h2>
            <p className="text-sm sm:text-lg opacity-90">Extract transactions and export into XML, Excel, or CSV formats.</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
              <a href="#upload" className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold">Get Started</a>
              {/* <a href="#features" className="border-2 border-white px-6 py-3 rounded-lg font-semibold">Learn More</a> */}
            </div>
          </div>
          <div className="max-w-md w-full mx-auto">
            <img src="/hero.png" alt="Tally Integration" className="rounded-xl shadow-2xl w-full" />
          </div>
        </div>
      </section>

      {/* Upload & Content */}
      <main id="upload" className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-10">

        {/* Upload card */}
        <div className="bg-white rounded-2xl shadow-lg p-5 sm:p-8">
          <h2 className="text-xl sm:text-2xl font-semibold mb-4">Upload Bank Statement</h2>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-6 sm:p-10 text-center transition ${isDragging ? 'border-blue-600 bg-blue-50' : 'border-gray-300'}`}
          >
            <input id="file-upload" type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" disabled={!isAuthenticated} />
            <label htmlFor="file-upload" onClick={(e) => { if (!isAuthenticated) { e.preventDefault(); setAuthMode('login'); } }} className="cursor-pointer inline-block bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg font-medium">
              {loading ? (
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Processing...</span>
                </div>
              ) : 'Select PDF File'}
            </label>
            {file && <div className="mt-3 text-sm text-gray-700">Selected: {file.name}</div>}
          </div>

          {showPasswordPrompt && (
            <div className="mt-4 space-y-2">
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter PDF password" className="w-full border rounded-lg px-4 py-3" />
              <button disabled={!password || loading} onClick={() => uploadFile()} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3 rounded-lg">Unlock & Process</button>
            </div>
          )}

          {loading && (
            <div className="mt-5 rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-5 shadow-sm">

              {/* Title */}
              <div className="flex items-center gap-3 mb-3">
                <div className="w-5 h-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                <span className="text-sm font-semibold text-blue-700">
                  Processing your statement
                </span>

                <span className="ml-auto text-xs font-medium text-blue-700 bg-blue-100 px-2 py-1 rounded-full">
                  {Math.round(progress)}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="relative h-3 w-full rounded-full bg-blue-100 overflow-hidden">

                {/* Actual progress */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full
        bg-gradient-to-r from-blue-500 via-indigo-500 to-blue-600
        transition-all duration-500 ease-out shadow-md"
                  style={{ width: `${progress}%` }}
                />

                {/* Shimmer overlay */}
                <div
                  className="absolute inset-y-0 left-0 w-1/3
        bg-gradient-to-r from-transparent via-white/50 to-transparent
        animate-shimmer"
                  style={{ width: '35%' }}
                />
              </div>

              {/* Status text with more detailed feedback */}
              <p className="mt-2 text-xs text-blue-600">
                {progress < 20 && 'Uploading PDF securely…'}
                {progress >= 20 && progress < 40 && 'Analyzing document structure…'}
                {progress >= 40 && progress < 70 && 'Extracting transactions…'}
                {progress >= 70 && progress < 90 && 'Processing data…'}
                {progress >= 90 && 'Finalizing results…'}
              </p>
            </div>
          )}

          {error && <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">{error}</div>}
        </div>

        {/* Transactions */}
        {transactions.length > 0 && (
          <div className="mt-8 space-y-5">

            {/* Header + view toggle */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold tracking-tight">Transaction Preview</h3>
                <p className="text-sm text-gray-600">{transactions.length} transactions found</p>
              </div>

              {/* <div className="flex gap-2 justify-end">
                <button
                  className={`px-4 py-2 text-sm rounded-full border transition ${
                    viewMode === "table"
                      ? "bg-gray-900 text-white shadow"
                      : "bg-white hover:bg-gray-100"
                  }`}
                  onClick={() => setViewMode("table")}
                >
                  📊 Table
                </button>

                <button
                  className={`px-4 py-2 text-sm rounded-full border transition ${
                    viewMode === "cards"
                      ? "bg-gray-900 text-white shadow"
                      : "bg-white hover:bg-gray-100"
                  }`}
                  onClick={() => setViewMode("cards")}
                >
                  🗂️ Cards
                </button>
              </div> */}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block">
              <div className="rounded-2xl border shadow-xl bg-white">
                <div className="w-full overflow-x-auto">
                  <table className="min-w-[800px] w-full table-fixed text-[15px]">
                    <thead className="sticky top-0 z-10 bg-gray-100">
                      <tr>
                        {columns.map((col, i) => (
                          <th
                            key={i}
                            style={{ width: `${100 / (columns.length + 1)}%` }}
                            className={`px-4 py-3 font-semibold text-gray-700 border-b text-left break-words whitespace-normal ${
                              isColumnHiddenOnMobile(col) ? 'hidden sm:table-cell' : ''
                            }`}
                          >
                            {col}
                          </th>
                        ))}
                        <th
                          style={{ width: `${100 / (columns.length + 1)}%` }}
                          className="px-4 py-3 font-semibold text-gray-700 border-b text-left break-words whitespace-normal"
                        >
                          Action
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {paginated.map((row, r) => (
                        <tr
                          key={r}
                          className="even:bg-gray-50 hover:bg-blue-50/40 transition"
                        >
                          {row.map((cell, c) => (
                            <td
                              key={c}
                              style={{ width: `${100 / (columns.length + 1)}%` }}
                              className={`px-4 py-3 border-b break-words whitespace-normal align-top ${
                                isColumnHiddenOnMobile(columns[c]) ? 'hidden sm:table-cell' : ''
                              } ${
                                columns[c].toLowerCase().includes('withdrawal') && cell && cell !== '-' && parseFloat(cell.replace(/[^\d.-]/g, '')) > 0
                                  ? "text-left font-semibold text-red-600"
                                  : columns[c].toLowerCase().includes('deposit') && cell && cell !== '-' && parseFloat(cell.replace(/[^\d.-]/g, '')) > 0
                                    ? "text-left font-semibold text-green-600"
                                    : columns[c].toLowerCase().includes('amount') && row.some(rowCell => String(rowCell).trim().toLowerCase() === 'dr')
                                      ? "text-left font-semibold text-red-600"
                                      : columns[c].toLowerCase().includes('amount') && row.some(rowCell => String(rowCell).trim().toLowerCase() === 'cr')
                                        ? "text-left font-semibold text-green-600"
                                        : (/amount/i.test(columns[c]) && /^\s*[\d,.-]+\s*$/.test(cell) && row.some(rowCell => /^\s*dr\s*$/i.test(rowCell))) ||
                                          (/debit/i.test(columns[c]) && /^\s*[\d,.-]+\s*$/.test(cell) && parseFloat(cell.replace(/[^\d.-]/g, '')) > 0)
                                          ? "text-left font-semibold text-red-600"
                                          : (/amount/i.test(columns[c]) && /^\s*[\d,.-]+\s*$/.test(cell) && row.some(rowCell => /^\s*cr\s*$/i.test(rowCell))) ||
                                            (/credit/i.test(columns[c]) && /^\s*[\d,.-]+\s*$/.test(cell) && parseFloat(cell.replace(/[^\d.-]/g, '')) > 0)
                                            ? "text-left font-semibold text-green-600"
                                            : /amount|balance/i.test(columns[c])
                                              ? "text-left font-semibold text-gray-900"
                                              : "text-gray-700"
                              }`}

                            >
                              {(() => {
                                const cleanCell = String(cell || '').trim();
                                return cleanCell === '' || cleanCell === 'null' || cleanCell === 'undefined' ? '-' : cleanCell;
                              })()}
                            </td>
                          ))}
                          <td
                            style={{ width: `${100 / (columns.length + 1)}%` }}
                            className="px-4 py-3 border-b break-words whitespace-normal align-top relative"
                          >
                            <button
                              onClick={() => toggleDropdown(start + r)}
                              className="p-3 sm:p-2 hover:bg-gray-100 rounded-full transition"
                            >
                              <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                              </svg>
                            </button>
                            {openDropdown === start + r && (
                              <div className="absolute sm:right-0 left-0 sm:left-auto top-10 bg-white border rounded-xl shadow-lg z-10 w-full sm:w-[160px]">
                                <button
                                  onClick={() => addAboveTransaction(start + r)}
                                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-t-lg"
                                >
                                  Add Above
                                </button>
                                <button
                                  onClick={() => addBelowTransaction(start + r)}
                                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                                >
                                  Add Row
                                </button>
                                <button
                                  onClick={() => editTransaction(start + r, row)}
                                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => deleteTransaction(start + r)}
                                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-b-lg text-red-600"
                                >
                                  Delete
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination & Page Size */}
                <div className="px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-gray-50">

                  {/* rows per page */}
                  <div className="flex items-center gap-2 text-sm">
                    <span>Rows per page:</span>

                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setPage(0);
                      }}
                      className="border rounded-lg px-2 py-1"
                    >
                      {[10, 20, 30, 40, 50, 100].map((size) => (
                        <option key={size} value={size}>
                          {size}
                        </option>
                      ))}
                    </select>

                    <span className="text-gray-600">
                      Showing {start + 1}–{Math.min(end, transactions.length)} of {transactions.length}
                    </span>
                  </div>

                  {/* pagination */}
                  <div className="flex items-center gap-2">

                    <button
                      onClick={prevPage}
                      disabled={page === 0}
                      className="px-3 py-2 rounded-xl shadow-sm disabled:opacity-40 flex items-center gap-1 bg-white hover:bg-gray-100"
                    >
                      {/* ← Previous */} Previous
                    </button>

                    <span className="text-sm font-medium">
                      Page {page + 1} of {totalPages}
                    </span>

                    <button
                      onClick={nextPage}
                      disabled={page >= totalPages - 1}
                      className="px-3 py-2 rounded-xl shadow-sm disabled:opacity-40 flex items-center gap-1 bg-white hover:bg-gray-100"
                    >
                      {/* Next → */}   Next
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden">
              <div className="grid grid-cols-1 gap-4">
                {paginated.map((row, i) => (
                  <div
                    key={i}
                    className="bg-white rounded-2xl border shadow-sm p-4"
                  >
                    {columns.map((col, j) => (
                      <div key={j} className="flex justify-between text-sm py-1">
                        <span className="text-gray-500">{col}</span>
                        <span className="font-medium text-gray-900 text-right max-w-[60%] break-all">
                          {(() => {
                            const cleanCell = String(row[j] || '').trim();
                            return cleanCell === '' || cleanCell === 'null' || cleanCell === 'undefined' ? '-' : cleanCell;
                          })()}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              
              {/* Mobile pagination */}
              <div className="mt-4 flex flex-col gap-3">
                <div className="text-center text-sm text-gray-600">
                  Showing {start + 1}–{Math.min(end, transactions.length)} of {transactions.length}
                </div>
                <div className="flex items-center justify-center gap-2">
                  <button
                    onClick={prevPage}
                    disabled={page === 0}
                    className="px-4 py-2 rounded-lg shadow-sm disabled:opacity-40 bg-white hover:bg-gray-100 text-sm"
                  >
                    Previous
                  </button>
                  <span className="text-sm font-medium px-3">
                    {page + 1} / {totalPages}
                  </span>
                  <button
                    onClick={nextPage}
                    disabled={page >= totalPages - 1}
                    className="px-4 py-2 rounded-lg shadow-sm disabled:opacity-40 bg-white hover:bg-gray-100 text-sm"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

              {/* Total Transactions */}
              <div className="bg-[rgb(205_216_227)]
                border border-slate-200
                rounded-2xl
                p-6
                shadow-sm
                hover:shadow-md
                transition">
                <div className="text-sm text-slate-600 font-medium">Total Transactions</div>
                <div className="text-2xl font-semibold text-slate-900">{transactions.length}</div>
              </div>

              {/* Opening Balance */}
              <div className="bg-[rgb(205_216_227)]
                border border-slate-200
                rounded-2xl
                p-6
                shadow-sm
                hover:shadow-md
                transition">
                <div className="text-sm text-slate-600 font-medium">Opening Balance</div>
                <div className="text-2xl font-semibold text-slate-900">
                  {(() => {
                    // Use backend provided opening balance if available
                    if (metadata.opening_balance && metadata.opening_balance !== 'null' && metadata.opening_balance !== 'undefined') {
                      const cleanBalance = String(metadata.opening_balance).replace(/[^\d.-]/g, '');
                      const numBalance = parseFloat(cleanBalance);
                      if (!isNaN(numBalance)) {
                        return `₹${numBalance.toLocaleString()}`;
                      }
                    }

                    // Default to 0 if no valid opening balance
                    return "₹0";
                  })()}
                </div>
              </div>

              {/* Closing Balance */}
              <div className="bg-[rgb(205_216_227)]
                border border-slate-200
                rounded-2xl
                p-6
                shadow-sm
                hover:shadow-md
                transition">
                <div className="text-sm text-slate-600 font-medium">Closing Balance</div>
                <div className="text-2xl font-semibold text-slate-900">
                  {(() => {
                    // Use backend provided closing balance if available
                    if (metadata.closing_balance && metadata.closing_balance !== 'null' && metadata.closing_balance !== 'undefined') {
                      const cleanBalance = String(metadata.closing_balance).replace(/[^\d.-]/g, '');
                      const numBalance = parseFloat(cleanBalance);
                      if (!isNaN(numBalance)) {
                        return `₹${numBalance.toLocaleString()}`;
                      }
                    }

                    // Fallback to last transaction balance
                    if (transactions.length === 0 || columns.length === 0) return "₹0";

                    const balanceColIndex = columns.findIndex(col =>
                      String(col).toLowerCase().includes('balance')
                    );

                    if (balanceColIndex === -1) return "₹0";

                    const lastTransaction = transactions[transactions.length - 1];
                    const rawBalance = lastTransaction[balanceColIndex];

                    const cleanBalance = String(rawBalance).trim().replace(/[^\d.-]/g, '');
                    const numBalance = parseFloat(cleanBalance);

                    return `₹${!isNaN(numBalance) ? numBalance.toLocaleString() : '0'}`;
                  })()}
                </div>
              </div>

            </div>

            {/* Download Buttons */}
            <div className="mt-6 flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => {
                  // Check subscription status before opening modal
                  if (!user?.stats?.pages_remaining || user.stats.pages_remaining <= 0) {
                    setCurrentPage('subscription');
                    setError('Page limit reached. Please upgrade your plan to download files.');
                    return;
                  }
                  setShowCsvModal(true);
                }}
                className="w-full sm:w-auto inline-flex items-center gap-2
                  px-8 py-3
                  rounded-xl
                  font-semibold
                  bg-slate-700
                  text-white
                  shadow-md
                  transition-all
                  hover:bg-slate-800
                  active:bg-slate-900
                  justify-center
                "
              >
                {/* <span className="text-lg">📥</span> */}
                <span>Download CSV</span>

                <span
                  className="
                    absolute inset-0 rounded-2xl
                    opacity-0 group-hover:opacity-20
                    bg-white
                    transition-opacity
                  "
                />
              </button>

              <button
                onClick={() => {
                  // Check subscription status before opening modal
                  if (!user?.stats?.pages_remaining || user.stats.pages_remaining <= 0) {
                    setCurrentPage('subscription');
                    setError('Page limit reached. Please upgrade your plan to download files.');
                    return;
                  }

                  // Set dates directly when modal opens
                  if (transactions.length > 0 && columns.length > 0) {
                    const dateColIndex = columns.findIndex(col =>
                      col.toLowerCase().includes('date') && !col.toLowerCase().includes('value')
                    );
                    if (dateColIndex !== -1) {
                      const firstDate = transactions[0][dateColIndex];
                      const lastDate = transactions[transactions.length - 1][dateColIndex];

                      console.log('Setting dates from:', firstDate, 'to:', lastDate);

                      const convertToDateInput = (dateStr) => {
                        if (!dateStr) return '';
                        console.log('Converting date:', dateStr);

                        // Handle YYYY-MM-DD format (from Canara Bank)
                        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                          return dateStr; // Already in correct format
                        }

                        // Handle DD/MM/YYYY format (from HDFC)
                        if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
                          const [day, month, year] = dateStr.split('/');
                          return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
                        }

                        // Handle DD/MM/YY format (2-digit year)
                        if (/^\d{2}\/\d{2}\/\d{2}$/.test(dateStr)) {
                          const [day, month, year] = dateStr.split('/');
                          const fullYear = parseInt(year) < 50 ? '20' + year : '19' + year;
                          return `${fullYear}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
                        }

                        // Handle DD-MM-YYYY format
                        if (/^\d{2}-\d{2}-\d{4}$/.test(dateStr)) {
                          const [day, month, year] = dateStr.split('-');
                          return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
                        }

                        // Handle DD-MM-YY format (2-digit year)
                        if (/^\d{2}-\d{2}-\d{2}$/.test(dateStr)) {
                          const [day, month, year] = dateStr.split('-');
                          const fullYear = parseInt(year) < 50 ? '20' + year : '19' + year;
                          return `${fullYear}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
                        }

                        // Handle DD-MMM-YYYY format (from other banks)
                        const parts = String(dateStr).split(/[-/]/);
                        if (parts.length === 3) {
                          let [day, month, year] = parts;
                          const monthNames = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                          };
                          if (monthNames[month]) {
                            month = monthNames[month];
                          } else {
                            month = month.padStart(2, '0');
                          }
                          if (year.length === 2) year = '20' + year;
                          return `${year}-${month}-${day.padStart(2, '0')}`;
                        }
                        return '';
                      };

                      // Update config with converted dates
                      const fromDate = convertToDateInput(firstDate);
                      const endDate = convertToDateInput(lastDate);

                      console.log('Converted dates:', fromDate, 'to', endDate);

                      setXmlConfig(prev => ({
                        ...prev,
                        fromDate: fromDate,
                        endDate: endDate
                      }));
                    }
                  }
                  setShowXmlModal(true);
                }}
                className="w-full sm:w-auto inline-flex items-center gap-2
                  px-8 py-3
                  rounded-xl
                  font-semibold
                  bg-slate-600
                  text-white
                  shadow-md
                  transition-all
                  hover:bg-slate-700
                  active:bg-slate-800
                  justify-center
                "
              >
                {/* <span className="text-lg">📄</span> */}
                <span>Download XML</span>
              </button>
            </div>
          </div>
        )}

        {/* Add Transaction Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
              <h3 className="text-xl font-semibold mb-4">Add Transaction {addPosition === 'above' ? 'Above' : 'Below'}</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {columns.map((col) => (
                  <div key={col}>
                    <label className="block text-sm font-medium mb-2">{col}</label>
                    <input
                      type="text"
                      value={formData[col] || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, [col]: e.target.value }))}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder={`Enter ${col}`}
                    />
                  </div>
                ))}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={closeModals}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddSubmit}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Add Transaction
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Transaction Modal */}
        {showEditModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
              <h3 className="text-xl font-semibold mb-4">Edit Transaction</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {columns.map((col) => (
                  <div key={col}>
                    <label className="block text-sm font-medium mb-2">{col}</label>
                    <input
                      type="text"
                      value={formData[col] || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, [col]: e.target.value }))}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder={`Enter ${col}`}
                    />
                  </div>
                ))}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={closeModals}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditSubmit}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-sm mx-4">
              <h3 className="text-xl font-semibold mb-4 text-gray-900">Delete Transaction</h3>
              <p className="text-gray-600 mb-6">Are you sure you want to delete this transaction? This action cannot be undone.</p>

              <div className="flex gap-3">
                <button
                  onClick={cancelDelete}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* CSV File Name Modal */}
        {showCsvModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-sm mx-4">
              <h3 className="text-xl font-semibold mb-4">Save CSV File</h3>

              <div>
                <label className="block text-sm font-medium mb-2">File Name</label>
                <input
                  type="text"
                  value={csvFileName}
                  onChange={(e) => setCsvFileName(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Enter file name"
                />
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCsvModal(false)}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCsvDownload}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Download
                </button>
              </div>
            </div>
          </div>
        )}

        {/* XML Configuration Modal */}
        {showXmlModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
              <h3 className="text-xl font-semibold mb-4">Download XML With Bank Name</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Bank Name (As per tally)</label>
                  <input
                    type="text"
                    placeholder="Bank Name (As per tally)"
                    value={xmlConfig.ledgerName}
                    onChange={(e) => setXmlConfig(prev => ({ ...prev, ledgerName: e.target.value }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">From Date</label>
                    <input
                      type="date"
                      value={xmlConfig.fromDate}
                      onChange={(e) => setXmlConfig(prev => ({ ...prev, fromDate: e.target.value }))}
                      className="w-full border rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">To Date</label>
                    <input
                      type="date"
                      value={xmlConfig.endDate}
                      onChange={(e) => setXmlConfig(prev => ({ ...prev, endDate: e.target.value }))}
                      className="w-full border rounded-lg px-3 py-2"
                    />
                  </div>
                </div>

                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-700">
                    Transactions to export: <span className="font-semibold">{filteredCount}</span>
                  </p>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={async () => {
                    try {
                      const response = await fetch(`${API_BASE_URL}/download/tdl`);
                      const blob = await response.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = 'Ledgerit_TDL.zip';
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                    } catch (error) {
                      console.error('Download failed:', error);
                    }
                  }}
                  className="flex-1 px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
                >
                  Tally TDL
                </button>
                <button
                  onClick={handleXmlDownload}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  Download
                </button>
                <button
                  onClick={() => setShowXmlModal(false)}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50 text-gray-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}


      </main>

      {/* Toast Notification */}
      {toast.show && (
        <div className="fixed top-4 right-4 z-[9999] animate-slide-in">
          <div className={`px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px] ${toast.type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
            }`}>
            <span className="text-lg">{toast.type === 'error' ? '⚠️' : '✅'}</span>
            <span className="flex-1">{toast.message}</span>
            <button
              onClick={() => setToast({ show: false, message: '', type: 'error' })}
              className="text-white hover:text-gray-200 text-xl leading-none"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Ledgerit</h4>
              <p className="text-gray-400 text-sm">Convert bank statements to Tally XML effortlessly.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Quick Links</h4>
              <ul className="space-y-1 text-sm">
                <li><button onClick={() => setCurrentPage('home')} className="text-gray-300 hover:text-white">Home</button></li>
                <li><button onClick={() => setCurrentPage('features')} className="text-gray-300 hover:text-white">Features</button></li>
                <li><button onClick={() => setCurrentPage('support')} className="text-gray-300 hover:text-white">Support</button></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Contact</h4>
              <p className="text-gray-300 text-sm">support@ledgerit.com</p>
              <p className="text-gray-300 text-sm">+91 8777654651</p>
            </div>
          </div>
          <div className="border-t border-gray-700 pt-4 text-center text-sm text-gray-400">© 2024 Ledgerit. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}