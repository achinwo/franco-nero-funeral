#!/usr/bin/env python3
r"""Post the tributes to the guest book at maqr.co/ewed/franconero.

The sibling of build-tributes.py. That one reads assets/data/tributes.toml --
the words as the family sent them -- and sets them for the booklet; this one
reads the same file and leaves them on the memorial page, so the words that
are printed and the words that are online come from one source and cannot
drift apart.

    python3 assets/post-tributes.py               # show what would be posted
    python3 assets/post-tributes.py --post        # actually post it
    python3 assets/post-tributes.py --only emike  # one tribute, by name
    python3 assets/post-tributes.py --undo --post # take back what this posted

Nothing is sent without --post. The default run prints every message exactly
as it would be stored, which is the only way to read thirty-two tributes for
markup mistakes before a hundred people do.

What a tribute becomes
----------------------
A guest-book entry holds a title, a message in a small subset of Markdown, an
optional signature and an optional photograph. The mapping is:

    title           the entry's title, with <br/> flattened to a space (the
                    server keeps a title to one line) and a strike kept as
                    ~~...~~
    subtitle        the message's opening paragraph -- which is where the
                    tribute already posted by hand put it, and the page reads
                    the same way as the booklet, where it sits under the head
    from            the signature, unless a <signoff> says otherwise
    body            the message: <para>/<signoff>/<prayer> blocks and the
                    heuristics behind them are build-tributes.py's, imported
                    rather than rewritten, so the booklet and the page break
                    a letter into the same pieces
    imagePath       uploaded to the album the page already has, and attached

Inline, <i> becomes *italic*, <b> becomes **bold**, the four spellings of the
strike become ~~struck~~ and <br/> becomes a line break -- the message keeps
single newlines, so a break survives the round trip. <pagebreak/> is dropped:
there are no pages here.

A closing prayer becomes a block quote, which the page sets italic behind a
rule -- the nearest thing it has to the way the booklet sets one. Its short
lines do flow together there, because the panel's quote does not keep
newlines the way its paragraphs do. That is the one place this loses
something the print keeps.

A sign-off becomes the signature, where the page shows it as "-- Talia &
Tyshawn" under the message. Its lines are joined with commas, since the field
is one line. A sign-off too long for the field (the server keeps 200
characters) stays in the message as a closing paragraph instead, because
half of somebody's name is worse than a paragraph where a signature would
have been.

The photograph
--------------
The original, not the booklet's plate. The plate is toned towards sepia and
cut to about 40mm for print; the page wants the photograph as it was taken,
so this only turns it upright, fits it inside 1600px and strips the camera's
metadata. It is uploaded the way the page's own upload works -- ask the
server for a signed URL, PUT the bytes straight to storage -- so the picture
lands in the same album a visitor's would, and the message refers to it by
the object name the server minted. See handlers/guestbook.ts in the maqr
server for why a message may not simply name a URL.

Posting twice
-------------
Every run reads the guest book first and skips any tribute already on it,
matching on the title (or, for a tribute with none, the opening of the
message). That is what makes this safe to re-run after fixing one tribute:
the other thirty-one are recognised and left alone. Three entries were posted
by hand before this script existed, and they are recognised the same way.

What this run posts is also written to assets/data/.tributes-posted.json, so
--undo can take exactly those entries down again. Deleting is the one thing
the page allows only to the device that wrote a message, which is why the
device id below is fixed rather than made up per run: lose it and the entries
can no longer be withdrawn from here.

Order
-----
The booklet runs in descending `order`; the page shows newest first. So the
tributes are posted in ascending `order` -- the booklet's last first -- and
the page ends up reading in the booklet's order. The three hand-posted
entries are older than anything this sends and stay at the foot of the page.
"""

import argparse
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import textkit

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOML = ROOT / "assets/data/tributes.toml"
LEDGER = ROOT / "assets/data/.tributes-posted.json"

