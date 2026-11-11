"""Builds wix-guide/index.html: a step-by-step guide for rebuilding this
site in Wix. All page text is read straight from the site's HTML files, so
the guide always matches the site. Re-run after changing the site:

    python3 wix-guide/build.py
"""
import html
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "wix-guide", "index.html")
PHONE = "(727) 692-7112"
EMAIL = "armosealinsulation@gmail.com"

# Site image -> file in wix-guide/upload
IMAGES = {
    "logo-small.png": "01-armoseal-logo.jpg",
    "logo-panel.jpg": "01-armoseal-logo.jpg",
    "logo.webp": "01-armoseal-logo.jpg",
    "founder-family.jpg": "02-founder-antonio-johnson-jr-family.jpg",
    "spray-foam-sunroom.jpg": "03-spray-foam-sunroom.jpg",
    "fiberglass-install.jpg": "04-fiberglass-install.jpg",
    "home-inspection-attic.jpg": "05-home-inspection-attic.jpg",
    "work-room-spray-foam.jpg": "06-work-small-room.jpg",
    "work-garage-spray-foam.jpg": "07-work-metal-garage.jpg",
    "work-ceiling-spray-foam.jpg": "08-work-roof-rafters.jpg",
}

PAGE_NAMES = {
    "index.html": "Home", "services.html": "Services", "about.html": "About Us",
    "blog.html": "Blog", "contact.html": "Contact",
}
SECTION_NAMES = {"spray-foam": "Spray Foam section", "fiberglass": "Fiberglass section",
                 "inspection": "Home Inspection section"}


def link_target(href):
    """Explain in plain words where a link should point in Wix."""
    href = href.split("?v=")[0]
    if href.startswith("tel:"):
        return f"Phone number {PHONE}  (Wix: Link → Phone)"
    if href.startswith("mailto:"):
        return f"Email {EMAIL}  (Wix: Link → Email)"
    path = href.split("/")[-1]
    page, _, rest = path.partition("#")
    page, _, query = page.partition("?")
    if page.startswith("blog") or href.startswith("blog/"):
        if page == "blog.html":
            return "Blog page"
        return "That blog post (Wix: Link → Page → the post)"
    name = PAGE_NAMES.get(page, page)
    if rest:
        return f"{name} page → {SECTION_NAMES.get(rest, rest)}  (Wix: Link → Anchor)"
    if query.startswith("service="):
        svc = html.unescape(query.split("=", 1)[1].replace("%20", " "))
        return f"{name} page  (the site preselects “{svc}” in the form; in Wix just link to the page)"
    return f"{name} page"


