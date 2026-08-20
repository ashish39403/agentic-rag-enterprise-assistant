
import logfire
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text:str , chunk_size:int =1500 , chunk_overlap:int =200)->list[str]:
    """
    Chunk text using LangChain RecursiveCharacterTextSplitter.
    Splits by paragraphs/lines/sentences where possible, with overlap for context continuity.
    """
    with logfire.span("Text Chunking", text_length = len(text)):
        if not text or not  text.strip():
            return []   #text = "" or text = " "
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        chunks = splitter.split_text(text)
        valid_chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]

        logfire.info(f"Generated {len(valid_chunks)} chunks")
        return valid_chunks
        
        