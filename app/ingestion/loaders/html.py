import logfire
from bs4 import BeautifulSoup
from langchain_community.document_loaders import BSHTMLLoader


def _clean_html_text(html: str) -> str:
    """Extract readable text from raw HTML."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def parse_html(file_path: str) -> str:
    """
    Parse an HTML file with LangChain and return readable text.
    """
    with logfire.span("HTML Parsing with LangChain", filename=file_path):
        try:
            loader = BSHTMLLoader(
                file_path,
                open_encoding="utf-8",
                get_text_separator="\n",
            )
            documents = loader.load()

            text_parts = [
                doc.page_content.strip()
                for doc in documents
                if doc.page_content and doc.page_content.strip()
            ]

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                logfire.warning(f"No text extracted from HTML: {file_path}")
            else:
                logfire.info(f"Extracted {len(full_text)} characters from HTML.")

            return full_text

        except UnicodeDecodeError as e:
            logfire.warning(
                f"LangChain HTML loader encoding failed for {file_path}: {e}. "
                "Retrying with UTF-8 errors ignored."
            )

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = _clean_html_text(f.read())

            if not full_text.strip():
                logfire.warning(f"No text extracted from HTML fallback: {file_path}")
            else:
                logfire.info(
                    f"Extracted {len(full_text)} characters from HTML fallback."
                )

            return full_text

        except Exception as e:
            logfire.error(f"HTML parse failed for {file_path}: {e}")
            raise
