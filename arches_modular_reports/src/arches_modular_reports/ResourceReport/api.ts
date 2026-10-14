import Cookies from "js-cookie";

import arches from "arches";

import type {
    EditHistoryPage,
    ExportFormat,
    ReportContext,
} from "@/arches_modular_reports/ResourceReport/types.ts";

async function parseResponse<ResponseBody>(
    response: Response,
): Promise<ResponseBody> {
    const parsed = await response.json();
    if (!response.ok) {
        throw new Error(parsed.message || response.statusText);
    }
    return parsed;
}

export async function fetchReportContext(
    resourceInstanceId: string,
): Promise<ReportContext> {
    const response = await fetch(
        arches.urls.api_report_context(resourceInstanceId),
    );
    return parseResponse<ReportContext>(response);
}

export async function fetchEditHistory(
    resourceInstanceId: string,
    page: number,
    query: string,
): Promise<EditHistoryPage> {
    const params = new URLSearchParams({ page: String(page), q: query });
    const response = await fetch(
        `${arches.urls.api_edit_history(resourceInstanceId)}?${params}`,
    );
    return parseResponse<EditHistoryPage>(response);
}

export async function updateLifecycleState(
    resourceInstanceId: string,
    lifecycleStateId: string,
): Promise<void> {
    const response = await fetch(
        arches.urls.api_resource_instance_lifecycle_state(resourceInstanceId),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") ?? "",
            },
            body: JSON.stringify(lifecycleStateId),
        },
    );
    await parseResponse<unknown>(response);
}

export function buildExportUrl(
    resourceInstanceId: string,
    exportFormat: ExportFormat,
): string {
    if (exportFormat === "json-ld") {
        return `${arches.urls.api_resources(resourceInstanceId)}?format=json-ld`;
    }
    if (exportFormat === "json") {
        return `${arches.urls.api_resources(resourceInstanceId)}?format=json&v=beta`;
    }
    const searchParams = new URLSearchParams({
        format: "tilecsv",
        total: "1",
        "term-filter": JSON.stringify([
            {
                inverted: false,
                type: "string",
                context: "",
                context_label: "",
                id: resourceInstanceId,
                value: resourceInstanceId,
                selected: true,
            },
        ]),
    });
    return `${arches.urls.export_results}?${searchParams.toString()}`;
}