class Extract(HTMLParser):
    """Turns a chunk of page HTML into an ordered list of guide items."""

    CAPTURE = {"h1", "h2", "h3", "p", "li", "figcaption", "label", "option", "th", "td", "button"}

    def __init__(self, icons):
        super().__init__(convert_charrefs=True)
        self.icons = icons
        self.items = []
        self.cap = None          # (tag, attrs, [text])
        self.link = None         # [href, classes, [text]] for button-like links
        self.row = None
        self.skip = 0            # depth inside skipped elements (.related)
        self.stack = []

    def classes(self, attrs):
        return dict(attrs).get("class", "").split()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = self.classes(attrs)
        if tag not in ("img", "input", "br", "meta", "link"):
            self.stack.append((tag, "related" in cls or "back-link" in cls))
            if "related" in cls or "back-link" in cls:
                self.skip += 1
        if self.skip:
            return
        if tag == "img":
            if "icon-ref" in cls:
                self.items.append(("icon", self.icons[int(a["data-i"])]))
            elif "brand-logo" not in cls:
                src = a.get("src", "").split("/")[-1].split("?")[0]
                self.items.append(("image", IMAGES.get(src, src), a.get("alt", "")))
            return
        if tag in ("input", "textarea", "select"):
            if self.items and self.items[-1][0] == "field":
                kind = {"tel": "phone number", "email": "email", "text": "short text"}.get(a.get("type", "text"), a.get("type"))
                if tag == "textarea":
                    kind = "long text (paragraph)"
                if tag == "select":
                    kind = "dropdown"
                req = "required" if "required" in a else "optional"
                self.items[-1] = ("field", self.items[-1][1], f"{kind}, {req}")
            if tag == "input":
                return
        if tag == "tr":
            self.row = []
            return
        if tag == "span" and ({"eyebrow", "post-tag"} & set(cls)) and not self.cap:
            self.cap = ("eyebrow", cls, [])
            return
        if tag == "div" and "step-num" in cls and not self.cap:
            self.cap = ("stepnum", cls, [])
            return
        if tag == "a" and not self.cap and ({"btn", "big-phone", "read-more"} & set(cls) or a.get("href", "").startswith("tel:")):
            self.link = [a.get("href", ""), cls, []]
            return
        if tag == "a" and "post-card" in cls:
            self.items.append(("cardlink", a.get("href", "")))
            return
        if tag in self.CAPTURE and not self.cap:
            self.cap = (tag, cls, [])

    def handle_endtag(self, tag):
        if tag not in ("img", "input", "br", "meta", "link") and self.stack:
            t, skipping = self.stack.pop()
            if skipping:
                self.skip -= 1
                return
        if self.skip:
            return
        if tag == "tr" and self.row is not None:
            self.items.append(("row", self.row))
            self.row = None
            return
        if tag == "a" and self.link:
            href, cls, txt = self.link
            text = clean("".join(txt))
            if "read-more" in cls:
                pass
            elif text:
                self.items.append(("button", text, link_target(href), "big-phone" in cls))
            self.link = None
            return
        if self.cap and (tag == self.cap[0] or (self.cap[0] in ("eyebrow",) and tag == "span") or (self.cap[0] == "stepnum" and tag == "div")):
            kind, cls, txt = self.cap
            text = clean("".join(txt))
            self.cap = None
            if not text:
                return
            if kind in ("th", "td") and self.row is not None:
                self.row.append(text)
            elif kind == "label":
                self.items.append(("field", text, ""))
            elif kind == "option":
                self.items.append(("option", text))
            else:
                self.items.append(("formbutton" if kind == "button" else kind, text, cls))

    def handle_data(self, data):
        if self.skip:
            return
        if self.link:
            self.link[2].append(data)
        if self.cap:
            self.cap[2].append(data)


def clean(t):
    return re.sub(r"\s+", " ", t).strip()


def split_blocks(page_html):
    """Return [(classes, inner_html)] for the top bar, each top-level section of <main>, and the footer."""
    icons = []

    def stash(m):
        icons.append(m.group(1))
        return f'<img class="icon-ref" data-i="{len(icons) - 1}">'

    page_html = re.sub(r'<div class="icon-badge">(<svg.*?</svg>)</div>', stash, page_html, flags=re.S)
    main = re.search(r"<main[^>]*>(.*)</main>", page_html, re.S).group(1)
    blocks = []
    for m in re.finditer(r'<(section|article)\b([^>]*)>(.*?)</\1>\s*(?=<section|<article|<!--|$)', main, re.S):
        cls = re.search(r'class="([^"]*)"', m.group(2))
        blocks.append((cls.group(1) if cls else "", m.group(3)))
    return blocks, icons


def describe(cls, inner):
    """Plain-words layout and background for a section, from its CSS classes."""
    c = cls.split()
    if "hero" in c:
        return "Top banner", "Cream background that fades slightly darker at the bottom (#FBF6EE → #F3E8D6). Two columns: text and buttons on the left, a white card with an orange top edge on the right."
    if "page-hero" in c:
        return "Page banner", "Light sand background (#F3E8D6 fading to #FBF6EE). Text on the left, nothing on the right."
    if "cta-band" in c:
        return "Call-to-action strip", "Full-width royal-blue strip (#0B3A6F). White text on the left, the big phone number in white on the right."
    if "article" in c:
        return "Blog post", "One narrow column of text, about 820px wide, centered."
    bg = "White background (#FFFFFF)." if "section-alt" in c else "Cream background (#FBF6EE)."
    if "gallery" in inner:
        lay = "3 photos in a row, each with a short caption underneath."
    elif 'class="service"' in inner:
        lay = "Each service is a row: photo on one side, text on the other. Switch sides on every other row."
    elif "contact-grid" in inner:
        lay = "Two columns: contact details on the left, the quote form in a white box on the right."
    elif "split" in inner:
        lay = "Two columns: picture on the left, text on the right."
    elif "grid-4" in inner:
        lay = "4 cards in a row (2 per row on tablets, 1 per row on phones)."
    elif "steps" in inner:
        lay = "3 steps side by side, each with a navy number circle on top."
    elif "post-grid" in inner:
        lay = "3 article cards per row. In Wix, the Blog app makes this list for you."
    elif "grid-3" in inner:
        lay = "3 cards in a row, each with a photo on top and a button at the bottom."
    elif "grid-2" in inner:
        lay = "2 cards side by side."
    else:
        lay = "One column of text."
    return "Section", f"{bg} {lay}"


