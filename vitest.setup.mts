import { beforeAll, vi } from 'vitest';

class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
}

vi.stubGlobal('ResizeObserver', ResizeObserverStub);

beforeAll(() => {
    vi.mock('arches', () => ({
        default: '',
    }));

    vi.mock('vue3-gettext', () => {
        const HTML_ESCAPES: Record<string, string> = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
        };
        return {
            useGettext: () => ({
                $gettext: (
                    text: string,
                    parameters: Record<string, unknown> = {},
                    disableHtmlEscaping = false,
                ) =>
                    text.replace(/%\{\s*(\w+)\s*\}/g, (placeholder, name) => {
                        if (!(name in parameters)) {
                            return placeholder;
                        }
                        const value = String(parameters[name]);
                        if (disableHtmlEscaping) {
                            return value;
                        }
                        return value.replace(
                            /[&<>"']/g,
                            (character) => HTML_ESCAPES[character],
                        );
                    }),
            }),
        };
    });
});
