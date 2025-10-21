import arches from "arches";

import Cookies from "js-cookie";

import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";

export const fetchModularReportResource = async ({
    graphSlug,
    resourceId,
    fillBlanks = false,
}: {
    graphSlug: string;
    resourceId: string;
    fillBlanks: boolean;
}) => {
    const params = new URLSearchParams();
    params.append("fill_blanks", fillBlanks.toString());
    const response = await fetch(
        `${arches.urls.api_modular_reports_resource(
            graphSlug,
            resourceId,
        )}?${params}`,
    );
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const updateModularReportResource = async (
    graphSlug: string,
    resourceId: string,
    data: ResourceData,
) => {
    const url = arches.urls.api_modular_reports_resource(graphSlug, resourceId);
    const response = await fetch(url, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken"),
        },
        body: JSON.stringify(data),
    });
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchModularReportTile = async (
    graphSlug: string,
    nodegroupAlias: string,
    tileId: string,
) => {
    const url = arches.urls.api_modular_reports_tile(
        graphSlug,
        nodegroupAlias,
        tileId,
    );
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchNodePresentation = async (resourceId: string) => {
    const url = arches.urls.api_node_presentation(resourceId);
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchReportConfig = async (
    resourceId: string,
    slug: string | undefined,
) => {
    const params = new URLSearchParams();

    if (slug) {
        params.append("slug", slug);
    }
    params.append("resourceId", resourceId);
    const url = `${arches.urls.modular_report_config}?${params.toString()}`;

    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchNodegroup = async (nodegroupId: string) => {
    const url = arches.urls.api_nodegroup(nodegroupId);
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchNodeTileData = async (
    resourceInstanceId: string,
    nodeAliases: string[],
    tileLimit: number,
) => {
    const params = new URLSearchParams();
    nodeAliases.forEach((alias) => params.append("node_alias", alias));
    params.append("tile_limit", tileLimit.toString());

    const response = await fetch(
        `${arches.urls.api_node_tile_data(resourceInstanceId)}?${params}`,
    );
    const parsed = await response.json();

    if (!response.ok) {
        throw new Error(parsed.message || response.statusText);
    }

    return parsed;
};

export const fetchNodegroupTileData = async (
    resourceInstanceId: string,
    nodegroupAlias: string,
    rowsPerPage: number,
    page: number,
    sortNodeId: string | null,
    direction: string | null,
    query: string | null,
    filters: { alias: string; value: string; field_lookup: string }[] | null,
) => {
    const url = arches.urls.api_nodegroup_tile_data(
        resourceInstanceId,
        nodegroupAlias,
    );
    const params = new URLSearchParams({
        rows_per_page: rowsPerPage.toString(),
        page: page.toString(),
        sort_node_id: sortNodeId || "",
        direction: direction || "",
        query: query || "",
        filters: JSON.stringify(filters || []),
    });

    const response = await fetch(url + "?" + params.toString());
    const parsed = await response.json();

    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchRelatedResourceData = async (
    resourceInstanceId: string,
    relatedGraphSlug: string,
    nodeAliases: string[],
    rowsPerPage: number,
    page: number,
    sortField: string,
    direction: string,
    query: string,
) => {
    const url = arches.urls.api_related_resources(
        resourceInstanceId,
        relatedGraphSlug,
    );
    const params = new URLSearchParams({
        node_aliases: nodeAliases.join(","),
        rows_per_page: rowsPerPage.toString(),
        page: page.toString(),
        sort_field: sortField,
        direction,
        query,
    });

    const response = await fetch(url + "?" + params.toString());
    const parsed = await response.json();

    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchCardFromNodegroupId = async (nodegroupId: string) => {
    const url = arches.urls.api_card_from_nodegroup_id(nodegroupId);
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchUserResourcePermissions = async (
    resourceInstanceId: string,
) => {
    const url =
        arches.urls.api_instance_permissions +
        "?resourceinstanceid=" +
        resourceInstanceId;
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchUserPermissions = async (permissions: [string]) => {
    const url = arches.urls.api_has_permissions;
    const params = new URLSearchParams({
        permissions: JSON.stringify(permissions),
    });
    const response = await fetch(url + "?" + params.toString());
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchLanguageSettings = async () => {
    const url = arches.urls.api_client_language_settings;
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};
