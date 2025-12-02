#!/usr/bin/env python3
"""Quick test to verify configuration loads correctly."""

import sys

def test_config():
    """Test that configuration loads without errors."""
    try:
        print("Testing configuration loading...")
        
        # Test 1: Import config module
        print("  1. Importing config module...", end=" ")
        from src.config import get_config
        print("✓")
        
        # Test 2: Load configuration
        print("  2. Loading configuration...", end=" ")
        config = get_config()
        print("✓")
        
        # Test 3: Access system.device (this was the bug)
        print("  3. Accessing config.system.device...", end=" ")
        device = config.system.device
        print(f"✓ (device={device})")
        
        # Test 4: Access other config sections
        print("  4. Accessing other config sections...", end=" ")
        _ = config.pdf.primary_tool
        _ = config.audio.asr_model
        _ = config.embeddings.model
        _ = config.llm.provider
        print("✓")
        
        # Test 5: Verify LLM config
        print("  5. Checking LLM configuration...", end=" ")
        assert config.llm.provider == "local", "LLM provider should be 'local'"
        print(f"✓ (provider={config.llm.provider})")
        
        # Test 6: Verify embeddings config
        print("  6. Checking embeddings configuration...", end=" ")
        assert not config.embeddings.model.startswith("text-embedding"), \
            "Should not use OpenAI embeddings"
        print(f"✓ (model={config.embeddings.model})")
        
        print("\n✅ All configuration tests passed!")
        print(f"\nConfiguration summary:")
        print(f"  - Device: {config.system.device}")
        print(f"  - LLM Provider: {config.llm.provider}")
        print(f"  - LLM Model: {config.llm.local_model}")
        print(f"  - Embeddings: {config.embeddings.model}")
        print(f"  - OCR: {config.pdf.ocr_fallback}")
        print(f"  - ASR: {config.audio.asr_model}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nMissing dependencies. Install with:")
        print("  pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)

