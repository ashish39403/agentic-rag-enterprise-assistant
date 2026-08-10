import logfire
from langchain_community.document_loaders import TextLoader


def parse_text(file_path: str) -> str:
    """
    Parse a plain text file with LangChain and return text.
    """
    with logfire.span("Text Parsing with LangChain", filename=file_path):
        try:
            loader = TextLoader(
                file_path,
                encoding="utf-8",
                autodetect_encoding=True,
            )
            documents = loader.load()

            full_text = "\n\n".join(
                doc.page_content.strip()
                for doc in documents
                if doc.page_content and doc.page_content.strip()
            )

            if not full_text.strip():
                logfire.warning(f"No text extracted from text file: {file_path}")
            else:
                logfire.info(f"Extracted {len(full_text)} characters from text file.")

            return full_text

        except Exception as e:
            logfire.error(f"Text parse failed for {file_path}: {e}")
            raise