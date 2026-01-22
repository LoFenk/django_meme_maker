# Project Intent

This package is designed to be used in other Django projects in two primary modes:

1) Embed mode: use the built-in templates and front end, optionally themed and scoped,
   while inheriting a host project's base template.
2) Backend-only mode: use the models, views, and APIs while supplying a fully custom UI.

The goal is flexibility: a full ready-to-use UI for fast integration, plus clean
backend primitives that allow custom frontends without fighting the package.

# Known Issues / Follow-ups

1) Admin still references legacy fields removed from the Meme model. Update admin
   to match the current schema and remove leftover "legacy" messaging.
2) JS assets are loaded in both the base template and child templates, which can
   cause duplicate event handlers (e.g., rating). Consolidate to one path.
3) Flagging endpoints do not enforce linked-object scoping. Decide whether scoped
   access should apply to flags and align with detail/download/rate rules.
4) CONTENT_BLOCK_NAME is defined but unused; templates still hardcode the
   "content" block. Either implement or remove to avoid confusion.
5) CBV list views do not annotate unflagged meme counts used by templates;
   align CBVs with function views for parity.
6) The meme_maker_css template tag is out of sync with static CSS/themes and
   may not reflect the current frontend. Decide whether to update or deprecate.
7) Theme sets are full template copies. Consider a lighter override mechanism
   or shared base/partials to reduce drift.
