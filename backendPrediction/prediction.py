"""
Normali: ['TCGA-EW-A2FW']
Tumor: ['TCGA-A8-A07G']
"""

import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
import preprocessing as pre
import re
import os

def extract_gene_id_from_feature(feature_name):
    """
    Estrae l'ID del gene dal nome della feature.
    Cerca dal primo '_' fino al primo '|' trovato.
    
    Args:
        feature_name (str): Nome della feature
    
    Returns:
        str: ID del gene estratto o la feature originale se l'estrazione fallisce
    """
    try:
        # Cerca il pattern: dal primo _ fino al primo |
        match = re.search(r'_([^_|]+)\|', feature_name)
        if match:
            return match.group(1)
        
        # Se non trova il pattern, prova a estrarre tutto dopo il primo _
        if '_' in feature_name:
            parts = feature_name.split('_', 1)
            if len(parts) > 1:
                # Rimuovi tutto dopo il primo | se presente
                gene_part = parts[1].split('|')[0]
                return gene_part
        
        # Se non riesce a estrarre, restituisce la feature originale
        return feature_name
    except Exception:
        return feature_name

def load_gene_mapping_from_tsv(tsv_path):
    """
    Carica la mappatura gene_id -> gene_name dal file TSV.
    
    Args:
        tsv_path (str): Percorso del file TSV
    
    Returns:
        dict: Dizionario con mappatura gene_id -> gene_name
    """
    try:
        # Leggi il file TSV
        df = pd.read_csv(tsv_path, sep='\t', comment='#')
        
        # Crea dizionario di mappatura gene_id -> gene_name
        gene_mapping = {}
        if 'gene_id' in df.columns and 'gene_name' in df.columns:
            for _, row in df.iterrows():
                gene_id = str(row['gene_id'])
                gene_name = str(row['gene_name'])
                if gene_id and gene_name and gene_id != 'nan' and gene_name != 'nan':
                    gene_mapping[gene_id] = gene_name
        
        print(f"Caricata mappatura per {len(gene_mapping)} geni dal file TSV")
        return gene_mapping
    
    except Exception as e:
        print(f"Errore nel caricamento del file TSV {tsv_path}: {e}")
        return {}

def map_features_to_gene_names(top_features_df, base_dir):
    """
    Mappa le feature più importanti ai nomi dei geni.
    
    Args:
        top_features_df (pd.DataFrame): DataFrame con le top features
        base_dir (str): Directory base per trovare i file TSV
    
    Returns:
        pd.DataFrame: DataFrame arricchito con colonna 'gene_name'
    """    # Cerca il file TSV augmented_star_gene_counts
    tsv_path = None
    # Nel container Docker, la struttura è /app/assets/data
    data_dir = os.path.join(base_dir, "assets", "data")
    
    print(f"DEBUG: Cercando file TSV in directory: {data_dir}")
    print(f"DEBUG: Directory esiste: {os.path.exists(data_dir)}")
    
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        print(f"DEBUG: File trovati: {files}")
        for file in files:
            if file.endswith("augmented_star_gene_counts.tsv"):
                tsv_path = os.path.join(data_dir, file)
                print(f"DEBUG: File TSV trovato: {tsv_path}")
                break
    
    if not tsv_path:
        print("DEBUG: File TSV augmented_star_gene_counts non trovato")
        # Aggiungi colonna gene_name uguale alla feature
        result_df = top_features_df.copy()
        result_df['gene_name'] = result_df['feature']
        return result_df
    else:
        print(f"DEBUG: Usando file TSV: {tsv_path}")
        # Carica la mappatura dei geni
        gene_mapping = load_gene_mapping_from_tsv(tsv_path)
    
        # Estrai gli ID dei geni e mappa ai nomi
        result_df = top_features_df.copy()
        gene_names = []
    
        for feature in result_df['feature']:
            # Estrai l'ID del gene
            gene_id = extract_gene_id_from_feature(feature)
        
            # Cerca il nome del gene nella mappatura
            if gene_id in gene_mapping:
                gene_name = gene_mapping[gene_id]
            else:
                # Se non trova la mappatura, usa l'ID estratto come nome
                gene_name = gene_id
        
            gene_names.append(gene_name)
    
        result_df['gene_name'] = gene_names
        return result_df

