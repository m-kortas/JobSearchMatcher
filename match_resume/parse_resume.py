"""
Resume Parser Module

This module extracts text from a PDF resume using PyMuPDF (fitz).
It handles various PDF formats and cleans the extracted text.
"""

import fitz  # PyMuPDF
import re
import os

class ResumeParser:
    """Class to parse and extract text from resume PDFs."""
    
    def __init__(self, pdf_path):
        """
        Initialize the resume parser.
        
        Args:
            pdf_path (str): Path to the resume PDF file
        """
        self.pdf_path = pdf_path
        
        # Verify the file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Resume file not found: {pdf_path}")
        
        # Verify it's a PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("Resume file must be a PDF")
    
    def extract_text(self):
        """
        Extract text content from the PDF resume.
        
        Returns:
            str: Cleaned text extracted from the resume
        """
        text = ""
        
        try:
            # Open the PDF document
            doc = fitz.open(self.pdf_path)
            
            # Extract text from each page
            for page in doc:
                text += page.get_text()
                
            # Close the document
            doc.close()
            
            # Clean the extracted text
            cleaned_text = self._clean_text(text)
            
            return cleaned_text
            
        except Exception as e:
            print(f"Error extracting text from resume: {str(e)}")
            
            # Try alternate method if primary fails
            return self._extract_text_alternate()
    
    def _clean_text(self, text):
        """
        Clean the extracted text to improve processing.
        
        Args:
            text (str): Raw text extracted from the PDF
            
        Returns:
            str: Cleaned text
        """
        # Replace multiple newlines with a single one
        text = re.sub(r'\n+', '\n', text)
        
        # Replace multiple spaces with a single one
        text = re.sub(r' +', ' ', text)
        
        # Remove any non-printable characters
        text = ''.join(c for c in text if c.isprintable() or c == '\n')
        
        # Strip whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def _extract_text_alternate(self):
        """
        Alternative method to extract text using pdfminer if available.
        
        Returns:
            str: Extracted text or empty string if failed
        """
        try:
            # Try to import pdfminer
            from pdfminer.high_level import extract_text as pm_extract_text
            
            # Extract text
            text = pm_extract_text(self.pdf_path)
            
            # Clean the extracted text
            cleaned_text = self._clean_text(text)
            
            return cleaned_text
            
        except ImportError:
            print("pdfminer.six is not installed. Cannot use alternate extraction method.")
            return ""
        except Exception as e:
            print(f"Error in alternate text extraction: {str(e)}")
            return ""
    
    def extract_sections(self):
        """
        Attempt to extract common resume sections.
        
        Returns:
            dict: Dictionary with resume sections and their content
        """
        text = self.extract_text()
        
        # Common section headers in resumes
        sections = {
            'education': r'(?i)education|academic|qualifications',
            'experience': r'(?i)experience|work|employment|job|career',
            'skills': r'(?i)skills|competencies|technologies|tools|technical',
            'projects': r'(?i)projects|portfolio',
            'certifications': r'(?i)certifications|certificates|awards',
            'contact': r'(?i)contact|personal|details|information'
        }
        
        extracted_sections = {}
        
        # Split the text into lines
        lines = text.split('\n')
        
        current_section = 'other'
        section_content = []
        
        # Process each line
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            section_found = False
            for section_name, pattern in sections.items():
                if re.search(pattern, line) and len(line) < 50:  # Assuming headers are not too long
                    # Save previous section content
                    if section_content:
                        if current_section in extracted_sections:
                            extracted_sections[current_section] += '\n'.join(section_content)
                        else:
                            extracted_sections[current_section] = '\n'.join(section_content)
                    
                    # Start new section
                    current_section = section_name
                    section_content = []
                    section_found = True
                    break
            
            if not section_found:
                section_content.append(line)
        
        # Save the last section
        if section_content:
            if current_section in extracted_sections:
                extracted_sections[current_section] += '\n'.join(section_content)
            else:
                extracted_sections[current_section] = '\n'.join(section_content)
        
        return extracted_sections