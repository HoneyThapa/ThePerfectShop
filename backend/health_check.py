#!/usr/bin/env python3
"""
Health check script for ExpiryShield Backend.

This script can be used by deployment systems, load balancers,
and monitoring tools to verify the application is healthy.
"""

import sys
import requests
import json
import argparse
from typing import Dict, Any
import time


def check_endpoint(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Check a single endpoint and return status."""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = (time.time() - start_time) * 1000
        
        return {
            'url': url,
            'status_code': response.status_code,
            'response_time_ms': round(response_time, 2),
            'healthy': response.status_code == 200,
            'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'status_code': None,
            'response_time_ms': timeout * 1000,
            'healthy': False,
            'error': 'Timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'url': url,
            'status_code': None,
            'response_time_ms': None,
            'healthy': False,
            'error': 'Connection Error'
        }
    except Exception as e:
        return {
            'url': url,
            'status_code': None,
            'response_time_ms': None,
            'healthy': False,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Health check for ExpiryShield Backend')
    parser.add_argument('--host', default='localhost', help='Host to check')
    parser.add_argument('--port', default='8000', help='Port to check')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    # Define endpoints to check
    endpoints = [
        f"{base_url}/health",
        f"{base_url}/health/ready",
        f"{base_url}/health/live",
        f"{base_url}/monitoring/health/detailed",
        f"{base_url}/docs"  # API documentation
    ]
    
    results = []
    overall_healthy = True
    
    for endpoint in endpoints:
        if args.verbose:
            print(f"Checking {endpoint}...")
        
        result = check_endpoint(endpoint, args.timeout)
        results.append(result)
        
        if not result['healthy']:
            overall_healthy = False
        
        if args.verbose and not args.json:
            status = "✓" if result['healthy'] else "✗"
            print(f"  {status} {endpoint} - {result.get('status_code', 'ERROR')} ({result.get('response_time_ms', 'N/A')}ms)")
    
    # Summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'overall_healthy': overall_healthy,
        'total_endpoints': len(endpoints),
        'healthy_endpoints': sum(1 for r in results if r['healthy']),
        'unhealthy_endpoints': sum(1 for r in results if not r['healthy']),
        'average_response_time_ms': round(
            sum(r['response_time_ms'] for r in results if r['response_time_ms'] is not None) / 
            len([r for r in results if r['response_time_ms'] is not None]), 2
        ) if any(r['response_time_ms'] is not None for r in results) else None,
        'results': results
    }
    
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\nHealth Check Summary:")
        print(f"Overall Status: {'HEALTHY' if overall_healthy else 'UNHEALTHY'}")
        print(f"Endpoints: {summary['healthy_endpoints']}/{summary['total_endpoints']} healthy")
        if summary['average_response_time_ms']:
            print(f"Average Response Time: {summary['average_response_time_ms']}ms")
        
        if not overall_healthy:
            print("\nUnhealthy Endpoints:")
            for result in results:
                if not result['healthy']:
                    error_msg = result.get('error', f"HTTP {result.get('status_code', 'Unknown')}")
                    print(f"  ✗ {result['url']} - {error_msg}")
    
    # Exit with appropriate code
    sys.exit(0 if overall_healthy else 1)


if __name__ == '__main__':
    main()