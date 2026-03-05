export function getUnloadPageLink(event: MouseEvent) {
    const anchor = (event.target as Element).closest("a");
    if (!anchor) return null;

    const href = anchor.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("javascript:"))
        return null;
    if (anchor.target === "_blank") return null;

    return anchor;
}
