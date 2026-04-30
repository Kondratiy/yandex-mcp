"""Yandex Direct ad images tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import GetImagesInput, UploadImageInput, DeleteImagesInput
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register ad image tools."""

    @mcp.tool(
        name="direct_upload_image",
        annotations={
            "title": "Upload Ad Image to Yandex Direct",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_upload_image(params: UploadImageInput) -> str:
        """Upload a base64-encoded image to Yandex Direct.

        Returns AdImageHash which can be used in image ads.
        Supported formats: JPEG, GIF, PNG.
        Image types: REGULAR (min 450x450) or WIDE (min 1080x607).
        """
        try:
            ad_image = {
                "ImageData": params.image_data,
                "Name": params.name,
                "Type": params.image_type.value
            }

            request_params = {"AdImages": [ad_image]}

            result = await api_client.direct_request("adimages", "add", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("AdImageHash"):
                image_hash = add_results[0]["AdImageHash"]
                return (
                    f"Image uploaded successfully!\n"
                    f"AdImageHash: {image_hash}\n"
                    f"Name: {params.name}\n"
                    f"Type: {params.image_type.value}\n\n"
                    f"Use this hash when creating image ads."
                )

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([
                        f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}"
                        for e in r["Errors"]
                    ])

            return f"Failed to upload image:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_images",
        annotations={
            "title": "Get Ad Images from Yandex Direct",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_images(params: GetImagesInput) -> str:
        """Get ad images metadata from Yandex Direct.

        Returns image hashes, names, types, sizes, and association status.
        Use ad_image_hashes to filter by specific images.
        Use associated=YES/NO to filter by whether images are linked to ads.
        """
        try:
            selection_criteria = {}
            if params.ad_image_hashes:
                selection_criteria["AdImageHashes"] = params.ad_image_hashes
            if params.associated:
                selection_criteria["Associated"] = params.associated.value

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["AdImageHash", "Name", "Type", "Subtype", "OriginalUrl", "PreviewUrl", "Associated"],
                "Page": {
                    "Limit": params.limit,
                    "Offset": params.offset
                }
            }

            result = await api_client.direct_request("adimages", "get", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            images = result.get("result", {}).get("AdImages", [])

            if not images:
                return "No ad images found."

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"data": images, "total": len(images)}, indent=2, ensure_ascii=False)

            # Format as markdown
            lines = [f"# Ad Images ({len(images)} found)\n"]
            lines.append("| Hash | Name | Type | Associated |")
            lines.append("|------|------|------|------------|")
            for img in images:
                lines.append(
                    f"| {img.get('AdImageHash', 'N/A')} "
                    f"| {img.get('Name', 'N/A')} "
                    f"| {img.get('Type', 'N/A')} "
                    f"| {img.get('Associated', 'N/A')} |"
                )

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_images",
        annotations={
            "title": "Delete Ad Images from Yandex Direct",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_images(params: DeleteImagesInput) -> str:
        """Delete ad images by their hashes. WARNING: Irreversible.

        Only images not associated with any ad can be deleted.
        Use direct_get_images with associated=NO to find deletable images.
        """
        try:
            request_params = {
                "SelectionCriteria": {
                    "AdImageHashes": params.ad_image_hashes
                }
            }

            result = await api_client.direct_request("adimages", "delete", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [
                r["AdImageHash"] for r in delete_results
                if r.get("AdImageHash") and not r.get("Errors")
            ]
            errors = []
            for r in delete_results:
                if r.get("Errors"):
                    errors.extend([
                        f"Hash {r.get('AdImageHash', '?')}: {e.get('Message')}"
                        for e in r["Errors"]
                    ])

            response = f"Successfully deleted {len(success)} image(s)."
            if success:
                response += "\nDeleted hashes: " + ", ".join(success)
            if errors:
                response += f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors)

            return response

        except Exception as e:
            return handle_api_error(e)
