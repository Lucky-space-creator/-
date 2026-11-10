# Front-end Task — "Upload Your Resume" (final step)

**Live files:** `code/index.html`, `code/styles.css`, `code/app.js` — no build step, no dependencies.

```bash
# simplest possible: open the file
start code/index.html          # Windows
# or serve it (needed only if you want a non-file:// origin)
python -m http.server 5500 -d code
```

| Screenshot | File |
|---|---|
| Desktop, empty state | `assets/desktop-default.png` |
| Desktop, file selected | `assets/desktop-selected.png` |
| Mobile 390 px | `assets/mobile.png` |

---

## 1. What the design asks for

The Figma file (`node-id=0-1`) is a three-step wizard; this screen is the **final step**, and the
annotation frame next to it lists the grading criteria:

| Requirement (from the design file) | Where it is implemented |
|---|---|
| Page structure & layout correctness | white page, copy at the top of the left column, illustration bleeding off the bottom edge, upload card on the right |
| Style fidelity: type scale, colours, button styles, icon placement, radius, shadow | tokens in `:root`, colours sampled from the design (see §2), 18 px card radius, 4 px dashed dropzone, 6 px buttons |
| Semantic HTML / clear structure | `main > section > h1/h2`, real `<form>`, `<input type="file">`, `<ol>` stepper, `aria-*` |
| Click the dropzone to open the file picker | `app.js` → `openPicker()` (+ keyboard `Enter` / `Space`) |
| Hover / active states | `.dropzone:hover`, `.is-dragover`, `.btn:hover`, `.btn:active`, `:focus-visible` rings |
| Responsive: stack to one column on small screens | `@media (max-width: 900px)` → single column, smaller art, full-width buttons at 420 px |
| Show the uploaded file name | `#file-name` swaps in for the dropzone hint, shows name + size |

## 2. Fidelity against the design

The design was supplied as a screenshot of the Figma canvas, so the numbers below were measured
from it (colours by pixel sampling, geometry by proportion) rather than copied from Figma's
inspect panel.

| Design element | Implemented value |
|---|---|
| Finish button | `#2360FF`, white 14 px label, 42 px tall, 6 px radius |
| Last step button | `#7FB0F8` (light blue, white label) — a *filled* secondary, not an outlined ghost |
| Dropzone | fill `#F2FAFF`, 1.5 px dashed `#7FA6F0`, 4 px radius, cloud-with-arrow icon `#2C63F3`, two centred lines of 11.5 px `#A3A8B0` copy |
| Card | white, 18 px radius, soft shadow, title "Upload file" 20 px/600 |
| Stepper | three 18 px `#4B7BFF` dots, each with a white check, on a `#C9D8FF` track that runs past the outer dots |
| Layout | left column 300 px, 96 px gap, card 584 × 542 px (h/w 0.93 vs 0.88 in the design) |
| Copy | "Finish!", "Upload Your Resume", the paragraph, "Upload file", both button labels, the dropzone instructions — verbatim |

**On the illustration:** it is the design's own artwork, not a redraw. It was cropped from the
supplied design screenshot (`assets/illustration.png`, 630 × 544, 2× the rendered size), the Figma
canvas background `rgb(248,251,249)` was flattened to pure white so no grey box shows on the page,
and it is referenced as a normal asset. If a vector export is available, replacing that file with
`illustration.svg` and pointing the `<img src>` at it is the only change needed — the layout code
does not care which format the art is in.

**One line of copy is still inferred.** In the supplied screenshot a Figma avatar chip covers the
second line of the paragraph; only "…then click … step" is visible. It is completed as
"…then click Next step", which matches the visible tail and the wizard context, even though the
button on this screen says *Finish*. Worth confirming with whoever owns the copy.

Sizes are therefore proportional rather than exact: the screenshot is a 29 %-zoom capture, so
absolute type sizes were derived from the ratio between elements, and type sizes sit within ±2 px of
the original. All of it lives in `:root` and the component blocks, so correcting against the real
file is a 10-minute edit.

## 3. Implementation notes

**No framework, deliberately.** The screen is one static view with three interactions. A
`create-react-app`/Vite scaffold would add ~40 MB of `node_modules` and a build step to deliver
what is ~150 lines of vanilla JS. If the team wants a component, the markup maps 1:1 to a
`<ResumeUploader>` component, so porting it is mechanical.

**Drag & drop details that are usually missed:**

* `dragenter`/`dragleave` fire for every child node, so a naive handler flickers the highlight —
  solved with a depth counter.
* A drop outside the dropzone navigates the browser to the file; a window-level `dragover`/`drop`
  handler with `preventDefault()` stops that.
* Multi-file drops are rejected with a toast instead of silently taking `files[0]`.

**Validation** runs before the UI commits, not after submit: extension allow-list
(`pdf/doc/docx/png/jpg/jpeg`), ≤ 10 MB, non-empty. Errors render in a `role="alert"` paragraph and
the dropzone turns red; the selected state is cleared so the field can never look "filled" while
holding an invalid file.

**Accessibility:** the dropzone is a real `role="button"` with `tabindex="0"` and an
`aria-label` that changes to *"Selected file X. Click to replace it."*; the file-name line is
announced through the toast (`role="status"`); focus rings are explicit (`:focus-visible`);
`prefers-reduced-motion` disables transitions; the stepper exposes `aria-current="step"` and
screen-reader-only labels.

**State model** (single source of truth = `selectedFile`):

```
empty ──choose valid──▶ selected ──choose valid──▶ selected (replaced)
  ▲                        │
  └────choose invalid──────┘  (error shown, selection cleared)
```

## 4. Next steps

1. **Swap in the vector export** of the illustration if Figma hands one over (`assets/illustration.svg`);
   the bitmap currently in place is a 2× crop of the design and will look soft on 3× displays.
2. **Confirm the last line of the paragraph** with whoever owns the copy, and whether *Last step*
   navigates back or collapses to step 2 (the demo calls `history.back()` and falls back to a toast).
3. **Wire it up**: `POST /resume` with `FormData`, upload progress, and error mapping — the form
   already dispatches a `resume:submit` event carrying the `File`, so the handler is a drop-in.
4. **Add a visual regression check** (Playwright screenshot diff at 1440 / 834 / 390 px) so the next
   style pass cannot silently break the layout.
