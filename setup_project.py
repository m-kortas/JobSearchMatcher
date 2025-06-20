"""
Create the necessary folder structure and __init__.py files
"""

import os
import sys

def create_project_structure():
    """Create the basic project folder structure."""
    
    # Define the project directories
    directories = [
        "fetch_jobs",
        "match_resume",
        "enrich_data"
    ]
    
    # Create each directory and its __init__.py file
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "__init__.py"), "w") as f:
            f.write(f'"""{directory.replace("_", " ").title()} package for the job matcher system."""')
    
    # Create a sample folder for sample data
    os.makedirs("sample", exist_ok=True)
    
    print("Project structure created successfully!")
    print("Next steps:")
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Create a .env file with your API keys")
    print("3. Run the system: python main.py --resume your_resume.pdf")

if __name__ == "__main__":
    create_project_structure()