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

## 2. The funeral-mass scan is a different person's booklet

**This is the biggest problem in the file and needs a decision before print.**

The pages pasted into `sections/05-funeral-mass.tex` are a scan of the order of
service for **Lady Veronica Omebere Morgan, KSJI (nee Omeke), 1953--2026** — a
woman, buried under a different family name, with a different date range. Her
name appears fourteen times in the source, and the page furniture reads
"FOREVER IN OUR HEARTS" and "Scanned with CamScanner".

Following the precedent already set for the vigil (item 3 below), I transcribed
it **as Francis Atsekhameh throughout**, with masculine pronouns, so that the
booklet is internally coherent:

| Source | Now |
|---|---|
| Lady Veronica Omebere Morgan (x14) | Francis Atsekhameh |
| the Morgan family | the Atsekhameh family |
| our sister / our departed brother (mixed) | our brother |
| her / she / his (mixed, see below) | he / him / his |

If this scan was handed over as a *template* — "use this order of service" —
that is the right outcome and only needs a read-through. If it was handed over
because these are genuinely the prayers chosen for Francis, the same applies.
**But if it was pasted in by mistake**, the whole section needs replacing, not
correcting.

The source's own gendering was incoherent regardless of which name is used —
within a single paragraph of the Final Commendation it reads "the body of our
sister... May God unite **his** soul... May **she** be given a merciful
judgment", and the Song of Farewell alternates "Receive **her** soul and present
**him** to God". So a pronoun sweep was unavoidable in any case.

---

## 2a. Content the scan replaced

The previous `05-funeral-mass.tex` held a placeholder outline — Elgar's
"Nimrod", a Psalm 121 reading by Marcus Miller, a Tennyson poem by Sarah Miller.
None of it survived, which resolves the old "reader names still say Miller"
item: those names are gone. But so are the **reader and tribute assignments** —
the scanned booklet names no readers at all. If the family want individuals
named against the readings, that has to be added back by hand.

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

## 6a. Photographs — captions are descriptions, not facts

The four scans now fill the Photographs section and back the section
openings. I can describe what is visible in them; I cannot date them or name
what is happening, so the captions say only what the picture shows:

| Print | Caption as set |
|---|---|
| Landscape, hand-tinted, at a desk with a telephone | *At the desk — the shop books, and the telephone* |
| Standing in patterned agbada against a cloth backdrop | *Dressed for the occasion* |
| Standing with a ledger before stacked cartons | *Taking stock* |
| Seated studio portrait, suit and bow tie | (no caption — it is the full-page frontispiece) |

Two of them are plainly taken in a shop or warehouse — Kellogg's cartons on
the shelves behind the desk, Johnson's baby powder cases stacked behind the
ledger. If that was his business, the captions should say so by name, and
the family will know roughly what years these are. **Replace all three.**

Note also that the frontispiece and the back cover both carry the studio
portrait. That is deliberate — the booklet closes on the face it opened
with — but if the family would rather see a fourth photograph on the back,
it is a one-word change.

---

## 6b. Photographs — the hand-tinting is mostly gone

Two of the four prints were hand-coloured: a blue headwrap in the desk
photograph, a blue-tinted face in the warehouse one. The four scans are
otherwise so unlike each other in age and cast that setting them beside one
another untreated looked like four photographs from four different books, so
`assets/make-plates.sh` tones them all to one warm sepia, laid down at 78%
with the original colour left showing through at 22%.

That unifies the set, but the blue is now barely there. If the family would
rather keep the tinting, lower the `78` in the `tone()` function; the tradeoff
is that the set stops matching.

---

## 7. Unwritten sections

One section is still a heading and a `% TODO` only. It is paginated and
appears in the contents, so the page numbers will shift once it is filled:

- `sections/03-biography.tex` — biography copy

(`sections/06-photobook.tex` is now built out from the four scans, so this
list is down from two.)

