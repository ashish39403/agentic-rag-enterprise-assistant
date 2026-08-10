import logfire
from langchain_community.document_loaders import PyPDFLoader


def parse_pdf(file_path: str) -> str:
    """
    Parse a PDF with LangChain and return one combined text string.
    """
    with logfire.span("PDF Parsing with LangChain", filename=file_path):
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()

            text_parts = []
            for doc in documents:
                page_text = doc.page_content.strip()
                page = doc.metadata.get("page")

                if page_text:
                    if page is not None:
                        text_parts.append(f"[Page {page + 1}]\n{page_text}")
                    else:
                        text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                logfire.warning(f"No text extracted from PDF: {file_path}")
            else:
                logfire.info(f"Extracted {len(full_text)} characters from PDF.")

            return full_text

        except Exception as e:
            logfire.error(f"PDF parse failed for {file_path}: {e}")
            raise