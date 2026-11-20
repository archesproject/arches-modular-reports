import { inject, provide, shallowRef } from "vue";

import type { InjectionKey, ShallowRef } from "vue";

const WORKSPACE_OVERLAY_HOST_KEY: InjectionKey<
    Readonly<ShallowRef<HTMLElement | null>>
> = Symbol("workspaceOverlayHost");

export function provideWorkspaceOverlayHost(
    element: Readonly<ShallowRef<HTMLElement | null>>,
): void {
    provide(WORKSPACE_OVERLAY_HOST_KEY, element);
}

export function useWorkspaceOverlayHost(): Readonly<
    ShallowRef<HTMLElement | null>
> {
    return inject(WORKSPACE_OVERLAY_HOST_KEY, shallowRef(null));
}