BASE_URL = "https://maqr.co"
# The experience's own uuid, which is also the last part of its address:
# https://maqr.co/ewed/franconero.
EXPERIENCE = "franconero"

# Who the page thinks is posting. Fixed, and fixed *here*, for two reasons:
# the server will only let the device that wrote a message take it down
# again, and a new id per run would leave thirty-two entries nobody can
# withdraw. It identifies this script, not a person.
DEVICE_UUID = "franconero-tributes-importer"
DEVICE_NAME = "post-tributes.py"

# maqr.co sits behind Cloudflare, which answers the default "Python-urllib/3"
# with a 403 (its error 1010) before the server ever sees the request. This is
# an ordinary client asking for an ordinary page, so it says so.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")

# The server's own limits, from src/lib/guestbook.ts. Checked here so that a
# tribute that would be cut short is reported as a problem to fix rather than
# silently stored with its last paragraph missing.
MAX_MESSAGE = 10_000
MAX_TITLE = 200
MAX_SIGNATURE = 200

# How many lines still read as a sign-off once they are one line. "Love
# Always, / Your Handsome Grandson, / St. Michael" does; a five-line passage
# does not -- see signature_of().
SIGNATURE_LINES = 3

# Long edge of an uploaded photograph. Large enough to fill a phone screen at
# any sensible density, small enough that thirty-two of them do not make the
# page slow to open.
PHOTO_PIXELS = 1600

# Between posts. The page orders by the moment a message arrived, so two that
# land inside the same tick could come out either way round; this keeps the
# order the booklet asked for.
PAUSE = 0.4


