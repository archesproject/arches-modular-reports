import { describe, expect, it } from "vitest";

import { resolveViews } from "@/arches_modular_reports/ResourceReport/utils/resolve-views.ts";

import type { ViewConfig } from "@/arches_modular_reports/ResourceReport/types.ts";

const VIEW_CONFIGS: ViewConfig[] = [
    {
        id: "report",
        component: "ReportView",
        label: { en: "Report", es: "Informe" },
        description: { en: "A curated summary" },
    },
    { id: "data", component: "DataView", label: "Data" },
    { id: "custom", component: "my_app/Report/CustomView" },
];

describe("resolveViews", () => {
    it("resolves configured views with their layouts", () => {
        const views = resolveViews(VIEW_CONFIGS, {
            canEdit: true,
            activeLanguage: "en",
        });

        expect(views.map((view) => [view.id, view.label, view.layout])).toEqual(
            [
                ["report", "Report", "report"],
                ["data", "Data", "data"],
                ["custom", "custom", "full"],
            ],
        );
        expect(views[0].description).toBe("A curated summary");
        expect(views[2].description).toBe("");
    });

    it("localizes labels for the active language", () => {
        const views = resolveViews(VIEW_CONFIGS, {
            canEdit: true,
            activeLanguage: "es",
        });

        expect(views[0].label).toBe("Informe");
    });

    it("hides the data view from users who cannot edit", () => {
        const views = resolveViews(VIEW_CONFIGS, {
            canEdit: false,
            activeLanguage: "en",
        });

        expect(views.map((view) => view.id)).toEqual(["report", "custom"]);
    });

    it("resolves no views when none are configured", () => {
        expect(
            resolveViews([], { canEdit: true, activeLanguage: "en" }),
        ).toEqual([]);
    });
});
