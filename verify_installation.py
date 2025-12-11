#!/usr/bin/env python3
"""
Harmonix Installation Verification Script
Tests that all components are properly installed and configured
"""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (requires 3.10+)")
        return False


def check_dependency(package_name, import_name=None):
    """Check if a package is installed"""
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
        print(f"   ✅ {package_name}")
        return True
    except ImportError:
        print(f"   ❌ {package_name} (not installed)")
        return False


def check_dependencies():
    """Check all required dependencies"""
    print("\n🔍 Checking dependencies...")
    
    deps = [
        ("torch", "torch"),
        ("torchaudio", "torchaudio"),
        ("demucs", "demucs"),
        ("librosa", "librosa"),
        ("soundfile", "soundfile"),
        ("numpy", "numpy"),
        ("FastAPI", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
    ]
    
    results = [check_dependency(name, import_name) for name, import_name in deps]
    return all(results)


def check_harmonix_modules():
    """Check Harmonix modules can be imported"""
    print("\n🔍 Checking Harmonix modules...")
    
    modules = [
        "harmonix_splitter",
        "harmonix_splitter.core.separator",
        "harmonix_splitter.analysis.detector",
        "harmonix_splitter.core.preprocessor",
        "harmonix_splitter.core.orchestrator",
        "harmonix_splitter.api.main",
        "harmonix_splitter.cli",
        "harmonix_splitter.config.settings",
    ]
    
    results = []
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"   ✅ {module}")
            results.append(True)
        except Exception as e:
            print(f"   ❌ {module}: {e}")
            results.append(False)
    
    return all(results)


def check_directories():
    """Check required directories exist"""
    print("\n🔍 Checking directories...")
    
    base_dir = Path(__file__).parent
    dirs = [
        base_dir / "data" / "uploads",
        base_dir / "data" / "outputs",
        base_dir / "data" / "temp",
        base_dir / "models",
        base_dir / "logs",
    ]
    
    results = []
    for dir_path in dirs:
        if dir_path.exists():
            print(f"   ✅ {dir_path.relative_to(base_dir)}")
            results.append(True)
        else:
            print(f"   ❌ {dir_path.relative_to(base_dir)} (missing)")
            results.append(False)
    
    return all(results)


def check_gpu():
    """Check GPU availability"""
    print("\n🔍 Checking GPU support...")
    try:
        import torch
        if torch.cuda.is_available():
            device = torch.cuda.get_device_name(0)
            print(f"   ✅ GPU available: {device}")
            return True
        else:
            print("   ⚠️  No GPU detected (will use CPU)")
            return True
    except Exception as e:
        print(f"   ❌ GPU check failed: {e}")
        return False


def check_ffmpeg():
    """Check ffmpeg availability"""
    print("\n🔍 Checking ffmpeg...")
    import shutil
    
    if shutil.which("ffmpeg"):
        print("   ✅ ffmpeg available")
        return True
    else:
        print("   ⚠️  ffmpeg not found (some features may not work)")
        return True  # Not critical


def main():
    """Run all checks"""
    print("=" * 60)
    print("   Harmonix Installation Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Harmonix Modules", check_harmonix_modules),
        ("Directories", check_directories),
        ("GPU Support", check_gpu),
        ("FFmpeg", check_ffmpeg),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name} check failed with error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("   Summary")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Harmonix is ready to use.")
        print("\nQuick start:")
        print("  python -m harmonix_splitter.cli --help")
        print("  uvicorn harmonix_splitter.api.main:app --reload")
    else:
        print("⚠️  Some checks failed. Please review errors above.")
        print("\nInstallation:")
        print("  pip install -r requirements.txt")
        print("  pip install -e .")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
