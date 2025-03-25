# Resume Analyzer AI A simple web application that analyzes resumes and extracts key information using AI and natural language processing.


A simple web application that analyzes resumes and extracts key information using AI and natural language processing.

## Features

- Upload PDF or DOCX resumes
- Extract contact information (email, phone)
- Identify skills and technical expertise
- Extract education information
- Extract work experience
- Modern and responsive UI

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone this repository or download the files
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Download the spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Usage

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`
3. Upload your resume (PDF or DOCX format)
4. View the analysis results

## Supported File Formats

- PDF (.pdf)
- Microsoft Word (.docx)

## Technical Details

The application uses:
- Flask for the web framework
- PyPDF2 for PDF processing
- python-docx for DOCX processing
- NLTK for natural language processing
- spaCy for entity recognition
- Bootstrap for the frontend

## Limitations

- Maximum file size: 16MB
- Text extraction quality depends on the resume format
- Some complex layouts might not be processed correctly
- Limited to English language resumes

## License

This project is open source and available under the MIT License. 
