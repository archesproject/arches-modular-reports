import { describe, expect, it } from "vitest";

import { resolveViews } from "@/arches_modular_reports/ResourceReport/utils/resolve-views.ts";

const BUILT_IN_VIEW_TEXT = {
    ReportView: { label: "Report", description: "A curated summary" },
    DataView: { label: "Data", description: "Browse and edit" },
    GraphView: { label: "Graph", description: "A visual overview" },
};

describe("resolveViews", () => {
    it("falls back to the built-in views with translated text", () => {
        const views = resolveViews(undefined, {
            canEdit: true,
            activeLanguage: "en",
            builtInViewText: BUILT_IN_VIEW_TEXT,
        });
        expect(views.map((view) => [view.id, view.label, view.layout])).toEqual(
            [
                ["report", "Report", "report"],
                ["data", "Data", "data"],
                ["graph", "Graph", "full"],
            ],
        );
    });

    it("hides the data view from users who cannot edit", () => {
        const views = resolveViews(undefined, {
            canEdit: false,
            activeLanguage: "en",
            builtInViewText: BUILT_IN_VIEW_TEXT,
        });
        expect(views.map((view) => view.id)).toEqual(["report", "graph"]);
    });

    it("prefers configured labels and gives custom views a full-width layout", () => {
        const views = resolveViews(
            [
                {
                    id: "report",
                    component: "ReportView",
                    label: { en: "Summary", es: "Resumen" },
                },
                { id: "custom", component: "my_app/Report/CustomView" },
            ],
            {
                canEdit: true,
                activeLanguage: "es",
                builtInViewText: BUILT_IN_VIEW_TEXT,
            },
        );
        expect(views[0].label).toBe("Resumen");
        expect(views[1]).toMatchObject({
            label: "custom",
            description: "",
            layout: "full",
        });
    });
});