LABELS = {
    "h1": "Page title (largest heading)",
    "h2": "Section heading",
    "h3": "Smaller heading",
    "eyebrow": "Small label above heading (orange, ALL CAPS)",
    "p": "Paragraph",
    "figcaption": "Photo caption",
    "stepnum": "Number in navy circle",
    "formbutton": "Form’s send button (orange, full width)",
}
P_LABELS = {
    "lead": "Intro paragraph (a bit larger than normal text)",
    "hero-note": "Small note under the buttons",
    "quote-block": "Paragraph with a thick orange line on its left side",
    "founder-name": "Name line (orange, bold, heading font)",
    "article-byline": "Byline (small, gray)",
    "article-note": "Note at the end of the article (small, gray)",
}


def esc(t):
    return html.escape(t, quote=True)


def copy_row(label, text, extra=""):
    return (f'<div class="item"><div class="item-label">{esc(label)}</div>'
            f'<div class="item-body"><div class="item-text">{esc(text)}</div>{extra}</div>'
            f'<button class="copy" data-copy="{esc(text)}" type="button">Copy</button></div>')


# Lines that only make sense on the hand-built site, adjusted for Wix
WIX_TEXT = {
    "This opens your email app with your details filled in. Rather talk? Call (727) 692-7112.":
        "Rather talk? Call (727) 692-7112.",
}


def render_items(items):
    items = [(x[0], WIX_TEXT.get(x[1], x[1])) + tuple(x[2:]) if len(x) > 1 and isinstance(x[1], str) else x for x in items]
    out = []
    i = 0
    while i < len(items):
        it = items[i]
        kind = it[0]
        if kind == "li":
            lines = []
            while i < len(items) and items[i][0] == "li":
                lines.append(items[i][1])
                i += 1
            text = "\n".join(lines)
            out.append(f'<div class="item"><div class="item-label">Bullet list</div><div class="item-body"><ul>{"".join("<li>" + esc(x) + "</li>" for x in lines)}</ul></div><button class="copy" data-copy="{esc(text)}" type="button">Copy</button></div>')
            continue
        if kind == "row":
            rows = []
            while i < len(items) and items[i][0] == "row":
                rows.append(items[i][1])
                i += 1
            head, body = rows[0], rows[1:]
            if len(head) < len(body[0]):
                head = [""] + head
            t = "<table>" + "<tr>" + "".join(f"<th>{esc(x)}</th>" for x in head) + "</tr>"
            t += "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in r) + "</tr>" for r in body) + "</table>"
            text = "\n".join(" | ".join(r) for r in [head] + body)
            out.append(f'<div class="item"><div class="item-label">Comparison table<br><small>Wix: Add → Table, or use the blog editor’s Table button</small></div><div class="item-body">{t}</div><button class="copy" data-copy="{esc(text)}" type="button">Copy</button></div>')
            continue
        if kind == "field":
            fields = []
            while i < len(items) and items[i][0] in ("field", "option"):
                fields.append(items[i])
                i += 1
            rows = []
            for f in fields:
                if f[0] == "field":
                    rows.append([f[1], f[2], []])
                else:
                    rows[-1][2].append(f[1])
            li = "".join(f'<li><b>{esc(n)}</b> — {esc(k)}{(": " + esc(", ".join(o))) if o else ""}</li>' for n, k, o in rows)
            out.append(f'<div class="item"><div class="item-label">Quote form fields<br><small>Wix: Add → Contact &amp; Forms, then edit the fields to match</small></div><div class="item-body"><ol>{li}</ol></div><span></span></div>')
            continue
        if kind == "option":
            i += 1
            continue
        if kind == "image":
            _, file, alt = it
            out.append(f'<div class="item"><div class="item-label">Photo<br><small>Upload: <b>{esc(file)}</b></small></div><div class="item-body"><img class="thumb" src="upload/{esc(file)}" alt=""><div class="alt">Alt text (Wix: image Settings → “What’s in the image?”):<br>{esc(alt)}</div></div><button class="copy" data-copy="{esc(alt)}" type="button">Copy alt text</button></div>')
        elif kind == "icon":
            out.append(f'<div class="item"><div class="item-label">Small icon<br><small>Wix: Add → Decorative → Icons. Pick one like this, inside a light-orange rounded square (#FFE6CC), orange icon (#B04C00).</small></div><div class="item-body"><span class="icon">{it[1]}</span></div><span></span></div>')
        elif kind == "button":
            _, text, target, big = it
            label = "Big phone number (white, large heading font) — make it a link" if big else "Button"
            out.append(copy_row(label, text, f'<div class="link">Links to: {esc(target)}</div>'))
        elif kind == "cardlink":
            pass
        else:
            text, cls = it[1], it[2]
            label = LABELS.get(kind, kind)
            if kind == "p":
                for c in cls:
                    label = P_LABELS.get(c, label)
            if "quick-answer" in cls:
                label = "Box heading"
            out.append(copy_row(label, text))
        i += 1
    return "".join(out)


