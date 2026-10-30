import arches from "arches";

export const fetchGraphSlugFromId = async (graphId: string) => {
    const url = arches.urls.api_graph_slug(graphId);
    const response = await fetch(url);
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
        params.append("report_config_slug", slug);
    }
    params.append("resourceId", resourceId);
    const url = `${arches.urls.modular_report_config}?${params.toString()}`;

    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
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
