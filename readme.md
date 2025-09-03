# 📜 Historical Research Assistant

A powerful AI-powered application for historical research that combines document management, vector search, and intelligent question-answering capabilities. Built with Streamlit, LangChain, and Qdrant, this tool helps researchers, historians, and students efficiently process, organize, and query historical documents.

## ✨ Features

### 📚 Document Management
- **Multi-format Support**: Upload and process various document types including books, journals, newspapers, reports, and web articles
- **Intelligent Parsing**: Specialized parsers for different document types with metadata extraction
- **Batch Processing**: Process multiple documents simultaneously with progress tracking
- **Document Sync**: Keep your document collection synchronized and up-to-date

### 🔍 Advanced Search & Retrieval
- **Vector Search**: Semantic search through your document collection using embeddings
- **Metadata Filtering**: Filter by document type, date range, and other metadata
- **Source Citations**: Automatic extraction and display of source citations
- **Contextual Retrieval**: Find relevant information even with imprecise queries

### 🤖 AI-Powered Question Answering
- **Intelligent Responses**: Get comprehensive answers combining historical documents with current context
- **Web Search Integration**: Optional web search to supplement historical information with current data
- **Offline Mode**: Work completely offline using only your uploaded documents
- **Chat History**: Persistent conversation history with timestamps and source tracking

### 📁 Project Management
- **Multi-Project Support**: Organize research into separate projects
- **Archive System**: Archive completed projects for backup and future reference
- **Project Statistics**: View document counts, storage usage, and collection status
- **Easy Restoration**: Restore archived projects when needed

### 🎯 User Interface
- **Streamlit Web App**: Clean, intuitive web interface
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live progress tracking and status updates
- **Export Capabilities**: Save and export your research findings

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Tavily API key (optional, for web search features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd historical_research_assistant
   ```

2. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   COHERE_API_KEY=your_cohere_api_key_here  # Optional
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 📖 Usage Guide

### Getting Started

1. **Create a New Project**
   - Select "New Project" from the sidebar
   - Enter a project name
   - Click "Create Project"

2. **Upload Documents**
   - Navigate to "Upload Documents"
   - Drag and drop files or use the file browser
   - Supported formats: PDF, TXT, DOCX, and more

3. **Process Documents**
   - Go to "Process Pending" to convert documents to searchable format
   - Monitor progress and handle any parsing errors

4. **Ask Questions**
   - Use the "Ask Questions" interface to query your documents
   - Enable/disable web search as needed
   - View source citations for all answers

### Advanced Features

#### Document Types & Parsers
The system includes specialized parsers for different document types:
- **Books**: Chapter and section detection
- **Journals**: Article and citation extraction
- **Newspapers**: Article and headline parsing
- **Reports**: Structured document analysis
- **Web Articles**: HTML content extraction

#### Vector Search
- Documents are automatically converted to embeddings
- Semantic search finds relevant content even with different wording
- Metadata filtering allows precise document targeting

#### Project Management
- **Archive Projects**: Move completed projects to archive
- **Delete Projects**: Remove projects with safety confirmations
- **Restore Projects**: Bring back archived projects
- **View Statistics**: Monitor project size and document counts

## 🏗️ Architecture

### Core Components

- **`app.py`**: Main Streamlit application and navigation
- **`langgraph_agent.py`**: AI agent for question-answering
- **`retriever_chain.py`**: Document retrieval and RAG implementation
- **`local_qdrant.py`**: Vector database management
- **`embedder.py`**: Text embedding generation
- **`db.py`**: SQLite database operations

### Document Processing Pipeline

1. **Upload**: Documents uploaded via web interface
2. **Parse**: Specialized parsers extract text and metadata
3. **Chunk**: Text split into manageable segments
4. **Embed**: Convert chunks to vector embeddings
5. **Store**: Save embeddings in Qdrant vector database
6. **Index**: Create searchable index with metadata

### AI Integration

- **LangChain**: Framework for document processing and retrieval
- **LangGraph**: Agent orchestration and conversation flow
- **OpenAI GPT-4**: Language model for answer generation
- **Tavily**: Web search integration for current context

## 🔧 Configuration

### Environment Variables
```env
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
TAVILY_API_KEY=your_tavily_api_key
COHERE_API_KEY=your_cohere_api_key
```

### Project Structure
```
historical_research_assistant/
├── components/          # UI components
├── projects/           # Active projects
├── archive/            # Archived projects
├── app.py              # Main application
├── config.py           # Configuration
└── requirements.txt    # Dependencies
```

## 🛠️ Troubleshooting

### Common Issues

#### Qdrant "Already Accessed" Error
If you encounter Qdrant connection errors:
```bash
python clear_qdrant_locks.py
streamlit run app.py
```

#### Document Processing Errors
- Check file format compatibility
- Verify file permissions
- Review parser-specific error messages

#### API Key Issues
- Ensure all required API keys are set in `.env`
- Verify API key validity and quotas
- Check network connectivity

### Performance Tips
- Use specific, focused questions for faster responses
- Process documents in smaller batches
- Monitor disk space for large document collections
- Consider archiving completed projects

## 📚 Documentation

Additional documentation is available in the project:
- `PROJECT_MANAGEMENT_FEATURES.md`: Detailed project management guide
- `README_QA_INTERFACE.md`: Question-answering interface documentation
- `QDRANT_TROUBLESHOOTING.md`: Vector database troubleshooting
- `VECTOR_DELETION_FIXES.md`: Vector store management

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [LangChain](https://langchain.com/) and [LangGraph](https://langchain.com/langgraph)
- Vector search by [Qdrant](https://qdrant.tech/)
- AI capabilities by [OpenAI](https://openai.com/)

## 📞 Support

For issues, questions, or feature requests:
1. Check the troubleshooting documentation
2. Review existing issues on GitHub
3. Create a new issue with detailed information

---

**Happy Researching! 📜🔍**