The contents page gloss for the biography ("Born 14th August 1946 — his story,
in brief") is placeholder wording I wrote; replace it with something the family
would choose.

---

## 8. Funeral mass — text the scan lost or garbled

These are places where the OCR ran out of source, not places I could repair.

**Second reading (1 Cor 15:53) was missing a clause.** The scan read "we shall
be changed as well, because our present nature must put on immortality", which
drops half the verse and makes the sentence that follows it a non sequitur. I
restored the standard reading: "because this perishable nature of ours must put
on imperishability, and this mortal nature must put on immortality". Verify
against the lectionary the parish uses.

**Two prayers are truncated in the source and remain so:**

- Rite of Peace — the scan reads only `Priest: Lord Jesus Christ, who said
  to...` before jumping to the Amen. I supplied the full Missal text, which is
  fixed and not a matter of choice.
- The embolism after the Our Father reads `Deliver us, Lord, we pray, from every
  evil,...` and is left with an ellipsis, as the vigil does.

**"Take Our Bread" has only two verses** in the scan (the hymn has three in most
settings). Refrain-verse-refrain-verse-refrain in the source was collapsed to a
single printed refrain at the head, matching how the vigil sets its choruses.

**The Latin ordinary was badly scanned** and has been corrected against the
Missal: `Requiem aetenam` to *aeternam*; `lux perpetual` to *perpetua*;
`orationem mean` to *meam*; `Christ eleison` to *Christe eleison*; `Pleni sunt
coeli et terra Gloria tua` to *gloria tua*. The English gloss for *Te decet
hymnus Deus in Sion* was printed as "The hymns of the Lord are sung in Sion",
which is not a translation of it; I used the usual "To you our praise is due in
Sion, O God".

---

## 9. Funeral mass — editorial calls worth a second opinion

**The date in the section header was wrong.** The pasted block carried the
vigil's header verbatim — Thursday 28 September, 4:00 pm. I set it to the
cover's funeral date, Friday 4 September 2026, 11:30 am. This does not resolve
item 1 above; it only stops the funeral from claiming the vigil's slot.

**The Opening Prayer was split mid-sentence between speakers.** The scan gives
"Priest: Let us pray, O God, Almighty Father, our faith professes that your Son
died and rose again." then "All: Mercifully grant, that through this mystery
your servant..." — the congregation cannot be saying the second half of a
presidential prayer. I gave the whole prayer to the Priest, with the Amen to
all. Same fix applied to the reception prayer at the church door.

**Abide with Me now appears twice in the booklet** — as the vigil's closing
hymn (verses 1--2) and as the funeral's recessional (verses 1--4). That may well
be deliberate, but it is worth a deliberate decision.

**Petition 3 addressed the congregation in the second person** ("that God will
bless you all and grant you journey mercies") in the middle of a prayer spoken
about them in the third. Normalised to "them".

**Numbering in the source was broken** — the scan runs "4. Homily, 5. Prayers
of the Faithful, 5. Offertory, 6. Offertory Hymn, 7. Take Our Bread, 7. Liturgy
of the Eucharist, 8. Communion". I dropped the numbers entirely and used the
same heading hierarchy as the vigil.

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

Scan errors fixed in `05-funeral-mass.tex`: `YES, ISHALLARISE` → *Yes, I Shall
Arise*; `GOSPELACCLAMATION` → *Gospel Acclamation*; `ROCK OFAGES` → *Rock of
Ages*; `Olet your ears` → *O let*; `Out Of The Depth` → *depths*; `pray for me
to the Lord our Lord` → *our God*; `pattern with the host` → *paten*; `come
from marriage feast` → *from the marriage feast*; `find them so` → *finds*;
`would have not left` → *would not have*; `the son of man` → *the Son of Man*;
`Israel indeed He will free from all its iniquity` → *will redeem from*; `Take
you to Holy City` → *to the Holy City*; `Lady Veronica Mobere Morgan` (twice)
-> the Omebere spelling used elsewhere, before the rename; `fulfillment` /
`labor` / `fulfill` / `Savior` → British spellings, to match the vigil; running
heads, folios, `FOREVER IN OUR HEARTS` and the CamScanner watermark stripped.
