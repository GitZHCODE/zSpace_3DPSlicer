#!/usr/bin/env python3
"""
Build script for the z3DPSlicer C++/Python integration project.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed!")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"✗ Python 3.9+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required dependencies are available."""
    required_packages = ['compas', 'numpy']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            print(f"✗ {package} not found")
            return False
    return True

def install_dependencies():
    """Install Python dependencies."""
    commands = [
        ("pip install -r requirements.txt", "Installing main dependencies"),
        ("pip install -r requirements-dev.txt", "Installing development dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def build_extensions():
    """Build the C++ extensions."""
    return run_command("pip install -e .", "Building C++ extensions")

def main():
    """Main build process."""
    print("z3DPSlicer C++/Python Integration Project Build Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    print("\nChecking dependencies...")
    if not check_dependencies():
        print("\nInstalling missing dependencies...")
        if not install_dependencies():
            print("Failed to install dependencies")
            sys.exit(1)
    
    # Build extensions
    if not build_extensions():
        print("Failed to build C++ extensions")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ Build completed successfully!")
    print("=" * 50)
    print("\nYou can now run the example:")
    print("  python examples/basic_example.py")
    print("\nOr import the package in Python:")
    print("  import z3DPSlicer as ppc")
    print("  result = ppc.add(5, 3)")

if __name__ == "__main__":
    main() 