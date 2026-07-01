from bs4 import BeautifulSoup
soup = BeautifulSoup(open(".claude/tmp/page-faena-20260629-165916.html", encoding="utf-8").read(), "html.parser")
el = soup.select_one(".offer-price--alternative")
parent = el.parent
for _ in range(4):
    if parent and parent.parent:
        parent = parent.parent
print(parent.prettify()[:5000])
