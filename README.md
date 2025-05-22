# Document to Markdown Converter
A web application that converts documents from the `input/` folder to Markdown format in the `output/` folder using Docling. The application provides a simple web interface for document conversion and management.

## ✨ Features
test
- 📤 Upload individual or multiple documents through web interface
- 🔄 Process documents from the input folder
- 📝 Convert documents to Markdown format
- 💾 Save converted content to the output folder
- 🔍 Search content within converted documents
- 🖼️ Support for various document formats:
  - PDF (.pdf)
  - Word (.docx)
  - Excel (.xlsx)
  - HWP (.hwp)     # More robust HWP processing via internal parser
- 🚀 Easy one-click startup scripts for Windows and Unix-like systems

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Windows Users

1. Double-click on `start.bat`
2. The script will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Create necessary directories
   - Start the web server
3. Open your browser and go to: http://127.0.0.1:5000

### Linux/Mac Users

1. Open a terminal in the project directory
2. Make the script executable:
   ```bash
   chmod +x start.sh
   ```
3. Run the script:
   ```bash
   .\start.bat
   ./start.sh
   ```
4. Open your browser and go to: http://127.0.0.1:5000

## 🛠️ Manual Installation

If you prefer to set up the environment manually:

1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create necessary directories:
   ```bash
   mkdir input output
   ```

4. Run the application:
   ```bash
   # Windows
   set FLASK_APP=app.py
   set FLASK_ENV=development
   flask run

   # Linux/Mac
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run
   ```

## 📋 Usage

1. **Upload Documents**:
   - Use the web interface to upload files
   - Or place files directly in the `input/` folder

2. **Convert Documents**:
   - Select one or more documents from the list
   - Click "Convert to Markdown"
   - Find your converted files in the `output/` folder

3. **Search Content**:
   - Use the search bar to find specific content
   - View snippets of matching content

## 📁 Project Structure

```
find-doc-content/
├── app.py           # Main Flask application file
├── controllers/     # Handles request routing and business logic
├── services/        # Core backend services (e.g., document parsing, HWP processing)
├── models/          # Data models and structures
├── templates/       # HTML templates for the web UI
├── input/           # Directory for source documents
├── output/          # Directory for converted Markdown files
├── logs/            # Application log files
├── requirements.txt # Python dependencies
├── package.json     # Node.js dependencies and scripts (if any for frontend assets)
├── .env             # Environment variables configuration
├── start.bat        # Windows startup script
└── start.sh         # Linux/Mac startup script
```

## 🔍 Searching Documents

The application includes a powerful search feature that allows you to:
- Search for keywords across all converted documents
- View context around matches
- Navigate to specific sections of documents

## ⚠️ Troubleshooting

- If you encounter any issues, try deleting the `venv` folder and running the startup script again
- Make sure all required ports (5000) are available
- Check the terminal for any error messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
