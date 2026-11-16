// Markup or a character entity; plain text such as "a < b" doesn't match.
const MARKUP_PATTERN = /<[a-z!/]|&(#\d+|#x[\da-f]+|[a-z]+);/i;

// Where one block of rich text ends and the next begins, so their words don't
// run together once the tags are gone.
const BLOCK_BOUNDARY_PATTERN =
    /<\/(p|div|li|h[1-6]|blockquote|pre|tr|td|th)>|<br\s*\/?>/gi;

const WHITESPACE_PATTERN = /\s+/g;

// The text a reader sees in a value that may be rich text (e.g. from the rich
// text widget): tags dropped, entities decoded and whitespace, including
// non-breaking spaces, collapsed. Parsing with DOMParser runs no scripts.
export function plainText(value: string): string {
    if (!MARKUP_PATTERN.test(value)) {
        return value;
    }
    const document = new DOMParser().parseFromString(
        value.replace(BLOCK_BOUNDARY_PATTERN, "$& "),
        "text/html",
    );
    return (document.body.textContent ?? "")
        .replace(WHITESPACE_PATTERN, " ")
        .trim();
}
