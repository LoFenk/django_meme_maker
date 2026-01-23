/* Meme Maker Editor */
(function() {
    'use strict';

    function initEditor() {
        var topTextInput = document.getElementById('id_top_text');
        var bottomTextInput = document.getElementById('id_bottom_text');
        var textColorInput = document.getElementById('id_text_color');
        var strokeColorInput = document.getElementById('id_stroke_color');
        var fontSizeInput = document.getElementById('id_font_size');
        var uppercaseInput = document.getElementById('id_uppercase');
        var fontSizeDisplay = document.getElementById('font-size-display');
        var previewTopText = document.getElementById('preview-top-text');
        var previewBottomText = document.getElementById('preview-bottom-text');
        var previewImage = document.getElementById('preview-image');
        var overlaysField = document.getElementById('text-overlays-json');
        var editorForm = document.getElementById('meme-editor-form');

        if (!topTextInput || !previewImage) return; // Not on editor page

        function updatePreview() {
            var topText = topTextInput.value;
            var bottomText = bottomTextInput.value;

            if (uppercaseInput && uppercaseInput.checked) {
                topText = topText.toUpperCase();
                bottomText = bottomText.toUpperCase();
            }

            if (previewTopText) previewTopText.textContent = topText;
            if (previewBottomText) previewBottomText.textContent = bottomText;

            var textColor = textColorInput ? textColorInput.value : '#FFFFFF';
            var strokeColor = strokeColorInput ? strokeColorInput.value : '#000000';
            var fontSize = fontSizeInput ? (parseInt(fontSizeInput.value) || 48) : 48;
            var strokeWidth = Math.max(2, Math.floor(fontSize / 16));

            var textShadow = strokeWidth + 'px ' + strokeWidth + 'px 0 ' + strokeColor + ',' +
                '-' + strokeWidth + 'px -' + strokeWidth + 'px 0 ' + strokeColor + ',' +
                strokeWidth + 'px -' + strokeWidth + 'px 0 ' + strokeColor + ',' +
                '-' + strokeWidth + 'px ' + strokeWidth + 'px 0 ' + strokeColor + ',' +
                '0 ' + strokeWidth + 'px 0 ' + strokeColor + ',' +
                strokeWidth + 'px 0 0 ' + strokeColor + ',' +
                '0 -' + strokeWidth + 'px 0 ' + strokeColor + ',' +
                '-' + strokeWidth + 'px 0 0 ' + strokeColor + ',' +
                '0 ' + (strokeWidth + 3) + 'px 6px rgba(0,0,0,0.5)';

            if (previewTopText) {
                previewTopText.style.color = textColor;
                previewTopText.style.textShadow = textShadow;
            }
            if (previewBottomText) {
                previewBottomText.style.color = textColor;
                previewBottomText.style.textShadow = textShadow;
            }

            var previewWidth = previewImage.offsetWidth || 500;
            var scaleFactor = previewWidth / 800;
            var scaledFontSize = Math.max(12, Math.round(fontSize * scaleFactor));
            
            // Force width to exactly 90% of image width (matching Pillow's wrap behavior)
            // NOTE: max-width alone doesn't work because position:absolute elements
            // shrink-to-fit their content. We must set explicit width.
            var textWidth = Math.round(previewWidth * 0.9) + 'px';

            if (previewTopText) {
                previewTopText.style.fontSize = scaledFontSize + 'px';
                previewTopText.style.width = textWidth;
                previewTopText.style.maxWidth = 'none';
            }
            if (previewBottomText) {
                previewBottomText.style.fontSize = scaledFontSize + 'px';
                previewBottomText.style.width = textWidth;
                previewBottomText.style.maxWidth = 'none';
            }

            if (fontSizeDisplay) fontSizeDisplay.textContent = fontSize;

            var textTransform = (uppercaseInput && uppercaseInput.checked) ? 'uppercase' : 'none';
            if (previewTopText) previewTopText.style.textTransform = textTransform;
            if (previewBottomText) previewBottomText.style.textTransform = textTransform;
        }

        function buildOverlaysPayload() {
            var overlays = [];
            var textColor = textColorInput ? textColorInput.value : '#FFFFFF';
            var strokeColor = strokeColorInput ? strokeColorInput.value : '#000000';
            var fontSize = fontSizeInput ? (parseInt(fontSizeInput.value) || 48) : 48;
            var uppercase = uppercaseInput ? uppercaseInput.checked : true;
            var topText = topTextInput.value.trim();
            var bottomText = bottomTextInput ? bottomTextInput.value.trim() : '';
            var previewWidth = previewImage.offsetWidth || 800;
            var previewHeight = previewImage.offsetHeight || 0;

            if (topText) {
                overlays.push({
                    text: topText,
                    position: 'top',
                    color: textColor,
                    stroke_color: strokeColor,
                    font_size: fontSize,
                    uppercase: uppercase
                });
            }
            if (bottomText) {
                overlays.push({
                    text: bottomText,
                    position: 'bottom',
                    color: textColor,
                    stroke_color: strokeColor,
                    font_size: fontSize,
                    uppercase: uppercase
                });
            }

            return {
                overlays: overlays,
                meta: {
                    preview_width: previewWidth,
                    preview_height: previewHeight
                }
            };
        }

        topTextInput.addEventListener('input', updatePreview);
        if (bottomTextInput) bottomTextInput.addEventListener('input', updatePreview);
        if (textColorInput) textColorInput.addEventListener('input', updatePreview);
        if (strokeColorInput) strokeColorInput.addEventListener('input', updatePreview);
        if (fontSizeInput) fontSizeInput.addEventListener('input', updatePreview);
        if (uppercaseInput) uppercaseInput.addEventListener('change', updatePreview);

        window.addEventListener('resize', updatePreview);
        previewImage.addEventListener('load', updatePreview);

        updatePreview();
        setTimeout(updatePreview, 100);

        if (editorForm && overlaysField) {
            editorForm.addEventListener('submit', function () {
                try {
                    if (overlaysField.value) {
                        var parsed = JSON.parse(overlaysField.value);
                        if (parsed && typeof parsed === 'object') {
                            parsed.meta = parsed.meta || {};
                            parsed.meta.preview_width = previewImage.offsetWidth || 800;
                            parsed.meta.preview_height = previewImage.offsetHeight || 0;
                            overlaysField.value = JSON.stringify(parsed);
                            return;
                        }
                    }
                } catch (e) {
                    // Fall through to rebuild payload
                }
                overlaysField.value = JSON.stringify(buildOverlaysPayload());
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEditor);
    } else {
        initEditor();
    }
})();
