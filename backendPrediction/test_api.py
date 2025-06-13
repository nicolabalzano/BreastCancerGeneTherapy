"""
Script di test per l'API Flask
"""

import requests
import os

def test_api():
    """Testa l'API con file di esempio"""
    
    # URL dell'API
    api_url = "http://localhost:5000/api/predict"
    
    # File di test (usa i file esistenti nella cartella data)
    files_to_upload = [
        ("files", ("normal.rna_seq.augmented_star_gene_counts.tsv", 
                  open("backendPrediction/assets/data/normal.rna_seq.augmented_star_gene_counts.tsv", "rb"), "text/plain")),
        ("files", ("tumor.mirbase21.mirnas.quantification.txt", 
                  open("backendPrediction/assets/data/tumor.mirbase21.mirnas.quantification.txt", "rb"), "text/plain")),
        ("files", ("tumor.mirbase21.isoforms.quantification.txt", 
                  open("backendPrediction/assets/data/tumor.mirbase21.isoforms.quantification.txt", "rb"), "text/plain"))
    ]
    
    # Dati del form
    form_data = {
        'sample_type': 'tumor'
    }
    
    try:
        print("Testando l'API...")
        
        # Invia la richiesta
        response = requests.post(api_url, files=files_to_upload, data=form_data)
        
        # Chiudi i file
        for _, (_, file_obj, _) in files_to_upload:
            file_obj.close()
        
        # Controlla la risposta
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Test riuscito!")
                print(f"Patient ID: {result['patient_id']}")
                print(f"Classe predetta: {result['prediction']['class']}")
                print(f"Confidenza: {result['prediction']['confidence']:.4f}")
                print(f"Probabilità: {result['prediction']['probabilities']}")
            else:
                print(f"❌ Errore API: {result['error']}")
        else:
            print(f"❌ Errore HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")

def test_health():
    """Testa l'endpoint di health check"""
    try:
        response = requests.get("http://localhost:5000/health")
        if response.status_code == 200:
            print("✅ Health check OK:", response.json())
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore health check: {e}")

if __name__ == "__main__":
    print("=== Test Flask API ===")
    test_health()
    print()
    test_api()
