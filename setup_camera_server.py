import subprocess
import sys
import os

def install_requirements():
    requirements = [
        'flask',
        'flask-cors',
        'opencv-python',
        'numpy'
    ]
    
    for package in requirements:
    try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:

def main():
    install_requirements()

if __name__ == "__main__":
    main()
