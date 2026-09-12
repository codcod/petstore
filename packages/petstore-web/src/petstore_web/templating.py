from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parent / 'templates'


def load_template(relative_path: str) -> Template:
    return Template((TEMPLATES_DIR / relative_path).read_text())
