# Step 0: setup_confusion_matrix.py
# This script checks requirements and sets up the environment

import sys
import subprocess
import importlib

def check_and_install_packages():
    """Check and install required packages"""
    
    required_packages = [
        'numpy',
        'pandas', 
        'matplotlib',
        'seaborn',
        'scikit-learn'
    ]
    
    print("=== PAM System Confusion Matrix Setup ===")
    print("Checking required packages...\n")
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Successfully installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                print(f"Please install manually: pip install {package}")
                return False
    
    print(f"\n🎉 All required packages are available!")
    return True

def create_directory_structure():
    """Create necessary directories for outputs"""
    
    import os
    
    directories = [
        'confusion_matrix_results',
        'confusion_matrix_results/figures',
        'confusion_matrix_results/data',
        'confusion_matrix_results/reports'
    ]
    
    print(f"\n📁 Creating directory structure...")
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created: {directory}")
        else:
            print(f"✅ Exists: {directory}")

def display_execution_plan():
    """Display the step-by-step execution plan"""
    
    print(f"\n" + "="*60)
    print("EXECUTION PLAN - CONFUSION MATRIX ANALYSIS")
    print("="*60)
    
    steps = [
        {
            "step": "Step 1", 
            "file": "confusion_matrix_generator.py",
            "description": "Generate realistic test data based on your PAM system",
            "output": "pam_confusion_matrix_data.csv"
        },
        {
            "step": "Step 2", 
            "file": "confusion_matrix_visualizer.py", 
            "description": "Create professional confusion matrix visualization",
            "output": "figure_6_3_confusion_matrix.png"
        },
        {
            "step": "Step 3", 
            "file": "classification_report_generator.py",
            "description": "Generate detailed classification report table", 
            "output": "figure_6_4_classification_report.png"
        },
        {
            "step": "Step 4", 
            "file": "roc_curve_generator.py",
            "description": "Create ROC curves and AUC analysis",
            "output": "figure_6_5_roc_curves.png"
        }
    ]
    
    for step_info in steps:
        print(f"\n🔸 {step_info['step']}: {step_info['file']}")
        print(f"   Purpose: {step_info['description']}")
        print(f"   Output: {step_info['output']}")
    
    print(f"\n💡 Execution Instructions:")
    print(f"   1. Run each script in order (Step 1 → Step 2 → Step 3 → Step 4)")
    print(f"   2. Each script depends on the previous one's output")
    print(f"   3. All figures will be saved in high-quality PNG and PDF formats")
    print(f"   4. Detailed analysis will be printed to console and saved to files")

def run_quick_test():
    """Run a quick test to ensure everything works"""
    
    print(f"\n🧪 Running quick functionality test...")
    
    try:
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.metrics import confusion_matrix
        
        # Quick test
        y_true = [0, 1, 2, 3, 0, 1, 2, 3]
        y_pred = [0, 1, 2, 2, 0, 1, 3, 3]
        cm = confusion_matrix(y_true, y_pred)
        
        print(f"✅ All libraries working correctly!")
        print(f"✅ Test confusion matrix shape: {cm.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting PAM System Confusion Matrix Setup...\n")
    
    # Step 1: Check packages
    if not check_and_install_packages():
        print("❌ Setup failed. Please install missing packages manually.")
        sys.exit(1)
    
    # Step 2: Create directories
    create_directory_structure()
    
    # Step 3: Run test
    if not run_quick_test():
        print("❌ Setup failed. Please check your installation.")
        sys.exit(1)
    
    # Step 4: Display plan
    display_execution_plan()
    
    print(f"\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Run: python confusion_matrix_generator.py")
    print(f"2. Run: python confusion_matrix_visualizer.py")
    print(f"3. Run: python classification_report_generator.py")
    print(f"4. Run: python roc_curve_generator.py")
    print(f"\nAll figures will be ready for your thesis!")