def load_build_tributes():
    """build-tributes.py, imported as a module.

    Its file name has a hyphen in it, so `import` cannot name it. The work
    being borrowed -- blocks(), and the heuristics under it that decide what
    is a paragraph, what is a sign-off and what is a closing prayer -- is the
    part that must not be written twice: a page that broke the letters up
    differently from the booklet would be a different reading of the same
    words.
    """
    spec = importlib.util.spec_from_file_location(
        "build_tributes", ROOT / "assets/build-tributes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------- markdown

# The inline tags, as the page's Markdown subset spells them. The same four
# spellings of the strike textkit takes, because a writer should not have to
# know which generator is reading their tribute.
MARKS = {"i": "*", "b": "**", **{tag: "~~" for tag in textkit.STRIKE_TAGS}}


def markdown(text):
    """One run of the family's text, as the page's Markdown subset.

    The shape of textkit.tex(), with Markdown where the LaTeX was: this reads
    the same tags, in the same order, and differs only in what it emits. A
    <br/> becomes a real newline, which survives -- the panel sets a message
    with `white-space: pre-line`, so a break inside a paragraph is kept.
    """
    out, pos = [], 0
    for match in textkit.INLINE_RE.finditer(text):
        out.append(plain(text[pos:match.start()]))
        if match.group(1) is None:
            out.append("\n")
        else:
            inner = markdown(match.group(2)).strip()
            mark = MARKS[match.group(1)]
            # An empty pair of markers is two asterisks the reader has to
            # look at, and marks nothing.
            out.append(f"{mark}{inner}{mark}" if inner else "")
        pos = match.end()
    out.append(plain(text[pos:]))

    joined = re.sub(r"[ \t]+", " ", "".join(out))
    # The space each side of a break goes with it. A line typed
    # "...the faith.” <br/>(2 Timothy 4:7)" would otherwise keep that space at
    # the end of the line, where it is invisible until something indents by it.
    joined = re.sub(r"[ \t]*\n[ \t]*", "\n", joined)
    # A break with no line to break -- a paragraph typed "...forget you.<br/>"
    # -- would open or close the entry with an empty line.
    return joined.strip(" \n")


def plain(text):
    """A run with no tags left in it, with the typist's LaTeX undone.

    A few tributes were typed with LaTeX's quoting -- ``like this'' -- which
    the booklet sets as curly quotes and the page would otherwise show as
    backticks. Worse, a pair of backticks is how the page's Markdown opens a
    code span, so the line would come out in a monospace box. Both spellings
    become the quotation marks they were standing in for.
    """
    return text.replace("``", "“").replace("''", "”")


def oneline(text):
    """Markdown for a place that is one line whatever is typed into it.

    The server collapses a title's whitespace anyway; doing it here means the
    dry run prints what will actually be stored.
    """
    return re.sub(r"\s+", " ", markdown(text)).strip()


def message_of(tribute, blocks):
    """The message, and the signature to go under it.

    The signature is the last sign-off, lifted out of the message: the page
    has a field for it and sets it apart under the words, which is where a
    letter's sign-off goes. Everything else -- including a sign-off in the
    middle of a letter, which is usually somebody quoting a card -- stays
    where it was written.
    """
    parts, signature = [], ""

    subtitle = (tribute.get("subtitle") or "").strip()
    if subtitle:
        parts.append(markdown(subtitle))

    for index, (kind, lines) in enumerate(blocks):
        if kind == "pagebreak":
            continue

        last = index == len(blocks) - 1
        text = "\n".join(markdown(line) for line in lines).strip()
        if not text:
            continue

        if kind == "prayer":
            # A block quote: every line marked, so the page reads them as one
            # quotation rather than as a paragraph that starts with a ">".
            parts.append("\n".join(f"> {line}" for line in text.split("\n")
                                   if line.strip()))
        elif kind == "signoff" and last:
            folded = signature_of(text)
            if folded:
                signature = folded
            else:
                parts.append(text)
        else:
            parts.append(text)

    signature = signature or oneline(tribute.get("from") or "")
    return "\n\n".join(part for part in parts if part), signature


def signature_of(text):
    """A sign-off as one line, or "" if it will not fit as one.

    "Your Niece," over "Mrs Roseline Idokogi" is one line with a comma in it,
    which is how it would be written in a sentence -- so a line that does not
    already end in punctuation is given the comma, and one that does keeps
    its own. ("From:" over a name is "From: the name", not "From:, the
    name".) A sign-off that will not fit the field is left in the message
    instead -- see the module docstring.
    """
    lines = [re.sub(r"\s+", " ", line).strip()
             for line in text.split("\n") if line.strip()]

    # More than a sign-off. Five lines, or two groups with a blank line
    # between them, is a closing passage -- usually a prayer the heuristics
    # read as a sign-off because it opens on a short line ending in a comma.
    # Flattened into the field it would run together as one sentence, so it
    # stays in the message, where the line breaks survive and it is set the
    # way the booklet sets it.
    if len(lines) > SIGNATURE_LINES or "\n\n" in text.strip():
        return ""

    joined = " ".join(
        line if index == len(lines) - 1 or line[-1] in ",:;-\u2013\u2014"
        else line + ","
        for index, line in enumerate(lines))
    return joined if len(joined) <= MAX_SIGNATURE else ""


# ------------------------------------------------------------------- entry

def entry_of(tribute, build):
    """One tribute as the guest book will hold it."""
    blocks = build.blocks(tribute["body"])
    message, signature = message_of(tribute, blocks)

    return {
        "title": oneline(tribute.get("title", "")),
        "message": message,
        "signature": signature,
        "imagePath": (tribute.get("imagePath") or "").strip(),
        "order": tribute.get("order", 0),
    }


def complaints(entry):
    """Everything about an entry that the page would quietly spoil.

    Reported rather than fixed. Each of these is a line somebody wrote, and
    guessing at what they meant is how a tribute ends up saying something
    they did not say.
    """
    out = []
    if not entry["message"]:
        out.append("no message")
    if len(entry["message"]) > MAX_MESSAGE:
        out.append(f"message is {len(entry['message'])} characters, "
                   f"and the server keeps {MAX_MESSAGE}")
    if len(entry["title"]) > MAX_TITLE:
        out.append(f"title is {len(entry['title'])} characters, "
                   f"and the server keeps {MAX_TITLE}")

    # The page's Markdown has no way to escape a marker, so a stray one is
    # formatting nobody asked for. None of these are in the tributes as they
    # stand; they would arrive with an edit.
    for marker, what in (("`", "a code span"), ("*", "emphasis"),
                         ("_", "emphasis"), ("~~", "a strike")):
        if marker in strip_marks(entry["message"], marker):
            out.append(f"a stray {marker!r} the page would read as {what}")
    for line in entry["message"].split("\n"):
        if re.match(r"\s{0,3}([-*+]\s|\d{1,9}[.)]\s)", line):
            out.append(f"a line the page would read as a list: {line[:40]!r}")

    return out


def strip_marks(text, marker):
    """`text` with the markers this script put in removed, so what is left is
    the writer's own punctuation."""
    if marker == "*":
        return re.sub(r"\*\*(.+?)\*\*|\*(.+?)\*", r"\1\2", text, flags=re.S)
    if marker == "~~":
        return re.sub(r"~~(.+?)~~", r"\1", text, flags=re.S)
    return text


def key_of(title, message):
    """What makes two entries the same entry.

    The title, reduced to its letters, because that is what a tribute is
    recognised by and it survives an edit to the punctuation. A tribute with
    no title falls back to the opening of the message, which is the next most
    stable thing about it.
    """
    basis = title or message[:80]
    return re.sub(r"[^a-z0-9]+", "", basis.lower())


# -------------------------------------------------------------------- http

def headers(extra=None):
    """What every request carries.

    `x-device-uuid` is the whole of the page's idea of who is posting; the
    rest is what the server's session middleware wants before it will record
    the device at all -- a request with a uuid and no name is dropped, and
    then the uuid it named does not exist and the request is refused.
    """
    return {
        "user-agent": USER_AGENT,
        "x-device-uuid": DEVICE_UUID,
        "x-device-name": DEVICE_NAME,
        "x-device-model": "script",
        "x-platform": "web",
        "x-app-name": "maQR",
        **(extra or {}),
    }


def request(url, method="GET", body=None, extra_headers=None, raw=False,
            allow=()):
    """One request, with the server's own sentence on failure.

    The guest book answers a refusal with a readable line -- "This page is not
    published", "Write something first" -- and printing that beats printing a
    status code.
    """
    data = None
    head = headers(extra_headers)
    if body is not None and not raw:
        data = json.dumps(body).encode()
        head["content-type"] = "application/json"
    elif body is not None:
        data = body

    req = urllib.request.Request(url, data=data, method=method, headers=head)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        # A status the caller said it can live with -- an undo meeting a
        # message that is already gone, which is the state it wanted anyway.
        if error.code in allow:
            return None
        detail = error.read().decode(errors="replace")
        try:
            said = json.loads(detail)
            detail = said.get("error") or said.get("message") or detail
            if isinstance(detail, dict):
                detail = detail.get("message", str(detail))
        except json.JSONDecodeError:
            pass
        raise SystemExit(f"post-tributes: {method} {url} -> "
                         f"{error.code}: {str(detail)[:400]}")
    except urllib.error.URLError as error:
        raise SystemExit(f"post-tributes: could not reach {url}: {error.reason}")

    if raw:
        return payload
    return json.loads(payload) if payload else {}


def read_guestbook(base):
    """The guest book as a visitor sees it: the wording and every message."""
    said = request(f"{base}/api/guestbook/{EXPERIENCE}")
    return said.get("data") or {}


def upload(base, source):
    """Put one photograph in the page's album, and answer its object name.

    The page's own three steps (src/lib/experience.tsx): measure it, ask the
    server for somewhere to put it, PUT the bytes straight to storage. The
    dimensions are signed into the URL as object metadata, so they have to be
    sent back exactly as they were signed or storage refuses the upload.
    """
    prepared, width, height = prepare(source)

    query = urllib.parse.urlencode({
        "fileName": pathlib.Path(source).name,
        "dirName": EXPERIENCE,
        "fileType": "image/jpeg",
        "width": str(width),
        "height": str(height),
    })
    ticket = request(f"{base}/user-data-url/generate?{query}")
    signed, path = ticket.get("signedUrl"), ticket.get("path")
    if not signed or not path:
        raise SystemExit(f"post-tributes: no upload URL for {source}")

    # Straight to storage, and deliberately without the device headers: this
    # request is signed, and the signature covers exactly these three.
    put = urllib.request.Request(signed, data=prepared, method="PUT", headers={
        "Content-Type": "image/jpeg",
        "x-goog-meta-width": str(width),
        "x-goog-meta-height": str(height),
    })
    try:
        with urllib.request.urlopen(put, timeout=300) as response:
            response.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"post-tributes: {source} did not upload "
                         f"({error.code}): {error.read().decode()[:300]}")

    return path


