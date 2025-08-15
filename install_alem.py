import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("Alem Installation Script")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Install essential dependencies
    essential_packages = [
        "PyQt6",
        "numpy", 
        "sqlite3"  # Usually built-in
    ]

    print("\n📦 Installing essential packages...")
    for package in essential_packages:
        if package == "sqlite3":
            continue  # Skip sqlite3 as it's built-in

        if not run_command(f"{sys.executable} -m pip install {package}", 
                          f"Installing {package}"):
            print(f"⚠️ Failed to install {package}. Alem may not work properly.")

    # Ask about AI features
    print("\n🧠 AI Features Setup")
    print("Alem can run with basic search or full AI semantic search.")

    choice = input("Install AI dependencies? (y/n) [default: n]: ").strip().lower()

    if choice in ['y', 'yes']:
        ai_packages = [
            "sentence-transformers",
            "torch",  
            "transformers"
        ]

        print("Installing AI packages (this may take a while)...")
        for package in ai_packages:
            run_command(f"{sys.executable} -m pip install {package}", 
                       f"Installing {package}")

    # Install optional packages
    optional_packages = [
        "memory-profiler",
        "psutil",
        "Pygments", 
        "pyperclip"
    ]

    print("\n🔧 Installing optional enhancements...")
    for package in optional_packages:
        run_command(f"{sys.executable} -m pip install {package}", 
                   f"Installing {package}")

    print("\n" + "=" * 50)
    print(" Alem installation completed!")
    print("\n To run Alem:")
    print("   python Alem.py")
    print("\n Features available:")
    print("• Modern GUI note-taking interface")
    print("• SQLite database storage") 
    print("• Search and filtering")
    print("• Tag-based organization")
    print("• Performance monitoring")

    if choice in ['y', 'yes']:
        print("• AI-powered semantic search")
    else:
        print("• Basic keyword search (AI features not installed)")

    # Test the installation
    test_choice = input("\nTest Alem now? (y/n) [default: n]: ").strip().lower()
    if test_choice in ['y', 'yes']:
        print("\n Testing Alem...")
        if run_command(f"{sys.executable} alem.py --test", 
                      "Testing Alem GUI"):
            print("✅ Alem is ready to use!")
        else:
            print("⚠️ There may be issues. Check the error messages above.")

if __name__ == "__main__":
    main()
