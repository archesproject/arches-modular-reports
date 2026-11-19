import { describe, expect, it } from "vitest";

import { plainText } from "@/arches_modular_reports/ResourceReport/utils/plain-text.ts";

describe("plainText", () => {
    it("keeps words in separate paragraphs and lines apart", () => {
        expect(
            plainText(
                "<p>First <strong>bold</strong></p><p>Second<br>Third</p>",
            ),
        ).toBe("First bold Second Third");
    });
});
