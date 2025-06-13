from flask import Flask, render_template, request, jsonify, send_file
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import tempfile
import zipfile
from io import BytesIO
import json
import time
import logging
from functools import wraps
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

class PubMedClient:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.search_url = f"{self.base_url}esearch.fcgi"
        self.fetch_url = f"{self.base_url}efetch.fcgi"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gene-Research-App/1.0 (mailto:your-email@example.com)'
        })
    
    def validate_gene_name(self, gene_name):
        """Validate gene name format"""
        if not gene_name or len(gene_name.strip()) < 2:
            return False
        # Basic validation - alphanumeric, hyphens, underscores
        return bool(re.match(r'^[A-Za-z0-9_-]+$', gene_name.strip()))
    
    def search_gene(self, gene_name, max_results=50):
        """Search PubMed for articles about a specific gene"""
        if not self.validate_gene_name(gene_name):
            raise ValueError("Invalid gene name format")
        
        # Limit max results to prevent abuse
        max_results = min(max_results, 200)
        
        params = {
            'db': 'pubmed',
            'term': f'({gene_name}[Title/Abstract] OR {gene_name}[Gene Name]) AND ("last 10 years"[PDat])',
            'retmax': max_results,
            'retmode': 'xml',
            'sort': 'relevance'
        }
        
        try:
            logger.info(f"Searching PubMed for gene: {gene_name}")
            response = self.session.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Check for errors in the response
            error_list = root.find('ErrorList')
            if error_list is not None:
                error_msg = error_list.find('PhraseNotFound')
                if error_msg is not None:
                    logger.warning(f"PubMed search warning: {error_msg.text}")
            
            id_list = root.find('IdList')
            if id_list is not None:
                pmids = [id_elem.text for id_elem in id_list.findall('Id')]
                logger.info(f"Found {len(pmids)} articles for {gene_name}")
                return pmids
            
            return []
        except requests.exceptions.Timeout:
            logger.error("PubMed search timeout")
            raise Exception("PubMed search timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"PubMed API error: {e}")
            raise Exception("Failed to connect to PubMed. Please try again later.")
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise Exception("Invalid response from PubMed.")
    
    def fetch_abstracts(self, pmids):
        """Fetch abstracts for given PubMed IDs"""
        if not pmids:
            return []
        
        # Process in batches to avoid overwhelming the API
        batch_size = 20
        all_articles = []
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i+batch_size]
            logger.info(f"Fetching batch {i//batch_size + 1}/{(len(pmids)-1)//batch_size + 1}")
            
            params = {
                'db': 'pubmed',
                'id': ','.join(batch_pmids),
                'retmode': 'xml'
            }
            
            try:
                response = self.session.get(self.fetch_url, params=params, timeout=60)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                articles = self._parse_articles(root)
                all_articles.extend(articles)
                
                # Be respectful to NCBI servers
                if i + batch_size < len(pmids):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error fetching batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(all_articles)} articles")
        return all_articles
    
    def _parse_articles(self, root):
        """Parse articles from XML response"""
        articles = []
        
        for article in root.findall('.//PubmedArticle'):
            try:
                # Extract title
                title_elem = article.find('.//ArticleTitle')
                title = self._clean_text(title_elem.text if title_elem is not None else "No title")
                
                # Extract abstract - handle multiple abstract sections
                abstract_texts = []
                for abstract_elem in article.findall('.//Abstract/AbstractText'):
                    if abstract_elem.text:
                        # Check if it has a label attribute
                        label = abstract_elem.get('Label', '')
                        text = self._clean_text(abstract_elem.text)
                        if label:
                            abstract_texts.append(f"{label}: {text}")
                        else:
                            abstract_texts.append(text)
                
                abstract = ' '.join(abstract_texts) if abstract_texts else "No abstract available"
                
                # Extract PMID
                pmid_elem = article.find('.//PMID')
                pmid = pmid_elem.text if pmid_elem is not None else "No PMID"
                
                # Extract publication date
                pub_date = article.find('.//PubDate')
                year = "Unknown"
                if pub_date is not None:
                    year_elem = pub_date.find('Year')
                    if year_elem is not None:
                        year = year_elem.text
                
                # Extract authors
                authors = []
                for author in article.findall('.//Author'):
                    last_name = author.find('LastName')
                    first_name = author.find('ForeName')
                    if last_name is not None:
                        author_name = last_name.text
                        if first_name is not None:
                            author_name += f", {first_name.text}"
                        authors.append(author_name)
                
                # Extract journal
                journal_elem = article.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else "Unknown Journal"
                
                articles.append({
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'year': year,
                    'authors': authors[:5],  # Limit to first 5 authors
                    'journal': journal
                })
            except Exception as e:
                logger.error(f"Error parsing individual article: {e}")
                continue
        
        return articles
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        return ' '.join(text.split())

