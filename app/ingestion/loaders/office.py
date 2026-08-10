import os
import logfire
from langchain_community.document_loaders import (
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
)


def parse_office(file_path: str) -> str:
    """
    Parse DOCX/PPTX files with LangChain Unstructured loaders.
    """
    with logfire.span("Office Parsing with LangChain", filename=file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".docx":
                loader = UnstructuredWordDocumentLoader(file_path)
            elif ext == ".pptx":
                loader = UnstructuredPowerPointLoader(file_path)
            else:
                raise ValueError(f"Unsupported office file type: {ext}")

            documents = loader.load()

            text_parts = [
                doc.page_content.strip()
                for doc in documents
                if doc.page_content and doc.page_content.strip()
            ]

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                logfire.warning(f"No text extracted from office file: {file_path}")
            else:
                logfire.info(f"Extracted {len(full_text)} characters from office file.")

            return full_text

        except Exception as e:
            logfire.error(f"Office parse failed for {file_path}: {e}")
            raise