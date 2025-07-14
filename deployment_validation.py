#!/usr/bin/env python3
"""
Comprehensive Deployment Validation Tests
=========================================

This script runs comprehensive validation tests to prevent build failures 
BEFORE attempting Google Cloud deployment. It catches issues like:
- Yarn.lock synchronization problems
- Dependency conflicts  
- Docker build problems
- Python requirements issues
- Cloud Run configuration problems

Run this script BEFORE any deployment attempt to ensure success.
"""

import os
import sys
import subprocess
import json
import yaml
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
import time

class DeploymentValidator:
    def __init__(self):
        self.app_root = Path("/app")
        self.frontend_dir = self.app_root / "frontend"
        self.backend_dir = self.app_root / "backend"
        self.deployment_dir = self.app_root / "deployment"
        
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.warnings = []
        
        print("🚀 Comprehensive Deployment Validation Tests")
        print("=" * 60)
        print("🎯 Goal: Prevent build failures before Google Cloud deployment")
        print("📋 Testing: Frontend, Backend, Docker, Cloud Run configuration")
        print("=" * 60)

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.app_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def test_result(self, name: str, success: bool, details: str = "", critical: bool = True):
        """Record test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            
            if critical:
                self.critical_failures.append(f"{name}: {details}")
            else:
                self.warnings.append(f"{name}: {details}")

    def validate_frontend_build(self) -> bool:
        """Comprehensive frontend build validation"""
        print("\n🔍 FRONTEND BUILD VALIDATION")
        print("-" * 40)
        
        all_passed = True
        
        # Test 1: Check if package.json exists
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            self.test_result("Package.json exists", False, "package.json not found", critical=True)
            return False
        
        self.test_result("Package.json exists", True)
        
        # Test 2: CRITICAL - Check for packageManager field that causes Docker build failures
        print("\n🚨 Testing PackageManager Field (Critical for Docker builds)...")
        try:
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            if 'packageManager' in package_data:
                package_manager = package_data['packageManager']
                self.test_result("PackageManager field check", False, 
                               f"packageManager field '{package_manager}' will cause Docker build failures. Remove this field from package.json", critical=True)
                all_passed = False
            else:
                self.test_result("PackageManager field check", True, "No packageManager field - Docker builds will work")
        except Exception as e:
            self.test_result("PackageManager field check", False, f"Error reading package.json: {e}", critical=True)
            all_passed = False
        
        # Test 3: JSON syntax validation
        print("\n📝 Testing Package.json Syntax...")
        try:
            with open(package_json, 'r') as f:
                json.load(f)
            self.test_result("Package.json syntax", True, "Valid JSON syntax")
        except json.JSONDecodeError as e:
            self.test_result("Package.json syntax", False, f"Invalid JSON: {e}", critical=True)
            all_passed = False
        except Exception as e:
            self.test_result("Package.json syntax", False, f"Error reading file: {e}", critical=True)
            all_passed = False
        
        # Test 4: Yarn.lock synchronization check
        print("\n📦 Testing Yarn.lock Synchronization...")
        yarn_lock = self.frontend_dir / "yarn.lock"
        
        if not yarn_lock.exists():
            self.test_result("Yarn.lock exists", False, "yarn.lock not found - run 'yarn install' first", critical=True)
            all_passed = False
        else:
            self.test_result("Yarn.lock exists", True)
            
            # Test frozen lockfile (simulates Docker --frozen-lockfile)
            success, stdout, stderr = self.run_command(
                ["yarn", "install", "--frozen-lockfile", "--dry-run"],
                cwd=self.frontend_dir,
                timeout=120
            )
            
            if success:
                self.test_result("Frozen lockfile test", True, "yarn.lock synchronized with package.json")
            else:
                self.test_result("Frozen lockfile test", False, 
                               f"yarn.lock out of sync: {stderr[:200]}", critical=True)
                all_passed = False
        
        # Test 5: Check for duplicate yarn.lock files (another source of build failures)
        print("\n🔍 Testing for Duplicate Yarn.lock Files...")
        yarn_lock_files = []
        for root, dirs, files in os.walk(self.app_root):
            # Skip node_modules directories
            if 'node_modules' in root:
                continue
            if 'yarn.lock' in files:
                yarn_lock_files.append(os.path.join(root, 'yarn.lock'))
        
        if len(yarn_lock_files) == 1 and yarn_lock_files[0] == str(self.frontend_dir / "yarn.lock"):
            self.test_result("Duplicate yarn.lock check", True, "Only one yarn.lock file found in correct location")
        elif len(yarn_lock_files) > 1:
            self.test_result("Duplicate yarn.lock check", False, 
                           f"Multiple yarn.lock files found: {yarn_lock_files}. Remove extras to prevent Docker build confusion.", critical=True)
            all_passed = False
        else:
            self.test_result("Duplicate yarn.lock check", False, 
                           f"Unexpected yarn.lock configuration: {yarn_lock_files}", critical=True)
            all_passed = False
        
        # Test 3: Dependency resolution check
        print("\n🔍 Testing Dependency Resolution...")
        success, stdout, stderr = self.run_command(
            ["yarn", "check", "--verify-tree"],
            cwd=self.frontend_dir,
            timeout=60
        )
        
        if success:
            self.test_result("Dependency resolution", True, "All dependencies resolve correctly")
        else:
            # Check if it's a critical error or just warnings
            if "error" in stderr.lower():
                self.test_result("Dependency resolution", False, 
                               f"Dependency conflicts: {stderr[:200]}", critical=True)
                all_passed = False
            else:
                self.test_result("Dependency resolution", True, "Minor warnings only")
        
        # Test 4: Check for outdated dependencies
        print("\n📊 Checking for Outdated Dependencies...")
        success, stdout, stderr = self.run_command(
            ["yarn", "outdated"],
            cwd=self.frontend_dir,
            timeout=60
        )
        
        # yarn outdated returns non-zero when outdated packages exist, but that's not critical
        if "No outdated packages" in stdout or not stdout.strip():
            self.test_result("Outdated dependencies check", True, "All dependencies up to date")
        else:
            outdated_count = len([line for line in stdout.split('\n') if line.strip() and not line.startswith('Package')])
            self.test_result("Outdated dependencies check", True, 
                           f"{outdated_count} outdated packages found (not critical)", critical=False)
        
        # Test 5: Frontend build process
        print("\n🏗️  Testing Frontend Build Process...")
        success, stdout, stderr = self.run_command(
            ["yarn", "build"],
            cwd=self.frontend_dir,
            timeout=300
        )
        
        if success:
            # Check if build directory was created
            build_dir = self.frontend_dir / "build"
            if build_dir.exists():
                self.test_result("Frontend build", True, "Build completed successfully")
            else:
                self.test_result("Frontend build", False, "Build succeeded but no build directory", critical=True)
                all_passed = False
        else:
            self.test_result("Frontend build", False, 
                           f"Build failed: {stderr[:300]}", critical=True)
            all_passed = False
        
        # Test 6: Node.js version compatibility
        print("\n🔧 Testing Node.js Version Compatibility...")
        success, stdout, stderr = self.run_command(["node", "--version"])
        
        if success:
            node_version = stdout.strip()
            # Check if it's Node 20.x (required for our setup)
            if node_version.startswith("v20."):
                self.test_result("Node.js version", True, f"Using {node_version} (compatible)")
            else:
                self.test_result("Node.js version", False, 
                               f"Using {node_version}, expected Node 20.x", critical=False)
        else:
            self.test_result("Node.js version", False, "Could not determine Node.js version", critical=True)
            all_passed = False
        
        return all_passed

    def validate_backend_build(self) -> bool:
        """Comprehensive backend build validation"""
        print("\n🔍 BACKEND BUILD VALIDATION")
        print("-" * 40)
        
        all_passed = True
        
        # Test 1: Check requirements.txt exists
        requirements_file = self.backend_dir / "requirements.txt"
        if not requirements_file.exists():
            self.test_result("Requirements.txt exists", False, "requirements.txt not found", critical=True)
            return False
        
        self.test_result("Requirements.txt exists", True)
        
        # Test 2: Python version compatibility
        print("\n🐍 Testing Python Version Compatibility...")
        success, stdout, stderr = self.run_command(["python3", "--version"])
        
        if success:
            python_version = stdout.strip()
            # Check if it's Python 3.13 or compatible
            if "Python 3.13" in python_version or "Python 3.12" in python_version or "Python 3.11" in python_version:
                self.test_result("Python version", True, f"Using {python_version} (compatible)")
            else:
                self.test_result("Python version", False, 
                               f"Using {python_version}, may have compatibility issues", critical=False)
        else:
            self.test_result("Python version", False, "Could not determine Python version", critical=True)
            all_passed = False
        
        # Test 3: Requirements validation (dry run install)
        print("\n📦 Testing Requirements Installation...")
        
        # Create a temporary virtual environment for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "test_venv"
            
            # Create virtual environment
            success, stdout, stderr = self.run_command(
                ["python3", "-m", "venv", str(venv_path)],
                timeout=60
            )
            
            if not success:
                self.test_result("Virtual environment creation", False, 
                               f"Failed to create test venv: {stderr}", critical=True)
                all_passed = False
            else:
                self.test_result("Virtual environment creation", True)
                
                # Test pip install with requirements
                pip_path = venv_path / "bin" / "pip"
                success, stdout, stderr = self.run_command(
                    [str(pip_path), "install", "-r", str(requirements_file), "--dry-run"],
                    timeout=180
                )
                
                if success:
                    self.test_result("Requirements validation", True, "All requirements can be installed")
                else:
                    # Check if it's a critical error
                    if "error" in stderr.lower() or "failed" in stderr.lower():
                        self.test_result("Requirements validation", False, 
                                       f"Requirements installation failed: {stderr[:300]}", critical=True)
                        all_passed = False
                    else:
                        self.test_result("Requirements validation", True, "Minor warnings only")
        
        # Test 4: OpenAI library verification
        print("\n🤖 Testing OpenAI Library Integration...")
        
        # Test that we can import AsyncOpenAI
        test_script = '''
import sys
try:
    from openai import AsyncOpenAI
    print("SUCCESS: AsyncOpenAI imported successfully")
    
    # Test client instantiation
    client = AsyncOpenAI(api_key="test-key")
    print("SUCCESS: AsyncOpenAI client created successfully")
    
    sys.exit(0)
except ImportError as e:
    print(f"ERROR: Failed to import AsyncOpenAI: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to create AsyncOpenAI client: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = self.run_command(
            ["python3", "-c", test_script],
            cwd=self.backend_dir,
            timeout=30
        )
        
        if success and "SUCCESS" in stdout:
            self.test_result("OpenAI library integration", True, "AsyncOpenAI working correctly")
        else:
            self.test_result("OpenAI library integration", False, 
                           f"OpenAI integration failed: {stderr or stdout}", critical=True)
            all_passed = False
        
        # Test 5: FastAPI server startup test
        print("\n🚀 Testing FastAPI Server Startup...")
        
        # Test that server.py can be imported without errors
        test_script = '''
import sys
import os
sys.path.insert(0, "/app/backend")

try:
    # Set minimal environment variables
    os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
    os.environ.setdefault("DB_NAME", "test_db")
    os.environ.setdefault("FRONTEND_URL", "https://example.com")
    
    from server import app
    print("SUCCESS: FastAPI app imported successfully")
    
    # Test that app is a FastAPI instance
    from fastapi import FastAPI
    if isinstance(app, FastAPI):
        print("SUCCESS: FastAPI app instance created correctly")
    else:
        print("ERROR: app is not a FastAPI instance")
        sys.exit(1)
    
    sys.exit(0)
except Exception as e:
    print(f"ERROR: Failed to import server: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = self.run_command(
            ["python3", "-c", test_script],
            timeout=30
        )
        
        if success and "SUCCESS" in stdout:
            self.test_result("FastAPI server startup", True, "Server can be imported and initialized")
        else:
            self.test_result("FastAPI server startup", False, 
                           f"Server startup failed: {stderr or stdout}", critical=True)
            all_passed = False
        
        return all_passed

    def validate_docker_build(self) -> bool:
        """Simulate Docker build process"""
        print("\n🔍 DOCKER BUILD SIMULATION")
        print("-" * 40)
        
        all_passed = True
        
        # Check if Docker is available
        success, stdout, stderr = self.run_command(["docker", "--version"])
        if not success:
            self.test_result("Docker availability", False, 
                           "Docker not available - skipping Docker tests", critical=False)
            return True  # Not critical for validation
        
        self.test_result("Docker availability", True, f"Docker available: {stdout.strip()}")
        
        # Test 1: Check Dockerfile exists
        frontend_dockerfile = self.deployment_dir / "Dockerfile.frontend" if self.deployment_dir.exists() else None
        backend_dockerfile = self.deployment_dir / "Dockerfile.backend" if self.deployment_dir.exists() else None
        
        if not frontend_dockerfile or not frontend_dockerfile.exists():
            self.test_result("Frontend Dockerfile", False, "Dockerfile.frontend not found", critical=False)
        else:
            self.test_result("Frontend Dockerfile", True)
            
            # Test frontend Docker build (dry run)
            print("\n🏗️  Testing Frontend Docker Build...")
            success, stdout, stderr = self.run_command(
                ["docker", "build", "-f", str(frontend_dockerfile), ".", "--dry-run"],
                cwd=self.app_root,
                timeout=60
            )
            
            if success:
                self.test_result("Frontend Docker build simulation", True, "Docker build syntax valid")
            else:
                # Docker --dry-run might not be supported, try build context validation
                self.test_result("Frontend Docker build simulation", False, 
                               f"Docker build issues: {stderr[:200]}", critical=False)
        
        if not backend_dockerfile or not backend_dockerfile.exists():
            self.test_result("Backend Dockerfile", False, "Dockerfile.backend not found", critical=False)
        else:
            self.test_result("Backend Dockerfile", True)
            
            # Test backend Docker build (dry run)
            print("\n🏗️  Testing Backend Docker Build...")
            success, stdout, stderr = self.run_command(
                ["docker", "build", "-f", str(backend_dockerfile), ".", "--dry-run"],
                cwd=self.app_root,
                timeout=60
            )
            
            if success:
                self.test_result("Backend Docker build simulation", True, "Docker build syntax valid")
            else:
                self.test_result("Backend Docker build simulation", False, 
                               f"Docker build issues: {stderr[:200]}", critical=False)
        
        return self.simulate_docker_build_environment()

    def simulate_docker_build_environment(self) -> bool:
        """Simulate Docker build environment to catch platform-specific issues"""
        print("\n🔍 DOCKER BUILD ENVIRONMENT SIMULATION")
        print("-" * 40)
        
        all_passed = True
        
        # Test 1: Simulate Docker's copy operation and yarn install
        print("\n🐳 Simulating Docker COPY and yarn install...")
        
        # Create a temporary directory to simulate Docker build context
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Copy package.json and yarn.lock as Docker would
                shutil.copy2(self.frontend_dir / "package.json", temp_path / "package.json")
                shutil.copy2(self.frontend_dir / "yarn.lock", temp_path / "yarn.lock")
                
                # Test yarn install --frozen-lockfile in isolated environment
                success, stdout, stderr = self.run_command(
                    ["yarn", "install", "--frozen-lockfile"],
                    cwd=temp_path,
                    timeout=300
                )
                
                if success:
                    self.test_result("Docker build simulation", True, "yarn install --frozen-lockfile works in isolated environment")
                else:
                    # Check for specific error patterns that indicate deployment issues
                    if "lockfile needs to be updated" in stderr:
                        self.test_result("Docker build simulation", False, 
                                       "CRITICAL: yarn.lock synchronization issue detected - this will cause Docker build failure", critical=True)
                        all_passed = False
                    elif "packageManager" in stderr.lower():
                        self.test_result("Docker build simulation", False, 
                                       "CRITICAL: packageManager field issue detected - remove from package.json", critical=True)
                        all_passed = False
                    else:
                        self.test_result("Docker build simulation", False, 
                                       f"Docker build simulation failed: {stderr[:300]}", critical=True)
                        all_passed = False
                
            except Exception as e:
                self.test_result("Docker build simulation", False, 
                               f"Failed to simulate Docker environment: {e}", critical=True)
                all_passed = False
        
        # Test 2: Yarn version compatibility check
        print("\n📦 Testing Yarn Version Compatibility...")
        success, stdout, stderr = self.run_command(["yarn", "--version"])
        
        if success:
            local_yarn_version = stdout.strip()
            
            # Check if package.json has packageManager field
            try:
                with open(self.frontend_dir / "package.json", 'r') as f:
                    package_data = json.load(f)
                
                if 'packageManager' in package_data:
                    package_manager = package_data['packageManager']
                    if 'yarn@' in package_manager:
                        required_version = package_manager.split('@')[1].split('+')[0]
                        if local_yarn_version != required_version:
                            self.test_result("Yarn version compatibility", False, 
                                           f"Local yarn {local_yarn_version} != required {required_version}. Remove packageManager field from package.json", critical=True)
                            all_passed = False
                        else:
                            self.test_result("Yarn version compatibility", True, 
                                           f"Yarn version matches: {local_yarn_version}")
                    else:
                        self.test_result("Yarn version compatibility", False, 
                                       f"Invalid packageManager format: {package_manager}", critical=True)
                        all_passed = False
                else:
                    self.test_result("Yarn version compatibility", True, 
                                   f"No packageManager field - using system yarn {local_yarn_version}")
                    
            except Exception as e:
                self.test_result("Yarn version compatibility", False, 
                               f"Error checking package.json: {e}", critical=True)
                all_passed = False
        else:
            self.test_result("Yarn version compatibility", False, 
                           "Could not determine yarn version", critical=True)
            all_passed = False
        
        return all_passed

    def validate_cloud_run_config(self) -> bool:
        """Validate Cloud Run configuration"""
        print("\n🔍 CLOUD RUN CONFIGURATION VALIDATION")
        print("-" * 40)
        
        all_passed = True
        
        # Test 1: Check cloudbuild.yaml exists
        cloudbuild_file = self.app_root / "cloudbuild.yaml"
        if not cloudbuild_file.exists():
            self.test_result("cloudbuild.yaml exists", False, "cloudbuild.yaml not found", critical=False)
        else:
            self.test_result("cloudbuild.yaml exists", True)
            
            # Test YAML syntax
            try:
                with open(cloudbuild_file, 'r') as f:
                    yaml.safe_load(f)
                self.test_result("cloudbuild.yaml syntax", True, "Valid YAML syntax")
            except yaml.YAMLError as e:
                self.test_result("cloudbuild.yaml syntax", False, 
                               f"Invalid YAML: {str(e)}", critical=True)
                all_passed = False
        
        # Test 2: Environment variables documentation
        print("\n🔧 Testing Environment Variables Configuration...")
        
        # Check backend .env template or documentation
        backend_env = self.backend_dir / ".env"
        frontend_env = self.frontend_dir / ".env"
        
        required_backend_vars = [
            "MONGO_URL", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", 
            "OPENAI_API_KEY", "FRONTEND_URL", "ADMIN_EMAILS"
        ]
        
        required_frontend_vars = [
            "REACT_APP_BACKEND_URL", "REACT_APP_GOOGLE_CLIENT_ID"
        ]
        
        # Check if environment variables are documented or configured
        env_vars_documented = True
        
        if backend_env.exists():
            with open(backend_env, 'r') as f:
                backend_env_content = f.read()
            
            missing_backend_vars = [var for var in required_backend_vars 
                                  if var not in backend_env_content]
            
            if missing_backend_vars:
                self.test_result("Backend environment variables", False, 
                               f"Missing variables: {', '.join(missing_backend_vars)}", critical=False)
                env_vars_documented = False
            else:
                self.test_result("Backend environment variables", True, "All required variables present")
        else:
            self.test_result("Backend .env file", False, "Backend .env file missing", critical=False)
            env_vars_documented = False
        
        if frontend_env.exists():
            with open(frontend_env, 'r') as f:
                frontend_env_content = f.read()
            
            missing_frontend_vars = [var for var in required_frontend_vars 
                                   if var not in frontend_env_content]
            
            if missing_frontend_vars:
                self.test_result("Frontend environment variables", False, 
                               f"Missing variables: {', '.join(missing_frontend_vars)}", critical=False)
                env_vars_documented = False
            else:
                self.test_result("Frontend environment variables", True, "All required variables present")
        else:
            self.test_result("Frontend .env file", False, "Frontend .env file missing", critical=True)
            all_passed = False
        
        # Test 3: Port configuration
        print("\n🔌 Testing Port Configuration...")
        
        # Check if server.py handles PORT environment variable
        server_file = self.backend_dir / "server.py"
        if server_file.exists():
            with open(server_file, 'r') as f:
                server_content = f.read()
            
            if "PORT" in server_content and "os.environ.get" in server_content:
                self.test_result("Port configuration", True, "Server handles dynamic PORT variable")
            else:
                self.test_result("Port configuration", False, 
                               "Server may not handle Cloud Run PORT variable", critical=False)
        else:
            self.test_result("Server file exists", False, "server.py not found", critical=True)
            all_passed = False
        
        return all_passed

    def validate_dependency_conflicts(self) -> bool:
        """Detect dependency conflicts"""
        print("\n🔍 DEPENDENCY CONFLICT DETECTION")
        print("-" * 40)
        
        all_passed = True
        
        # Frontend dependency conflicts
        print("\n📦 Checking Frontend Dependencies...")
        
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                dependencies = package_data.get('dependencies', {})
                dev_dependencies = package_data.get('devDependencies', {})
                
                # Check for common conflict patterns
                conflicts = []
                
                # React version conflicts
                react_version = dependencies.get('react', '')
                react_dom_version = dependencies.get('react-dom', '')
                
                if react_version and react_dom_version:
                    if react_version.split('.')[0] != react_dom_version.split('.')[0]:
                        conflicts.append(f"React version mismatch: react@{react_version} vs react-dom@{react_dom_version}")
                
                # Check for duplicate dependencies in dev and prod
                common_deps = set(dependencies.keys()) & set(dev_dependencies.keys())
                if common_deps:
                    conflicts.append(f"Duplicate dependencies in dev and prod: {', '.join(common_deps)}")
                
                if conflicts:
                    self.test_result("Frontend dependency conflicts", False, 
                                   f"Conflicts found: {'; '.join(conflicts)}", critical=False)
                else:
                    self.test_result("Frontend dependency conflicts", True, "No obvious conflicts detected")
                
            except json.JSONDecodeError:
                self.test_result("Frontend package.json parsing", False, 
                               "Invalid JSON in package.json", critical=True)
                all_passed = False
        
        # Backend dependency conflicts
        print("\n🐍 Checking Backend Dependencies...")
        
        requirements_file = self.backend_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.read().strip().split('\n')
                
                # Parse requirements
                parsed_reqs = {}
                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        # Simple parsing - just get package name
                        pkg_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                        parsed_reqs[pkg_name.lower()] = req.strip()
                
                # Check for common conflicts
                conflicts = []
                
                # Check for known incompatible combinations
                if 'fastapi' in parsed_reqs and 'flask' in parsed_reqs:
                    conflicts.append("FastAPI and Flask both present (unusual)")
                
                if 'asyncio' in parsed_reqs:
                    conflicts.append("asyncio in requirements (built-in module)")
                
                if conflicts:
                    self.test_result("Backend dependency conflicts", False, 
                                   f"Potential issues: {'; '.join(conflicts)}", critical=False)
                else:
                    self.test_result("Backend dependency conflicts", True, "No obvious conflicts detected")
                
            except Exception as e:
                self.test_result("Backend requirements parsing", False, 
                               f"Error parsing requirements.txt: {str(e)}", critical=False)
        
        return all_passed

    def run_comprehensive_validation(self) -> bool:
        """Run all validation tests"""
        print(f"\n🎯 Starting Comprehensive Deployment Validation...")
        print(f"📁 App Root: {self.app_root}")
        print(f"📁 Frontend: {self.frontend_dir}")
        print(f"📁 Backend: {self.backend_dir}")
        
        # Run all validation tests
        results = []
        
        try:
            results.append(self.validate_frontend_build())
        except Exception as e:
            print(f"❌ Frontend validation failed with exception: {str(e)}")
            results.append(False)
        
        try:
            results.append(self.validate_backend_build())
        except Exception as e:
            print(f"❌ Backend validation failed with exception: {str(e)}")
            results.append(False)
        
        try:
            results.append(self.validate_docker_build())
        except Exception as e:
            print(f"❌ Docker validation failed with exception: {str(e)}")
            results.append(False)
        
        try:
            results.append(self.validate_cloud_run_config())
        except Exception as e:
            print(f"❌ Cloud Run validation failed with exception: {str(e)}")
            results.append(False)
        
        try:
            results.append(self.validate_dependency_conflicts())
        except Exception as e:
            print(f"❌ Dependency validation failed with exception: {str(e)}")
            results.append(False)
        
        # Print final results
        self.print_final_results()
        
        # Return True only if all critical tests passed
        return len(self.critical_failures) == 0

    def print_final_results(self):
        """Print comprehensive final results"""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT VALIDATION RESULTS")
        print("=" * 60)
        
        print(f"📈 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES ({len(self.critical_failures)}):")
            for i, failure in enumerate(self.critical_failures, 1):
                print(f"   {i}. {failure}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        print("\n" + "=" * 60)
        
        if len(self.critical_failures) == 0:
            print("🎉 DEPLOYMENT VALIDATION PASSED!")
            print("✅ Safe to proceed with Google Cloud deployment")
            print("🚀 All critical build requirements validated successfully")
        else:
            print("🛑 DEPLOYMENT VALIDATION FAILED!")
            print("❌ DO NOT ATTEMPT DEPLOYMENT - Fix critical issues first")
            print("🔧 Address all critical failures before deployment")
        
        print("=" * 60)

def main():
    """Main entry point"""
    validator = DeploymentValidator()
    
    try:
        success = validator.run_comprehensive_validation()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Validation failed with unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())