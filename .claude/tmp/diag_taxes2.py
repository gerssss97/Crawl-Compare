from bs4 import BeautifulSoup
soup = BeautifulSoup(open(".claude/tmp/page-faena-20260629-165916.html", encoding="utf-8").read(), "html.parser")

# Encontrar el tag que contiene "Taxes" directamente
taxes_texts = soup.find_all(string=lambda s: s and "Taxes" in s)
for tx in taxes_texts[:2]:
    el = tx.parent
    print("--- TAG con Taxes ---")
    print(el.prettify()[:500])
    print("  classes:", el.get("class"))
    print("--- PARENT 1 ---")
    p1 = el.parent
    print("  tag:", p1.name, "classes:", p1.get("class"))
    print("--- PARENT 2 ---")
    p2 = p1.parent
    print("  tag:", p2.name, "classes:", p2.get("class"))
    print(p2.prettify()[:1500])
    print("===")
