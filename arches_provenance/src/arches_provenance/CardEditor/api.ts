import arches from "arches";

export const fetchProvenanceResource = async (
    graphSlug: string,
    resourceId: string,
) => {
    const response = await fetch(
        arches.urls.api_provenance_resource(graphSlug, resourceId),
    );
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};
