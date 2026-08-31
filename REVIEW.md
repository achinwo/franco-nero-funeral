# Outstanding issues for review

Compiled 31 August 2026. Everything here needs a human decision — none of it
is something I could resolve without inventing facts, liturgy, or hymn text.
Ordered roughly by how badly it would embarrass the family in print.

---

## 1. Dates contradict each other

**The vigil is scheduled after the funeral.**

| Where | What it says |
|---|---|
| `sections/01-cover.tex:22` | Funeral service **Friday, 4 September 2026**, 11:30 am |
| `sections/04-vigil-mass.tex:9` | Vigil Mass **Thursday 28th September, 2026**, 4:00 pm |

A vigil precedes the funeral. One of these two dates is wrong.

**The vigil's weekday does not match its date.** 28 September 2026 is a
**Monday**, not a Thursday. (For reference: 4 September 2026 *is* a Friday, so
the cover is internally consistent.)

Also worth a glance: the cover gives the date of death as 18 August 2026 —
a Tuesday, which is consistent, but it leaves only two weeks to the 4 September
funeral and six to a 28 September vigil.

---

## 2. Reader names still say "Miller"

`sections/05-funeral-mass.tex` lists three readers:

- line 24 — `Marcus Miller (Son)`
- line 27 — `David Miller (Brother)`
- line 30 — `Sarah Miller (Granddaughter)`

These are living family, not the deceased, so they fell outside the
"Francis Atsekhameh" rename and I left them untouched. If the family surname is
Atsekhameh, all three need correcting — and the given names are probably
placeholders too.

---

## 3. Pronoun and kinship changes made on inference — please verify

The source text for the vigil was internally inconsistent about the deceased's
gender:

- Opening prayer: "since **she** hoped and believed"
- Prayer over the Gifts: "that **he**, who did not doubt your Son to be **his**
  loving Saviour"

I made everything masculine, on the strength of the already-masculine passage
and the cover's "De Sky Man". That decision cascaded into four related edits in
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

## 4. Missing hymn text — three gaps left as-is

I did not fill these in, because inventing hymn verses for a funeral programme
is not a call I should make.

**Trust and Obey, verse 4** (`04-vigil-mass.tex`) — the source begins
mid-sentence, so the verse currently opens with an ellipsis:

> … the delights of His love, / Until all on the altar we lay,

The standard opening is *"But we never can prove / The delights of His love"*.

**It Is Well with My Soul** — the source jumps from verse 1 straight to verse 3,
and verse 3 breaks off unfinished:

> Though Satan should buffet, / Though trials should come, /
> Let this blessed assurance control…

Verse 2 is missing entirely, and verse 3 needs its last line.

**Guide Me, O Thou Great Redeemer** — the source read `2. 3.` followed by two
four-line stanzas, which I set as verses 2 and 3. But neither stanza belongs to
this hymn:

> We gather, Lord, around your table / Waiting for the Bread of life…
> Living bread come down from heaven / He who eats it shall not die…

This looks like two different hymns merged during transcription. Decide whether
you want the real verses 2–3 of *Guide Me*, or these stanzas under their own
title.

---

## 5. Uncertain hymn line — "Yes, Heaven Is the Prize"

Verse 3 currently ends:

> All earthly goods despise / For such a crown of **pain**.

The rhyme scheme (this / despise) and verse 4's own closing "conquer pain"
suggest the original word was something else — possibly *bliss*. I left the
source reading rather than guess.

---

## 6. Possible geographic mismatch

The booklet places the funeral and reception in **London / Bromley** (St
Augustine's Church; The Warren Function Hall, Croydon Road, Hayes, Bromley BR2
7AL; donations to the British Heart Foundation), but the Prayer of the Faithful
names **Archbishop Augustine Akubeze**, who is Archbishop of Benin City,
Nigeria (`04-vigil-mass.tex`, intercession 1).

That combination is entirely plausible for a diaspora family — but if the vigil
is being celebrated in the UK, the local ordinary is probably the name that
belongs there.

---

## 7. Unwritten sections

Three sections are headings and a `% TODO` only. They are paginated and appear
in the contents, so the page numbers will shift once they are filled:

- `sections/03-biography.tex` — biography copy
- `sections/06-photobook.tex` — photograph grid

The contents page gloss for the biography ("Born 14th August 1946 — his story,
in brief") is placeholder wording I wrote; replace it with something the family
would choose.

---

## 8. Content moved during editing — confirm it landed right

The order-of-service list that originally lived in `02-toc.tex` was moved
verbatim into `sections/05-funeral-mass.tex` under a "The Funeral Mass"
heading, so it would not be lost when that file became the contents page. It
has not otherwise been restyled — unlike the vigil, it still uses the older
`\serviceitem` / `\servicedesc` macros rather than the liturgy macro set in
`main.tex`. Converting it would make the two masses match.

---

## Already corrected (recorded here only so you can spot-check)

Scan errors fixed in `04-vigil-mass.tex`: `1 shall want` → *I*; `Martha aid` →
*said*; `Deliverus` → *Deliver us*; `Forall` → *For all*; `death no longer have
dominion` → *has*; `with your always` → *with you always*; `Lord, 1 am not
worthy` → *I am*; `Praim 23` → *Psalm 23*; `Lord, have many` → *mercy*;
`Christ. have mercy` → *Christ, have mercy*; `Thanks to God` → *Thanks be to
God*; `whose nature in always` → *is always*; `it will he said` → *be said*;
`He surety wins` → *surely*; psalm response cues `RL` / `RI` / `RV.` normalised
to `R.`; `3. heaven is the prize` → *Yes, heaven is the prize*.
