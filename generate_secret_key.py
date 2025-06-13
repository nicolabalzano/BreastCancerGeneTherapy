#!/usr/bin/env python3
"""
Utility per generare SECRET_KEY sicure per Flask
"""

import secrets
import string
import os
import sys

def generate_secret_key(length=64):
    """
    Genera una SECRET_KEY sicura per Flask compatibile con Docker Compose
    
    Args:
        length (int): Lunghezza della chiave (default: 64)
    
    Returns:
        str: SECRET_KEY sicura senza caratteri problematici
    """
    # Usa solo caratteri alfanumerici per evitare problemi con Docker Compose
    # Evita caratteri come $, !, {, }, &, *, (, ), [, ], ", ', \, `, |, <, >, ;, :, =, +
    alphabet = string.ascii_letters + string.digits + '-_.'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_hex_key(length=32):
    """
    Genera una SECRET_KEY esadecimale sicura (solo 0-9, a-f)
    
    Args:
        length (int): Lunghezza in bytes (default: 32)
    
    Returns:
        str: SECRET_KEY esadecimale
    """
    return secrets.token_hex(length)

def generate_alphanumeric_key(length=64):
    """
    Genera una SECRET_KEY alfanumerica sicura (solo lettere e numeri)
    
    Args:
        length (int): Lunghezza della chiave (default: 64)
    
    Returns:
        str: SECRET_KEY alfanumerica
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_base64_key(length=32):
    """
    Genera una SECRET_KEY base64 sicura
    
    Args:
        length (int): Lunghezza in bytes (default: 32)
    
    Returns:
        str: SECRET_KEY base64 (senza padding =)
    """
    return secrets.token_urlsafe(length).rstrip('=')  # Rimuove padding che può creare problemi

def update_env_file(env_path=".env", backup=True):
    """
    Aggiorna il file .env con una nuova SECRET_KEY
    
    Args:
        env_path (str): Percorso del file .env
        backup (bool): Se creare un backup del file esistente
    """
    new_key = generate_alphanumeric_key()  # Usa la versione più sicura per Docker
    
    if not os.path.exists(env_path):
        print(f"❌ File {env_path} non trovato")
        return False
    
    # Leggi il file esistente
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crea backup se richiesto
    if backup:
        backup_path = f"{env_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📁 Backup creato: {backup_path}")
    
    # Aggiorna o aggiungi SECRET_KEY
    lines = content.splitlines()
    updated = False
    
    for i, line in enumerate(lines):
        if line.startswith('SECRET_KEY='):
            lines[i] = f"SECRET_KEY={new_key}"
            updated = True
            break
    
    if not updated:
        lines.append(f"SECRET_KEY={new_key}")
    
    # Scrivi il file aggiornato
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    
    print(f"✅ SECRET_KEY aggiornata nel file {env_path}")
    print(f"🔑 Nuova chiave: {new_key}")
    return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Genera SECRET_KEY sicure per Flask')
    parser.add_argument('--length', '-l', type=int, default=64, 
                       help='Lunghezza della chiave (default: 64)')
    parser.add_argument('--type', '-t', choices=['standard', 'hex', 'urlsafe', 'alphanumeric'], 
                       default='alphanumeric', help='Tipo di chiave (default: alphanumeric - solo lettere e numeri)')
    parser.add_argument('--update-env', '-u', action='store_true',
                       help='Aggiorna il file .env con la nuova chiave')
    parser.add_argument('--env-file', '-e', default='.env',
                       help='Percorso del file .env (default: .env)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Non creare backup del file .env')
    
    args = parser.parse_args()
    
    print("🔐 Generatore SECRET_KEY per Flask")
    print("=" * 40)
    
    # Genera la chiave del tipo richiesto
    if args.type == 'hex':
        key = generate_hex_key(args.length)
        print(f"🔑 SECRET_KEY esadecimale ({args.length} bytes):")
    elif args.type == 'urlsafe':
        key = generate_base64_key(args.length)
        print(f"🔑 SECRET_KEY base64 ({args.length} bytes):")
    elif args.type == 'alphanumeric':
        key = generate_alphanumeric_key(args.length)
        print(f"🔑 SECRET_KEY alfanumerica ({args.length} caratteri):")
    else:
        key = generate_secret_key(args.length)
        print(f"🔑 SECRET_KEY standard ({args.length} caratteri):")
    
    print(f"   {key}")
    print()
    
    # Aggiorna il file .env se richiesto
    if args.update_env:
        print("📝 Aggiornamento file .env...")
        success = update_env_file(args.env_file, not args.no_backup)
        if not success:
            sys.exit(1)
    else:
        print("💡 Per aggiornare automaticamente il file .env:")
        print(f"   python {sys.argv[0]} --update-env")
        print()
        print("📋 Oppure copia manualmente questa riga nel tuo file .env:")
        print(f"   SECRET_KEY={key}")
    
    print()
    print("ℹ️  Informazioni sulla sicurezza:")
    print("   • Non condividere mai la SECRET_KEY")
    print("   • Usa chiavi diverse per sviluppo e produzione")
    print("   • Rigenera periodicamente la chiave in produzione")
    print("   • Mantieni la chiave nel file .env (escluso da Git)")

if __name__ == "__main__":
    main()
