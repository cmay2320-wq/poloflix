"""
Generates placeholder poster/backdrop artwork so the catalogue looks
populated before you've uploaded real posters. Used only by seed.py.
Swap these out any time by uploading real files through /admin -
the poster_key just needs to point at a real file.
"""
import hashlib

PALETTES = [
    ("#0b1220", "#123a6b", "#1f6fd1"),
    ("#120a1e", "#3a1265", "#7c2ee0"),
    ("#170a0a", "#5a1414", "#d13a3a"),
    ("#0a1712", "#124a2c", "#1fd17a"),
    ("#1a1206", "#5a3a10", "#d18a1f"),
    ("#0a0f17", "#1d2b4a", "#3f6fd1"),
]


def _palette_for(title):
    idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(PALETTES)
    return PALETTES[idx]


def poster_svg(title, subtitle=""):
    dark, mid, accent = _palette_for(title)
    words = title.upper().split()
    lines = []
    line = ""
    for w in words:
        if len(line + " " + w) > 12:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    lines = lines[:4]
    text_svg = ""
    start_y = 300 - (len(lines) - 1) * 22
    for i, l in enumerate(lines):
        text_svg += (
            f'<text x="150" y="{start_y + i * 44}" text-anchor="middle" '
            f'font-family="Helvetica, Arial, sans-serif" font-size="30" '
            f'font-weight="700" fill="#ffffff" letter-spacing="1">{l}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{mid}"/>
      <stop offset="100%" stop-color="{dark}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="30%" r="70%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="300" height="450" fill="url(#g)"/>
  <rect width="300" height="450" fill="url(#glow)"/>
  <rect x="0" y="0" width="300" height="450" fill="none" stroke="{accent}" stroke-opacity="0.35" stroke-width="2"/>
  {text_svg}
  <text x="150" y="420" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{accent}" letter-spacing="3">POLOFLIX</text>
</svg>'''


def backdrop_svg(title):
    dark, mid, accent = _palette_for(title)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{mid}"/>
      <stop offset="100%" stop-color="{dark}"/>
    </linearGradient>
    <radialGradient id="glow" cx="30%" cy="30%" r="60%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#bg)"/>
  <rect width="1600" height="900" fill="url(#glow)"/>
</svg>'''
