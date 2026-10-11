"""
================================================================================
SCRIPT: push_to_github.py
PROPÓSITO: Sincroniza y sube cambios al repositorio GitHub automáticamente.
================================================================================
Lee de forma segura el token OAuth desde el Administrador de Credenciales de Windows
(guardado por GitHub Desktop) y ejecuta git push en la rama main.
"""

import os, sys, subprocess, ctypes
from ctypes import wintypes

tools_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.abspath(os.path.join(tools_dir, ".."))
git_exe = r"C:\Users\51949\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe"

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)), ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR)
    ]

def get_token():
    advapi32 = ctypes.windll.advapi32
    CredReadW = advapi32.CredReadW
    CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    CredReadW.restype = wintypes.BOOL

    target = 'GitHub - https://api.github.com/Aquiles-ryp360'
    pcred = ctypes.POINTER(CREDENTIAL)()
    res = CredReadW(target, 1, 0, ctypes.byref(pcred))
    if not res:
        return None

    cred = pcred.contents
    token = bytes((cred.CredentialBlob[i] for i in range(cred.CredentialBlobSize))).decode('utf-8', errors='ignore')
    advapi32.CredFree(pcred)
    return token

def main():
    token = get_token()
    if not token:
        print("No se encontró token en Credential Manager. Usa GitHub Desktop para sincronizar.")
        return

    username = "Aquiles-ryp360"
    repo_name = "Catastro_Limbani"
    auth_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    clean_url = f"https://github.com/{username}/{repo_name}.git"

    print("Configurando remoto y sincronizando con GitHub...")
    subprocess.run([git_exe, "remote", "set-url", "origin", auth_url], cwd=repo_dir, check=True)
    res = subprocess.run([git_exe, "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    subprocess.run([git_exe, "remote", "set-url", "origin", clean_url], cwd=repo_dir, check=True)
    print(f"Sincronización finalizada. Remoto seguro: {clean_url}")

if __name__ == "__main__":
    main()
