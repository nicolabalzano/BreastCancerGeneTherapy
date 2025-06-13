"""
Flask API per il servizio di predizione con upload di file
"""

import os
import uuid
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
import prediction as pred
import preprocessing as pre

app = Flask(__name__)

# Configurazione Flask
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB default
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'assets/data')

# Avviso se si sta usando la chiave di default in produzione
if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production' and os.getenv('FLASK_ENV') == 'production':
    print("⚠️  ATTENZIONE: Stai usando la SECRET_KEY di default in produzione! Cambiala nel file .env")

# Configurazione legacy (mantieni per compatibilità)
ALLOWED_EXTENSIONS = {'tsv', 'txt'}

def allowed_file(filename):
    """Controlla se il file ha un'estensione permessa"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_patient_id():
    """Genera un ID paziente unico"""
    return f"TCGA-{str(uuid.uuid4())[:8].upper()}"

def determine_file_type(filename):
    """Determina il tipo di file basato sul nome"""
    filename_lower = filename.lower()
    
    if 'rna_seq' in filename_lower or 'gene' in filename_lower:
        return 'rna_seq'
    elif 'mirna' in filename_lower and 'isoform' in filename_lower:
        return 'mirna_isoform'
    elif 'mirna' in filename_lower:
        return 'mirna_aggregate'
    else:
        return 'unknown'


@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint per upload file e predizione"""
    try:
        # Controlla se ci sono file nella richiesta
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file fornito'})
        
        files = request.files.getlist('files')
        sample_type = request.form.get('sample_type', 'tumor')
        
        # Controlla il numero di file
        if len(files) == 0:
            return jsonify({'success': False, 'error': 'Nessun file selezionato'})
        
        if len(files) > 3:
            return jsonify({'success': False, 'error': 'Massimo 3 file permessi'})
        
        # Controlla che tutti i file abbiano nomi validi
        for file in files:
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Nome file vuoto'})
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': f'Tipo file non permesso: {file.filename}'})
        
        # Genera ID paziente unico
        patient_id = generate_patient_id()
          # Salva i file e crea la lista dei percorsi
        uploaded_files = []
        file_path = "assets/data/"  # Percorso relativo corretto per il container
        
        for file in files:
            if file and allowed_file(file.filename):
                # Usa secure_filename per sicurezza
                filename = secure_filename(file.filename)
                
                # Aggiungi timestamp per evitare conflitti
                timestamp = str(uuid.uuid4())[:8]
                filename = f"{timestamp}_{filename}"
                
                file_full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_full_path)
                
                # Aggiungi il percorso relativo alla lista
                uploaded_files.append(file_path + filename)
                
                print(f"File salvato: {filename} come tipo: {determine_file_type(filename)}")
        
        # Crea il dizionario JSON per la predizione
        json_data = {
            sample_type: {
                patient_id: uploaded_files
            }
        }
        
        print(f"JSON creato: {json_data}")        # Crea il dataset e fai la predizione
        base_dir = os.getcwd()
        print(f"DEBUG: base_dir = {base_dir}")
        sample_df = pre.create_patient_dataset_from_json(json_data, base_dir)        # Effettua la predizione
        model_path = "assets/catboost.cbm"
        
        print(f"DEBUG: Chiamando load_and_predict_from_dataframe con base_dir = {base_dir}")
        results = pred.load_and_predict_from_dataframe(model_path, sample_df, top_features=10, base_dir=base_dir)
        print(f"DEBUG: Risultati chiavi: {list(results.keys())}")
        print(f"DEBUG: 'top_features_with_gene_names' in results: {'top_features_with_gene_names' in results}")
          # Converti i risultati in formato JSON serializzabile
        result_data = {
            'predicted_class': results['predicted_class'],
            'confidence': float(results['confidence']),                
            'prediction_probability': results['prediction_probability'].tolist(),
            'top_features': results['top_features'].to_dict('records')[:10],  # Prime 10 features
            'sample_info': results['sample_info']
        }
        
        # Aggiungi top_features_with_gene_names se disponibile
        if 'top_features_with_gene_names' in results:
            result_data['top_features_with_gene_names'] = results['top_features_with_gene_names'].to_dict('records')[:10]
        
        response_data = {
            'success': True,
            'patient_id': patient_id,
            'uploaded_files': uploaded_files,
            'sample_type': sample_type,
            'result': result_data
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Errore durante la predizione: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'Errore durante la predizione: {str(e)}'
        })


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint per controllo stato servizio"""
    return jsonify({'status': 'healthy', 'service': 'cancer-prediction-api'})

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Endpoint API senza interfaccia web per integrazione"""
    try:
        # Stesso codice di /predict ma senza HTML
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file fornito'})
        
        files = request.files.getlist('files')
        sample_type = request.form.get('sample_type', 'tumor')
        
        if len(files) == 0 or len(files) > 3:
            return jsonify({'success': False, 'error': 'Numero file non valido (1-3 file)'})
        
        # Processo identico a /predict
        patient_id = generate_patient_id()
        uploaded_files = []
        file_path = "app/assets/data/"
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = str(uuid.uuid4())[:8]
                filename = f"{timestamp}_{filename}"
                file_full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_full_path)
                uploaded_files.append(file_path + filename)
        
        json_data = {sample_type: {patient_id: uploaded_files}}
        
        base_dir = os.getcwd()
        sample_df = pre.create_patient_dataset_from_json(json_data, base_dir)
        
        model_path = "app/assets/catboost.cbm"
        results = pred.load_and_predict_from_dataframe(model_path, sample_df, top_features=10, base_dir=base_dir)
        
        # Converti i risultati in formato JSON serializzabile
        result_data = {
            'predicted_class': results['predicted_class'],
            'confidence': float(results['confidence']),                
            'prediction_probability': results['prediction_probability'].tolist(),
            'top_features': results['top_features'].to_dict('records')[:10],  # Prime 10 features
            'sample_info': results['sample_info']
        }
        
        # Aggiungi top_features_with_gene_names se disponibile
        if 'top_features_with_gene_names' in results:
            result_data['top_features_with_gene_names'] = results['top_features_with_gene_names'].to_dict('records')[:10]
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'uploaded_files': uploaded_files,
            'sample_type': sample_type,
            'result': result_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Crea la cartella di upload se non esiste
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)    
    print("Avvio Flask server...")

    app.run(debug=True, host='0.0.0.0', port=5000)
