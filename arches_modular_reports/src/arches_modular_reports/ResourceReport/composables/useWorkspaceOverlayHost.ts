import { inject, provide, shallowRef } from "vue";

import type { InjectionKey, ShallowRef } from "vue";

const WORKSPACE_OVERLAY_HOST_KEY: InjectionKey<
    Readonly<ShallowRef<HTMLElement | null>>
> = Symbol("workspaceOverlayHost");

// Called by a workspace (e.g. SplitPane) that offers a layer spanning all of
// its panes, pinned header included.
export function provideWorkspaceOverlayHost(
    element: Readonly<ShallowRef<HTMLElement | null>>,
): void {
    provide(WORKSPACE_OVERLAY_HOST_KEY, element);
}

// Returns the element an aside panel can be teleported into to span the whole
// workspace, or null when the workspace offers no such layer.
export function useWorkspaceOverlayHost(): Readonly<
    ShallowRef<HTMLElement | null>
> {
    return inject(WORKSPACE_OVERLAY_HOST_KEY, shallowRef(null));
}
