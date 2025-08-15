import argparse
import subprocess
import sys
import os
import time
from typing import List, Optional

try:
    # Optional pretty console. Falls back to prints if unavailable.
    import importlib
    _rc = importlib.import_module("rich.console")
    _rp = importlib.import_module("rich.panel")
    _rprogress = importlib.import_module("rich.progress")
    _rt = importlib.import_module("rich.table")
    Console = getattr(_rc, "Console", None)
    Panel = getattr(_rp, "Panel", None)
    Progress = getattr(_rprogress, "Progress", None)
    SpinnerColumn = getattr(_rprogress, "SpinnerColumn", None)
    TextColumn = getattr(_rprogress, "TextColumn", None)
    BarColumn = getattr(_rprogress, "BarColumn", None)
    TimeElapsedColumn = getattr(_rprogress, "TimeElapsedColumn", None)
    Table = getattr(_rt, "Table", None)
    console = Console()
    RICH = True
except Exception:
    console = None
    RICH = False


def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def print_header():
    title = "Alem Package Installer"
    if RICH:
        console.print(Panel.fit(title, subtitle="Automated dependency management", style="bold blue"))
    else:
        print(title)
        print("=" * len(title))


def run_command_stream(cmd: List[str], description: str, env=None, quiet: bool = False) -> bool:
    """Run a command and stream stdout/stderr live for progress bars (pip)."""
    if RICH and not quiet:
        console.rule(f"[bold]{description}")
    else:
        print(f"\n{description}...")

    start = time.time()
    try:
        # Stream output; keep pip's progress bar intact.
        proc = subprocess.Popen(
            cmd,
            stdout=None if not quiet else subprocess.DEVNULL,
            stderr=None if not quiet else subprocess.DEVNULL,
            env=env,
        )
        ret = proc.wait()
        duration = time.time() - start
        if ret == 0:
            if RICH and not quiet:
                console.print(f"COMPLETED: {description} [dim](duration: {duration:.1f}s)")
            else:
                print(f"COMPLETED: {description} (duration: {duration:.1f}s)")
            return True
        else:
            if RICH and not quiet:
                console.print(f"[red]FAILED: {description} (exit code {ret})")
            else:
                print(f"FAILED: {description} (exit code {ret})")
            return False
    except Exception as e:
        if RICH and not quiet:
            console.print(f"[red]ERROR: {description} - {e}")
        else:
            print(f"ERROR: {description} - {e}")
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
        msg = f"Python 3.8+ required. Current: {sys.version.split()[0]}"
        if RICH:
            console.print(f"[red]REQUIREMENT NOT MET: {msg}")
        else:
            print(f"REQUIREMENT NOT MET: {msg}")
        sys.exit(1)

    if RICH:
        console.print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected\n", style="green")
    else:
        print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Define package groups
    essential = [
        "PyQt6",
        "numpy",
        # sqlite3 is part of the stdlib; don't install via pip
    ]

    optional = [
        "memory-profiler",
        "psutil",
        "Pygments",
        "pyperclip",
    ] if args.optional else []

    ai = []
    if args.ai:
        ai = [
            "transformers",
            "sentence-transformers",
            "torch",
        ]

    # Decide torch index URL if CPU-only
    env = os.environ.copy()
    torch_extra_args: List[str] = []
    if args.ai:
        if args.torch_index:
            torch_extra_args.extend(["--index-url", args.torch_index])
        elif args.cpu_only:
            # Default to CPU-only wheels (smaller, avoids CUDA download)
            torch_extra_args.extend(["--index-url", "https://download.pytorch.org/whl/cpu"])

    # Speed: batch installs per group to avoid repeated resolver runs
    started = time.time()

    # Essentials
    ok = install_packages(
        essential,
        "Installing essential packages",
        env=env,
        verbose=args.verbose,
        quiet=args.quiet,
        dry_run=args.dry_run,
    )
    if not ok:
        eprint("Some essential packages failed to install. Alem may not work properly.")

    # Optional
    if optional:
        install_packages(
            optional,
            "Installing optional enhancements",
            env=env,
            verbose=args.verbose,
            quiet=args.quiet,
            dry_run=args.dry_run,
        )

    # AI
    if ai:
        # Install transformers & sentence-transformers first (fast), then torch with optional index
        non_torch = [p for p in ai if p != "torch"]
        if non_torch:
            install_packages(
                non_torch,
                "Installing AI libraries (NLP)",
                env=env,
                verbose=args.verbose,
                quiet=args.quiet,
                dry_run=args.dry_run,
            )
        # torch separately to apply index-url if provided
        install_packages(
            ["torch"],
            "Installing PyTorch",
            extra_args=torch_extra_args if torch_extra_args else None,
            env=env,
            verbose=args.verbose,
            quiet=args.quiet,
            dry_run=args.dry_run,
        )

    total_time = time.time() - started
    if RICH:
        console.rule("Installation Summary")
        console.print(f"Installation completed in {total_time:.1f} seconds")
    else:
        print("\n" + "=" * 50)
        print(f"Installation completed in {total_time:.1f} seconds")

    # Next steps summary
    if RICH:
        feats = [
            "Modern GUI note-taking interface",
            "SQLite database storage",
            "Search and filtering capabilities",
            "Tag-based organization",
            "Performance monitoring",
        ]
        if args.ai:
            feats.append("AI-powered semantic search")
        else:
            feats.append("Basic keyword search")
        table = Table(title="Available Features")
        table.add_column("Feature")
        for f in feats:
            table.add_row(f)
        console.print(table)
    else:
        print("\nAvailable Features:")
        print("- Modern GUI note-taking interface")
        print("- SQLite database storage")
        print("- Search and filtering capabilities")
        print("- Tag-based organization")
        print("- Performance monitoring")
        print("- AI-powered semantic search" if args.ai else "- Basic keyword search")

    # Post-install test (optional)
    auto_test = args.test
    if not args.yes and not args.dry_run and not args.test:
        try:
            resp = input("\nRun a quick Alem test now? (y/N): ").strip().lower()
            auto_test = resp in {"y", "yes"}
        except EOFError:
            auto_test = False

    if auto_test and not args.dry_run:
        # Prefer launch script if present
        here = os.path.dirname(os.path.abspath(__file__))
        launch_path = os.path.join(here, "launch_alem.py")
        main_path = os.path.join(here, "Alem.py")
        target = launch_path if os.path.exists(launch_path) else main_path
        if not os.path.exists(target):
            eprint("Couldn't find Alem entry point to test.")
        else:
            run_command_stream([sys.executable, target, "--test"], "Testing Alem GUI", quiet=args.quiet)

    if RICH:
        console.print("\nTo launch Alem: [bold]python Alem.py[/bold]\n")
    else:
        print("\nTo launch Alem:")
        print("   python Alem.py\n")


if __name__ == "__main__":
    main()
