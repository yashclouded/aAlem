import argparse
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


def pip_base_args(verbose: bool = False, quiet: bool = False) -> List[str]:
    args = [sys.executable, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check"]
    if verbose:
        args.append("-v")
    if quiet:
        args.append("-q")
    return args


def install_packages(packages: List[str], description: str, *, extra_args: Optional[List[str]] = None, env=None, verbose=False, quiet=False, dry_run=False) -> bool:
    pkgs = [p for p in packages if p and p != "sqlite3"]
    if not pkgs:
        return True

    if dry_run:
        if RICH:
            table = Table(title=description)
            table.add_column("Package")
            for p in pkgs:
                table.add_row(p)
            console.print(table)
        else:
            print(f"\n{description} (dry run):")
            for p in pkgs:
                print(f"  - {p}")
        return True

    args = pip_base_args(verbose=verbose, quiet=quiet)
    if extra_args:
        args.extend(extra_args)
    args.extend(pkgs)
    return run_command_stream(args, description, env=env, quiet=quiet)


def main():
    parser = argparse.ArgumentParser(description="Alem installer with progress and flags")
    parser.add_argument("--yes", "-y", action="store_true", help="Run non-interactively; assume yes to prompts")
    parser.add_argument("--ai", dest="ai", action="store_true", help="Install AI features (torch, transformers, sentence-transformers)")
    parser.add_argument("--no-ai", dest="ai", action="store_false", help="Skip AI features")
    parser.set_defaults(ai=False)
    parser.add_argument("--cpu-only", action="store_true", help="Install CPU-only PyTorch (faster, smaller)")
    parser.add_argument("--optional", dest="optional", action="store_true", help="Install optional enhancements")
    parser.add_argument("--no-optional", dest="optional", action="store_false", help="Skip optional enhancements")
    parser.set_defaults(optional=True)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be installed without making changes")
    parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output noise")
    parser.add_argument("--verbose", "-v", action="store_true", help="Increase output verbosity for pip")
    parser.add_argument("--test", action="store_true", help="Launch a quick post-install test of Alem")
    parser.add_argument("--torch-index", default=None, help="Override index URL for torch (e.g. https://download.pytorch.org/whl/cpu)")

    args = parser.parse_args()

    print_header()

    # Check Python version early
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Define package groups
    essential = [
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
    print("🎉 Alem installation completed!")
    print("\n🚀 To run Alem:")
    print("   python Alem.py")
    print("\n📚 Features available:")
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
        print("\n🧪 Testing Alem...")
        if run_command(f"{sys.executable} alem.py --test", 
                      "Testing Alem GUI"):
            print("✅ Alem is ready to use!")
        else:
            run_command_stream([sys.executable, target, "--test"], "Testing Alem GUI", quiet=args.quiet)

    if RICH:
        console.print("\n🚀 To run Alem: [bold]python Alem.py[/bold]\n")
    else:
        print("\n🚀 To run Alem:\n   python Alem.py\n")


if __name__ == "__main__":
    main()
