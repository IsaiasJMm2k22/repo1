import base64
import requests
import os
from pathlib import Path

def subir_archivos_github(token, repo_owner, repo_name, archivos, mensaje_commit="Subida automática de archivos", branch="main"):
    """
    Sube múltiples archivos a un repositorio GitHub
    
    Args:
        token (str): Token de acceso personal de GitHub
        repo_owner (str): Dueño del repositorio (usuario u organización)
        repo_name (str): Nombre del repositorio
        archivos (list): Lista de diccionarios con:
            - 'path': Ruta relativa en el repositorio (ej. "carpeta/archivo.txt")
            - 'content': Contenido del archivo como string
            - 'encoding': Opcional ("utf-8", "base64", etc.)
        mensaje_commit (str): Mensaje para el commit
        branch (str): Rama destino (default "main")
    
    Returns:
        dict: Resultado de la operación
    """
    
    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    resultados = []
    errores = []
    
    for archivo in archivos:
        try:
            path = archivo['path']
            content = archivo['content']
            encoding = archivo.get('encoding', 'utf-8')
            
            # Codificar contenido según especificación
            if encoding.lower() == 'base64':
                encoded_content = content  # Asume que ya viene en base64
            else:
                encoded_content = base64.b64encode(content.encode(encoding)).decode('utf-8')
            
            data = {
                "message": mensaje_commit,
                "content": encoded_content,
                "branch": branch
            }
            
            # Verificar si el archivo existe para actualizar (necesita sha)
            check_url = base_url + path
            response = requests.get(check_url, headers=headers)
            
            if response.status_code == 200:
                data["sha"] = response.json()["sha"]
            
            # Subir/actualizar archivo
            upload_url = base_url + path
            response = requests.put(upload_url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                resultados.append({
                    "path": path,
                    "status": "success",
                    "response": response.json()
                })
            else:
                errores.append({
                    "path": path,
                    "status": "error",
                    "error": response.json(),
                    "status_code": response.status_code
                })
                
        except Exception as e:
            errores.append({
                "path": archivo.get('path', 'desconocido'),
                "status": "exception",
                "error": str(e)
            })
    
    return {
        "success": len(errores) == 0,
        "resultados": resultados,
        "errores": errores,
        "total_subidos": len(resultados),
        "total_errores": len(errores)
    }


# Función auxiliar para preparar archivos desde el sistema de archivos
def preparar_archivos_desde_directorio(directorio_local, directorio_remoto=""):
    """
    Prepara archivos de un directorio local para subirlos a GitHub
    
    Args:
        directorio_local (str): Ruta al directorio local
        directorio_remoto (str): Ruta base remota (opcional)
    
    Returns:
        list: Lista de diccionarios con estructura para subir_archivos_github
    """
    archivos = []
    directorio_local = Path(directorio_local)
    
    for item in directorio_local.rglob('*'):
        if item.is_file():
            # Calcular ruta relativa
            rel_path = item.relative_to(directorio_local)
            remote_path = str(Path(directorio_remoto) / rel_path) if directorio_remoto else str(rel_path)
            
            # Leer contenido
            with open(item, 'r', encoding='utf-8') as f:
                content = f.read()
            
            archivos.append({
                'path': remote_path.replace('\\', '/'),  # Usar / para GitHub
                'content': content,
                'encoding': 'utf-8'
            })
    
    return archivos


from os import getenv
from dotenv import load_dotenv

# Ejemplo de uso
if __name__ == "__main__":
    load_dotenv(".env")
    # Configuración
    TOKEN = getenv("GITHUB_TOKEN")
    print(f"Token: {TOKEN}")
    REPO_OWNER = "IsaiasJMm2k22"
    REPO_NAME = "repo1"
    
    # # Opción 1: Subir archivos creados dinámicamente
    # archivos_dinamicos = [
    #     {
    #         "path": "README.md",
    #         "content": "# Mi Proyecto\n\nEste es un repositorio creado automáticamente",
    #         "encoding": "utf-8"
    #     },
    #     {
    #         "path": "src/main.py",
    #         "content": "print('Hola mundo!')",
    #         "encoding": "utf-8"
    #     }
    # ]
    
    # resultado = subir_archivos_github(
    #     token=TOKEN,
    #     repo_owner=REPO_OWNER,
    #     repo_name=REPO_NAME,
    #     archivos=archivos_dinamicos,
    #     mensaje_commit="Subida inicial de archivos"
    # )
    # print(resultado)
    
    # Opción 2: Subir archivos desde un directorio local
    archivos_locales = preparar_archivos_desde_directorio("mcp", "mcp")
    resultado = subir_archivos_github(TOKEN, REPO_OWNER, REPO_NAME, archivos_locales)
    print(resultado)