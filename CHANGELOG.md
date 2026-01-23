# Changelog

All notable changes to django-meme-maker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.2] - 2026-01-22

### Added
- **Bundled fallback font**: Anton font (open-source Impact alternative) bundled for servers without Impact installed
- **Custom font setting**: New `MEME_MAKER['FONT_PATH']` setting to specify a custom .ttf font for meme text rendering

### Fixed
- **Text size mismatch**: Fixed preview text appearing different size than generated meme image
  - Preview metadata (`preview_width`) is now properly preserved through form submission
  - Pillow image generation now uses actual preview dimensions for accurate font scaling
- **Font availability**: Image generation no longer falls back to tiny default font when Impact is unavailable

### Changed
- **Font loading priority**: Custom font → System Impact → Bundled Anton → Pillow default
- Form method `get_overlays()` now has companion `get_overlays_with_meta()` for accessing preview dimensions

## [1.3.1] - 2026-01-22

### Added
- **Template sets**: Built-in themed frontends (`compact`, `modern`, `tech`, `classic`) with selectable `TEMPLATE_SET`
- **Custom base guidance**: Documented how to apply theme classes when using a custom `BASE_TEMPLATE`

### Changed
- **Theme selection**: `TEMPLATE_SET` now selects the themed base template unless `BASE_TEMPLATE` is explicitly set
- **Custom base assets**: Added a shared `extra_head` partial to inject CSS only for custom base templates
- **Browse cards**: Added top padding to card image blocks to avoid flush alignment

## [1.3.0] - 2026-01-22

### Added
- **Linked object resolver**: Optional `MEME_MAKER['LINKED_OBJECT_RESOLVER']` hook to auto-link and scope templates/memes by request context
- **Scoped access enforcement**: Detail, download, and rating endpoints now 404 when scoped objects are not linked
- **Per-page controls**: Pagination with 10/25/50 per-page selector for template and meme lists
- **NSFW flags**: `nsfw` fields for templates and memes, exposed in forms and admin
- **Flagging system**: User flagging with daily limit, admin flags view, and removal from circulation
- **Template meme filters**: "Memes using this template" with Recent/Best/Popular/Worst/Random sorting and AJAX refresh

### Changed
- **Breaking**: Removed legacy direct-upload workflow, URLs, forms, and fields (`image`, `top_text`, `bottom_text`)
- **Detail displays**: Use overlays-only rendering for memes, no legacy text fallbacks
- **Template counts**: Count only unflagged memes in template displays

### Fixed
- **Resolver performance**: Cached linked object resolver result per request
- **Scoped downloads/ratings**: Prevented cross-scope access by ID

## [1.2.4] - 2026-01-06

### Changed
- **Thumbnail display**: Changed from `object-fit: cover` (crop) to `object-fit: contain` (letterbox/pillarbox) for card images
- Thumbnails now show entire image with grey bars on sides/top-bottom instead of cropping

### Fixed
- **Storage compatibility**: Removed hardcoded `default_storage` from ImageField definitions to support both local media and S3 storage backends

## [1.2.3] - 2026-01-06

### Added
- **Navigation Partial**: Created `partials/nav.html` for navigation and messages
- All child templates now include nav partial for custom base template support

### Fixed
- Navigation menu now displays when using custom `BASE_TEMPLATE`
- Messages/alerts now display when using custom `BASE_TEMPLATE`

## [1.2.2] - 2026-01-06

### Fixed
- **Custom Base Template Support**: All child templates now include CSS/JS via `{% block extra_head %}` and `{% block extra_js %}`
- Static assets now load correctly when using custom `BASE_TEMPLATE` setting
- Updated documentation with required template blocks (`extra_head`, `extra_js`, `content`)

## [1.2.1] - 2026-01-05

### Added
- **CSP Nonce Support**: Templates now check for `CSP_NONCE` context variable
- Automatic nonce attributes on script/style tags when using django-csp
- CSP documentation section in README

### Changed
- Script and style tags now include `{% if CSP_NONCE %}nonce="{{ CSP_NONCE }}"{% endif %}`


## [1.2.0] - 2026-01-05

### Changed
- **CSP Compliance**: Moved all CSS and JavaScript to static files
- CSS now served from `meme_maker/static/meme_maker/css/meme_maker.css`
- Rating JS moved to `meme_maker/static/meme_maker/js/rating.js`
- Editor JS moved to `meme_maker/static/meme_maker/js/editor.js`
- Sort utility JS added to `meme_maker/static/meme_maker/js/utils.js`
- Simplified and consolidated CSS (reduced from ~650 lines inline to ~180 lines)
- Only dynamic CSS variables (colors) remain inline when customized

## [1.1.0] - 2025-12-13

### Added
- **Template Bank**: Searchable library of meme templates
- **MemeTemplate Model**: Store reusable template images with titles and tags
- **Template Search**: Search templates by title and tags using `icontains` (database-agnostic)
- **Template Upload**: Users can upload new templates with title and tags
- **Meme Editor**: Interactive editor for creating memes from templates
- **Text Overlays**: JSON-based text overlay system with positioning, colors, fonts
- **Image Generation**: Automatic composite image generation using Pillow
- **Download Endpoints**: Download both templates and generated memes
- **Live Preview**: JavaScript-powered real-time preview in editor
- **Styling Options**: Color pickers, font size slider, uppercase toggle

### Changed
- Updated `Meme` model to support template-based creation
- Added `text_overlays` JSONField for flexible text positioning
- Added `generated_image` field for pre-rendered composite images
- Updated navigation to include template bank workflow
- Home page now redirects to template list instead of create page

### Deprecated
- Direct image upload workflow (still supported but template bank is preferred)

### Fixed
- Backward compatibility maintained for existing memes
- Legacy fields (`image`, `top_text`, `bottom_text`) preserved

## [1.0.0] - 2024-12-12

### Added
- Initial release
- Basic meme creation with image upload
- Top and bottom text support
- Customizable themes and embeddable templates
- Storage-agnostic file handling
- Template tags and components
- Context processors for settings
