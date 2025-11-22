#!/usr/bin/env python
"""
Run Gradio UI with model preloading and shared link.

Usage:
    python run_ui.py
    python run_ui.py --no-share
    python run_ui.py --port 7861
"""
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Run Nanonets OCR UI")
    parser.add_argument("--no-share", action="store_true", help="Disable public URL")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    args = parser.parse_args()

    print("=" * 60)
    print("NANONETS OCR - GRADIO UI")
    print("=" * 60)

    # Initialize model first
    print("\n[1/3] Initializing OCR engine...")
    from core.ocr_engine import get_ocr_engine
    engine = get_ocr_engine()
    engine.initialize()
    print("  ✓ Model loaded successfully")

    # Create interface
    print("\n[2/3] Creating Gradio interface...")
    from ui.app import create_gradio_interface
    demo = create_gradio_interface()
    print("  ✓ Interface created")

    # Launch
    print("\n[3/3] Launching server...")
    share = not args.no_share

    print(f"\n  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Share: {share}")
    print("=" * 60 + "\n")

    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=share
    )


if __name__ == "__main__":
    main()
