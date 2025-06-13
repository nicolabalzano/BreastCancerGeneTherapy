# Gene Research Flask Application

## Requirements

Create a `requirements.txt` file with the following dependencies:

```
Flask==2.3.3
requests==2.31.0
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Cheshire Cat AI

First, you need to have Cheshire Cat AI running. Follow these steps:

1. **Install Cheshire Cat using Docker:**
   ```bash
   docker run --rm -it -p 1865:80 ghcr.io/cheshire-cat-ai/core:latest
   ```

2. **Or install locally:**
   ```bash
   pip install cheshire-cat-ai
   cheshire-cat
   ```

3. **Verify Cheshire Cat is running:**
   - Open your browser to `http://localhost:1865`
   - You should see the Cheshire Cat interface

### 3. Project Structure

Create the following directory structure:

```
gene_research_app/
├── app.py                 # Main Flask application
├── requirements.txt       # Dependencies
├── templates/
│   └── index.html        # HTML template
└── README.md             # This file
```

### 4. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Features

### 🧬 Gene Research Panel
- **Search Gene**: Enter a gene name (e.g., BRCA1, TP53, EGFR)
- **Set Max Results**: Control how many abstracts to download (1-200)
- **Auto-load to Cheshire Cat**: Automatically uploads abstracts to Cheshire Cat's knowledge base
- **Download Abstracts**: Download all abstracts as a ZIP file

### 💬 Chat Interface
- **Ask Questions**: Query the loaded gene abstracts using natural language
- **Real-time Responses**: Get AI-powered answers from Cheshire Cat
- **Chat History**: View conversation history
- **Clear Chat**: Reset the conversation

## Usage Examples

### 1. Research a Gene
1. Enter gene name: `BRCA1`
2. Set max results: `50`
3. Click "Search & Load to Cheshire Cat"
4. Wait for abstracts to be loaded

### 2. Ask Questions
- "What are the main functions of this gene?"
- "What diseases is this gene associated with?"
- "What are the latest research findings?"
- "Summarize the key mutations mentioned in the abstracts"

### 3. Download Data
- Click "Download Abstracts" to get a ZIP file with all abstracts
- Each abstract is saved as a separate text file
- Includes a summary file with metadata

## API Endpoints

### POST /search_gene
Search PubMed for gene abstracts and load them into Cheshire Cat.

**Request:**
```json
{
    "gene_name": "BRCA1",
    "max_results": 50
}
```

**Response:**
```json
{
    "success": true,
    "gene_name": "BRCA1",
    "total_articles": 45,
    "uploaded_count": 45,
    "articles": [...]
}
```

### POST /ask_question
Ask a question to Cheshire Cat about the loaded abstracts.

**Request:**
```json
{
    "question": "What are the main functions of this gene?"
}
```

**Response:**
```json
{
    "question": "What are the main functions of this gene?",
    "answer": "Based on the loaded abstracts...",
    "timestamp": "2025-06-03T10:30:00.000Z"
}
```

### POST /download_abstracts
Download all abstracts as a ZIP file.

**Request:**
```json
{
    "gene_name": "BRCA1"
}
```

**Response:**
ZIP file download containing individual text files for each abstract.

## Troubleshooting

### Common Issues

1. **Cheshire Cat Connection Error**
   - Ensure Cheshire Cat is running on `http://localhost:1865`
   - Check if the port is accessible
   - Try restarting Cheshire Cat

2. **PubMed API Limits**
   - NCBI has rate limits for API requests
   - If you get errors, wait a few minutes before retrying
   - Consider reducing max_results for large queries

3. **No Abstracts Found**
   - Check gene name spelling
   - Try alternative gene names or symbols
   - Some genes may have limited research publications

4. **Upload Failures**
   - Check Cheshire Cat storage capacity
   - Ensure proper file permissions
   - Try uploading smaller batches

### Error Messages

- **"Gene name is required"**: Enter a valid gene name
- **"No articles found"**: Try different gene names or check spelling
- **"Failed to fetch abstracts"**: PubMed API issue, try again later
- **"Error communicating with Cheshire Cat"**: Check Cheshire Cat connection

## Advanced Configuration

### Custom Cheshire Cat URL
If your Cheshire Cat instance runs on a different URL, modify the CheshireCatClient initialization:

```python
cheshire_client = CheshireCatClient("http://your-custom-url:port")
```

### Increase Search Results
You can modify the maximum results limit in the search function:

```python
def search_gene(self, gene_name, max_results=200):  # Increased from 50
```

### Custom PubMed Queries
Modify the search term in PubMedClient.search_gene():

```python
'term': f'{gene_name}[Title/Abstract] AND gene AND cancer',  # Add more filters
```

## Security Considerations

1. **Input Validation**: The app validates gene names and limits results
2. **Rate Limiting**: Consider implementing rate limiting for production
3. **HTTPS**: Use HTTPS in production environments
4. **CORS**: Configure CORS if accessing from different domains

## Extending the Application

### Add More Data Sources
- **arXiv**: For preprint papers
- **Google Scholar**: For broader academic coverage
- **Clinical Trials**: For ongoing research

### Enhanced Features
- **User Authentication**: Add login system
- **Save Searches**: Store search history
- **Batch Processing**: Process multiple genes simultaneously
- **Data Visualization**: Add charts and graphs
- **Export Options**: PDF, Excel, CSV formats

### Integration Options
- **REST API**: Make it a pure API service
- **Database**: Store results in PostgreSQL/MongoDB
- **Queue System**: Use Celery for background processing
- **Caching**: Add Redis for faster responses

## Performance Optimization

### For Large Datasets
1. **Pagination**: Implement pagination for results
2. **Async Processing**: Use async/await for concurrent requests
3. **Caching**: Cache PubMed results
4. **Database**: Store abstracts locally for faster access

### Memory Management
```python
# Process abstracts in batches
def upload_documents_batch(self, documents, batch_size=10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        self.upload_documents(batch)
        time.sleep(1)  # Prevent overwhelming
```

## Contributing

Feel free to contribute by:
1. Adding new data sources
2. Improving the UI/UX
3. Adding more AI capabilities
4. Optimizing performance
5. Adding tests

## License

This project is open source. Make sure to comply with:
- PubMed API terms of service
- Cheshire Cat AI licensing
- Flask licensing terms