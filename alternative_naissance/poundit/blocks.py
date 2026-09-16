"""
Presentation blocks for Pound It.

Deliberately small. ``core`` already has a rich block library, but its labels
are French and its templates carry Alternative Naissance's markup and classes,
so reusing them would pull that site's presentation into this one. These follow
the same conventions — StructBlock with an inner Meta carrying icon, label and
template — and Codex owns the templates.
"""

from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True)
    level = blocks.ChoiceBlock(
        choices=[("h2", "Heading 2"), ("h3", "Heading 3"), ("h4", "Heading 4")],
        default="h2",
    )

    class Meta:
        icon = "title"
        label = "Heading"
        template = "poundit/blocks/heading_block.html"


class RichTextBlock(blocks.RichTextBlock):
    class Meta:
        icon = "pilcrow"
        label = "Text"
        template = "poundit/blocks/rich_text_block.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False)
    full_bleed = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Let the image run the full width of the page.",
    )

    class Meta:
        icon = "image"
        label = "Image"
        template = "poundit/blocks/image_block.html"


class GalleryBlock(blocks.StructBlock):
    images = blocks.ListBlock(ImageChooserBlock())

    class Meta:
        icon = "image"
        label = "Gallery"
        template = "poundit/blocks/gallery_block.html"


class VideoEmbedBlock(blocks.StructBlock):
    embed = EmbedBlock(required=True)
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "media"
        label = "Video"
        template = "poundit/blocks/video_embed_block.html"


class CTASectionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    text = blocks.TextBlock(required=False)
    button_label = blocks.CharBlock(required=False)
    button_url = blocks.CharBlock(
        required=False,
        help_text="Leave empty to fall back to the studio-wide registration URL.",
    )

    class Meta:
        icon = "link"
        label = "Call to action"
        template = "poundit/blocks/cta_section_block.html"


#: The body StreamField every Pound It page uses. One list, one place to extend.
CONTENT_BLOCKS = [
    ("heading", HeadingBlock()),
    ("rich_text", RichTextBlock()),
    ("image", ImageBlock()),
    ("gallery", GalleryBlock()),
    ("video", VideoEmbedBlock()),
    ("cta", CTASectionBlock()),
]
