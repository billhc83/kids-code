import subprocess
import sys

with open("pytest_output_clean.txt", "w") as f:
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], stdout=f, stderr=f)
