import arches from "arches";

export const fetchReportConfig = async (resourceId: string) => {
    const url =
        arches.urls.provenance_editable_report_config +
        `?resourceId=${resourceId}`;
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
};