def align_features_with_model(sample_df, model):
    """
    Allinea le features del sample con quelle attese dal modello
    
    Args:
        sample_df (pd.DataFrame): DataFrame con le features del sample
        model: Modello CatBoost caricato
    
    Returns:
        pd.DataFrame: DataFrame allineato con le features del modello
    """
    try:
        # Ottieni le feature names dal modello
        model_features = model.feature_names_
        
        # Prepara le colonne da concatenare
        columns_to_concat = []
        
        # Per ogni feature attesa dal modello
        for feature in model_features:
            if feature in sample_df.columns:
                # Se la feature esiste nel sample, usala
                columns_to_concat.append(sample_df[[feature]])
            else:
                # Se la feature non esiste, crea una serie con valore 0
                zero_series = pd.DataFrame({feature: [0] * len(sample_df)}, index=sample_df.index)
                columns_to_concat.append(zero_series)
        
        # Concatena tutte le colonne in una volta sola per evitare frammentazione
        if columns_to_concat:
            aligned_df = pd.concat(columns_to_concat, axis=1)
        else:
            aligned_df = pd.DataFrame(index=sample_df.index)
        
        print(f"Features originali: {len(sample_df.columns)}")
        print(f"Features attese dal modello: {len(model_features)}")
        print(f"Features allineate: {len(aligned_df.columns)}")
        
        return aligned_df
        
    except Exception as e:
        print(f"Errore nell'allineamento delle features: {e}")
        # Fallback: usa le prime N features del sample dove N è il numero atteso dal modello
        try:
            expected_features = len(model.feature_names_)
            if len(sample_df.columns) > expected_features:
                print(f"Troncando da {len(sample_df.columns)} a {expected_features} features")
                return sample_df.iloc[:, :expected_features]
            elif len(sample_df.columns) < expected_features:
                print(f"Padding da {len(sample_df.columns)} a {expected_features} features")
                # Aggiungi colonne mancanti con valore 0
                missing_cols = expected_features - len(sample_df.columns)
                for i in range(missing_cols):
                    sample_df[f'missing_feature_{i}'] = 0
                return sample_df
            else:
                return sample_df
        except:
            return sample_df

