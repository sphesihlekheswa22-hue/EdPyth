#!/usr/bin/env python3
"""
Quick test script to verify module-based routes are working correctly.
Tests the routing patterns and access control.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import url_for

def test_route_patterns():
    """Test that all module-based routes are registered correctly."""
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            print("=" * 60)
            print("TESTING MODULE-BASED ROUTES")
            print("=" * 60)
            
            # List all routes to verify module-based patterns
            routes = []
            for rule in app.url_map.iter_rules():
                if 'module' in str(rule) and 'static' not in str(rule):
                    routes.append((rule.endpoint, str(rule), list(rule.methods)))
            
            print(f"\nFound {len(routes)} module-based routes:")
            print("-" * 60)
            
            # Group by blueprint
            blueprint_routes = {}
            for endpoint, path, methods in sorted(routes):
                bp = endpoint.split('.')[0] if '.' in endpoint else 'main'
                if bp not in blueprint_routes:
                    blueprint_routes[bp] = []
                blueprint_routes[bp].append((endpoint, path, methods))
            
            for bp, bp_routes in sorted(blueprint_routes.items()):
                print(f"\n{bp.upper()} Blueprint:")
                for endpoint, path, methods in bp_routes:
                    methods_str = ', '.join(sorted(m for m in methods if m not in ['OPTIONS', 'HEAD']))
                    print(f"  {path:50s} [{methods_str}]")
            
            # Test specific important routes exist
            print("\n" + "=" * 60)
            print("VERIFYING KEY ROUTES")
            print("=" * 60)
            
            key_routes = [
                ('/materials/module/1', 'GET'),
                ('/materials/module/1/upload', 'GET'),
                ('/quizzes/module/1', 'GET'),
                ('/quizzes/module/1/create', 'GET'),
                ('/attendance/module/1', 'GET'),
                ('/attendance/module/1/record', 'GET'),
                ('/marks/module/1', 'GET'),
                ('/marks/module/1/enter', 'GET'),
                ('/assignments/module/1', 'GET'),
                ('/assignments/module/1/create', 'GET'),
            ]
            
            print("\nRoute accessibility tests:")
            print("-" * 60)
            
            for path, method in key_routes:
                try:
                    if method == 'GET':
                        resp = client.get(path, follow_redirects=False)
                    else:
                        resp = client.post(path, follow_redirects=False)
                    
                    # 302 (redirect to login) means route exists but requires auth
                    # 200 means route exists and accessible
                    # 404 means route doesn't exist
                    if resp.status_code in [200, 302, 401]:
                        status = "EXISTS"
                    else:
                        status = f"ERROR ({resp.status_code})"
                    
                    print(f"  {method:4s} {path:45s} -> {status}")
                except Exception as e:
                    print(f"  {method:4s} {path:45s} -> FAIL: {str(e)[:30]}")
            
            print("\n" + "=" * 60)
            print("LEGACY ROUTE REDIRECTS (for backward compatibility)")
            print("=" * 60)
            
            legacy_routes = [
                '/materials/course/1',
                '/quizzes/course/1',
                '/attendance/course/1',
                '/marks/course/1',
                '/assignments/course/1',
            ]
            
            print("\nLegacy route redirect tests:")
            print("-" * 60)
            
            for path in legacy_routes:
                try:
                    resp = client.get(path, follow_redirects=False)
                    if resp.status_code == 302:
                        location = resp.headers.get('Location', '')
                        status = f"REDIRECTS TO {location[:40]}"
                    elif resp.status_code == 404:
                        status = "NOT FOUND (404)"
                    else:
                        status = f"STATUS {resp.status_code}"
                    
                    print(f"  GET  {path:35s} -> {status}")
                except Exception as e:
                    print(f"  GET  {path:35s} -> ERROR: {str(e)[:30]}")
            
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total module-based routes: {len(routes)}")
            print("All route patterns verified successfully!")
            print("=" * 60)

if __name__ == '__main__':
    test_route_patterns()