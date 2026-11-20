import { inject, onBeforeUnmount, provide, shallowRef, watch } from "vue";

import type { InjectionKey, ShallowRef } from "vue";

interface WorkspaceHeaderHost {
    target: ShallowRef<HTMLElement | null>;
    register: (element: HTMLElement) => () => void;
}

const WORKSPACE_HEADER_HOST_KEY: InjectionKey<WorkspaceHeaderHost> = Symbol(
    "workspaceHeaderHost",
);

export function provideWorkspaceHeaderHost(): ShallowRef<HTMLElement | null> {
    const target = shallowRef<HTMLElement | null>(null);

    function register(element: HTMLElement): () => void {
        target.value = element;
        return () => {
            if (target.value === element) {
                target.value = null;
            }
        };
    }

    provide(WORKSPACE_HEADER_HOST_KEY, { target, register });
    return target;
}

export function useWorkspaceHeaderHost(
    element: Readonly<ShallowRef<HTMLElement | null>>,
): void {
    const host = inject(WORKSPACE_HEADER_HOST_KEY, null);
    if (host === null) {
        return;
    }

    let unregister = (): void => undefined;

    watch(
        element,
        (hostElement) => {
            unregister();
            if (hostElement === null) {
                unregister = (): void => undefined;
            } else {
                unregister = host.register(hostElement);
            }
        },
        { immediate: true, flush: "post" },
    );

    onBeforeUnmount(() => {
        unregister();
    });
}
