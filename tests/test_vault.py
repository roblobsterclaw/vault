import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_manifest_has_required_shape_and_files_exist():
    data = json.loads((ROOT / 'manifest.json').read_text())
    assert data['count'] == len(data['documents'])
    assert data['count'] > 0
    required = {'name', 'folder', 'date', 'description', 'url', 'type', 'versionKey'}
    for doc in data['documents']:
        assert required.issubset(doc)
        assert (ROOT / doc['url']).exists(), doc['url']
        assert doc['folder'] in data['departments']
        assert doc['type'] in {'docx', 'pdf', 'xlsx'}

def test_app_contains_core_features():
    html = (ROOT / 'index.html').read_text()
    js = (ROOT / 'app.js').read_text()
    css = (ROOT / 'styles.css').read_text()
    assert "Rob's Document Vault" in html
    assert 'manifest.json' in js
    assert 'History' in js
    assert 'groupDocuments' in js
    assert 'familyKey' in js
    assert 'Showing Families' in js
    assert 'VAULT_PUBLIC_BASE' in js
    assert 'view.officeapps.live.com' in js
    assert 'target="_blank"' in js
    assert 'sessionStorage' in js
    assert "VAULT_PASSWORD='soccer12'" in js
    assert 'ROBLOBSTER' not in js
    assert '.view' in css
    assert '@media(max-width:700px)' in css

def test_department_folders_exist():
    expected = ['tuckerton-group','investing','rebolt','firehouse','real-estate','family','lobster-press','research','daily-rundowns']
    for folder in expected:
        assert (ROOT / 'docs' / folder).is_dir()

def test_manifest_has_collapsible_document_families():
    data = json.loads((ROOT / 'manifest.json').read_text())
    family_counts = {}
    for doc in data['documents']:
        key = family_key(doc)
        family_counts[key] = family_counts.get(key, 0) + 1

    assert len(family_counts) < data['count']
    assert family_counts['jfl ttd'] >= 50
    assert family_counts['morning joes rundown'] >= 20
    assert family_counts['mission control'] >= 10
    assert family_counts['morning package'] >= 5

def family_key(doc):
    seed = (doc.get('versionKey') or doc.get('name') or doc.get('fileName') or '').lower()
    normalized = re.sub(r'\.[a-z0-9]+$', ' ', seed)
    normalized = re.sub(r'\b20\d{2}[-_ ]\d{1,2}[-_ ]\d{1,2}\b', ' ', normalized)
    normalized = re.sub(r'\b\d{1,2}[-_ ]\d{1,2}[-_ ]\d{2,4}\b', ' ', normalized)
    normalized = re.sub(r'\b(v|version)\s*\d+(\.\d+)*\b', ' ', normalized)
    normalized = re.sub(r'\b[a-f0-9]{8}\b', ' ', normalized)
    normalized = re.sub(
        r'\b(updated|revised|clean|formatted|print|baseline|working|final|latest|from joe|joeedits|edits)\b',
        ' ',
        normalized,
    )
    normalized = re.sub(r'[^a-z0-9]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized or seed.strip() or doc['url']