def load_and_predict_from_dataframe(model_path, sample_df, top_features=10, base_dir=None):
    """
    Carica un modello CatBoost e effettua predizione su un singolo sample da DataFrame
    
    Args:
        model_path (str): Percorso del file .cbm
        sample_df (pd.DataFrame): DataFrame contenente un singolo sample (1 riga)
        top_features (int): Numero di top features da restituire
        base_dir (str): Directory base per trovare i file di mappatura dei geni
    
    Returns:
        dict: Risultati della predizione e feature importance con nomi dei geni
    """
    # Carica il modello
    model = CatBoostClassifier()
    model.load_model(model_path)
    
    # Verifica che sia un singolo sample
    if len(sample_df) != 1:
        raise ValueError("Il DataFrame deve contenere esattamente un sample (1 riga)")
      # Allinea le features con quelle attese dal modello
    aligned_df = align_features_with_model(sample_df, model)
    aligned_df = pre.check_and_replace_nan_in_dataframe(aligned_df)
    
    # Gestisci specificamente i NaN per le categorical features di CatBoost
    # Ottieni gli indici delle categorical features dal modello
    try:
        cat_features = model.get_cat_feature_indices()
        if cat_features:
            print(f"Trovate {len(cat_features)} categorical features nel modello")
            for cat_idx in cat_features:
                if cat_idx < len(aligned_df.columns):
                    col_name = aligned_df.columns[cat_idx]
                    # Converti NaN a stringa per le categorical features
                    aligned_df[col_name] = aligned_df[col_name].fillna("missing").astype(str)
    except Exception as e:
        print(f"Avviso: Impossibile ottenere categorical features dal modello: {e}")
        # Fallback: converti tutti i NaN rimanenti a 0 per sicurezza
        aligned_df = aligned_df.fillna(0)

    # Effettua la predizione usando le features allineate
    prediction = model.predict(aligned_df)[0]
    prediction_proba = model.predict_proba(aligned_df)[0]
    
    # Ottieni feature importance
    feature_importance = model.get_feature_importance()
    feature_names = aligned_df.columns.tolist()
    
    # Crea DataFrame con feature importance
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': feature_importance,
        'sample_value': aligned_df.iloc[0].values
    }).sort_values('importance', ascending=False)
      # Seleziona top features
    top_features_df = importance_df.head(top_features)
    
    # Mappa le feature ai nomi dei geni se base_dir è fornito
    result = {
        'prediction': prediction,
        'prediction_probability': prediction_proba,
        'predicted_class': int(prediction),
        'confidence': float(prediction_proba.max()),
        'top_features': top_features_df,
        'all_feature_importance': importance_df,
        'sample_info': {
            'total_features': len(feature_names),
            'sample_shape': aligned_df.shape,
            'features_aligned': True
        }
    }
    
    # Aggiungi mappatura dei nomi dei geni se base_dir è fornito
    if base_dir:
        mapped_features = map_features_to_gene_names(top_features_df, base_dir)
        result['top_features_with_gene_names'] = mapped_features
    
    return result

def predict_and_explain(model_path, sample_df, show_top=15, base_dir=None):
    """
    Funzione semplificata con output formattato
    
    Args:
        model_path (str): Percorso del modello CatBoost
        sample_df (pd.DataFrame): DataFrame del sample
        show_top (int): Numero di feature da mostrare
        base_dir (str): Directory base per trovare il file TSV (opzionale)
    """
    results = load_and_predict_from_dataframe(model_path, sample_df, show_top)
    
    print(f"Predizione: Classe {results['predicted_class']}")
    print(f"Confidenza: {results['confidence']:.4f}")
    print(f"Probabilità per classe: {results['prediction_probability']}")
    print(f"Numero totale di features: {results['sample_info']['total_features']}")
    # Mappa le feature ai nomi dei geni se base_dir è fornito
    if base_dir:
        mapped_features = map_features_to_gene_names(results['top_features'], base_dir)
        print(f"\nTop {show_top} features più importanti (con nomi geni):")
        
        # Configura pandas per mostrare tutte le colonne
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        
        print(mapped_features[['feature', 'gene_name', 'importance', 'sample_value']])
        results['top_features_with_gene_names'] = mapped_features
    else:
        print(f"\nTop {show_top} features più importanti:")
        
        # Configura pandas per mostrare tutte le colonne
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        
        print(results['top_features'][['feature', 'importance', 'sample_value']])
    
    return results

# Esempio di utilizzo
if __name__ == "__main__":
    # Carica il modello
    model_path = "backendPrediction/assets/catboost.cbm"
    file_path = "backendPrediction/assets/data/"
    base_dir=r"c:\Users\nikba\Desktop\roba\uni\urban\urban"
    json_data = {"tumor":{"TCGA-AA-AAAA":
        [file_path+"normal.rna_seq.augmented_star_gene_counts.tsv", 
         file_path+"tumor.mirbase21.mirnas.quantification.txt", 
         file_path+"tumor.mirbase21.isoforms.quantification.txt"
         ]}}
    sample_df=pre.create_patient_dataset_from_json(json_data, base_dir)
    
    try:
        # Mostra risultati con mappatura dei geni
        predict_and_explain(model_path, sample_df, show_top=10, base_dir=base_dir)
    except Exception as e:
        print(f"Errore durante la predizione: {e}")