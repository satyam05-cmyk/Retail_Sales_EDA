import sys
import subprocess
import os

def main():
    """Test runner that executes the entire pytest suite for the project."""
    print("======================================================================")
    print("Executing E2E Test Suite for Retail Sales EDA Upgrade...")
    print("======================================================================")
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run pytest on the tests directory
    cmd = ["pytest", "tests/", "-v"]
    
    # Execute subprocess
    result = subprocess.run(cmd, cwd=project_dir)
    
    print("\n======================================================================")
    print(f"Test Execution Completed with Exit Code: {result.returncode}")
    print("======================================================================")
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
