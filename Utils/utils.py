import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import pymupdf

def pdf_to_text(file):
    assert isinstance(file, UploadedFile), "You did not upload a valid PDF file"
    
    file.seek(0)
    pdf = pymupdf.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text()
    return text