def page_meta(page_html):
    title = html.unescape(re.search(r"<title>(.*?)</title>", page_html, re.S).group(1))
    desc = re.search(r'<meta name="description" content="([^"]*)"', page_html)
    return clean(title), html.unescape(desc.group(1)) if desc else ""


def seo_block(page_html):
    title, desc = page_meta(page_html)
    return ('<details class="seo"><summary>SEO settings for this page (helps Google)</summary>'
            '<p class="hint">Wix: Pages menu → this page → ⋯ → SEO basics.</p>'
            + copy_row("Title tag", title) + copy_row("Meta description", desc) + "</details>")


def render_page(fname, heading, intro):
    src = open(os.path.join(ROOT, fname), encoding="utf-8").read()
    blocks, icons = split_blocks(src)
    parts = [f'<p class="lead">{intro}</p>', seo_block(src)]
    for n, (cls, inner) in enumerate(blocks, 1):
        kind, layout = describe(cls, inner)
        p = Extract(icons)
        p.feed(inner)
        items = render_items(p.items)
        if not items:
            continue
        first = next((x[1] for x in p.items if x[0] in ("h1", "h2")), "")
        name = f"{kind}: {first}" if first else kind
        parts.append(f'<div class="block"><div class="block-head"><span class="num">{n}</span><div><h4>{esc(name)}</h4><p class="layout">{esc(layout)}</p></div></div>{items}</div>')
    return "".join(parts)


def render_blog_posts():
    idx = open(os.path.join(ROOT, "blog.html"), encoding="utf-8").read()
    cards = re.findall(r'<a class="card post-card" href="blog/([^"]+)">\s*<span class="post-tag">(.*?)</span>\s*<h2>(.*?)</h2>\s*<p>(.*?)</p>', idx, re.S)
    out = []
    for n, (file, tag, title, excerpt) in enumerate(cards, 1):
        src = open(os.path.join(ROOT, "blog", file), encoding="utf-8").read()
        blocks, icons = split_blocks(src)
        art = next(inner for cls, inner in blocks if "article" in cls.split())
        p = Extract(icons)
        p.feed(art)
        items = [x for x in p.items if not (x[0] in ("h1", "eyebrow") or (x[0] == "p" and "article-byline" in x[2]))]
        body = render_items(items)
        title, tag, excerpt = html.unescape(title), html.unescape(tag), html.unescape(excerpt)
        _, desc = page_meta(src)
        out.append(
            f'<details class="post"><summary><span class="num">{n}</span> {esc(title)}</summary>'
            + copy_row("Post title", title)
            + copy_row("Category (Wix Blog: Categories)", tag)
            + copy_row("Excerpt (Wix Blog: post Settings → Excerpt)", excerpt)
            + copy_row("SEO description (post Settings → SEO)", desc)
            + '<p class="hint">Post body, top to bottom. “The short answer” sits in a light-orange box at the top. In the Wix blog editor you can use a Quote or a highlighted paragraph for it.</p>'
            + body + "</details>")
    return "".join(out)


