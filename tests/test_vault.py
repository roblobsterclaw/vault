import json
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
    assert 'sessionStorage' in js
    assert '@media(max-width:700px)' in css

def test_department_folders_exist():
    expected = ['tuckerton-group','investing','rebolt','firehouse','real-estate','family','lobster-press','research','daily-rundowns']
    for folder in expected:
        assert (ROOT / 'docs' / folder).is_dir()
