
import os
import logging
import subprocess
from datetime import datetime

def git_push_changes(message=None):
    """
    Executa git add, commit e push após alterações no banco de dados
    """
    if not message:
        message = f"Atualização automática em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        # Configurar os comandos git para executar
        git_commands = [
            ['git', 'add', '.'],
            ['git', 'commit', '-m', message],
            ['git', 'push']
        ]
        
        # Executar cada comando
        for cmd in git_commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0 and not (result.stderr and 'nothing to commit' in result.stderr):
                logging.error(f"Erro ao executar {' '.join(cmd)}: {result.stderr}")
                return False
            
        logging.info(f"Git push realizado com sucesso: {message}")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar para o git: {str(e)}")
        return False
