---
name: Dictate
description: Native Windows tray utility with a compact transcript recovery popup.
colors:
  surface: "#171717"
  row: "#252525"
  hover: "#333333"
  edge: "#4B4B4B"
  text: "#F5F5F5"
  muted: "#B8B8B8"
  accent: "#E8DBBE"
  action: "#AD8326"
  action-text: "#FFFFFF"
  idle: "#777777"
  recording: "#AD8326"
  processing: "#E8DBBE"
  tray-glyph: "#F5F5F5"
typography:
  heading:
    fontFamily: "Segoe UI Variable Display, Segoe UI"
    fontSize: "18px"
    fontWeight: 700
  row:
    fontFamily: "Segoe UI Variable Text, Segoe UI"
    fontSize: "16px"
    fontWeight: 400
  instruction:
    fontFamily: "Segoe UI Variable Text, Segoe UI"
    fontSize: "13px"
    fontWeight: 400
  shortcut:
    fontFamily: "Segoe UI Variable Display, Segoe UI"
    fontSize: "12px"
    fontWeight: 700
rounded:
  popup: "20px"
  row: "11px"
  shortcut: "12px"
spacing:
  inset: "16px"
  row-gap: "5px"
  row-leading: "10px"
  shortcut-label-gap: "12px"
components:
  popup:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.popup}"
    padding: "{spacing.inset}"
    width: "500px"
  recovery-row:
    backgroundColor: "{colors.row}"
    textColor: "{colors.text}"
    typography: "{typography.row}"
    rounded: "{rounded.row}"
    height: "44px"
  recovery-row-hover:
    backgroundColor: "{colors.hover}"
  log-row:
    backgroundColor: "{colors.row}"
    textColor: "{colors.accent}"
    typography: "{typography.row}"
    rounded: "{rounded.row}"
    height: "44px"
  empty-row:
    backgroundColor: "{colors.row}"
    textColor: "{colors.muted}"
    typography: "{typography.row}"
    rounded: "{rounded.row}"
    height: "44px"
  shortcut:
    backgroundColor: "{colors.action}"
    textColor: "{colors.action-text}"
    typography: "{typography.shortcut}"
    rounded: "{rounded.shortcut}"
    size: "24px"
---

# Design System: Dictate

## Overview

Neutral dark gray surfaces, white text and SRC gold shortcut chips share the approved theme with Silent Type and Snip. The designed Windows surface is the Recent dictations popup and its tray icon. The separate macOS implementation is headless; this document does not prescribe a macOS screen.

The Windows appearance is owned by theme.py, recents.py and dictate.py. PRODUCT.md records the approved direction. Existing geometry and recovery behavior remain intact.

## Colors

Action gold fills keyboard shortcut chips, with white labels and light-gold edges. The light-gold accent identifies the full-log action. Surface, row and hover distinguish the popup from its interactive rows; edge outlines the popup. Text is used for transcripts and the heading, muted for instructions and the empty state.

Tray states use idle gray, recording gold and processing light gold. The microphone uses tray-glyph white on idle and recording, and surface charcoal on processing. Tooltip text names each state. Windows renders the context menu, scrollbar and notifications using its own controls.

White labels on solid gold retain the approved brand exception. This pairing does not establish ordinary small-text contrast compliance. This popup changes the neutral row fill on hover; it has no primary-button hover state.

## Typography

Use the installed Segoe UI Variable families, falling back to Segoe UI. Heading and shortcut use the display family; instructions and transcripts use the text family. The source specifies pixel sizes through negative Tk font sizes. Frontmatter sizes are the unscaled baseline; actual sizes are multiplied by system DPI / 96 and truncated to integers.

Transcript previews occupy one line. Collapse whitespace and ellipsize using measured font width. Preserve the full original transcript for copying.

## Layout

One heading, one instruction line, up to ten newest-first transcripts, then the full-log action. The empty state occupies one transcript row and retains the log action. The header reserves 52 baseline pixels; rows and gaps follow the frontmatter dimensions.

The canvas is at most 500 scaled pixels wide, further constrained by the pointer monitor's work area. It reserves 16 physical pixels of horizontal clearance and 17 scaled pixels for a possible scrollbar. Height is bounded by the work area minus 16 physical pixels. Overflow adds a native scrollbar; the complete canvas, including its header, scrolls. Mouse wheel and Page Up/Page Down are supported.

Place the popup near the pointer, clamped inside that monitor's work area with an 8 physical-pixel margin. Use native absolute desktop positioning so negative monitor coordinates retain their meaning. System DPI scaling is implemented; mixed-DPI hardware behavior is not certified by the scaled captures.

## Elevation & Depth

No custom shadow or animated transition. A thin outline, darker background and lighter rows separate the content. The popup is a borderless, topmost native window.

## Shapes

Rounded shapes are Tk smooth polygons with the frontmatter radius parameters, not CSS rounded rectangles. Shortcut chips are small rounded squares. The tray graphic is a transparent 64 × 64 image containing a state-colored circle and a contrasting microphone. The transparent window key is a rendering implementation detail, not a palette color.

## Components

- **Recovery row:** transcript preview with a numbered chip. Hover changes the row fill and shows the hand cursor. Clicking copies only when press and release occur on the same row. Physical keys 1–9 and 0 select the corresponding entries.
- **Log row:** the same geometry, with an L chip and accent text. Click or physical L opens the full log.
- **Empty row:** muted text without a chip or action. It retains the transcript text alignment.
- **Popup:** Escape or loss of focus closes it. Opening and dismissal do not copy text. There is no implemented Tab-driven row focus indicator or screen-reader semantics for the drawn canvas items; keyboard shortcuts are not a claim of full accessibility.
- **Tray:** colored microphone circle and state tooltip; native context menu. No bespoke settings form or navigation screen exists.

The sidecar describes the native components. Tk source and native captures determine their geometry and behavior.

## Do's and Don'ts

- Do retain the neutral palette, system type and restrained state colors.
- Do keep every transcript and the full-log action reachable when the popup exceeds the work area.
- Do preserve full transcript text behind shortened previews.
- Do preserve gold chips, light-gold links and neutral hovered rows through redraws.
- Don't add decorative marketing imagery or an unrelated product flow.
- Don't treat screenshots, keyboard shortcuts or system-DPI tests as full accessibility or mixed-DPI hardware certification.
