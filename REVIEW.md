# Outstanding issues for review

Compiled 31 August 2026; resolved items removed 7 September 2026. Everything
here needs a human decision — none of it is something I could resolve without
inventing facts, liturgy, or hymn text. Ordered roughly by how badly it would
embarrass the family in print.

Items that have since been fixed are gone from this file rather than marked
done. What they said, and the record of scan corrections that used to close
this file, are in the git history of this file if you need them.

---

## 1. The funeral and graveside liturgy came from another family's booklet

The pages in `sections/05-funeral-mass.tex` and `sections/06-at-the-graveside.tex`
were transcribed from a scan of the order of service for **Lady Veronica
Omebere Morgan, KSJI (nee Omeke), 1953–2026** — a woman, buried under a
different family name.

Every trace of that is now gone from the source: no occurrence of the name, of
the Morgan family, of "FOREVER IN OUR HEARTS" or the CamScanner watermark
survives, and the text reads as Francis Atsekhameh throughout with masculine
pronouns. **What remains is a question only the family can answer.**

If the scan was handed over as a *template* — "use this order of service" — the
booklet is right and needs only a read-through. If it was pasted in by mistake,
**the whole of both sections needs replacing, not correcting.** Nothing about
the text itself can tell you which.

---

## 2. No readers or tributes are assigned

The scanned booklet named no readers, so neither does this one. If the family
want individuals named against the readings, the bidding prayers or the
tributes, that has to be added by hand.

---

## 3. Pronoun and kinship changes made on inference — please verify

The source text for the vigil was internally inconsistent about the deceased's
gender:

- Opening prayer: "since **she** hoped and believed"
- Prayer over the Gifts: "that **he**, who did not doubt your Son to be **his**
  loving Saviour"

Everything was made masculine, on the strength of the already-masculine passage
and "De Sky Man". That cascaded into four related edits in
`sections/04-vigil-mass.tex`:

| Was | Now |
|---|---|
| since she hoped / that she may be led | since he hoped / that he may be led |
| our sister, mother, mother-in-law and aunt | our brother, father, father-in-law and uncle |
| the family of your daughter | the family of your son |
| who called her / forgive her sins / welcome her | who called him / forgive his sins / welcome him |
| her children and relatives | his children and relatives |

If any of this is wrong, it is wrong in five places at once.

---

## 4. Missing hymn text — three gaps, all still open

Not filled in, because inventing hymn verses for a funeral programme is not a
call a machine should make.

**Trust and Obey, verse 4** (`04-vigil-mass.tex:281`) — the source begins
mid-sentence, so the verse still opens with an ellipsis:

> … the delights of His love, / Until all on the altar we lay,

The standard opening is *"But we never can prove / The delights of His love"*.

**It Is Well with My Soul** (`04-vigil-mass.tex:381`) — the source jumps from
verse 1 straight to verse 3, and verse 3 breaks off unfinished:

> Though Satan should buffet, / Though trials should come, /
> Let this blessed assurance control…

Verse 2 is missing entirely, and verse 3 needs its last line.

**Guide Me, O Thou Great Redeemer** (`04-vigil-mass.tex:398`) — the source read
`2. 3.` followed by two four-line stanzas, set here as verses 2 and 3. Neither
stanza belongs to this hymn:

> We gather, Lord, around your table / Waiting for the Bread of life…
> Living bread come down from heaven / He who eats it shall not die…

This looks like two different hymns merged during transcription. Decide whether
you want the real verses 2–3 of *Guide Me*, or these stanzas under their own
title.

---

## 5. Uncertain hymn line — "Yes, Heaven Is the Prize"

Verse 3 still ends (`04-vigil-mass.tex:51`):

> All earthly goods despise / For such a crown of **pain**.

The rhyme scheme (this / despise) and verse 4's own closing "conquer pain"
suggest the original word was something else — possibly *bliss*. The source
reading was left rather than guessed at.

---

## 6. Photographs — the three captions describe, they do not tell

The captions under the three mounted prints say only what is visible in the
picture, because nobody could date them or name what is happening:

| Print | Caption as set |
|---|---|
| Landscape, hand-tinted, at a desk with a telephone | *At the desk — the shop books, and the telephone* |
| Standing in patterned agbada against a cloth backdrop | *Dressed for the occasion* |
| Standing with a ledger before stacked cartons | *Taking stock* |

Two of them are plainly taken in a shop or warehouse — Kellogg's cartons on the
shelves behind the desk, Johnson's baby powder cases stacked behind the ledger.
If that was his business, the captions should say so by name, and the family
will know roughly what years these are. **Replace all three.**

They now live in `assets/data/captions.toml`, one line per photograph, keyed by
the image file — so changing them is editing that file and re-running
`sh assets/make-plates.sh`. No LaTeX involved.

Note also that the Photographs frontispiece and the back cover both carry the
studio portrait. That is deliberate — the section closes on the face it opened
with — but if the family would rather see a different photograph on the back,
it is a one-word change.

---

## 7. Photographs — the hand-tinting is mostly gone

Two of the four prints were hand-coloured: a blue headwrap in the desk
photograph, a blue-tinted face in the warehouse one. The four scans are
otherwise so unlike each other in age and cast that setting them beside one
another untreated looked like four photographs from four different books, so
`assets/make-plates.sh` tones them all to one warm sepia, laid down at 78% with
the original colour left showing through at 22%.

