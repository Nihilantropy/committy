def test_llamaindex_embedding_configuration():
    """Test that the LlamaIndex embedding model is properly configured."""
    from llama_index.core import Settings
    from llama_index.core.indices.vector_store import VectorStoreIndex
    from llama_index.core import Document
    
    # Import our module to trigger the embedding setup
    from committy.llm.index import DiffIndexer
    
    # Create a simple document and index
    doc = Document(text="Test document")
    
    # This should use the configured local embedding model
    index = VectorStoreIndex([doc])
    
    # Check that we're not using OpenAI embeddings (which would require an API key)
    assert "openai" not in str(type(Settings.embed_model)).lower()
    
    # Check that we're using a valid embedding model type - added huggingface
    embed_model_type = str(type(Settings.embed_model)).lower()
    assert any(t in embed_model_type for t in ["huggingface", "simple", "local"]), \
        f"Embedding model type '{embed_model_type}' is not recognized"