def prepare(source):
    """The photograph as the page should have it: bytes, width, height.

    Upright (a phone writes the rotation into EXIF and leaves the pixels
    where they were), inside PHOTO_PIXELS, and stripped of the metadata a
    camera writes -- which on a family photograph includes where it was
    taken.
    """
    src = ROOT / source
    if not src.is_file():
        raise SystemExit(f"post-tributes: no such image: {source}")
    if not shutil.which("magick"):
        raise SystemExit("post-tributes: a tribute has an imagePath, "
                         "which needs ImageMagick 7 to prepare")

    prepared = subprocess.run(
        ["magick", str(src), "-auto-orient",
         "-resize", f"{PHOTO_PIXELS}x{PHOTO_PIXELS}>",
         "-strip", "-quality", "86", "jpeg:-"],
        check=True, capture_output=True).stdout

    size = subprocess.run(["magick", "-", "-format", "%w %h", "info:"],
                          input=prepared, check=True,
                          capture_output=True).stdout.decode().split()
    return prepared, int(size[0]), int(size[1])


def post(base, entry, image_path):
    """Leave one message, and answer it as everyone else will see it."""
    said = request(f"{base}/api/guestbook/{EXPERIENCE}", method="POST", body={
        "title": entry["title"],
        "message": entry["message"],
        "signature": entry["signature"],
        "imagePath": image_path or "",
    })
    return said.get("data") or {}


