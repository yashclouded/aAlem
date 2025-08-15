"""
Alem Launcher
Cross-platform launcher with error handling
"""
import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    required = ['PyQt6']
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    return missing

def main():
    print("Alem Launcher")
    print("-" * 30)

    # Check for missing dependencies
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("\n Please install dependencies first:")
        print("   pip install PyQt6")
        print("   or run: python install_alem.py")
        return

    # Check if alem.py exists
    if not os.path.exists('alem.py'):
        print("❌ alem.py not found in current directory")
        print("Please make sure the Alem application file is present.")
        return

    print("All dependencies found")
    print("Launching Alem...")

    try:
        # Launch the main application
        subprocess.run([sys.executable, 'alem.py'], check=True)
    except KeyboardInterrupt:
        print("\n Alem closed by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Alem: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure PyQt6 is installed: pip install PyQt6")
        print("2. Check Python version (3.8+ required)")
        print("3. Try running directly: python alem.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
