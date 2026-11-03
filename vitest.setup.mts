import { vi } from 'vitest';

class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
}

vi.stubGlobal('ResizeObserver', ResizeObserverStub);

vi.mock('arches', () => ({
    default: '',
}));

vi.mock('vue3-gettext', () => ({
    useGettext: () => ({
        $gettext: (text: string) => (text)
    })
}));
