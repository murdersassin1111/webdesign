#!/usr/bin/env python3
"""
Auto web design generator — runs every 5 hours via OpenClaw cron.
Generates 3 unique website variations, pushes to GitHub, notifies Telegram.
"""

import os, json, random, subprocess, datetime, textwrap, anthropic

WORKSPACE = "/root/webdesign"
STATE_FILE = f"{WORKSPACE}/state.json"
GH_TOKEN   = subprocess.check_output(["gh", "auth", "token"]).decode().strip()
REPO_URL   = f"https://murdersassin1111:{GH_TOKEN}@github.com/murdersassin1111/webdesign.git"

# ── Industry themes ──────────────────────────────────────────────────────────
THEMES = [
    {"industry": "Cybersecurity SaaS",       "palette": "dark navy + electric cyan",   "style": "dark, techy, minimal"},
    {"industry": "Sustainable Architecture", "palette": "earthy green + warm cream",    "style": "organic, clean, editorial"},
    {"industry": "AI Healthcare Platform",   "palette": "clean white + deep violet",    "style": "clinical, trustworthy, modern"},
    {"industry": "Craft Coffee Roastery",    "palette": "warm brown + cream + orange",  "style": "artisan, warm, tactile"},
    {"industry": "Electric Vehicle Startup", "palette": "jet black + neon green",       "style": "bold, futuristic, fast"},
    {"industry": "Legal Tech Platform",      "palette": "deep charcoal + gold accent",  "style": "authoritative, clean, premium"},
    {"industry": "Fintech Banking App",      "palette": "midnight blue + lime green",   "style": "trustworthy, fresh, modern"},
    {"industry": "Remote Work Tools SaaS",   "palette": "light grey + coral + white",   "style": "friendly, productive, clean"},
    {"industry": "Luxury Real Estate",       "palette": "black + champagne gold",       "style": "opulent, minimal, sophisticated"},
    {"industry": "EdTech Learning Platform", "palette": "purple + yellow + white",      "style": "energetic, approachable, bright"},
    {"industry": "Fitness & Wellness App",   "palette": "black + neon orange",          "style": "high-energy, bold, athletic"},
    {"industry": "B2B Logistics Platform",   "palette": "slate blue + white + amber",   "style": "reliable, clear, professional"},
    {"industry": "Food Delivery App",        "palette": "red + white + dark grey",      "style": "appetising, fast, friendly"},
    {"industry": "Creative Agency",          "palette": "white + bold black + one pop colour", "style": "editorial, typographic, bold"},
    {"industry": "Web3 / Crypto Exchange",   "palette": "dark + purple gradient + gold","style": "futuristic, premium, bold"},
    {"industry": "Medical Device Company",   "palette": "white + blue + silver",        "style": "clinical, precise, trustworthy"},
    {"industry": "Agricultural Technology",  "palette": "dark green + yellow + white",  "style": "grounded, optimistic, modern"},
    {"industry": "Gaming Studio",            "palette": "black + neon purple + red",    "style": "immersive, dark, energetic"},
    {"industry": "Interior Design Studio",   "palette": "warm white + terracotta + brass","style": "elegant, tactile, editorial"},
    {"industry": "Cybersport / Esports Team","palette": "black + electric blue + white","style": "aggressive, dynamic, bold"},
]

LAYOUTS = [
    "centered hero with large bold headline, features in 3-column grid, alternating text/image sections",
    "full-bleed hero image with text overlay, asymmetric 2-column sections, large stats row",
    "split hero (text left, visual right), icon + text feature rows, testimonial cards",
    "minimal typographic hero (no images, just text and spacing), feature grid, pricing table",
    "video/animated hero placeholder with gradient overlay, horizontal scrolling features, CTA banner",
]