def render_header_footer():
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    top = clean(re.sub(r"<[^>]+>", " ", re.search(r'<div class="topbar">(.*?)</div>\s*</div>', src, re.S).group(1)))
    nav_html = re.search(r'<nav class="nav".*?</nav>', src, re.S).group(0)
    nav = [clean(re.sub(r"<[^>]+>", "", x)) for x in re.findall(r"<a\b[^>]*>(.*?)</a>", nav_html, re.S)]
    footer = re.search(r'<footer class="site-footer">(.*?)</footer>', src, re.S).group(1)
    cols = re.findall(r"<div>\s*(?:<a class=\"brand\".*?</a>)?(.*?)</div>", re.search(r'<div class="footer-grid">(.*?)</div>\s*<div class="footer-bottom">', footer, re.S).group(1), re.S)
    bottom = clean(re.sub(r"<[^>]+>", "", re.search(r'<div class="footer-bottom">(.*?)</div>', footer, re.S).group(1)))
    left, rest = top.split("Call us:")
    h = []
    h.append('<div class="block"><div class="block-head"><span class="num">1</span><div><h4>Top bar</h4><p class="layout">Thin full-width strip, dark navy (#061A33), white text. Left: service area. Right: phone number. On phones, show only the phone number, centered.</p></div></div>')
    h.append(copy_row("Left text", clean(left)))
    h.append(copy_row("Right text (make the number a phone link)", f"Call us: {PHONE}", f'<div class="link">Links to: Phone number {PHONE}  (Wix: Link → Phone)</div>'))
    h.append("</div>")
    h.append('<div class="block"><div class="block-head"><span class="num">2</span><div><h4>Header: logo and menu</h4><p class="layout">White background. The logo is centered at the top, with “Armoseal” (heading font, navy) and “INSULATION” (small, orange, all caps) to its right. The menu is centered underneath it. On phones: logo in the middle, Wix’s mobile menu button on the right.</p></div></div>')
    h.append(f'<div class="item"><div class="item-label">Logo<br><small>Upload: <b>01-armoseal-logo.jpg</b>. About 84px tall. Link it to the Home page.</small></div><div class="item-body"><img class="thumb small" src="upload/01-armoseal-logo.jpg" alt=""></div><span></span></div>')
    h.append(copy_row("Name next to logo (line 1)", "Armoseal"))
    h.append(copy_row("Name next to logo (line 2, small orange caps)", "INSULATION"))
    h.append(copy_row("Menu items, in this order (Wix: Menus → Manage Menu)", "\n".join(nav[:-1])))
    h.append(copy_row("Orange button at the end of the menu", nav[-1], f'<div class="link">Links to: Phone number {PHONE}  (Wix: Link → Phone)</div>'))
    h.append("</div>")
    h.append('<div class="block"><div class="block-head"><span class="num">3</span><div><h4>Footer</h4><p class="layout">Dark navy (#061A33), light text. Three columns: logo and short description; Contact; Pages. A thin line, then the copyright underneath.</p></div></div>')
    h.append(f'<div class="item"><div class="item-label">Logo<br><small>Upload: <b>01-armoseal-logo.jpg</b> on a small white rounded box, with “Armoseal / INSULATION” next to it in white</small></div><div class="item-body"><img class="thumb small" src="upload/01-armoseal-logo.jpg" alt=""></div><span></span></div>')
    names = ["Column 1: description", "Column 2: Contact", "Column 3: Pages"]
    for name, col in zip(names, cols):
        parts = [clean(html.unescape(re.sub(r"<[^>]+>", " ", x))) for x in re.split(r"</li>|</p>|<br>|</h2>", col)]
        parts = [x for x in parts if x]
        h.append(copy_row(name, "\n".join(parts)))
    h.append(f'<p class="hint">In the Contact column, link the phone number to Phone and the email to Email. In the Pages column, link each word to its page.</p>')
    h.append(copy_row("Copyright line", bottom.replace("2026", "2026")))
    h.append("</div>")
    return "".join(h)


