import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application/generate-arches-url.ts";
import {
    buildFileUploadFormData,
    extractFileEntriesFromAliasedData,
} from "@/arches_vue_components/generics/GenericCard/utils.ts";

import type {
    AliasedResourceData,
    EditHistoryPage,
    ExportFormat,
    ImageSource,
    RelatedResourceGroup,
    ReportContext,
    ResourceImagesPage,
} from "@/arches_modular_reports/ResourceReport/types.ts";

async function parseResponse<ResponseBody>(
    response: Response,
): Promise<ResponseBody> {
    if (response.ok) {
        return response.json();
    }
    if (response.headers.get("Content-Type")?.startsWith("application/json")) {
        const parsed = await response.json();
        throw new Error(parsed.message || response.statusText);
    }
    throw new Error(response.statusText);
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
        generateArchesURL("arches_modular_reports:api_report_context", {
            resourceid: resourceInstanceId,
        }),
    );
    return parseResponse<ReportContext>(response);
}

export async function fetchEditHistory(
    resourceInstanceId: string,
    cursor: string | null,
    query: string,
): Promise<EditHistoryPage> {
    const queryParameters: Record<string, string> = { q: query };
    if (cursor !== null) {
        queryParameters.after = cursor;
    }
    const response = await fetch(
        generateArchesURL(
            "arches_modular_reports:api_edit_history",
            { resourceid: resourceInstanceId },
            queryParameters,
        ),
    );
    return parseResponse<EditHistoryPage>(response);
}

export async function fetchRelatedResourceGroups(
    resourceInstanceId: string,
    graphSlugs: string[],
    query: string,
): Promise<RelatedResourceGroup[]> {
    const response = await fetch(
        generateArchesURL(
            "arches_modular_reports:api_related_resource_groups",
            { resourceid: resourceInstanceId },
            { graphs: graphSlugs.join(","), q: query },
        ),
    );
    const parsed = await parseResponse<{ groups: RelatedResourceGroup[] }>(
        response,
    );
    return parsed.groups;
}

export async function fetchRelatedResourceGroup(
    resourceInstanceId: string,
    graphSlug: string,
    cursor: string | null,
    query: string,
): Promise<RelatedResourceGroup> {
    const queryParameters: Record<string, string> = {
        graph: graphSlug,
        q: query,
    };
    if (cursor !== null) {
        queryParameters.after = cursor;
    }
    const response = await fetch(
        generateArchesURL(
            "arches_modular_reports:api_related_resource_groups",
            { resourceid: resourceInstanceId },
            queryParameters,
        ),
    );
    return parseResponse<RelatedResourceGroup>(response);
}

export async function fetchResourceImages(
    resourceInstanceId: string,
    imageSources: ImageSource[],
    cursor: string | null,
): Promise<ResourceImagesPage> {
    const queryParameters: Record<string, string> = {
        sources: imageSources
            .map((imageSource) => `${imageSource.model}:${imageSource.node}`)
            .join(","),
    };
    if (cursor !== null) {
        queryParameters.after = cursor;
    }
    const response = await fetch(
        generateArchesURL(
            "arches_modular_reports:api_resource_images",
            { resourceid: resourceInstanceId },
            queryParameters,
        ),
    );
    return parseResponse<ResourceImagesPage>(response);
}

export async function copyResource(
    resourceInstanceId: string,
): Promise<string> {
    const response = await fetch(
        generateArchesURL("arches:resource_copy", {
            resourceid: resourceInstanceId,
        }),
    );
    const parsed = await parseResponse<{ resourceid: string }>(response);
    return parsed.resourceid;
}

export async function deleteResource(
    resourceInstanceId: string,
): Promise<void> {
    const response = await fetch(
        generateArchesURL("arches:resource_editor", {
            resourceid: resourceInstanceId,
        }),
        {
            method: "DELETE",
            headers: { "X-CSRFToken": Cookies.get("csrftoken") ?? "" },
        },
    );
    await parseResponse<unknown>(response);
}

export function resourceReportUrl(resourceInstanceId: string): string {
    return generateArchesURL("arches:resource_report", {
        resourceid: resourceInstanceId,
    });
}

export function searchUrl(): string {
    return generateArchesURL("arches:search_home");
}

export async function updateLifecycleState(
    resourceInstanceId: string,
    lifecycleStateId: string,
): Promise<void> {
    const response = await fetch(
        generateArchesURL("arches:api_resource_instance_lifecycle_state", {
            resourceid: resourceInstanceId,
        }),
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
        return generateArchesURL(
            "arches:resources",
            { resourceid: resourceInstanceId },
            { format: "json-ld" },
        );
    }
    if (exportFormat === "json") {
        return generateArchesURL(
            "arches:resources",
            { resourceid: resourceInstanceId },
            { format: "json", v: "beta" },
        );
    }
    return generateArchesURL(
        "arches:export_results",
        {},
        {
            format: "tilecsv",
            total: 1,
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
        },
    );
}
