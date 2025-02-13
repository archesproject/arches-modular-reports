import arches from "arches";

import type { LabelBasedTile } from "@/arches_provenance/EditableReport/types";

export const fetchNodePresentation = async (resourceId: string) => {
    const url = arches.urls.api_node_presentation(resourceId);
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchReportConfig = async (resourceId: string) => {
    const url =
        arches.urls.provenance_editable_report_config +
        `?resourceId=${resourceId}`;
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
) => {
    const params = new URLSearchParams();
    nodeAliases.forEach((alias) => params.append("node_alias", alias));

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
    });

    const response = await fetch(url + "?" + params.toString());
    const parsed = await response.json();

    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};

export const fetchChildTileData = async (
    tileId: string,
): Promise<LabelBasedTile> => {
    const url = arches.urls.api_child_tile_data(tileId);
    const response = await fetch(url);
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
        "?resourceId=" +
        resourceInstanceId;
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};
