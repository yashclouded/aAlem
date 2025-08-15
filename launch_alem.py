#!/usr/bin/env python3
"""
Alem Launcher - Fast, reliable application launcher
"""
import argparse
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional

try:
    # Optional pretty console (fallback gracefully)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    console = Console()
    RICH = True
except ImportError:
    console = None
    RICH = False


def print_header():
    """Display launcher header"""
    if RICH:
        console.print(Panel.fit("Alem Launcher", subtitle="v1.0 • Fast • Reliable", style="bold blue"))
    else:
        print("Alem Launcher v1.0")
        print("=" * 20)


def check_python_version() -> bool:
    """Verify Python version compatibility"""
    if sys.version_info < (3, 8):
        if RICH:
            console.print(f"[red]❌ Python 3.8+ required. Current: {sys.version.split()[0]}")
        else:
            print(f"❌ Python 3.8+ required. Current: {sys.version.split()[0]}")
        return False
    return True


def check_dependencies(verbose: bool = False) -> List[str]:
    """Fast dependency check with detailed info if requested"""
    deps = {
        'PyQt6': 'GUI framework',
        'numpy': 'Numerical computing',
        'sqlite3': 'Database (built-in)'
    }
    
    missing = []
    if verbose and RICH:
        table = Table(title="Dependency Status")
        table.add_column("Package", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Description", style="dim")
    
    for pkg, desc in deps.items():
        try:
            if pkg == 'sqlite3':
                import sqlite3  # Built-in, always available
                status = "✅ Built-in"
            else:
                __import__(pkg)
                status = "✅ Available"
        except ImportError:
            missing.append(pkg)
            status = "❌ Missing"
        
        if verbose and RICH:
            table.add_row(pkg, status, desc)
    
    if verbose and RICH:
        console.print(table)
    
    return missing


def find_alem_executable() -> Optional[Path]:
    """Locate the main Alem application file"""
    candidates = ['Alem.py', 'alem.py', 'main.py']
    here = Path(__file__).parent
    
    for candidate in candidates:
        path = here / candidate
        if path.exists():
            return path
    
    return None


def launch_alem(target: Path, args: List[str], quiet: bool = False) -> bool:
    """Launch Alem with proper error handling"""
    cmd = [sys.executable, str(target)] + args
    
    if not quiet:
        if RICH:
            console.print(f"🚀 Launching [bold]{target.name}[/bold]...")
        else:
            print(f"🚀 Launching {target.name}...")
    
    try:
        start = time.time()
        proc = subprocess.run(cmd, check=True)
        duration = time.time() - start
        
        if not quiet:
            if RICH:
                console.print(f"✅ Alem closed normally [dim](ran for {duration:.1f}s)")
            else:
                print(f"✅ Alem closed normally (ran for {duration:.1f}s)")
        return True
        
    except KeyboardInterrupt:
        if not quiet:
            print("\n⏹️  Alem interrupted by user")
        return True
        
    except subprocess.CalledProcessError as e:
        if RICH:
            console.print(f"[red]❌ Alem exited with error code {e.returncode}")
        else:
            print(f"❌ Alem exited with error code {e.returncode}")
        return False
        
    except FileNotFoundError:
        if RICH:
            console.print(f"[red]❌ Python interpreter not found: {sys.executable}")
        else:
            print(f"❌ Python interpreter not found: {sys.executable}")
        return False
        
    except Exception as e:
        if RICH:
            console.print(f"[red]❌ Unexpected error: {e}")
        else:
            print(f"❌ Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Alem application launcher")
    parser.add_argument("--check", "-c", action="store_true", help="Check dependencies and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed dependency info")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--install", action="store_true", help="Run installer if dependencies missing")
    parser.add_argument("--force", action="store_true", help="Skip dependency checks and launch anyway")
    parser.add_argument("args", nargs="*", help="Arguments to pass to Alem")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_header()
    
    # Fast Python version check
    if not check_python_version():
        sys.exit(1)
    
    # Dependency verification
    if not args.force:
        missing = check_dependencies(verbose=args.verbose)
        
        if args.check:
            if missing:
                if RICH:
                    console.print(f"[red]Missing: {', '.join(missing)}")
                else:
                    print(f"Missing: {', '.join(missing)}")
                sys.exit(1)
            else:
                if RICH:
                    console.print("[green]✅ All dependencies satisfied")
                else:
                    print("✅ All dependencies satisfied")
                sys.exit(0)
        
        if missing:
            if RICH:
                console.print(f"[yellow]⚠️  Missing dependencies: {', '.join(missing)}")
            else:
                print(f"⚠️  Missing dependencies: {', '.join(missing)}")
            
            if args.install:
                installer = Path(__file__).parent / "install_alem.py"
                if installer.exists():
                    if RICH:
                        console.print("🔧 Running installer...")
                    else:
                        print("🔧 Running installer...")
                    subprocess.run([sys.executable, str(installer), "--yes", "--quiet"])
                else:
                    if RICH:
                        console.print("[red]❌ install_alem.py not found")
                    else:
                        print("❌ install_alem.py not found")
                    sys.exit(1)
            else:
                if RICH:
                    console.print("\n[bold]Quick fix:[/bold]")
                    console.print("  python install_alem.py --yes")
                    console.print("  [dim]or[/dim] python launch_alem.py --install")
                else:
                    print("\nQuick fix:")
                    print("  python install_alem.py --yes")
                    print("  or python launch_alem.py --install")
                sys.exit(1)
    
    # Find and launch Alem
    target = find_alem_executable()
    if not target:
        if RICH:
            console.print("[red]❌ Alem application not found")
            console.print("[dim]Expected: Alem.py, alem.py, or main.py")
        else:
            print("❌ Alem application not found")
            print("Expected: Alem.py, alem.py, or main.py")
        sys.exit(1)
    
    # Launch with timing
    success = launch_alem(target, args.args, quiet=args.quiet)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
