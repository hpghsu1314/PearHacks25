import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

def pdf_to_text(file):
    assert isinstance(file, UploadedFile), "You did not upload a valid PDF file"
    