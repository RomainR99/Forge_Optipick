#!/usr/bin/env python3
"""
Convertit rapport.md en rapport.pdf
Utilise markdown + weasyprint. Installation : pip install markdown weasyprint
Alternative : ouvrir rapport.html dans un navigateur et Imprimer > Enregistrer en PDF
"""
import sys
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    md_path = root / "rapport.md"
    html_path = root / "rapport.html"
    pdf_path = root / "rapport.pdf"

    if not md_path.exists():
        print(f"Erreur : {md_path} introuvable")
        sys.exit(1)

    try:
        import markdown
    except ImportError:
        print("Installez markdown : pip install markdown")
        sys.exit(1)

    md = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    html_full = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{{font-family:system-ui,sans-serif;max-width:800px;margin:2em auto;padding:1em;line-height:1.5}}
table{{border-collapse:collapse;margin:1em 0}} th,td{{border:1px solid #ccc;padding:6px 10px}}
h1{{font-size:1.5em}} h2{{font-size:1.2em;margin-top:1.5em}} h3{{font-size:1.05em}}
a{{color:#0066cc}}
</style></head><body>{html_body}</body></html>"""

    html_path.write_text(html_full, encoding="utf-8")
    print(f"HTML créé : {html_path}")

    try:
        from weasyprint import HTML
        HTML(str(html_path)).write_pdf(str(pdf_path))
        print(f"PDF créé : {pdf_path}")
    except Exception as e:
        print(f"WeasyPrint non disponible : {e}")
        print("→ Ouvrez rapport.html dans un navigateur et utilisez Imprimer > Enregistrer en PDF")

if __name__ == "__main__":
    main()
