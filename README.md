# Bbrush

**No More Compromises — Built for Tablet Artists**

Blender add-on that reshapes sculpt workflow toward a ZBrush-style tool shelf and shortcuts: **Ctrl** shows mask tools, **Ctrl + Shift** shows hide/visibility tools, and **Shift** (without Ctrl) drives the secondary brush—plus optional **silhouette** overlay, smarter LMB/RMB handling in sculpt mode, and a reset when Blender gets into a weird state after reloads.

---

## Installation

1. Download or clone this repository.
2. In Blender: **Edit → Preferences → Add-ons → Install…** and select the add-on folder or zip.
3. Enable **Bbrush**.

---

## Dynamic sculpt tool shelf

While modifiers are held, the add-on switches the **Sculpt** tool list in the 3D View sidebar:

| Modifiers held | Shelf mode |
|----------------|------------|
| **Ctrl** without **Shift** (optional **Alt**) | Mask-related tools (mask brush, box/lasso/line mask, …) |
| **Ctrl + Shift** (optional **Alt**) | Hide / visibility / trim tools |
| No **Ctrl** (including **Shift** alone, **Alt** alone, or none) | Normal sculpt brush shelf |

Releasing modifiers restores the matching shelf and tries to keep your active brush selection consistent.

Floor grid is turned off in the 3D View while the custom shelf is active (tablet-oriented viewport).

---

## Secondary brush (smooth while holding Shift)

**Hold Shift** to sculpt with a secondary brush—by default this behaves like **Smooth** (same idea as ZBrush).

- **Blender 5.1 and newer:** Shift uses Blender’s brush **asset** system: your primary brush is saved when Shift is pressed, a **secondary slot** is activated (defaults to a custom smooth asset if present, otherwise Essentials **Smooth**). Release Shift to return to the primary brush. If you pick another brush while Shift is held, that becomes the remembered secondary for next time.
- **Older Blender:** Shift still maps to smooth-style stroke behavior via the built-in sculpt stroke API.

https://github.com/user-attachments/assets/9652a539-83fe-443e-9d6a-0ae14841c060

---

## Face sets (polygroups)

ZBrush-like convenience on top of Blender’s face sets:

- **Ctrl + Shift + click** (release without dragging) on a face set under the cursor:
  - If the mesh is **fully visible**, it **isolates** that face set (toggle visibility for that set).
  - If something is **already hidden**, it **hides** the face set under the cursor instead (stack hide operations).

- **Ctrl + W** — **Face Set from Mask or Visible**
  - If there is a mask: create face sets from masked geometry, then clear the mask (ZBrush-style double use).
  - If there is no mask: create face sets from **currently visible** geometry (useful after partial hide).

https://github.com/user-attachments/assets/8b9bfd0c-437e-4145-89ac-a898bc61aafb

---

## Masking (ZBrush-style clicks and drag)

With the mask shelf active (**Ctrl**):

- **Ctrl + paint** on the mesh — mask.
- **Ctrl + drag** in empty space — clear mask.
- **Ctrl + click** in empty space — invert mask.
- **Ctrl + Alt** — unmask stroke behavior (via Blender’s sculpt stroke).
- **Ctrl + right-mouse drag** left/right — resize the mask brush (pixel size).

https://github.com/user-attachments/assets/5a429b49-1c71-46c1-a7c7-dd9c52154648

---

## Hide / visibility (ZBrush-style)

With the hide shelf active (**Ctrl + Shift** held):

- **Ctrl + Shift** — isolate visible verts (gesture tools behave like Blender’s hide/show tools).
- **Ctrl + Shift + Alt** — hide verts from view (depends on active hide tool; line hide uses **Alt** to invert hide/show direction where applicable).
- **Ctrl + Shift + click** in empty space — invert visibility.

Shape gestures (box, lasso, line, …) are routed so mask/hide/trim tools work with the add-on’s modal mouse handling.

---

## Supports mirroring

Sculpt symmetry is respected for the relevant brushes and gestures (see Blender’s symmetry settings for the active object).

https://github.com/user-attachments/assets/477809c8-8df0-4429-8305-d03139ed7056

---

## Silhouette overlay
![981b5107_9588511](https://github.com/user-attachments/assets/f02b0b50-e4ad-4e7b-9817-fec10ade2e6a)

Optional **depth silhouette** picture-in-picture in the 3D View:

- **Preferences → Silhouette:** display mode (**Always** / **Only Sculpt** / **Off**), scale, and screen offset.
- **3D View header:** quick control for silhouette display mode (next to the menus).
- **Click + drag on the silhouette:** move or scale the overlay (when the cursor is over the silhouette region).

Useful for checking proportions on a tablet without rotating the main model away.

---

## Other behavior

- **LMB on mesh** — sculpt stroke; uses ray casting so drag detection works reliably (helps Blender 5.x drag quirks).
- **LMB click on mesh** — can invoke Blender’s **transfer mode** to jump between overlapping objects when appropriate.
- **RMB** — opens the sculpt context menu; **Ctrl + RMB drag** while the mask shelf is active resizes brush size; **Shift + RMB** is passed through for other add-ons (e.g. HDRI gestures).
---

## Preferences (Edit → Preferences → Add-ons → Bbrush)

| Option | Purpose |
|--------|---------|
| **Depth ray check size (px)** | How far around the cursor counts as “over the model” for hit testing. |
| **Mouse move threshold (px)** | Minimum movement to treat input as a drag vs a click. |
| **Drag offset compensation** | Optional cursor warp to reduce edge dragging inaccuracy (off by default). |
| **Debug logging** | Print diagnostics to the **system console** (Windows: preference button to toggle console). |
| **Reset BBrush Keymap & Tool Shelf** | Re-register keymaps and rebuild the shelf — use after odd states (file load, add-on reload), not every session. |

---

## Operators

- **`Reset BBrush Keymap & Tool Shelf`** (`sculpt.bbrush_fix`) — available from **add-on preferences** or **F3** search; same as the preference button: fixes stuck keymaps or shelf.
- **`Face Set from Mask or Visible`** (`sculpt.bbrush_face_sets_create_zbrush`) — bound to **Ctrl + W** in sculpt mode via the add-on keymap.

---

## Requirements

- **Blender 4.0+** — matches `bl_info` in the root `__init__.py`.
- **Blender 5.1+** recommended for **Shift secondary brush asset** swapping and current stroke flags.

---

## Notices

- Hiding faces can interact badly with **Multires**; that limitation comes from Blender’s visibility pipeline, not only from this add-on.
- Older Blender builds combined with certain smooth/invert stroke combinations had stability issues; use a supported Blender version.
