import { describe, expect, it } from "vitest";

import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

describe("localizeLabel", () => {
    it("prefers the active language", () => {
        expect(localizeLabel({ en: "Names", es: "Nombres" }, "es")).toBe(
            "Nombres",
        );
    });

    it("falls back to the first populated language", () => {
        expect(localizeLabel({ en: "", de: "Namen" }, "es")).toBe("Namen");
    });
});
