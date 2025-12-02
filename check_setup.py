#!/usr/bin/env python3
"""Check if the Study Assistant setup is complete."""

import sys
from pathlib import Path

def check_dependencies():
    """Check if required Python packages are installed."""
    print("=" * 70)
    print("Checking Python Dependencies...")
    print("=" * 70)
    
    required = {
        "yaml": "pyyaml",
        "pydantic": "pydantic",
        "sentence_transformers": "sentence-transformers",
        "llama_cpp": "llama-cpp-python",
        "faiss": "faiss-gpu or faiss-cpu",
        "pdfplumber": "pdfplumber",
        "pytesseract": "pytesseract",
        "whisper": "openai-whisper",
    }
    
    missing = []
    installed = []
    
    for module, package in required.items():
        try:
            __import__(module)
            installed.append(f"✓ {package}")
        except ImportError:
            missing.append(f"✗ {package}")
    
    for pkg in installed:
        print(pkg)
    
    if missing:
        print("\n" + "=" * 70)
        print("Missing Dependencies:")
        print("=" * 70)
        for pkg in missing:
            print(pkg)
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All required dependencies installed!")
    return True


def check_models():
    """Check if GGUF model is downloaded."""
    print("\n" + "=" * 70)
    print("Checking Models...")
    print("=" * 70)
    
    models_dir = Path("models")
    
    if not models_dir.exists():
        print("✗ models/ directory not found")
        print("\nCreate it with: mkdir models")
        return False
    
    gguf_files = list(models_dir.glob("*.gguf"))
    
    if not gguf_files:
        print("✗ No GGUF model found in models/ directory")
        print("\nDownload a model:")
        print("  pip install huggingface-hub")
        print("  huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \\")
        print("    mistral-7b-instruct-v0.2.Q4_K_M.gguf \\")
        print("    --local-dir models/ --local-dir-use-symlinks False")
        print("\nSee MODELS_GUIDE.md for more options.")
        return False
    
    print(f"✓ Found {len(gguf_files)} GGUF model(s):")
    for model in gguf_files:
        size_mb = model.stat().st_size / (1024 * 1024)
        print(f"  - {model.name} ({size_mb:.1f} MB)")
    
    return True


def check_config():
    """Check if config.yaml is properly set up."""
    print("\n" + "=" * 70)
    print("Checking Configuration...")
    print("=" * 70)
    
    config_file = Path("config/config.yaml")
    
    if not config_file.exists():
        print("✗ config/config.yaml not found")
        return False
    
    print("✓ config/config.yaml exists")
    
    # Try to load config
    try:
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)
        print("✓ config.yaml is valid YAML")
        
        # Check LLM model name
        llm_model = config.get("llm", {}).get("local", {}).get("model", "")
        if llm_model:
            print(f"✓ LLM model configured: {llm_model}")
            
            # Check if model file exists
            model_path = Path("models") / f"{llm_model}.gguf"
            if model_path.exists():
                print(f"✓ Model file found: {model_path}")
            else:
                print(f"⚠ Model file not found: {model_path}")
                print(f"  Make sure the model name in config.yaml matches your downloaded file")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False


def main():
    """Run all checks."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Study Assistant Setup Check" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    deps_ok = check_dependencies()
    models_ok = check_models()
    config_ok = check_config()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    if deps_ok and models_ok and config_ok:
        print("✓ Setup complete! You're ready to run the Study Assistant.")
        print("\nTry: python examples/basic_usage.py")
        return 0
    else:
        print("✗ Setup incomplete. Please fix the issues above.")
        print("\nQuick setup:")
        print("  1. pip install -r requirements.txt")
        print("  2. Download a GGUF model (see MODELS_GUIDE.md)")
        print("  3. Update config.yaml with model name")
        return 1


if __name__ == "__main__":
    sys.exit(main())