COLORS = [
    ("Dark navy", "#061A33", "Top bar, footer, headings, button text"),
    ("Royal blue", "#0B3A6F", "Blue strips, number circles, outline buttons"),
    ("Logo orange", "#F57C00", "Main buttons (with dark navy text), orange lines and borders"),
    ("Dark orange", "#B04C00", "Small orange labels and links on light backgrounds"),
    ("Light orange", "#FFE6CC", "Icon squares, highlighted menu item"),
    ("Cream", "#FBF6EE", "Main page background"),
    ("Sand", "#F3E8D6", "Top-of-page banners"),
    ("White", "#FFFFFF", "Cards and every other section’s background"),
    ("Text navy", "#14213A", "Main body text"),
    ("Soft text", "#3A4A60", "Secondary text (still easy to read)"),
]

UPLOADS = [
    ("01-armoseal-logo.jpg", "Header, footer, and the Home page “Who we are” section"),
    ("02-founder-antonio-johnson-jr-family.jpg", "About Us page, founder section"),
    ("03-spray-foam-sunroom.jpg", "Spray Foam card (Home) and Spray Foam section (Services)"),
    ("04-fiberglass-install.jpg", "Fiberglass card (Home) and Fiberglass section (Services)"),
    ("05-home-inspection-attic.jpg", "Home Inspection card (Home) and section (Services)"),
    ("06-work-small-room.jpg", "“Examples of our work” (Home and Services)"),
    ("07-work-metal-garage.jpg", "“Examples of our work” (Home and Services)"),
    ("08-work-roof-rafters.jpg", "“Examples of our work” (Home and Services)"),
]


def build():
    color_rows = "".join(
        f'<div class="swatch"><span class="chip" style="background:{c}"></span><div><b>{n}</b> <code>{c}</code><br><small>{u}</small></div><button class="copy" data-copy="{c}" type="button">Copy</button></div>'
        for n, c, u in COLORS)
    upload_rows = "".join(
        f'<div class="upload"><img src="upload/{f}" alt=""><div><b>{f}</b><br><small>{u}</small></div></div>' for f, u in UPLOADS)

    pages = [
        ("home", "Home page", "index.html", "Build these sections from top to bottom. The header and footer from Step 4 appear above and below them automatically."),
        ("services", "Services page", "services.html", "Add a Wix Anchor at the start of each service row, named <b>spray-foam</b>, <b>fiberglass</b> and <b>inspection</b>, so the “Learn more” buttons on the Home page can jump straight to them."),
        ("about", "About Us page", "about.html", "This page introduces Antonio Johnson Jr. and the company’s mission and values."),
        ("blog", "Blog page", "blog.html", "Use the <b>Wix Blog app</b> (Add Apps → Wix Blog). It creates the blog list page for you, so you only need the top banner below. Then add the 7 posts in Step 10."),
        ("contact", "Contact page", "contact.html", "Use a <b>Wix Form</b> for the quote request. Requests then go to your Wix Inbox and email, which is better than the current site, where the form opens the visitor’s email app."),
    ]
    page_html = "".join(
        f'<section class="step" id="{pid}"><label class="done"><input type="checkbox" data-step="{pid}"> Done</label><h2><span class="stepno">Step {5 + i}</span> {title}</h2>{render_page(f, title, intro)}</section>'
        for i, (pid, title, f, intro) in enumerate(pages))
    doc = TEMPLATE
    for key, val in {"colors": color_rows, "uploads": upload_rows, "header": render_header_footer(),
                     "pages": page_html, "posts": render_blog_posts(), "phone": PHONE, "email": EMAIL}.items():
        doc = doc.replace("%%" + key + "%%", val)
    open(OUT, "w", encoding="utf-8").write(doc)
    print("wrote", OUT)


TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html"), encoding="utf-8").read()

if __name__ == "__main__":
    build()
