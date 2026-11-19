const MARKUP_PATTERN = /<[a-z!/]|&(#\d+|#x[\da-f]+|[a-z]+);/i;

const BLOCK_BOUNDARY_PATTERN =
    /<\/(p|div|li|h[1-6]|blockquote|pre|tr|td|th)>|<br\s*\/?>/gi;

const WHITESPACE_PATTERN = /\s+/g;

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
