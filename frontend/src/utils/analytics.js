/* global gtag */
// Google Analytics tracking functions
export const trackEvent = (eventName, parameters = {}) => {
  if (typeof gtag !== 'undefined') {
    gtag('event', eventName, parameters);
  }
};

export const trackFileUpload = (fileType, fileSize) => {
  trackEvent('file_upload', {
    file_type: fileType,
    file_size: fileSize
  });
};

export const trackConversion = (conversionType, transactionCount) => {
  trackEvent('conversion', {
    conversion_type: conversionType,
    transaction_count: transactionCount
  });
};

export const trackError = (errorType, errorMessage) => {
  trackEvent('error', {
    error_type: errorType,
    error_message: errorMessage
  });
};