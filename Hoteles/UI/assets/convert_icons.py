from pathlib import Path
import cairosvg

ICONS_DIR = Path(__file__).parent / "icons"
COLORS = {
    "light": "#374151",
    "dark":  "#F9FAFB",
}
SIZE = 48  # px — alta resolución para DPI alto; CTkImage hace el downscale


def recolor_svg(svg_text: str, color: str) -> str:
    return svg_text.replace('stroke="currentColor"', f'stroke="{color}"')


def main():
    svgs = list(ICONS_DIR.glob("*.svg"))
    print(f"Convirtiendo {len(svgs)} íconos...")

    for theme, color in COLORS.items():
        out_dir = ICONS_DIR / theme
        out_dir.mkdir(exist_ok=True)
        for svg_path in svgs:
            svg_text = svg_path.read_text(encoding="utf-8")
            svg_text = recolor_svg(svg_text, color)
            out_path = out_dir / svg_path.with_suffix(".png").name
            cairosvg.svg2png(
                bytestring=svg_text.encode("utf-8"),
                write_to=str(out_path),
                output_width=SIZE,
                output_height=SIZE,
            )
            print(f"  [{theme}] {svg_path.name} → {out_path.name}")

    print("Listo.")


if __name__ == "__main__":
    main()
