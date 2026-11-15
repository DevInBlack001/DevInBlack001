#!/usr/bin/env python3
"""Generate the profile README's cards as static SVGs in ./cards.

Replaces the third-party github-readme-stats image host, which can go down
or hit rate limits and leave broken images. Uses only the public GitHub API
(read-only) and the standard library. Set GITHUB_TOKEN to raise rate limits.
"""
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("CARDS_USER", "DevInBlack001")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cards")
MAX_BYTES = 4 * 1024 * 1024

# Repos shown as cards, in README order.
PINNED = [
    "tui-file-manager", "arch-transfer-manager", "omarchy-system-health",
    "omarchy-wazuh-view", "Omarchy-Wazuh-Server-View", "omarchy-clipboard-quickview",
    "lofi-launcher-terminal", "hyprland-battery-info-display",
    "hyprland-gpu-display-switcher", "Hyprland-Network-Test",
]

ACCENT = "#00FF41"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
BG = "#0d1117"
BORDER = "#30363d"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

LANG_COLORS = {
    "Python": "#3572A5", "Rust": "#dea584", "QML": "#44a51c", "Shell": "#89e051",
    "Java": "#b07219", "C": "#555555", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Go": "#00ADD8", "HTML": "#e34c26", "CSS": "#563d7c", "C++": "#f34b7d",
    "Lua": "#000080", "Nix": "#7e7eff", "Makefile": "#427819",
}


def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-cards",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read(MAX_BYTES).decode("utf-8"))


def clip(text, n):
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "..."


def wrap(text, width, lines):
    words, out, cur = (text or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: width - 3].rstrip(" .,;:") + "..."
    return out


def svg(width, height, body, title):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
        'role="img" aria-label="%s">\n'
        '<rect x="0.5" y="0.5" width="%d" height="%d" rx="6" fill="%s" stroke="%s"/>\n%s</svg>\n'
        % (width, height, width, height, escape(title, {'"': "&quot;"}),
           width - 1, height - 1, BG, BORDER, body)
    )


def repo_card(repo):
    lines = wrap(repo.get("description") or "No description", 52, 2)
    body = [
        '<text x="20" y="30" font-family="%s" font-size="15" font-weight="600" fill="%s">%s</text>'
        % (FONT, ACCENT, escape(clip(repo["name"], 40)))
    ]
    for i, line in enumerate(lines):
        body.append('<text x="20" y="%d" font-family="%s" font-size="12" fill="%s">%s</text>'
                    % (54 + i * 16, FONT, TEXT, escape(line)))
    lang = repo.get("language")
    x = 20
    if lang:
        body.append('<circle cx="26" cy="100" r="5" fill="%s"/>' % LANG_COLORS.get(lang, "#8b949e"))
        body.append('<text x="36" y="104" font-family="%s" font-size="12" fill="%s">%s</text>'
                    % (FONT, MUTED, escape(lang)))
        x = 36 + 8 * len(lang) + 16
    body.append('<text x="%d" y="104" font-family="%s" font-size="12" fill="%s">&#9733; %d</text>'
                % (x, FONT, MUTED, repo.get("stargazers_count", 0)))
    body.append('<text x="%d" y="104" font-family="%s" font-size="12" fill="%s">&#9095; %d</text>'
                % (x + 56, FONT, MUTED, repo.get("forks_count", 0)))
    return svg(400, 120, "\n".join(body), repo["name"])


def stats_card(repos, user):
    own = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in own)
    rows = [
        ("Public repos", user.get("public_repos", len(own))),
        ("Stars earned", stars),
        ("Followers", user.get("followers", 0)),
        ("Forks received", sum(r.get("forks_count", 0) for r in own)),
    ]
    body = ['<text x="20" y="30" font-family="%s" font-size="15" font-weight="600" fill="%s">%s</text>'
            % (FONT, ACCENT, escape(USER + "'s GitHub Stats"))]
    for i, (label, value) in enumerate(rows):
        y = 60 + i * 24
        body.append('<text x="20" y="%d" font-family="%s" font-size="13" fill="%s">%s</text>'
                    % (y, FONT, TEXT, escape(label)))
        body.append('<text x="240" y="%d" font-family="%s" font-size="13" font-weight="600" '
                    'text-anchor="end" fill="%s">%d</text>' % (y, FONT, ACCENT, value))
    return svg(260, 165, "\n".join(body), "GitHub stats")


def langs_card(repos):
    totals = {}
    for r in repos:
        if r.get("fork"):
            continue
        try:
            data = api("/repos/%s/%s/languages" % (USER, r["name"]))
        except OSError:
            continue
        for lang, n in data.items():
            totals[lang] = totals.get(lang, 0) + int(n)
    total = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    body = ['<text x="20" y="30" font-family="%s" font-size="15" font-weight="600" fill="%s">Top Languages</text>'
            % (FONT, ACCENT)]
    # Stacked bar, then a two-column legend.
    x = 20.0
    bar_w = 260.0
    body.append('<clipPath id="bar"><rect x="20" y="42" width="%d" height="8" rx="4"/></clipPath>' % bar_w)
    body.append('<g clip-path="url(#bar)">')
    for lang, n in top:
        w = bar_w * n / total
        body.append('<rect x="%.2f" y="42" width="%.2f" height="8" fill="%s"/>'
                    % (x, w, LANG_COLORS.get(lang, "#8b949e")))
        x += w
    body.append("</g>")
    for i, (lang, n) in enumerate(top):
        col, row = i % 2, i // 2
        cx, cy = 20 + col * 140, 74 + row * 22
        body.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (cx + 5, cy - 4, LANG_COLORS.get(lang, "#8b949e")))
        body.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s">%s %.1f%%</text>'
                    % (cx + 16, cy, FONT, TEXT, escape(clip(lang, 14)), 100.0 * n / total))
    return svg(300, 150, "\n".join(body), "Top languages")


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)


def main():
    repos = api("/users/%s/repos?per_page=100&type=owner" % USER)
    user = api("/users/" + USER)
    by_name = {r["name"]: r for r in repos}
    missing = [n for n in PINNED if n not in by_name]
    if missing:
        print("warning: pinned repos not found: " + ", ".join(missing), file=sys.stderr)
    for name in PINNED:
        if name in by_name:
            write(name + ".svg", repo_card(by_name[name]))
    write("stats.svg", stats_card(repos, user))
    write("languages.svg", langs_card(repos))
    print("wrote cards to", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
