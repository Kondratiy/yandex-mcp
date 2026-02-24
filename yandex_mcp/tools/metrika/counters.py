"""Yandex Metrika counter tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika import (
    GetCountersInput,
    GetCounterInput,
    CreateCounterInput,
    UpdateCounterInput,
)
from ...formatters.metrika import format_metrika_counters_markdown
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register counter tools."""

    @mcp.tool(
        name="metrika_get_counters",
        annotations={
            "title": "Get Yandex Metrika Counters",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_counters(params: GetCountersInput) -> str:
        """Get list of Metrika counters (tags).

        Retrieves all counters accessible to the user.
        """
        try:
            query_params = {}
            if params.favorite is not None:
                query_params["favorite"] = str(params.favorite).lower()
            if params.search_string:
                query_params["search_string"] = params.search_string

            result = await api_client.metrika_request(
                "/management/v1/counters",
                params=query_params
            )

            counters = result.get("counters", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"counters": counters, "total": result.get("rows", len(counters))}, indent=2, ensure_ascii=False)

            return format_metrika_counters_markdown(counters)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_get_counter",
        annotations={
            "title": "Get Yandex Metrika Counter Details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_counter(params: GetCounterInput) -> str:
        """Get detailed information about a specific counter.

        Retrieves full counter settings including code options, webvisor, and grants.
        """
        try:
            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}"
            )

            counter = result.get("counter", {})

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(counter, indent=2, ensure_ascii=False)

            lines = [f"# Counter: {counter.get('name', 'Unnamed')} (ID: {counter.get('id')})"]
            lines.append(f"\n## Basic Info")
            lines.append(f"- **Site**: {counter.get('site2', {}).get('site', 'N/A')}")
            lines.append(f"- **Status**: {counter.get('status', 'N/A')}")
            lines.append(f"- **Code Status**: {counter.get('code_status', 'N/A')}")
            lines.append(f"- **Owner**: {counter.get('owner_login', 'N/A')}")
            lines.append(f"- **Created**: {counter.get('create_time', 'N/A')}")

            if counter.get("webvisor"):
                webvisor = counter["webvisor"]
                lines.append(f"\n## Webvisor")
                lines.append(f"- **Version**: {webvisor.get('wv_version', 'N/A')}")
                lines.append(f"- **Enabled**: {webvisor.get('arch_enabled', False)}")

            goals = counter.get("goals", [])
            if goals:
                lines.append(f"\n## Goals ({len(goals)})")
                for goal in goals[:10]:
                    lines.append(f"- {goal.get('name', 'Unnamed')} (ID: {goal.get('id')})")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_create_counter",
        annotations={
            "title": "Create Yandex Metrika Counter",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_create_counter(params: CreateCounterInput) -> str:
        """Create a new Metrika counter.

        Creates a counter for tracking website statistics.
        """
        try:
            data = {
                "counter": {
                    "name": params.name,
                    "site2": {"site": params.site}
                }
            }

            result = await api_client.metrika_request(
                "/management/v1/counters",
                method="POST",
                data=data
            )

            counter = result.get("counter", {})
            counter_id = counter.get('id')

            return f"""Counter created successfully!

**ID**: {counter_id}
**Name**: {counter.get('name')}
**Site**: {counter.get('site2', {}).get('site')}

Add this tracking code to your website:
```html
<!-- Yandex.Metrika counter -->
<script type="text/javascript">
   (function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
   m[i].l=1*new Date();
   for (var j = 0; j < document.scripts.length; j++) {{if (document.scripts[j].src === r) {{ return; }}}}
   k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
   (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

   ym({counter_id}, "init", {{
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true
   }});
</script>
```"""

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_counter",
        annotations={
            "title": "Update Yandex Metrika Counter",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_counter(params: UpdateCounterInput) -> str:
        """Update a Metrika counter settings.

        Allows updating counter name, site, and favorite status.
        """
        try:
            counter_update = {}

            if params.name:
                counter_update["name"] = params.name
            if params.site:
                counter_update["site2"] = {"site": params.site}
            if params.favorite is not None:
                counter_update["favorite"] = params.favorite

            if not counter_update:
                return "No fields specified for update."

            data = {"counter": counter_update}

            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}",
                method="PUT",
                data=data
            )

            return f"Counter {params.counter_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_counter",
        annotations={
            "title": "Delete Yandex Metrika Counter",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_delete_counter(params: GetCounterInput) -> str:
        """Delete a Metrika counter.

        WARNING: This action is irreversible. All historical data will be lost.
        """
        try:
            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}",
                method="DELETE"
            )

            return f"Counter {params.counter_id} deleted successfully."

        except Exception as e:
            return handle_api_error(e)