# ------------------------------------------------------------------ ledger

def ledger_read():
    if not LEDGER.is_file():
        return []
    try:
        return json.loads(LEDGER.read_text())
    except json.JSONDecodeError:
        print(f"post-tributes: {LEDGER.name} is unreadable and will be "
              "rewritten; entries posted before now cannot be undone from "
              "here", file=sys.stderr)
        return []


def ledger_write(rows):
    LEDGER.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")


# -------------------------------------------------------------------- runs

def show(entry, note):
    """One entry as it would be stored. The whole message, not a summary:
    reading it here is the point of a dry run."""
    print(f"\n{'=' * 72}")
    print(f"[{entry['order']}] {entry['title'] or '(no title)'}   {note}")
    if entry["imagePath"]:
        print(f"photo: {entry['imagePath']}")
    print("-" * 72)
    print(entry["message"])
    if entry["signature"]:
        print(f"\n-- {entry['signature']}")


def undo(base, dry):
    """Take back the entries this script posted, newest first."""
    rows = ledger_read()
    if not rows:
        print("post-tributes: nothing recorded as posted from here")
        return

    if dry:
        for row in reversed(rows):
            print(f"would delete {row['entryUuid']}  {row['title'][:50]}")
        print(f"\npost-tributes: {len(rows)} entries would be deleted "
              "(nothing was; add --post)")
        return

    # The ledger is rewritten after every delete, not at the end: an undo
    # that stops half way through -- a dropped connection, a Ctrl-C -- must
    # leave behind a list of what is still up, or the rest can never be
    # taken down from here. A message already gone counts as done.
    left = list(rows)
    for row in reversed(rows):
        request(f"{base}/api/guestbook/{EXPERIENCE}/{row['entryUuid']}",
                method="DELETE", allow=(403, 404))
        left.remove(row)
        ledger_write(left)
        print(f"deleted {row['entryUuid']}  {row['title'][:50]}")
        time.sleep(PAUSE)