class CheshireCatClient:
    def __init__(self, base_url="http://localhost:1865"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gene-Research-App/1.0'
        })
    
    def test_connection(self):
        """Test connection to Cheshire Cat"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def upload_documents(self, documents):
        """Upload documents to Cheshire Cat with better error handling"""
        if not self.test_connection():
            raise Exception("Cannot connect to Cheshire Cat. Please ensure it's running on localhost:1865")
        
        uploaded_count = 0
        failed_uploads = []
        
        for i, doc in enumerate(documents):
            try:
                # Create well-formatted content
                content = self._format_document(doc)
                
                # Upload to Cheshire Cat
                files = {
                    'file': (f"pubmed_{doc['pmid']}.txt", content, 'text/plain')
                }
                
                response = self.session.post(
                    f"{self.base_url}/rabbithole/",
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    uploaded_count += 1
                    logger.info(f"Uploaded document {i+1}/{len(documents)}: PMID {doc['pmid']}")
                else:
                    failed_uploads.append(doc['pmid'])
                    logger.warning(f"Failed to upload PMID {doc['pmid']}: {response.status_code}")
                
                # Rate limiting to be respectful
                if i < len(documents) - 1:
                    time.sleep(0.2)
                
            except Exception as e:
                failed_uploads.append(doc['pmid'])
                logger.error(f"Error uploading document PMID {doc['pmid']}: {e}")
        
        if failed_uploads:
            logger.warning(f"Failed to upload {len(failed_uploads)} documents: {failed_uploads}")
        
        return uploaded_count, failed_uploads
    
    def _format_document(self, doc):
        """Format document content for better processing"""
        content = f"# {doc['title']}\n\n"
        content += f"**PMID:** {doc['pmid']}\n"
        content += f"**Journal:** {doc['journal']}\n"
        content += f"**Year:** {doc['year']}\n"
        
        if doc.get('authors'):
            content += f"**Authors:** {', '.join(doc['authors'])}\n"
        
        content += f"\n## Abstract\n\n{doc['abstract']}\n\n"
        content += "---\n"
        
        return content
    
    def ask_question(self, question):
        """Ask a question to Cheshire Cat with better error handling"""
        if not self.test_connection():
            return "Error: Cannot connect to Cheshire Cat. Please ensure it's running."
        
        try:
            payload = {
                "user_id":"ddf3b3c5-5667-42da-ac89-9daa7dcca066",
                'text': question.strip()
            }
            
            response = self.session.post(
                f"{self.base_url}/message",
                json=payload,
                timeout=500 
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('content', 'No response received from Cheshire Cat')
            else:
                logger.error(f"Cheshire Cat API error: {response.status_code}")
                return f"Error: Cheshire Cat returned status code {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Request to Cheshire Cat timed out. Please try again."
        except Exception as e:
            logger.error(f"Error communicating with Cheshire Cat: {e}")
            return f"Error communicating with Cheshire Cat: {str(e)}"

# Rate limiting decorator
def rate_limit(max_requests=10, window=60):
    """Simple rate limiting decorator"""
    requests_made = {}
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            requests_made[client_ip] = [
                req_time for req_time in requests_made.get(client_ip, [])
                if current_time - req_time < window
            ]
            
            # Check rate limit
            if len(requests_made.get(client_ip, [])) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            # Add current request
            requests_made.setdefault(client_ip, []).append(current_time)
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Initialize clients
pubmed_client = PubMedClient()
cheshire_client = CheshireCatClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    cheshire_status = cheshire_client.test_connection()
    return jsonify({
        'status': 'healthy' if cheshire_status else 'degraded',
        'cheshire_cat': 'connected' if cheshire_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/search_gene', methods=['POST'])
@rate_limit(max_requests=5, window=60)  # 5 requests per minute
def search_gene():
    """Search for gene and download abstracts"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        gene_name = data.get('gene_name', '').strip()
        max_results = min(int(data.get('max_results', 50)), 200)  # Cap at 200
        
        if not gene_name:
            return jsonify({'error': 'Gene name is required'}), 400
        
        # Search PubMed
        pmids = pubmed_client.search_gene(gene_name, max_results)
        
        if not pmids:
            return jsonify({'error': f'No articles found for gene: {gene_name}'}), 404
        
        # Fetch abstracts
        articles = pubmed_client.fetch_abstracts(pmids)
        
        if not articles:
            return jsonify({'error': 'Failed to fetch abstracts from PubMed'}), 500
        
        # Upload to Cheshire Cat
        uploaded_count, failed_uploads = cheshire_client.upload_documents(articles)
        
        return jsonify({
            'success': True,
            'gene_name': gene_name,
            'total_articles': len(articles),
            'uploaded_count': uploaded_count,
            'failed_count': len(failed_uploads),
            'articles': articles
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in search_gene: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@app.route('/send_prediction', methods=['POST'])
@rate_limit(max_requests=10, window=60) # 10 requests per minute
def send_prediction():
    """
    Receives files, looks up papers for a predefined gene (RAE1),
    loads them into Cheshire Cat, and asks a question.
    """
    try:
        # Check for uploaded files (retaining original file handling)
#        files = request.files
 #       if not files:
  #          return jsonify({'error': 'No files were uploaded.'}), 400
            
   #     file_info = {}
    #    for key, file_storage in files.items():
     #       file_info[key] = {
      #          'filename': file_storage.filename,
       #         'content_type': file_storage.content_type
        #    }

        # --- MOCK LOGIC ---
        file_info="DEBUG: No files uploaded, using predefined gene name"
        # 1. Use a temp variable for the gene name
        gene_name = "RUNX1"
        logger.info(f"Initiating prediction process for gene: {gene_name}")

        # 2. Look up papers in PubMed
        logger.info(f"Searching PubMed for articles related to '{gene_name}'...")
        pmids = pubmed_client.search_gene(gene_name, max_results=3) # Limit to 3 results for efficiency do not put higher otherwise it will go in conflict the upload
        
        if not pmids:
            return jsonify({
                'error': f'No PubMed articles found for the gene: {gene_name}',
                'files_received': file_info
            }), 404

        articles = pubmed_client.fetch_abstracts(pmids)
        
        if not articles:
            return jsonify({
                'error': f'Could not fetch abstract details for {gene_name}',
                'files_received': file_info
            }), 500
        
        logger.info(f"Found and fetched {len(articles)} articles for '{gene_name}'.")

        # 3. Load the articles into Cheshire Cat
        logger.info(f"Uploading {len(articles)} articles to Cheshire Cat...")
        uploaded_count, failed_uploads = cheshire_client.upload_documents(articles)
        
        if uploaded_count == 0:
            return jsonify({
                'error': f'Failed to upload any articles to Cheshire Cat for gene: {gene_name}',
                'files_received': file_info
            }), 500
            
        logger.info(f"Successfully uploaded {uploaded_count} articles. Failed: {len(failed_uploads)}.")

        # 4. Send a message to Cheshire Cat after loading
        question = f"Based on the documents, what is the role of the {gene_name} gene?"
        logger.info(f"Asking Cheshire Cat: '{question}'")
        
        answer = cheshire_client.ask_question(question)

        # 5. Return a comprehensive result
        result = {
            "prediction_id": f"pred_{gene_name}_{int(time.time())}",
            "status": "COMPLETED",
            "gene_analyzed": gene_name,
            "articles_found": len(articles),
            "articles_uploaded": uploaded_count,
            "question_asked": question,
            "cheshire_cat_answer": answer,
            "files_received": file_info
        }
        
        return jsonify({'result': result})

    except Exception as e:
        logger.error(f"Error in send_prediction: {e}")
        return jsonify({'error': 'An unexpected error occurred during the prediction process.'}), 500

@app.route('/ask_question', methods=['POST'])
@rate_limit(max_requests=20, window=60)  # 20 questions per minute
def ask_question():
    """Ask a question to Cheshire Cat"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        if len(question) > 1000:
            return jsonify({'error': 'Question too long (max 1000 characters)'}), 400
        
        # Get response from Cheshire Cat
        response = cheshire_client.ask_question(question)
        
        return jsonify({
            'question': question,
            'answer': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return jsonify({'error': 'Failed to get response from Cheshire Cat'}), 500

@app.route('/download_abstracts', methods=['POST'])
@rate_limit(max_requests=3, window=300)  # 3 downloads per 5 minutes
def download_abstracts():
    """Download all abstracts as a ZIP file"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        gene_name = data.get('gene_name', '').strip()
        
        if not gene_name:
            return jsonify({'error': 'Gene name is required'}), 400
        
        # Search and fetch abstracts
        pmids = pubmed_client.search_gene(gene_name, 100)  # Limit downloads to 100
        articles = pubmed_client.fetch_abstracts(pmids)
        
        if not articles:
            return jsonify({'error': 'No articles found'}), 404
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for article in articles:
                content = cheshire_client._format_document(article)
                filename = f"pubmed_{article['pmid']}.txt"
                zip_file.writestr(filename, content)
            
            # Add summary file
            summary = create_summary(gene_name, articles)
            zip_file.writestr("README.txt", summary)
        
        zip_buffer.seek(0)
        
        return send_file(
            BytesIO(zip_buffer.read()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{gene_name}_abstracts_{datetime.now().strftime("%Y%m%d")}.zip'
        )
        
    except Exception as e:
        logger.error(f"Error in download_abstracts: {e}")
        return jsonify({'error': 'Failed to create download file'}), 500

def create_summary(gene_name, articles):
    """Create a summary file for the download"""
    summary = f"Gene Research Summary: {gene_name}\n"
    summary += "=" * 50 + "\n\n"
    summary += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    summary += f"Total articles: {len(articles)}\n\n"
    
    # Year distribution
    years = {}
    for article in articles:
        year = article.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    summary += "Year Distribution:\n"
    for year in sorted(years.keys(), reverse=True):
        summary += f"  {year}: {years[year]} articles\n"
    
    summary += "\n" + "=" * 50 + "\n"
    summary += "Articles Included:\n\n"
    
    for i, article in enumerate(articles, 1):
        summary += f"{i}. PMID: {article['pmid']}\n"
        summary += f"   Title: {article['title']}\n"
        summary += f"   Journal: {article['journal']} ({article['year']})\n"
        if article.get('authors'):
            summary += f"   Authors: {', '.join(article['authors'][:3])}{'...' if len(article['authors']) > 3 else ''}\n"
        summary += "\n"
    
    return summary

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check Cheshire Cat connection on startup
    if cheshire_client.test_connection():
        logger.info("✅ Cheshire Cat connection successful")
    else:
        logger.warning("⚠️  Cannot connect to Cheshire Cat. Please ensure it's running on localhost:1865")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
