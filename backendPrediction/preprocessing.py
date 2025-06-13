# Functions to reader csv files and process gene expression, miRNA isoform, and miRNA aggregate data

import pandas as pd
import os
from tqdm import tqdm
import numpy as np
import string


def check_and_replace_nan_in_dataframe(df):
    """
    Sostituisce i valori NaN con "missing" nelle colonne di tipo stringa/object.
    """
    for column in df.columns:
        if df[column].dtype == 'object':  # Colonne di tipo stringa
            df[column] = df[column].fillna("missing")
    return df

def process_gene_expression(file_path, prefix="gene"):
    """
    Elabora il file di espressione genica e lo converte in una singola riga.
    """
    df = pd.read_csv(file_path, sep='\t', comment='#')
    
    # Filtra via le righe che iniziano con N_
    if 'gene_id' in df.columns:
        df = df[~df['gene_id'].str.startswith('N_')]
    
    # Mantieni solo le colonne che ci interessano
    feature_columns = ["unstranded", "stranded_first", "stranded_second", "tpm_unstranded", "fpkm_unstranded", "fpkm_uq_unstranded"]
    required_cols = ["gene_id"] + feature_columns
    
    # Verifica che le colonne esistano
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Colonne mancanti nel file {file_path}: {missing_cols}")
    
    # Filtra e rimuovi NA
    #df = df[required_cols].dropna()
    
    # Verifica duplicati
    if df['gene_id'].duplicated().any():
        duplicated_mask = df['gene_id'].duplicated(keep=False)
        duplicate_values = df.loc[duplicated_mask, 'gene_id'].unique()
        
        # Mostra più informazioni sui duplicati
        print(f"Trovati {len(duplicate_values)} geni duplicati in {file_path}")
        print(f"Primi 3 esempi: {', '.join(duplicate_values[:3])}")
        
        # Mostra un esempio dei dati duplicati (con rappresentazione binaria per vedere spazi nascosti)
        first_dup = duplicate_values[0]
        dup_rows = df[df['gene_id'] == first_dup]
        print(f"\nEsempio di righe duplicate per '{first_dup}':")
        print(f"Rappresentazione binaria: {[repr(g) for g in dup_rows['gene_id'].tolist()[:2]]}")
        
        # Continua con la rimozione dei duplicati
        df = df.drop_duplicates(subset=['gene_id'])
    
    # Crea il dizionario dei dati
    row_data = {}
    for feature in feature_columns:
        feature_series = df.set_index('gene_id')[feature]
        feature_series.index = [f"{prefix}_{gene}|{feature}" for gene in feature_series.index]
        row_data.update(feature_series.to_dict())
    
    return row_data

