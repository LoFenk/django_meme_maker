# Changelog

All notable changes to django-meme-maker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-12-13

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