That unifies the set, but the blue is now barely there. If the family would
rather keep the tinting, lower the `78` in the `tone()` function; the tradeoff
is that the set stops matching.

---

## 8. The family album is generated — three photographs are being dropped

`assets/images/family_pics/` holds 45 files, of which **42 are printed and three
are skipped.** Check this list — a photograph the family expects to see and
cannot find will be here:

| File | Why it was skipped |
|---|---|
| `WhatsApp ... 17.03.28.jpeg` | byte-identical to another file already printed |
| `WhatsApp ... 17.04.56.jpeg` | 225×225 pixels — about 19mm on the page |
| `WhatsApp ... 17.05.20.jpeg` | **editorial:** near-duplicate of `17.03.51` |

The first two are automatic and safe. **The third is a judgement call.**
`17.03.51` and `17.05.20` are the same moment — the couple by the car — shot
full-length and again as a closer crop; printed side by side they read as a
printing error, so the full-length one was kept. To put it back, delete its line
from the `SKIP` dictionary at the top of `assets/build-album.py` and re-run
`sh assets/make-plates.sh`.

The 225×225 one is a good photograph of Francis with a young woman, lost to
WhatsApp compression. **If anyone still has the original, it is worth adding** —
drop it into `family_pics/` and re-run the script; nothing else needs editing.

Near-duplicate detection is not attempted automatically. A perceptual hash was
tried and does not separate these: the redundant pair scores 19 bits apart while
two plainly different photographs score 17, so any threshold that caught the
pair would also silently delete something wanted. That reasoning is recorded in
the script.

---

## 9. Nobody in the photographs is named

Fifty-one photographs are printed without captions — 42 in the family album and
nine of his own — because nobody could say who is in them beyond Francis
himself. Several show him with a woman who appears throughout, presumably his
wife, and one is a large family group at a gate.

Captioning any of them is now one line each in `assets/data/captions.toml`,
keyed by the file the photograph arrived in. The mapping from each printed
plate back to its source file is written as a comment at the top of
`assets/images/plates/family-album.tex` and `plates/personal-photos.tex`.

One of his own photographs is a black-and-white studio portrait (`16.59.18`), a
different sitting from the one used as the frontispiece. It is worth confirming
it is Francis and not a relative.

---

## 10. The contents-page gloss for the biography is placeholder wording

`sections/02-toc.tex:63` reads "Born 10th October 1946 — his story, in brief".
That sentence was written to fill the slot, not chosen by anyone. Replace it
with something the family would say.

---

## 11. Funeral mass — text the scan lost, and could not supply

**Second reading (1 Cor 15:53).** The scan dropped half the verse; the standard
reading was restored: "because this perishable nature of ours must put on
imperishability, and this mortal nature must put on immortality". **Verify
against the lectionary the parish actually uses.**

**The embolism after the Our Father is still truncated**
(`05-funeral-mass.tex:429`) — it reads `Deliver us, Lord, we pray, from every
evil…` and ends there, as the vigil does. The full Missal text is fixed and
could be supplied if you want it printed in full.

**"Take Our Bread" has two verses**; the hymn has three in most settings. The
third is missing from the scan.

---

## 12. Funeral mass — editorial calls worth a second opinion

**Abide with Me appears twice in the booklet** — as the vigil's closing hymn
(verses 1–2, `04-vigil-mass.tex:442`) and as the funeral's recessional (verses
1–4, `05-funeral-mass.tex:644`). That may well be deliberate, but it is worth a
deliberate decision.

**The Opening Prayer was split mid-sentence between speakers** in the scan, with
the congregation given the second half of a presidential prayer. The whole
prayer was given to the Priest, with the Amen to all; the same fix was applied
to the reception prayer at the church door.

**Petition 3 addressed the congregation in the second person** ("that God will
bless you all and grant you journey mercies") in the middle of a prayer spoken
about them in the third. Normalised to "them".

---

## 13. No time is given for the graveside

`sections/06-at-the-graveside.tex:11` reads "Saturday 3rd October, 2026 —
following the Funeral Mass", which is true but vague. Replace it with the actual
time if there is one.

---

## 14. The cover artwork and the typeset cover are fighting

*Added 7 September 2026, after the Canva cover was brought in.*

`assets/data/plates.toml` now points the cover at `franco_nero_cover.jpg`, which
is placed unchanged and then has the booklet's own type set on top of it. The
two collide:

- The green **"Aged 80"** seal in the artwork sits over "Franco Nero
  Internation**al**", covering the last letters.
- **80 appears twice** — once in the seal, once in the typeset medallion below.
- "In Loving Memory of" has gone nearly invisible against the clouds.

Decide which layer owns the type. Either the artwork carries it and the type
block comes out of `sections/01-cover.tex`, or the artwork is re-exported as a
background only and the type stays as it is.

**Separately: the artwork is 1240×1748, which over a 148mm page is about 213
dpi.** Every other plate in the booklet is 300 dpi, and this one bleeds to the
trim on the most looked-at surface in the job. Re-export at **1748×2480** and it
matches.
