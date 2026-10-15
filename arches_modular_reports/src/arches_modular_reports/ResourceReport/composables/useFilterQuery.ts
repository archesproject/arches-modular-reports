import { ref, watch } from "vue";
import { debounce } from "es-toolkit";

import type { Ref } from "vue";

const FILTER_DELAY_MILLISECONDS = 300;

export function useFilterQuery(): {
    filterText: Ref<string>;
    query: Ref<string>;
} {
    const filterText = ref("");
    const query = ref("");

    watch(
        filterText,
        debounce((text: string) => {
            query.value = text.trim();
        }, FILTER_DELAY_MILLISECONDS),
    );

    return { filterText, query };
}
