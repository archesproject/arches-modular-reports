import { ref, watch } from "vue";

import type { Ref } from "vue";

const STORAGE_KEY = "arches-modular-reports-edit-links-shown";

export function useEditLinksPreference(): {
    areEditLinksShown: Ref<boolean>;
    toggleEditLinks: () => void;
} {
    const areEditLinksShown = ref(readPreference());

    watch(areEditLinksShown, (isShown) => {
        try {
            localStorage.setItem(STORAGE_KEY, String(isShown));
        } catch {
            return;
        }
    });

    function toggleEditLinks(): void {
        areEditLinksShown.value = !areEditLinksShown.value;
    }

    return { areEditLinksShown, toggleEditLinks };
}

function readPreference(): boolean {
    try {
        return localStorage.getItem(STORAGE_KEY) !== "false";
    } catch {
        return true;
    }
}
