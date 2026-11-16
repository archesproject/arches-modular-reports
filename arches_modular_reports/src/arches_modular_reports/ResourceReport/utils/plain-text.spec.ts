import { describe, expect, it } from "vitest";

import { plainText } from "@/arches_modular_reports/ResourceReport/utils/plain-text.ts";

describe("plainText", () => {
    it("drops tags and turns non-breaking spaces into spaces", () => {
        expect(
            plainText(
                "<p>Said&nbsp;to&nbsp;be&nbsp;a&nbsp;mythical&nbsp;figure</p>",
            ),
        ).toBe("Said to be a mythical figure");
    });

    it("keeps words in separate paragraphs and lines apart", () => {
        expect(
            plainText(
                "<p>First <strong>bold</strong></p><p>Second<br>Third</p>",
            ),
        ).toBe("First bold Second Third");
    });

    it("decodes entities", () => {
        expect(plainText("Fish &amp; Chips &#8212; &lt;sic&gt;")).toBe(
            "Fish & Chips — <sic>",
        );
    });

    it("leaves plain text alone, including a bare less-than sign", () => {
        expect(plainText("a < b  and  c")).toBe("a < b  and  c");
    });

    it("finds no text in empty markup", () => {
        expect(plainText("<p><br></p>")).toBe("");
    });
});
