import Cookies from "js-cookie";

import arches from "arches";

import { generateArchesURL } from "@/arches_vue_components/application/generate-arches-url.ts";
import {
    buildFileUploadFormData,
    extractFileEntriesFromAliasedData,
} from "@/arches_vue_components/generics/GenericCard/utils.ts";

import type {
    AliasedResourceData,
    EditHistoryPage,
    ExportFormat,
    RelatedResourceGroup,
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

function resourceUrl(graphSlug: string, resourceInstanceId: string): string {
    return generateArchesURL("arches_querysets:api-resource", {
        graph: graphSlug,
        pk: resourceInstanceId,
    });
}

export async function fetchResource(
    graphSlug: string,
    resourceInstanceId: string,
): Promise<AliasedResourceData> {
    const response = await fetch(resourceUrl(graphSlug, resourceInstanceId));
    return parseResponse<AliasedResourceData>(response);
}

export async function updateResource(
    graphSlug: string,
    resource: AliasedResourceData,
): Promise<AliasedResourceData> {
    const fileEntries = extractFileEntriesFromAliasedData(
        resource.aliased_data,
    );
    const headers: Record<string, string> = {
        "X-CSRFToken": Cookies.get("csrftoken") ?? "",
    };
    let body: BodyInit;
    if (fileEntries.length > 0) {
        body = buildFileUploadFormData(resource, fileEntries);
    } else {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(resource);
    }
    const response = await fetch(
        resourceUrl(graphSlug, resource.resourceinstanceid),
        { method: "PUT", headers, body },
    );
    return parseResponse<AliasedResourceData>(response);
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

export async function fetchRelatedResourceGroups(
    resourceInstanceId: string,
    graphSlugs: string[],
    query: string,
): Promise<RelatedResourceGroup[]> {
    const params = new URLSearchParams({
        graphs: graphSlugs.join(","),
        q: query,
    });
    const response = await fetch(
        `${arches.urls.api_related_resource_groups(resourceInstanceId)}?${params}`,
    );
    const parsed = await parseResponse<{ groups: RelatedResourceGroup[] }>(
        response,
    );
    return parsed.groups;
}

export async function fetchRelatedResourceGroup(
    resourceInstanceId: string,
    graphSlug: string,
    page: number,
    query: string,
): Promise<RelatedResourceGroup> {
    const params = new URLSearchParams({
        graph: graphSlug,
        page: String(page),
        q: query,
    });
    const response = await fetch(
        `${arches.urls.api_related_resource_groups(resourceInstanceId)}?${params}`,
    );
    return parseResponse<RelatedResourceGroup>(response);
}

export async function copyResource(
    resourceInstanceId: string,
): Promise<string> {
    const response = await fetch(
        arches.urls.resource_copy.replace("//", `/${resourceInstanceId}/`),
    );
    const parsed = await parseResponse<{ resourceid: string }>(response);
    return parsed.resourceid;
}

export async function deleteResource(
    resourceInstanceId: string,
): Promise<void> {
    const response = await fetch(
        `${arches.urls.resource_editor}${resourceInstanceId}`,
        {
            method: "DELETE",
            headers: { "X-CSRFToken": Cookies.get("csrftoken") ?? "" },
        },
    );
    await parseResponse<unknown>(response);
}

export function resourceReportUrl(resourceInstanceId: string): string {
    return `${arches.urls.resource_report}${resourceInstanceId}`;
}

export function searchUrl(): string {
    return arches.urls.search_home;
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
