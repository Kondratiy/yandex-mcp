"""Yandex Metrika labels, annotations, and delegates tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika_extended import (
    GetLabelsInput,
    CreateLabelInput,
    UpdateLabelInput,
    DeleteLabelInput,
    LinkCounterToLabelInput,
    GetAnnotationsInput,
    CreateAnnotationInput,
    UpdateAnnotationInput,
    DeleteAnnotationInput,
    GetDelegatesInput,
    AddDelegateInput,
    DeleteDelegateInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register labels, annotations, and delegates tools."""

    # =========================================================================
    # Labels
    # =========================================================================

    @mcp.tool(
        name="metrika_get_labels",
        annotations={
            "title": "Get Yandex Metrika Labels",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_labels(params: GetLabelsInput) -> str:
        """Get all labels for organizing counters.

        Labels help group and organize multiple Metrika counters.
        """
        try:
            result = await api_client.metrika_request("management/v1/labels")
            labels = result.get("labels", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"labels": labels, "total": len(labels)}, indent=2, ensure_ascii=False)

            if not labels:
                return "No labels found."

            lines = ["# Metrika Labels\n"]
            for label in labels:
                lines.append(f"- **{label.get('name')}** (ID: {label.get('id')})")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_create_label",
        annotations={
            "title": "Create Yandex Metrika Label",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_create_label(params: CreateLabelInput) -> str:
        """Create a new label for organizing counters."""
        try:
            result = await api_client.metrika_request(
                "management/v1/labels",
                method="POST",
                json_data={"label": {"name": params.name}}
            )

            label = result.get("label", {})
            if label.get("id"):
                return f"Label created successfully.\nID: {label['id']}\nName: {label.get('name')}"

            return f"Failed to create label. Response: {json.dumps(result, ensure_ascii=False)}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_label",
        annotations={
            "title": "Update Yandex Metrika Label",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_label(params: UpdateLabelInput) -> str:
        """Update a label's name."""
        try:
            result = await api_client.metrika_request(
                f"management/v1/label/{params.label_id}",
                method="PUT",
                json_data={"label": {"name": params.name}}
            )

            label = result.get("label", {})
            return f"Label {params.label_id} updated. New name: {label.get('name', params.name)}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_label",
        annotations={
            "title": "Delete Yandex Metrika Label",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_delete_label(params: DeleteLabelInput) -> str:
        """Delete a label.

        Counters linked to this label will be unlinked but not deleted.
        """
        try:
            await api_client.metrika_request(
                f"management/v1/label/{params.label_id}",
                method="DELETE"
            )
            return f"Label {params.label_id} deleted successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_link_counter_to_label",
        annotations={
            "title": "Link Counter to Label",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_link_counter_to_label(params: LinkCounterToLabelInput) -> str:
        """Link a counter to a label for organization."""
        try:
            await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/label/{params.label_id}",
                method="POST"
            )
            return f"Counter {params.counter_id} linked to label {params.label_id}."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_unlink_counter_from_label",
        annotations={
            "title": "Unlink Counter from Label",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_unlink_counter_from_label(params: LinkCounterToLabelInput) -> str:
        """Unlink a counter from a label."""
        try:
            await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/label/{params.label_id}",
                method="DELETE"
            )
            return f"Counter {params.counter_id} unlinked from label {params.label_id}."

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # Chart Annotations
    # =========================================================================

    @mcp.tool(
        name="metrika_get_annotations",
        annotations={
            "title": "Get Yandex Metrika Chart Annotations",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_annotations(params: GetAnnotationsInput) -> str:
        """Get chart annotations for a counter.

        Annotations mark important events on Metrika charts.
        """
        try:
            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/chart_annotations"
            )
            annotations = result.get("annotations", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"annotations": annotations, "total": len(annotations)}, indent=2, ensure_ascii=False)

            if not annotations:
                return "No chart annotations found."

            lines = ["# Chart Annotations\n"]
            for ann in annotations:
                lines.append(f"## {ann.get('title', 'Untitled')} (ID: {ann.get('id')})")
                lines.append(f"- **Date**: {ann.get('date', 'N/A')}")
                if ann.get('message'):
                    lines.append(f"- **Message**: {ann['message']}")
                if ann.get('group'):
                    lines.append(f"- **Group**: {ann['group']}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_create_annotation",
        annotations={
            "title": "Create Yandex Metrika Chart Annotation",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_create_annotation(params: CreateAnnotationInput) -> str:
        """Create a chart annotation to mark an important event.

        Useful for marking promotions, site changes, technical issues, etc.
        """
        try:
            annotation_data = {
                "date": params.date,
                "title": params.title
            }
            if params.message:
                annotation_data["message"] = params.message
            if params.group:
                annotation_data["group"] = params.group

            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/chart_annotation",
                method="POST",
                json_data={"annotation": annotation_data}
            )

            annotation = result.get("annotation", {})
            if annotation.get("id"):
                return f"Annotation created successfully.\nID: {annotation['id']}\nDate: {params.date}\nTitle: {params.title}"

            return f"Failed to create annotation. Response: {json.dumps(result, ensure_ascii=False)}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_annotation",
        annotations={
            "title": "Update Yandex Metrika Chart Annotation",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_annotation(params: UpdateAnnotationInput) -> str:
        """Update a chart annotation."""
        try:
            annotation_data = {}
            if params.title:
                annotation_data["title"] = params.title
            if params.message is not None:
                annotation_data["message"] = params.message

            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/chart_annotation/{params.annotation_id}",
                method="PUT",
                json_data={"annotation": annotation_data}
            )

            return f"Annotation {params.annotation_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_annotation",
        annotations={
            "title": "Delete Yandex Metrika Chart Annotation",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_delete_annotation(params: DeleteAnnotationInput) -> str:
        """Delete a chart annotation."""
        try:
            await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/chart_annotation/{params.annotation_id}",
                method="DELETE"
            )
            return f"Annotation {params.annotation_id} deleted successfully."

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # Delegates
    # =========================================================================

    @mcp.tool(
        name="metrika_get_delegates",
        annotations={
            "title": "Get Yandex Metrika Delegates",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_delegates(params: GetDelegatesInput) -> str:
        """Get list of delegates who have access to your counters.

        Delegates can view and manage counters on your behalf.
        """
        try:
            result = await api_client.metrika_request("management/v1/delegates")
            delegates = result.get("delegates", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"delegates": delegates, "total": len(delegates)}, indent=2, ensure_ascii=False)

            if not delegates:
                return "No delegates found."

            lines = ["# Metrika Delegates\n"]
            for delegate in delegates:
                lines.append(f"- **{delegate.get('user_login', 'Unknown')}**")
                if delegate.get('comment'):
                    lines.append(f"  - Comment: {delegate['comment']}")
                if delegate.get('created_at'):
                    lines.append(f"  - Added: {delegate['created_at']}")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_add_delegate",
        annotations={
            "title": "Add Yandex Metrika Delegate",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_add_delegate(params: AddDelegateInput) -> str:
        """Add a delegate who can access your counters.

        The delegate will be able to view and manage all your counters.
        """
        try:
            delegate_data = {"user_login": params.user_login}
            if params.comment:
                delegate_data["comment"] = params.comment

            result = await api_client.metrika_request(
                "management/v1/delegates",
                method="POST",
                json_data={"delegate": delegate_data}
            )

            return f"Delegate {params.user_login} added successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_delegate",
        annotations={
            "title": "Delete Yandex Metrika Delegate",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_delete_delegate(params: DeleteDelegateInput) -> str:
        """Remove a delegate's access to your counters."""
        try:
            await api_client.metrika_request(
                f"management/v1/delegate/{params.user_login}",
                method="DELETE"
            )
            return f"Delegate {params.user_login} removed successfully."

        except Exception as e:
            return handle_api_error(e)
