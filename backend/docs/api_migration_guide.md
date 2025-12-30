# ExpiryShield API Migration Guide

## Overview

This guide helps you migrate between different versions of the ExpiryShield Backend API. It covers breaking changes, new features, and best practices for version management.

## Version Selection

### Methods to Specify API Version

1. **URL Path (Recommended)**
   ```
   GET /v1.0/risk
   GET /v1.1/risk
   ```

2. **Accept-Version Header**
   ```
   Accept-Version: 1.1
   ```

3. **API-Version Header**
   ```
   API-Version: 1.1
   ```

### Version Resolution Priority

1. URL path version
2. Accept-Version header
3. API-Version header
4. Default version (1.0)

## Version History

### v1.0 (Initial Release)
- **Release Date**: January 1, 2024
- **Status**: Current, Supported
- **Features**:
  - File upload and data ingestion
  - Risk analysis and scoring
  - Action recommendations
  - KPI tracking and reporting
  - Authentication and authorization

### v1.1 (Enhanced Features)
- **Release Date**: February 1, 2024
- **Status**: Current, Recommended
- **New Features**:
  - Bulk operations support
  - Enhanced pagination with metadata
  - Improved error handling with correlation IDs
  - Standardized API response format
- **Backward Compatibility**: Full compatibility with v1.0

## Migration Scenarios

### From v1.0 to v1.1

#### Breaking Changes
**None** - v1.1 maintains full backward compatibility with v1.0.

#### New Features Available

1. **Bulk Operations**
   ```javascript
   // New in v1.1: Bulk file upload
   POST /v1.1/bulk/upload
   
   // New in v1.1: Bulk action operations
   POST /v1.1/bulk/actions
   ```

2. **Enhanced Pagination**
   ```javascript
   // v1.0 response
   [
     { "risk_score": 85.2, ... },
     { "risk_score": 78.1, ... }
   ]
   
   // v1.1 response with metadata
   {
     "success": true,
     "message": "Risk data retrieved successfully",
     "data": [
       { "risk_score": 85.2, ... },
       { "risk_score": 78.1, ... }
     ],
     "metadata": {
       "pagination": {
         "page": 1,
         "page_size": 50,
         "total_count": 150,
         "total_pages": 3,
         "has_next": true,
         "has_previous": false
       }
     }
   }
   ```

3. **Improved Error Responses**
   ```javascript
   // v1.0 error response
   {
     "detail": "Validation failed"
   }
   
   // v1.1 error response
   {
     "success": false,
     "message": "Request validation failed",
     "error_code": "VALIDATION_ERROR",
     "errors": [
       {
         "field": "email",
         "code": "REQUIRED",
         "message": "Email is required"
       }
     ],
     "timestamp": "2024-01-15T10:30:00Z",
     "request_id": "req_123456"
   }
   ```

#### Migration Steps

1. **Update Base URLs** (Optional but Recommended)
   ```javascript
   // Old
   const baseURL = 'https://api.expiryshield.com';
   
   // New
   const baseURL = 'https://api.expiryshield.com/v1.1';
   ```

2. **Update Response Handling** (Optional)
   ```javascript
   // Handle new response format
   const response = await fetch('/v1.1/risk');
   const result = await response.json();
   
   // v1.1 format
   const data = result.data;
   const pagination = result.metadata?.pagination;
   ```

3. **Implement Bulk Operations** (Optional)
   ```javascript
   // Use bulk upload for better performance
   const formData = new FormData();
   files.forEach(file => formData.append('files', file));
   formData.append('request_data', JSON.stringify({
     file_descriptions: descriptions,
     process_sequentially: false
   }));
   
   const response = await fetch('/v1.1/bulk/upload', {
     method: 'POST',
     body: formData
   });
   ```

4. **Update Error Handling** (Optional)
   ```javascript
   try {
     const response = await apiCall();
   } catch (error) {
     // v1.1 provides correlation IDs for debugging
     console.error('Request failed:', error.request_id);
     
     // Handle specific error codes
     if (error.error_code === 'VALIDATION_ERROR') {
       error.errors.forEach(err => {
         console.error(`${err.field}: ${err.message}`);
       });
     }
   }
   ```