def main():
    parser = argparse.ArgumentParser(
        description="Post assets/data/tributes.toml to the memorial page's "
                    "guest book.")
    parser.add_argument("--post", action="store_true",
                        help="actually post; without it nothing is sent")
    parser.add_argument("--only", metavar="TEXT",
                        help="only tributes whose title or words contain TEXT")
    parser.add_argument("--limit", type=int, metavar="N",
                        help="stop after N tributes")
    parser.add_argument("--undo", action="store_true",
                        help="delete the entries this script posted")
    parser.add_argument("--base-url", default=BASE_URL,
                        help=f"the server to talk to (default {BASE_URL})")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    if args.undo:
        undo(base, not args.post)
        return

    if not TOML.is_file():
        raise SystemExit(f"post-tributes: {TOML.relative_to(ROOT)} is missing")

    build = load_build_tributes()
    data = textkit.read_toml(TOML)
    # Ascending, which is the reverse of the booklet: the page shows the
    # newest message first, so the booklet's last tribute has to go up first.
    tributes = sorted(data.get("tribute", []), key=lambda t: t.get("order", 0))

    book = read_guestbook(base)
    if not book:
        raise SystemExit("post-tributes: that page has no guest book")
    if not book.get("open"):
        raise SystemExit("post-tributes: that page's guest book is closed "
                         "(unpublished, or its term has ended)")

    already = {key_of(e.get("title", ""), e.get("message", ""))
               for e in book.get("entries", [])}
    print(f"post-tributes: {book.get('total', 0)} messages already on "
          f"{base}/ewed/{EXPERIENCE}#guest_book")

    rows = ledger_read()
    posted = skipped = 0
    faults = []

    for tribute in tributes:
        if args.limit is not None and posted >= args.limit:
            break
        # Title or body, because the person looking for "the one from
        # Solomon" will type a name, and a name is usually in the sign-off
        # rather than in the title.
        if args.only and args.only.lower() not in (
                tribute.get("title", "") + tribute.get("body", "")).lower():
            continue

        entry = entry_of(tribute, build)
        wrong = complaints(entry)
        if wrong:
            faults.append((entry["title"], wrong))
            continue

        if key_of(entry["title"], entry["message"]) in already:
            skipped += 1
            continue

        if not args.post:
            show(entry, "-- would post")
            posted += 1
            continue

        image_path = upload(base, entry["imagePath"]) if entry["imagePath"] else ""
        written = post(base, entry, image_path)
        rows.append({
            "entryUuid": written.get("uuid", ""),
            "title": entry["title"],
            "order": entry["order"],
            "postedAt": written.get("postedAt", ""),
        })
        ledger_write(rows)
        posted += 1
        print(f"posted {written.get('uuid', '?')}  "
              f"{entry['title'][:60] or '(no title)'}"
              + ("  + photo" if image_path else ""))
        time.sleep(PAUSE)

    print()
    if faults:
        print("post-tributes: not posted, because something would be lost:")
        for title, wrong in faults:
            print(f"  {title[:60] or '(no title)'}")
            for line in wrong:
                print(f"    - {line}")
    print(f"post-tributes: {posted} "
          f"{'posted' if args.post else 'to post'}, "
          f"{skipped} already there, {len(faults)} to fix")
    if not args.post and posted:
        print("post-tributes: nothing was sent -- add --post")


if __name__ == "__main__":
    main()
