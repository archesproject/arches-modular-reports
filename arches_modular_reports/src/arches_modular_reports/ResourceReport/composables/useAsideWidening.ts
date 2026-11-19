import { inject, provide, ref } from "vue";

import type { InjectionKey, Ref } from "vue";

const ASIDE_WIDENING_KEY: InjectionKey<Ref<boolean>> = Symbol("asideWidening");

export function provideAsideWidening(): Ref<boolean> {
    const isAsideWidened = ref(false);
    provide(ASIDE_WIDENING_KEY, isAsideWidened);
    return isAsideWidened;
}

export function useAsideWidening(): Ref<boolean> | null {
    return inject(ASIDE_WIDENING_KEY, null);
}
