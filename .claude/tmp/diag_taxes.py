from bs4 import BeautifulSoup
soup = BeautifulSoup(open(".claude/tmp/page-faena-20260629-165916.html", encoding="utf-8").read(), "html.parser")

# Buscar todos los elementos que contienen el texto "Taxes"
taxes_els = soup.find_all(string=lambda s: s and "Taxes" in s)
print(f"Elementos con 'Taxes': {len(taxes_els)}")
for tx in taxes_els[:3]:
    parent = tx.parent
    # Subir 3 niveles para ver el contexto
    for _ in range(3):
        if parent and parent.parent:
            parent = parent.parent
    print("\n--- CONTEXTO ---")
    print(parent.prettify()[:2000])
    print("===")