def process_mirna_isoform(file_path, prefix="mirna_iso"):
    """
    Elabora il file dei miRNA a livello di isoforma con identificatori unici basati su lettere alfabetiche.
    """
    try:
        # Leggi il file
        df = pd.read_csv(file_path, sep='\t', comment='#')
        
        # Mantieni solo le colonne che ci interessano
        feature_columns = ["read_count", "reads_per_million_miRNA_mapped", "miRNA_region"]
        
        # Adatta i nomi delle colonne in base al formato del file
        if "isoform_coords" in df.columns:
            id_col = "miRNA_ID"
            coord_col = "isoform_coords"
        else:
            # Adatta per potenziali differenze nel formato del file
            id_col = next((col for col in df.columns if "miRNA" in col or "mirna" in col), "miRNA_ID")
            coord_col = next((col for col in df.columns if "coord" in col), "isoform_coords")
        
        required_cols = [id_col, coord_col] + [col for col in feature_columns if col in df.columns]
        
        # Verifica che le colonne esistano
        if not all(col in df.columns for col in required_cols):
            # Stampa le colonne disponibili per debugging
            print(f"Colonne disponibili: {df.columns.tolist()}")
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"Colonne mancanti nel file {file_path}: {missing}")
        
        # Filtra e rimuovi NA
        df = df[required_cols].dropna()
        
        # Aggiungi una lettera alfabetica per rendere ogni riga univoca per miRNA_ID
        df['unique_suffix'] = (
            df.groupby(id_col).cumcount().apply(lambda x: string.ascii_lowercase[x % 26] + (str(x // 26) if x >= 26 else ""))
        )
        df['unique_id'] = df[id_col] + "_" + df['unique_suffix']
        
        # Crea il dizionario dei dati
        row_data = {}
        for feature in feature_columns:
            if feature in df.columns:
                feature_series = df.set_index('unique_id')[feature]
                feature_series.index = [f"{prefix}_{id}|{feature}" for id in feature_series.index]
                row_data.update(feature_series.to_dict())
        
        return row_data
    except Exception as e:
        print(f"Errore durante l'elaborazione del file {file_path}: {e}")
        raise

def process_mirna_aggregate(file_path, prefix="mirna_agg"):
    """
    Elabora il file dei miRNA aggregati.
    """
    df = pd.read_csv(file_path, sep='\t', comment='#')
    
    # Mantieni solo le colonne che ci interessano
    feature_columns = ["read_count", "reads_per_million_miRNA_mapped"]
    
    # Adatta i nomi delle colonne in base al formato del file
    id_col = next((col for col in df.columns if "miRNA" in col or "mirna" in col), "miRNA_ID")
    required_cols = [id_col] + [col for col in feature_columns if col in df.columns]
    
    # Verifica che le colonne esistano
    if not all(col in df.columns for col in required_cols):
        print(f"Colonne disponibili: {df.columns.tolist()}")
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Colonne mancanti nel file {file_path}: {missing}")
    
    # Filtra e rimuovi NA
    #df = df[required_cols].dropna()
    
    # Verifica duplicati
    if df[id_col].duplicated().any():
        duplicated_mask = df[id_col].duplicated(keep=False)
        duplicate_values = df.loc[duplicated_mask, id_col].unique()
        print(f"miRNA_ID duplicati in {file_path}: {', '.join(duplicate_values)}")
        df = df.drop_duplicates(subset=[id_col])
    
    # Crea il dizionario dei dati
    row_data = {}
    for feature in feature_columns:
        if feature in df.columns:
            feature_series = df.set_index(id_col)[feature]
            feature_series.index = [f"{prefix}_{id}|{feature}" for id in feature_series.index]
            row_data.update(feature_series.to_dict())
    
    return row_data


# Function to create a complete patient dataset from JSON file paths
def create_patient_dataset_from_json(data, base_dir, output_file=None):
    """
    Crea un dataset completo per tutti i pazienti leggendo i path da un JSON.
    
    Parameters:
    -----------
    data : dict
        Dizionario contenente i path dei file per ogni paziente
    base_dir : str
        Directory di base da combinare con i path relativi nel JSON
    output_file : str, optional
        Percorso dove salvare il dataset finale in formato CSV
        
    Returns:
    --------
    pandas.DataFrame
        Dataset con una riga per paziente e colonne per tutte le features
    """
    
    def find_placeholder_file(file_type):
        """
        Trova un file placeholder nella cartella assets/data/tumor/ per il tipo specificato.
        """
        placeholder_dir = "backendPrediction/assets/data/"
        
        try:
            files = os.listdir(placeholder_dir)
            
            if file_type == "gene_expr":
                # Cerca file di gene expression
                for file in files:
                    if ("rna_seq" in file or "gene_counts" in file or "star_gene" in file):
                        return os.path.join(placeholder_dir, file)
            elif file_type == "mirna_iso":
                # Cerca file di miRNA isoforms
                for file in files:
                    if ("isoforms" in file or "isoform" in file):
                        return os.path.join(placeholder_dir, file)
            elif file_type == "mirna_agg":
                # Cerca file di miRNA aggregati
                for file in files:
                    if (("mirnas" in file or "mirna" in file) and "isoform" not in file):
                        return os.path.join(placeholder_dir, file)
        except FileNotFoundError:
            print(f"Cartella {placeholder_dir} non trovata!")
            return None
        
        return None
    
    all_patients_data = []
    
    # Processa i dati dei pazienti in tutte le categorie
    for category, patients in data.items():
        for patient_id, file_paths in tqdm(patients.items(), desc=f"Elaborazione pazienti {category}"):
            # Inizializza i dati del paziente
            patient_data = {"patient_id": patient_id, "category": category}
            
            # Filtra i file wxs e organizza per tipo
            gene_expr_file = None
            mirna_iso_file = None
            mirna_agg_file = None
            
            for path in file_paths:
                # Salta i file wxs
                if ".wxs." in path:
                    continue
                  # Identifica il tipo di file in base ai pattern nel nome
                if (("rna_seq" in path or "gene_counts" in path or "star_gene" in path) and 
                    not gene_expr_file):
                    gene_expr_file = os.path.join(base_dir, path)
                elif (("isoforms" in path or "isoform" in path) and 
                    not mirna_iso_file):
                    mirna_iso_file = os.path.join(base_dir, path)
                elif ((("mirnas" in path or "mirna" in path) and "isoform" not in path) and 
                    not mirna_agg_file):
                    mirna_agg_file = os.path.join(base_dir, path)
            
            # Se gene expression non è disponibile, scartiamo il paziente
            if not gene_expr_file:
                print(f"Paziente {patient_id} manca del file gene_expr, lo scartiamo.")
                continue
                
            try:
                # Elabora il file di espressione genica
                gene_data = process_gene_expression(gene_expr_file)
                patient_data.update(gene_data)
                  # Gestione dei file miRNA isoform
                try:
                    if mirna_iso_file:
                        mirna_iso_data = process_mirna_isoform(mirna_iso_file)
                    else:
                        # Usa un file placeholder dalla cartella assets/data/tumor/
                        placeholder_file = find_placeholder_file("mirna_iso")
                        if placeholder_file:
                            print(f"Usando file placeholder {placeholder_file} per mirna_iso del paziente {patient_id}")
                            temp_data = process_mirna_isoform(placeholder_file)
                            # Imposta tutti i valori a NaN
                            mirna_iso_data = {k: np.nan for k in temp_data.keys()}
                        else:
                            print(f"Nessun file placeholder trovato per mirna_iso. Dati non aggiunti per il paziente {patient_id}.")
                            mirna_iso_data = {}
                    patient_data.update(mirna_iso_data)
                except FileNotFoundError:
                    print(f"File mirna_iso non trovato per il paziente {patient_id}. Usando placeholder.")
                    placeholder_file = find_placeholder_file("mirna_iso")
                    if placeholder_file:
                        temp_data = process_mirna_isoform(placeholder_file)
                        mirna_iso_data = {k: np.nan for k in temp_data.keys()}
                        patient_data.update(mirna_iso_data)
                    else:
                        print(f"Nessun file placeholder per mirna_iso. Dati non aggiunti per il paziente {patient_id}.")
                except Exception as e:
                    print(f"Errore nell'elaborazione del mirna_iso per il paziente {patient_id}: {e}")
                    # Continuiamo comunque con il resto dei dati
                  # Gestione dei file miRNA aggregate
                try:
                    if mirna_agg_file:
                        mirna_agg_data = process_mirna_aggregate(mirna_agg_file)
                    else:
                        # Usa un file placeholder dalla cartella assets/data/tumor/
                        placeholder_file = find_placeholder_file("mirna_agg")
                        if placeholder_file:
                            print(f"Usando file placeholder {placeholder_file} per mirna_agg del paziente {patient_id}")
                            temp_data = process_mirna_aggregate(placeholder_file)
                            # Imposta tutti i valori a NaN
                            mirna_agg_data = {k: np.nan for k in temp_data.keys()}
                        else:
                            print(f"Nessun file placeholder trovato per mirna_agg. Dati non aggiunti per il paziente {patient_id}.")
                            mirna_agg_data = {}
                    patient_data.update(mirna_agg_data)
                except FileNotFoundError:
                    print(f"File mirna_agg non trovato per il paziente {patient_id}. Usando placeholder.")
                    placeholder_file = find_placeholder_file("mirna_agg")
                    if placeholder_file:
                        temp_data = process_mirna_aggregate(placeholder_file)
                        mirna_agg_data = {k: np.nan for k in temp_data.keys()}
                        patient_data.update(mirna_agg_data)
                    else:
                        print(f"Nessun file placeholder per mirna_agg. Dati non aggiunti per il paziente {patient_id}.")
                except Exception as e:
                    print(f"Errore nell'elaborazione del mirna_agg per il paziente {patient_id}: {e}")
                    # Continuiamo comunque con il resto dei dati
                
                all_patients_data.append(patient_data)
            except Exception as e:
                print(f"Errore nell'elaborazione del paziente {patient_id}: {e}")
    
    # Crea il DataFrame
    if not all_patients_data:
        print("Nessun dato paziente trovato!")
        return None
    df = pd.DataFrame(all_patients_data)
    df.pop('patient_id')
    df.pop('category')
    

    # Salva il dataset se richiesto
    """if output_file:
        df.to_csv(output_file, index=False)
        print(f"Dataset salvato in {output_file}")"""
    
    return df