## Best Practices

### Version Management

1. **Use Explicit Versioning**
   ```javascript
   // Good: Explicit version in URL
   GET /v1.1/risk
   
   // Avoid: Relying on default version
   GET /risk
   ```

2. **Handle Version Headers**
   ```javascript
   // Check response headers for version info
   const apiVersion = response.headers.get('API-Version');
   const warnings = response.headers.get('API-Compatibility-Warning');
   ```

3. **Monitor Deprecation Warnings**
   ```javascript
   // Log deprecation warnings
   if (response.headers.get('API-Compatibility-Warning')) {
     console.warn('API deprecation warning:', warnings);
   }
   ```

### Error Handling

1. **Use Correlation IDs**
   ```javascript
   // Include correlation ID in error reports
   const correlationId = error.request_id;
   reportError({ message: error.message, correlationId });
   ```

2. **Handle Specific Error Codes**
   ```javascript
   switch (error.error_code) {
     case 'VALIDATION_ERROR':
       handleValidationErrors(error.errors);
       break;
     case 'RATE_LIMIT_EXCEEDED':
       scheduleRetry();
       break;
     default:
       handleGenericError(error);
   }
   ```

### Performance Optimization

1. **Use Bulk Operations**
   ```javascript
   // Instead of multiple single uploads
   files.forEach(file => uploadFile(file));
   
   // Use bulk upload
   bulkUploadFiles(files);
   ```

2. **Implement Pagination**
   ```javascript
   // Handle paginated responses
   let page = 1;
   let allData = [];
   
   do {
     const response = await fetch(`/v1.1/risk?page=${page}`);
     const result = await response.json();
     
     allData.push(...result.data);
     page++;
   } while (result.metadata.pagination.has_next);
   ```

## Version Lifecycle

### Support Policy

- **Current Version**: Latest stable version with all features
- **Supported Versions**: Receive bug fixes and security updates
- **Deprecated Versions**: No new features, limited support
- **Sunset Versions**: No longer supported

### Deprecation Process

1. **Announcement**: 6 months advance notice
2. **Deprecation**: Version marked as deprecated
3. **Sunset Warning**: 3 months before sunset
4. **Sunset**: Version no longer supported

### Monitoring Version Health

```javascript
// Check version status
const versionInfo = await fetch('/version/1.0');
const info = await versionInfo.json();

if (info.data.status === 'deprecated') {
  console.warn('Using deprecated API version');
  
  if (info.data.migration_guide_url) {
    console.info('Migration guide:', info.data.migration_guide_url);
  }
}
```

## Support and Resources

### Documentation
- **API Documentation**: `/docs` (Swagger UI)
- **Alternative Documentation**: `/redoc` (ReDoc)
- **Version Information**: `/version/`

### Getting Help
- **Technical Support**: dev@expiryshield.com
- **Migration Assistance**: Available for enterprise customers
- **Community Forum**: https://community.expiryshield.com

### Tools and SDKs
- **JavaScript SDK**: Handles version management automatically
- **Python SDK**: Includes migration utilities
- **Postman Collection**: Updated for each version

## Troubleshooting

### Common Issues

1. **Version Not Found**
   ```
   Error: Unsupported API version: 2.0
   Solution: Check supported versions at /version/
   ```

2. **Compatibility Warnings**
   ```
   Warning: Requested version 1.0 not found, using compatible version 1.1
   Solution: Update to explicit version or handle compatibility
   ```

3. **Response Format Changes**
   ```
   Error: Cannot read property 'risk_score' of undefined
   Solution: Update response parsing for v1.1 format
   ```

### Debug Steps

1. Check version headers in response
2. Verify endpoint exists in target version
3. Review changelog for breaking changes
4. Test with explicit version specification
5. Contact support with correlation ID if needed