import streamlit as st
from .book_uploader import render_books_uploader
from .journal_uploader import render_journals_uploader
from .newspaper_uploader import render_newspapers_uploader
from .report_uploader import render_reports_uploader
from .web_article_uploader import render_web_articles_uploader

UPLOADERS = {
    "books": render_books_uploader,
    "journals": render_journals_uploader,
    "newspapers": render_newspapers_uploader,
    "reports": render_reports_uploader,
    "web_articles": render_web_articles_uploader
}

def render_uploader(proj_dir, con):
    doc_type = st.selectbox("Select document type", list(UPLOADERS.keys()))
    uploader = UPLOADERS[doc_type]
    uploader(proj_dir, con)