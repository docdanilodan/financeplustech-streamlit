from datetime import datetime
from pathlib import Path
import requests
import streamlit as st

ARCHIVE = Path('archive')
ARCHIVE.mkdir(exist_ok=True)


def get_storage_provider():
    try:
        return st.secrets.get('storage', {}).get('provider', 'local')
    except Exception:
        return 'local'


def save_file_local(cliente_id, categoria, uploaded_file):
    safe = categoria.lower().replace(' ', '_').replace('/', '_')
    folder = ARCHIVE / str(cliente_id) / safe
    folder.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uploaded_file.name
    path = folder / filename
    with open(path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return str(path)


def upload_to_google_drive(local_path, filename):
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    info = dict(st.secrets['gdrive_service_account'])
    folder_id = st.secrets['google_drive']['folder_id']
    credentials = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive.file'])
    service = build('drive', 'v3', credentials=credentials)
    media = MediaFileUpload(local_path, resumable=True)
    result = service.files().create(body={'name': filename, 'parents': [folder_id]}, media_body=media, fields='id, name').execute()
    return result.get('id', '')


def upload_to_pcloud(local_path, filename):
    token = st.secrets['pcloud']['access_token']
    folder_id = st.secrets['pcloud'].get('folder_id', '0')
    with open(local_path, 'rb') as f:
        response = requests.post('https://api.pcloud.com/uploadfile', data={'auth': token, 'folderid': folder_id, 'renameifexists': 1}, files={'file': (filename, f)}, timeout=60)
    response.raise_for_status()
    return response.json().get('metadata', [{}])[0].get('fileid', '')


def archive_uploaded_file(cliente_id, categoria, uploaded_file):
    local_path = save_file_local(cliente_id, categoria, uploaded_file)
    provider = get_storage_provider()
    cloud_id = ''
    if provider == 'google_drive':
        cloud_id = upload_to_google_drive(local_path, uploaded_file.name)
    elif provider == 'pcloud':
        cloud_id = upload_to_pcloud(local_path, uploaded_file.name)
    return local_path, provider, cloud_id
