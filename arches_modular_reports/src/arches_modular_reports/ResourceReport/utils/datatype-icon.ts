const DATATYPE_ICONS: Record<string, string> = {
    string: "pi pi-align-left",
    "non-localized-string": "pi pi-align-left",
    number: "pi pi-hashtag",
    date: "pi pi-calendar",
    edtf: "pi pi-calendar",
    boolean: "pi pi-check-circle",
    concept: "pi pi-tag",
    "concept-list": "pi pi-tag",
    reference: "pi pi-tag",
    "domain-value": "pi pi-list",
    "domain-value-list": "pi pi-list",
    "resource-instance": "pi pi-link",
    "resource-instance-list": "pi pi-link",
    "geojson-feature-collection": "pi pi-map-marker",
    annotation: "pi pi-map-marker",
    "file-list": "pi pi-paperclip",
    url: "pi pi-external-link",
    "node-value": "pi pi-share-alt",
};

const DEFAULT_DATATYPE_ICON = "pi pi-circle";

export function datatypeIcon(datatype: string): string {
    return DATATYPE_ICONS[datatype] ?? DEFAULT_DATATYPE_ICON;
}
