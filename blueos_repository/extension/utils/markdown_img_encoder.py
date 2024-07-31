import base64
import math
import re
from io import BytesIO  # pylint: disable=no-name-in-module
from typing import Optional, Tuple

import aiohttp
import markdown
from aiocache import cached
from bs4 import BeautifulSoup
from PIL import Image


class MarkdownImageEncoder:  # pylint: disable=too-few-public-methods
    def __init__(self, markdown_data: str, resource_url: Optional[str] = None) -> None:
        self.markdown_data = markdown_data
        self.resource_url = resource_url + "/" if resource_url else None

    @cached(ttl=3600, namespace="image_encoder")
    async def _fetch_resource(self, url: str) -> Tuple[bytes, str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read(), resp.headers["Content-Type"]

    @cached(ttl=3600, namespace="image_encoder")
    async def _fetch_resource_and_compress(self, url: str) -> Tuple[bytes, str]:
        data, mime_type = await self._fetch_resource(url)

        max_size_bytes = 200 * 1024
        if len(data) <= max_size_bytes:
            return data, mime_type

        if mime_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise ValueError("Data is to big and not compressible")

        image = Image.open(BytesIO(data))
        output = BytesIO()

        def get_scaling_factor(kilo_bytes: int) -> float:
            return math.sqrt(kilo_bytes / 150)

        # Resize the image keeping the aspect ratio and based on how big the image is
        scaling = get_scaling_factor(int(len(data) / 1024))
        image.thumbnail((int(image.width / scaling), int(image.height / scaling)))

        if image.format == "JPEG":
            image.save(output, format=image.format, quality=40, optimize=True)
        else:
            image.save(output, format=image.format, optimize=True)

        return output.getvalue(), mime_type

    async def _convert_image_to_base64(self, url: str) -> str:
        try:
            data, mime_type = await self._fetch_resource_and_compress(url)

            if not mime_type.startswith("image/"):
                return url

            image_data = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{image_data}"
        except Exception:  # pylint: disable=broad-except
            return url

    async def _process_html_images(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img"):
            img_url = img["src"]
            base64_image = await self._convert_image_to_base64(
                img_url if img_url.startswith(("http://", "https://")) else self.resource_url + img_url
            )
            if base64_image:
                img["src"] = base64_image
        return str(soup)

    async def _process_markdown_images(self, markdown_text: str) -> str:
        markdown_image_pattern = r"!\[.*?\]\((.*?)\)"
        matches = re.findall(markdown_image_pattern, markdown_text)
        for match in matches:
            base64_image = await self._convert_image_to_base64(
                match if match.startswith(("http://", "https://")) else self.resource_url + match
            )
            if base64_image:
                markdown_text = markdown_text.replace(match, base64_image)
        return str(markdown_text)

    async def get_processed_markdown(self) -> str:
        html = markdown.markdown(self.markdown_data)

        return str(await self._process_markdown_images(await self._process_html_images(html)))
