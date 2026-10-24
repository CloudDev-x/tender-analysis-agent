#!/usr/bin/env python3
"""
Build Lambda .zip packages for all 14 handler functions.
Portable across Windows, Linux, macOS.
"""

import os
import shutil
import zipfile
from pathlib import Path

def zip_directory(folder_path, output_path):
    """Zip a directory."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    build_dir = project_root / "build" / "lambda"
    output_dir = project_root / "infrastructure" / "lambda-packages"
    
    print("Building Lambda packages for Mayzerock Tender System...")
    build_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure src/__init__.py exists
    src_init = project_root / "src" / "__init__.py"
    if not src_init.exists():
        src_init.write_text("")
    
    # Build Lambda Layer
    print("Building Lambda Layer (shared code)...")
    layer_dir = build_dir / "python" / "lib" / "python3.11" / "site-packages"
    layer_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy src to layer
    shutil.copytree(project_root / "src", layer_dir / "src", dirs_exist_ok=True)
    
    # Install dependencies to layer
    os.system(f"python -m pip install boto3 botocore pydantic pydantic-settings python-json-logger -t \"{layer_dir}\" --quiet")
    
    # Zip layer
    layer_zip = output_dir / "lambda_layer_shared.zip"
    zip_directory(build_dir / "python", layer_zip)
    print(f"✓ Lambda Layer built: {layer_zip}")
    
    # Handler functions
    handlers = [
        "intake",
        "document_profile",
        "textract",
        "ocr_quality",
        "normalize",
        "extract_requirements",
        "retrieve_evidence",
        "compliance",
        "risk_analysis",
        "bid_drafting",
        "output_validation",
        "persistence",
        "notification",
        "failure_handler",
    ]
    
    # Build .zip for each handler
    for handler in handlers:
        print(f"Building lambda_{handler}.zip...")
        
        handler_dir = build_dir / f"handler_{handler}"
        if handler_dir.exists():
            shutil.rmtree(handler_dir)
        handler_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy handler file
        shutil.copy(
            project_root / "src" / "handlers" / f"{handler}.py",
            handler_dir / f"{handler}.py"
        )
        
        # Copy shared code
        for module in ["config", "models", "repositories", "services", "prompts"]:
            src_module = project_root / "src" / module
            if src_module.exists():
                shutil.copytree(
                    src_module,
                    handler_dir / "src" / module,
                    dirs_exist_ok=True
                )
        
        # Copy __init__.py
        if src_init.exists():
            shutil.copy(src_init, handler_dir / "src" / "__init__.py")
        else:
            (handler_dir / "src" / "__init__.py").write_text("")
        
        # Create handlers __init__.py
        handlers_init = handler_dir / "src" / "handlers"
        handlers_init.mkdir(parents=True, exist_ok=True)
        (handlers_init / "__init__.py").write_text("")
        
        # Zip handler
        handler_zip = output_dir / f"lambda_{handler}.zip"
        zip_directory(handler_dir, handler_zip)
        print(f"✓ lambda_{handler}.zip built")
    
    print()
    print("All Lambda packages built successfully:")
    for f in sorted(output_dir.glob("lambda_*.zip")):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name}: {size_mb:.1f} MB")
    
    print()
    print("Next steps:")
    print("1. Update infrastructure/environments/prod/terraform.tfvars with bedrock_kb_id")
    print("2. Run: cd infrastructure/environments/prod && terraform apply")

if __name__ == "__main__":
    main()
