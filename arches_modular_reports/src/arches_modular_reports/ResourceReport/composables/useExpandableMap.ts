import { onBeforeUnmount, ref, shallowRef, watch } from "vue";

import type { Ref, ShallowRef } from "vue";

// Set on the expanded map; styles key on it, and the editor panel rises above
// the report's sticky bars while any map inside it carries it.
export const EXPANDED_MAP_ATTRIBUTE = "data-report-map-expanded";

const MAP_HEADER_SELECTOR = ".map-component > .map-header";
const REPORT_SELECTOR = ".resource-report";
const REPORT_BOUNDS_PROPERTIES = {
    top: "--report-map-expanded-top",
    left: "--report-map-expanded-left",
    width: "--report-map-expanded-width",
    height: "--report-map-expanded-height",
} as const;

/*
 * The map widget renders inside a generic card, so its header is found in the
 * DOM rather than passed down. Expanding pins the map over the whole report
 * (MapLibre follows its container's size), sized to the report's box.
 */
export function useExpandableMap(
    container: Readonly<Ref<HTMLElement | null>>,
): {
    mapHeader: ShallowRef<HTMLElement | null>;
    isMapExpanded: Ref<boolean>;
    toggleMapExpanded: () => void;
} {
    const mapHeader = shallowRef<HTMLElement | null>(null);
    const isMapExpanded = ref(false);

    let headerObserver: MutationObserver | null = null;
    let reportResizeObserver: ResizeObserver | null = null;
    let expandedMap: HTMLElement | null = null;

    function findMapHeader(): void {
        mapHeader.value =
            container.value?.querySelector<HTMLElement>(MAP_HEADER_SELECTOR) ??
            null;
    }

    watch(
        container,
        (element) => {
            headerObserver?.disconnect();
            headerObserver = null;
            findMapHeader();
            if (element) {
                headerObserver = new MutationObserver(findMapHeader);
                headerObserver.observe(element, {
                    childList: true,
                    subtree: true,
                });
            }
        },
        { immediate: true },
    );

    // A new map (another entry, or the same one remounted) starts collapsed.
    watch(mapHeader, () => {
        isMapExpanded.value = false;
    });

    watch(isMapExpanded, (isExpanded) => {
        if (isExpanded) {
            expand();
        } else {
            collapse();
        }
    });

    function fitToReport(): void {
        const report = expandedMap?.closest<HTMLElement>(REPORT_SELECTOR);
        if (!expandedMap || !report) {
            return;
        }
        const bounds = report.getBoundingClientRect();
        for (const [side, property] of Object.entries(
            REPORT_BOUNDS_PROPERTIES,
        )) {
            expandedMap.style.setProperty(
                property,
                `${bounds[side as keyof typeof REPORT_BOUNDS_PROPERTIES]}px`,
            );
        }
    }

    function expand(): void {
        const map = mapHeader.value?.parentElement ?? null;
        const report = map?.closest<HTMLElement>(REPORT_SELECTOR);
        if (!map || !report) {
            isMapExpanded.value = false;
            return;
        }
        expandedMap = map;
        fitToReport();
        map.setAttribute(EXPANDED_MAP_ATTRIBUTE, "");
        reportResizeObserver = new ResizeObserver(fitToReport);
        reportResizeObserver.observe(report);
        window.addEventListener("resize", fitToReport);
        window.addEventListener("scroll", fitToReport, true);
    }

    function collapse(): void {
        reportResizeObserver?.disconnect();
        reportResizeObserver = null;
        window.removeEventListener("resize", fitToReport);
        window.removeEventListener("scroll", fitToReport, true);
        if (expandedMap) {
            expandedMap.removeAttribute(EXPANDED_MAP_ATTRIBUTE);
            for (const property of Object.values(REPORT_BOUNDS_PROPERTIES)) {
                expandedMap.style.removeProperty(property);
            }
        }
        expandedMap = null;
    }

    function toggleMapExpanded(): void {
        isMapExpanded.value = !isMapExpanded.value;
    }

    onBeforeUnmount(() => {
        headerObserver?.disconnect();
        collapse();
    });

    return { mapHeader, isMapExpanded, toggleMapExpanded };
}
