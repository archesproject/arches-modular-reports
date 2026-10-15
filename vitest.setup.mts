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

    vi.mock('vue3-gettext', () => ({
        useGettext: () => ({
            $gettext: (text: string, parameters: Record<string, unknown> = {}) =>
                text.replace(/%\{\s*(\w+)\s*\}/g, (placeholder, name) =>
                    name in parameters ? String(parameters[name]) : placeholder,
                ),
        }),
    }));
});
