import { defineComponent, h, ref } from "vue";
import { afterEach, describe, expect, it } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import {
    EXPANDED_MAP_ATTRIBUTE,
    useExpandableMap,
} from "@/arches_modular_reports/ResourceReport/composables/useExpandableMap.ts";

import type { VueWrapper } from "@vue/test-utils";

let expandableMap: ReturnType<typeof useExpandableMap>;
let wrapper: VueWrapper | null = null;

const MapHost = defineComponent({
    setup() {
        const container = ref<HTMLElement | null>(null);
        expandableMap = useExpandableMap(container);
        return () => h("div", { ref: container, class: "map-host" });
    },
});

function mountInReport(): HTMLElement {
    const report = document.createElement("div");
    report.className = "resource-report";
    report.getBoundingClientRect = () =>
        ({ top: 10, left: 20, width: 800, height: 600 }) as DOMRect;
    document.body.append(report);
    wrapper = mount(MapHost, { attachTo: report });
    return report;
}

// The map widget renders later than the card around it.
function renderMap(report: HTMLElement): HTMLElement {
    const map = document.createElement("div");
    map.className = "map-component";
    const header = document.createElement("div");
    header.className = "map-header";
    map.append(header);
    report.querySelector(".map-host")!.append(map);
    return map;
}

afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
    document.body.replaceChildren();
});

describe("useExpandableMap", () => {
    it("finds a map header rendered after mounting", async () => {
        const report = mountInReport();
        expect(expandableMap.mapHeader.value).toBeNull();

        const map = renderMap(report);
        await flushPromises();

        expect(expandableMap.mapHeader.value).toBe(
            map.querySelector(".map-header"),
        );
    });

    it("pins the map to the report's box until collapsed", async () => {
        const report = mountInReport();
        const map = renderMap(report);
        await flushPromises();

        expandableMap.toggleMapExpanded();
        await flushPromises();

        expect(map.hasAttribute(EXPANDED_MAP_ATTRIBUTE)).toBe(true);
        expect(map.style.getPropertyValue("--report-map-expanded-top")).toBe(
            "10px",
        );
        expect(map.style.getPropertyValue("--report-map-expanded-left")).toBe(
            "20px",
        );
        expect(map.style.getPropertyValue("--report-map-expanded-width")).toBe(
            "800px",
        );
        expect(map.style.getPropertyValue("--report-map-expanded-height")).toBe(
            "600px",
        );

        expandableMap.toggleMapExpanded();
        await flushPromises();

        expect(map.hasAttribute(EXPANDED_MAP_ATTRIBUTE)).toBe(false);
        expect(map.style.getPropertyValue("--report-map-expanded-top")).toBe(
            "",
        );
    });

    it("collapses when the editor closes", async () => {
        const report = mountInReport();
        const map = renderMap(report);
        await flushPromises();
        expandableMap.toggleMapExpanded();
        await flushPromises();

        wrapper!.unmount();
        wrapper = null;

        expect(map.hasAttribute(EXPANDED_MAP_ATTRIBUTE)).toBe(false);
    });
});
