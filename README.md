# Annotation Tool GUI

## Description
This Annotation Tool is a Python-based graphical user interface (GUI) application, developed using Tkinter. It allows users to load images and their corresponding JSON annotation files, providing an intuitive interface for viewing and editing image annotations. Key features include:
- Zoom in/out functionality for detailed viewing of images.
- Adding, editing, and deleting annotations.
- Navigating through multiple images and their annotations.
- Save updated annotations back to JSON format.
- Dark and Light theme toggle.

## Getting Started

### Dependencies
- Python 3.x
- Tkinter (usually comes with Python)
- PIL (Python Imaging Library): `pip install pillow`
- JSON support (included in Python standard library)
- OS module (included in Python standard library)

### Installing and Running
1. Clone the repository or download the source code.
2. Ensure that Python 3.x is installed on your system.
3. Install the required dependencies (Pillow) if they're not already installed.
4. Navigate to the downloaded code directory.
5. Run the script using Python:

python3 main.py

## How to Use
- **Open Folder**: Load multiple folders containing images and JSON files for annotations.
- **Navigation**: Use 'Previous' and 'Next' buttons to navigate between images.
- **Zoom**: Use 'Zoom In' and 'Zoom Out' buttons to adjust the view.
- **Annotations**: Use 'Add Annotation' to create new annotations, select existing annotations to edit or delete.
- **Theme Toggle**: Switch between light and dark themes for the user interface.
- **Saving**: Use 'Save JSON' to save updated annotations.

## File Structure
- `main.py`: Main application script.
- Additional files like JSON data and images need to be supplied by the user.

## License
Apache License 2.0
"""

with open("README.md", "w") as file:
 file.write(readme_content)

print("README.md file has been created successfully.")