# ── State tracking ───────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"run": 0, "used_themes": [], "generated": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── HTML generator via Claude API ────────────────────────────────────────────
def generate_website(theme, layout, filename):
    client = anthropic.Anthropic()
    prompt = f"""You are an expert web designer. Generate a complete, production-ready single-page website HTML file.

Industry: {theme['industry']}
Color palette: {theme['palette']}
Design style: {theme['style']}
Layout pattern: {layout}

Requirements:
- Single self-contained HTML file, Tailwind CSS via CDN only
- Inter font from Google Fonts
- Fully responsive, mobile-first
- Sections: sticky nav, hero, features/services (3-4 items), social proof or stats, CTA section, footer
- Invent a compelling fictional company name and tagline that fits the industry
- Write real, convincing copy — not placeholder text
- Realistic pricing, features, testimonials where appropriate
- Apply Refactoring UI principles: proper spacing scale, type hierarchy, color system
- Use emoji only for icons — NO external icon libraries
- Dark/light theme as fits the palette
- Hover effects on cards and buttons
- Smooth scroll between sections
- Output ONLY the complete HTML — no explanation, no markdown fences

The result must look like a real company's production website, not a tutorial or demo."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    html = message.content[0].text.strip()
    # Strip markdown fences if model added them
    if html.startswith("```"):
        html = "\n".join(html.split("\n")[1:])
    if html.endswith("```"):
        html = "\n".join(html.split("\n")[:-1])

    filepath = f"{WORKSPACE}/variations/{filename}"
    os.makedirs(f"{WORKSPACE}/variations", exist_ok=True)
    with open(filepath, "w") as f:
        f.write(html)

    return filepath

# ── Git push ─────────────────────────────────────────────────────────────────
def git_push(message):
    os.chdir(WORKSPACE)
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", message,
                    "--author", "OpenClaw Bot <bot@openclaw.ai>"], check=True)
    subprocess.run(["git", "remote", "set-url", "origin", REPO_URL], check=True)
    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "remote", "set-url", "origin",
                    "https://github.com/murdersassin1111/webdesign.git"], check=True)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(f"{WORKSPACE}/variations", exist_ok=True)
    state = load_state()
    state["run"] += 1
    run_num = state["run"]
    now     = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    ts      = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M")

    # Pick 3 unused themes; reset pool if exhausted
    used = set(state["used_themes"])
    available = [t for t in THEMES if t["industry"] not in used]
    if len(available) < 3:
        state["used_themes"] = []
        available = THEMES[:]
    random.shuffle(available)
    chosen = available[:3]

    print(f"\n🎨 Run #{run_num} — {now}")
    print(f"Generating: {', '.join(t['industry'] for t in chosen)}\n")

    generated = []
    for i, theme in enumerate(chosen, 1):
        layout   = random.choice(LAYOUTS)
        filename = f"run{run_num:03d}-{i}-{theme['industry'].lower().replace(' ', '-').replace('/', '')[:30]}-{ts}.html"
        print(f"  [{i}/3] {theme['industry']}...")
        try:
            filepath = generate_website(theme, layout, filename)
            generated.append({
                "file": filename,
                "industry": theme["industry"],
                "palette": theme["palette"],
                "run": run_num,
                "ts": now,
            })
            print(f"       ✅ {filename}")
        except Exception as e:
            print(f"       ❌ FAILED: {e}")

    # Update state
    state["used_themes"].extend(t["industry"] for t in chosen)
    state["generated"].extend(generated)
    save_state(state)

    # Update index
    write_index(state)

    # Push
    git_push(f"auto: run #{run_num} — {', '.join(t['industry'] for t in chosen[:3])}")

    # Report
    base_url = "https://murdersassin1111.github.io/webdesign/variations"
    lines = [f"✅ *Web Design Run #{run_num}* — {now}", ""]
    for g in generated:
        lines.append(f"🌐 *{g['industry']}*")
        lines.append(f"   {g['palette']}")
        url = f"{base_url}/{g['file']}"
        lines.append(f"   {url}")
        lines.append("")
    print("\n".join(lines))
    return "\n".join(lines)

def write_index(state):
    """Write an HTML index page listing all generated sites."""
    rows = ""
    for g in reversed(state["generated"][-30:]):  # last 30
        url = f"variations/{g['file']}"
        rows += f"""
        <tr>
          <td class="py-2 pr-6 text-sm text-slate-500">{g['ts']}</td>
          <td class="py-2 pr-6 font-medium">{g['industry']}</td>
          <td class="py-2 pr-6 text-sm text-slate-500">{g['palette']}</td>
          <td class="py-2"><a href="{url}" class="text-blue-600 hover:underline text-sm" target="_blank">View →</a></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Web Design Variations — Auto-Generated</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>body{{font-family:'Inter',sans-serif}}</style>
</head><body class="bg-slate-50 text-slate-900 p-8">
<div class="max-w-5xl mx-auto">
  <h1 class="text-3xl font-bold mb-2">🎨 Web Design Variations</h1>
  <p class="text-slate-500 mb-8">Auto-generated every 5 hours · Run #{state['run']} · {len(state['generated'])} total sites</p>
  <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
    <table class="w-full px-6">
      <thead class="bg-slate-50 border-b border-slate-200">
        <tr>
          <th class="py-3 px-6 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Generated</th>
          <th class="py-3 px-6 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Industry</th>
          <th class="py-3 px-6 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Palette</th>
          <th class="py-3 px-6 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Link</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100 px-6">{rows}
      </tbody>
    </table>
  </div>
  <p class="text-slate-400 text-xs mt-6">GitHub Pages auto-deploy · <a href="https://github.com/murdersassin1111/webdesign" class="hover:underline">View source</a></p>
</div>
</body></html>"""
    with open(f"{WORKSPACE}/variations/index.html", "w") as f:
        f.write(html)

if __name__ == "__main__":
    result = main()
    print("\nDone.")
