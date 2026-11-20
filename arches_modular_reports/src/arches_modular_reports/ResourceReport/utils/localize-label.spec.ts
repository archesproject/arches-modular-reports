import { describe, expect, it } from "vitest";

import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

describe("localizeLabel", () => {
    it("falls back to the default language, not the first entry", () => {
        const label = { de: "Übersicht", en: "Overview", fr: "Aperçu" };

        expect(localizeLabel(label, "fr", "en")).toBe("Aperçu");
        expect(localizeLabel(label, "pt", "en")).toBe("Overview");
    });
});
