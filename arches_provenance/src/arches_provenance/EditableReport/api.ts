import arches from "arches";

export const fetchResource = async (resourceId: string) => {
    const url =
        arches.urls.api_resources(resourceId) + "?format=json&version=beta";
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

export const fetchNodegroupTileData = async (
    resourceInstanceId: string,
    nodegroupId: string,
    rowsPerPage: number,
) => {
    const url = arches.urls.api_nodegroup_tile_data(
        resourceInstanceId,
        nodegroupId,
    );
    const params = new URLSearchParams({
        rows_per_page: rowsPerPage.toString(),
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
