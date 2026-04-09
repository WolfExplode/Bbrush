# Bbrush

"No More Compromises—Built for Tablet Artists"

Blender add-on that reshapes sculpt workflow toward a ZBrush-style tool shelf and shortcuts: mask/hide tools swap in when you hold modifiers, plus a small silhouette overlay for tablet work.

![981b5107_9588511](https://github.com/user-attachments/assets/f02b0b50-e4ad-4e7b-9817-fec10ade2e6a)

![screenshot-20250516-154529](https://github.com/user-attachments/assets/cd966ef1-4884-42ee-949d-745725566a3f)

## Getting started

1. Enable the **Bbrush** add-on in Blender preferences.
2. Select a mesh and enter **Sculpt** mode. The add-on swaps the sculpt tool shelf for Bbrush’s grouped layout while you are in sculpt mode (and restores Blender’s default list when you leave).
3. Optional: use the **Silhouette** control in the 3D View header (sculpt mode) or open add-on preferences for the same setting.

Display shortcut overlays if you use them; Bbrush does not replace Blender’s keymap for general navigation.

## Tool shelf and modifier keys

While the cursor is over the 3D View, **Ctrl / Shift / Alt** combinations decide which tool list is active:

| Modifiers | Shelf |
|-----------|--------|
| No **Ctrl** | Sculpt brushes (default) |
| **Ctrl** held (with or without **Alt**) | Mask tools |
| **Ctrl+Shift** held (with or without **Alt**) | Hide / trim / project tools |

The shelf updates on modifier **press** and **release** so you do not need to click the toolbar each time.

## Face sets (polygroups)

Blender’s **Face Sets** map to a ZBrush-like mental model here.

### Shift + Ctrl + click (on the mesh)

On **mouse / pen release**, with **Shift** and **Ctrl** held (no **Alt**), **without** dragging: Bbrush runs face-set visibility logic:

- If the mesh is **fully visible** (no hidden geometry): **isolate** the face set under the cursor (same idea as Blender’s face-set isolate / Shift+H style toggle).
- If you already have **partial hide**: **hide** the face set under the cursor as well (stacking hides, similar to pressing **H** on that set).

The click must start **on the sculpt mesh** (same hit-test used elsewhere in Bbrush).

### Ctrl + W

**Ctrl+W** runs **Face Set from Mask or Visible** (`sculpt.bbrush_face_sets_create_zbrush`):

- If there is a **non-zero sculpt mask**: create a face set from **masked** faces, then **clear the mask** (so a second **Ctrl+W** can run the visible path).
- If there is **no mask**: create a face set from **currently visible** geometry (useful after hiding parts of the mesh).

**Shift** and **Alt** must be off for this keymap item (see `sculpt/keymap.py`).

## Left mouse (sculpt)

Bbrush installs **`sculpt.bbrush_left_mouse`** on **left button press** in sculpt mode.

- **Drag on the mesh** (normal shelf): forwards to Blender’s sculpt stroke (invert with **Alt**, smooth with **Shift** per Blender’s stroke rules).
- **Drag** with a **line / box / lasso / polyline / circular / ellipse** mask or hide tool: starts the matching gesture (or **`sculpt.bbrush_shape`** for the tools Bbrush wraps).
- **Ctrl + drag** starting in **empty space**: starts **`sculpt.bbrush_shape`** for mask/hide box-style workflows when no stroke target is needed.
- **Single click** (no drag): **`sculpt.bbrush_click`**  
  - **Mask shelf**: on mesh — smooth mask; **Ctrl+Alt** on mesh — sharpen mask; off mesh — invert mask.  
  - **Hide shelf**: on mesh — invert visibility; off mesh — show all hidden.

**Polyline** mask/hide (and other shapes handled by `bbrush_shape`): add points with **left click**; **right click** removes the last point (or cancels if only one); **Esc** cancels; **Enter** or **numpad Enter** **commits**; **double-click** the last vertex also commits. **Space**: move the whole polyline while drawing.

Tools that remain **fully on Blender** (face set paint, annotate, transform, filters, etc.) use **`PASS_THROUGH`** so default Blender behavior is unchanged.

## Right mouse

**`sculpt.bbrush_right_mouse`**: **release** opens the sculpt **context menu**. **Drag** is passed through to Blender (rotation / zoom on RMB are **not** implemented by Bbrush).

## Silhouette (depth preview)

In **Add-on preferences → Silhouette** (and the 3D View header enum in sculpt mode):

- **Always display** — overlay even outside sculpt mode  
- **Only Sculpt** — overlay only in sculpt mode  
- **Not Display** — off  

Adjust **scale** and **offset** there. A small depth strip near the cursor can be used for depth brushing (see preferences for **Depth ray** and related options).

## Preferences and troubleshooting

- **Depth ray check size** — pixel radius used to decide if the pointer is “on” the mesh.  
- **Drag offset compensation** — optional stroke cursor compensation.  
- **Debug** — log to the system console; **Print State** / **System Console** operators for support.  
- **Reset BBrush Keymap & Tool Shelf** (`sculpt.bbrush_fix`) — if shortcuts or the shelf misbehave after reload or file load.

## Requirements

- Blender **4.0+** (see `bl_info` in `__init__.py` for the exact minimum).

## Notices

- Hiding faces can interact badly with **Multires**; that limitation comes from Blender’s visibility pipeline, not only from this add-on.
- Older Blender + certain smooth/invert stroke combinations had stability issues; use a supported Blender version.
