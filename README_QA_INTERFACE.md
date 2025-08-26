# 🤖 Question-Answering Interface

## Overview
The Historical Research Assistant now includes a powerful question-answering interface that allows users to ask questions about their uploaded historical documents and receive AI-powered answers that combine historical context with current information.

## Features

### 🧠 Intelligent Question Answering
- **Historical Document Search**: Automatically searches through your uploaded historical documents for relevant information
- **Web Search Integration**: Combines historical context with current information from the web
- **AI-Powered Responses**: Uses advanced language models to generate comprehensive, well-structured answers
- **Source Citations**: Automatically displays citations for all sources consulted in each answer

### 💬 Chat Interface
- **Question Input**: Large text area for entering detailed questions
- **Chat History**: Persistent storage of all questions and answers with timestamps
- **Easy Navigation**: Expandable chat history with delete functionality and source counts
- **Clear History**: Option to clear entire chat history
- **Source Tracking**: Each chat entry shows the number of sources consulted

### ⚙️ Advanced Options
- **Web Search Toggle**: Enable/disable web search for current context
  - When **enabled**: System provides note about supplementing with additional research
  - When **disabled**: System answers using ONLY uploaded historical documents
- **Response Length Control**: Adjust maximum response length (100-2000 tokens)
- **Example Questions**: Pre-loaded example questions for quick testing

### 🔧 Technical Features
- **LangGraph Agent**: Built on LangGraph for robust conversation flow
- **Tool Integration**: Combines document retrieval with web search tools
- **Session Management**: Maintains state across Streamlit sessions
- **Error Handling**: Graceful error handling with user-friendly messages

## How to Use

### 1. Access the Interface
1. Select a project from the sidebar
2. Choose "Ask Questions" from the navigation menu
3. The QA interface will load with your project's document collection

### 2. Ask a Question
1. Type your question in the text area
2. Adjust advanced options:
   - **Web Search**: Toggle to include/exclude current context
   - **Response Length**: Set maximum answer length
3. Click "Ask Question" to submit
4. Wait for the AI to process and respond

### 3. View Responses
- Answers appear below the question input
- **Source citations are automatically displayed** showing all documents consulted
- All Q&A pairs are saved to chat history with timestamps
- Use expandable chat history to review previous conversations

### 4. Manage Chat History
- Click on any chat entry to expand and view full content
- Use delete buttons to remove individual entries
- Clear entire history with the "Clear Chat History" button

## Example Questions

The interface includes several example questions to help you get started:

- "What were the main causes of the Industrial Revolution?"
- "How did World War II impact global trade?"
- "What were the key inventions of the 19th century?"
- "How did the printing press change society?"
- "What were the major economic policies during the Great Depression?"

## How It Works

### 1. Document Retrieval
The system searches your uploaded historical documents using vector similarity search to find relevant information.

### 2. Response Generation
The system generates answers based on the retrieved historical documents.

### 3. Source Citation Extraction
- **Metadata Analysis**: Extracts citation information from document metadata
- **Content Parsing**: Falls back to parsing citation patterns in document content
- **Deduplication**: Ensures each citation appears only once
- **Citation Display**: Shows all sources consulted for each answer

### 4. Web Search Integration (Optional)
- **When enabled**: System provides a note about supplementing with additional research
- **When disabled**: System answers using ONLY uploaded historical documents (offline mode)

### 5. Answer Display
The final answer is formatted and displayed, with clear indication of the information source and all citations consulted.

## Offline-Only Mode

The QA interface now supports a true offline mode where you can:
- **Disable web search**: Uncheck "Include web search for current context"
- **Get document-only answers**: Receive responses based solely on your uploaded historical documents
- **Avoid internet dependency**: Work completely offline with your local document collection
- **Focus on historical accuracy**: Get answers that are purely based on your source materials

This is particularly useful when:
- Working with sensitive or confidential historical documents
- Conducting research in offline environments
- Ensuring answers are based only on your verified source materials
- Avoiding potential misinformation from current web sources

## Technical Architecture

### Components
- **`components/qa_interface.py`**: Main UI component for the QA interface
- **`retriever_chain.py`**: Document retrieval and RAG chain implementation

### How It Works
1. User question → System receives input
2. System searches historical documents → Uses vector similarity search
3. System generates answer → Based on retrieved document content
4. **Source citation extraction** → From metadata and document content
5. Optional web search note → Added if web search is enabled
6. Response displayed to user → With citations and saved to chat history

## Citation System

### Automatic Citation Extraction
- **Primary Method**: Extracts citations from document metadata (`citation` field)
- **Fallback Method**: Parses document content for citation patterns
- **Smart Detection**: Recognizes various citation formats and patterns
- **Deduplication**: Ensures each unique citation appears only once

### Citation Display
- **Immediate Display**: Citations shown right after each answer
- **Chat History**: Citations preserved in chat history for reference
- **Source Counts**: Chat history shows number of sources per question
- **Timestamps**: Each chat entry includes when the question was asked

### Citation Sources
- **Document Metadata**: Primary source for citation information
- **Content Patterns**: Fallback for documents without metadata citations
- **Vector Store**: Citations extracted from retrieved document chunks
- **User Uploads**: Citations from your uploaded historical documents

## Requirements

### API Keys
- **OpenAI API Key**: Required for language model responses
- **Tavily API Key**: Required for web search functionality

### Dependencies
- `langchain`
- `langgraph`
- `streamlit`
- `qdrant-client`
- `langchain-openai`
- `langchain-community`

## Configuration

The system automatically uses:
- Current project's document collection
- Project-specific vector database
- Session-based chat history
- Configurable response parameters

## Troubleshooting

### Common Issues
1. **No Response Generated**: Check if documents are uploaded and processed
2. **Import Errors**: Ensure all dependencies are installed
3. **API Errors**: Verify API keys are set in environment variables
4. **Slow Responses**: Large document collections may take longer to search

### Performance Tips
- Use specific, focused questions for faster responses
- Ensure documents are properly processed and indexed
- Consider response length limits for complex questions

## Future Enhancements

Potential improvements for future versions:
- **Multi-language Support**: Support for questions in different languages
- **Citation Tracking**: Automatic citation of source documents
- **Export Functionality**: Save Q&A sessions to files
- **Advanced Filtering**: Filter responses by document type or date
- **Collaborative Features**: Share Q&A sessions with other users

## Testing the Citation System

### Citation Verification
1. **Ask a question** and verify citations are displayed below the answer
2. **Check chat history** for preserved citations and source counts
3. **Verify deduplication** - same citation shouldn't appear multiple times
4. **Test metadata extraction** from documents with citation fields

### Citation Display Features
- **Source Counts**: Chat history shows "(X sources)" in expander headers
- **Timestamps**: Each chat entry includes when the question was asked
- **Citation Lists**: Numbered lists of all sources consulted
- **Fallback Handling**: Graceful handling when citations aren't available

## Support

For issues or questions about the QA interface:
1. Check the error messages displayed in the interface
2. Verify your project setup and document processing
3. Ensure all required API keys are configured
4. Check the console for detailed error logs
5. **For citation issues**: Verify documents have citation metadata or content patterns
