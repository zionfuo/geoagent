"""Image insertion into article content at paragraph intervals."""
import re


def insert_images_by_paragraph_interval(
    content: str,
    markdown_images: list[str]
) -> str:
    """Insert images evenly distributed across paragraphs.

    Algorithm:
    1. Split content on double newlines (\n\n) to get paragraphs
    2. interval = floor(paragraphCount / (imageCount + 1))
    3. Insert image after paragraph when nextParagraphPosition % interval == 0
    4. Images format: ![alt](url) Markdown syntax
    """
    if not markdown_images:
        return content

    paragraphs = re.split(r'\n{2,}', content)
    if not paragraphs:
        return content

    paragraph_count = len(paragraphs)
    image_count = len(markdown_images)
    interval = max(1, paragraph_count // (image_count + 1))

    parts = []
    image_index = 0

    for i, para in enumerate(paragraphs):
        parts.append(para.strip())
        next_pos = i + 1

        if (
            image_index < image_count
            and next_pos % interval == 0
            and next_pos < paragraph_count
        ):
            parts.append(markdown_images[image_index])
            image_index += 1

    # Append any remaining images at the end
    while image_index < image_count:
        parts.append(markdown_images[image_index])
        image_index += 1

    return '\n\n'.join(parts)


def markdown_image(url: str, alt: str = "image") -> str:
    """Format a Markdown image tag."""
    return f"![{alt}]({url})"


def select_images_random(conn, library_id: int, image_count: int) -> list[dict]:
    """Select random images from an image library.

    Returns list of dicts with id, file_path, original_name.
    """
    rows = conn.execute(
        "SELECT id, file_path, original_name FROM images WHERE library_id = ? ORDER BY RANDOM() LIMIT ?",
        (library_id, image_count)
    ).fetchall()
    return [dict(row) for row in rows]
