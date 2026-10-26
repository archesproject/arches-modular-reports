<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Galleria from "openvue/galleria";
import Message from "openvue/message";
import Skeleton from "openvue/skeleton";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { fetchResourceImages } from "@/arches_modular_reports/ResourceReport/api.ts";

import type {
    ComponentNode,
    ImagesPanelConfig,
    ResourceImage,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const VISIBLE_THUMBNAIL_COUNT = 5;

const { component } = defineProps<{
    component: ComponentNode<ImagesPanelConfig>;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const images = ref<ResourceImage[]>([]);
const nextCursor = ref<string | null>(null);
const isLoading = ref(true);
const isLoadingMore = ref(false);
const loadError = ref<Error | null>(null);

const resourceInstanceId = computed(
    () => reportData.value.resource.resourceinstanceid,
);

watchEffect(async () => {
    isLoading.value = true;
    loadError.value = null;
    try {
        const imagesPage = await fetchResourceImages(
            resourceInstanceId.value,
            component.config.images ?? [],
            null,
        );
        images.value = imagesPage.images;
        nextCursor.value = imagesPage.next_cursor;
    } catch (error) {
        loadError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

async function loadMore(): Promise<void> {
    isLoadingMore.value = true;
    loadError.value = null;
    try {
        const imagesPage = await fetchResourceImages(
            resourceInstanceId.value,
            component.config.images ?? [],
            nextCursor.value,
        );
        images.value = [...images.value, ...imagesPage.images];
        nextCursor.value = imagesPage.next_cursor;
    } catch (error) {
        loadError.value = error as Error;
    } finally {
        isLoadingMore.value = false;
    }
}
</script>

<template>
    <div class="images">
        <Skeleton
            v-if="isLoading"
            height="24rem"
        />
        <Message
            v-else-if="loadError"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to load images: %{message}",
                        { message: loadError.message },
                        true,
                    )
                }}
            </span>
        </Message>
        <p
            v-else-if="images.length === 0"
            class="images-empty"
        >
            {{ $gettext("This resource does not have any associated images.") }}
        </p>
        <Galleria
            v-else
            :value="images"
            :num-visible="VISIBLE_THUMBNAIL_COUNT"
            :show-item-navigators="images.length > 1"
            :show-thumbnails="images.length > 1"
        >
            <template #item="{ item }">
                <figure class="images-item">
                    <img
                        class="images-main"
                        :src="item.url"
                        :alt="item.alt_text"
                    />
                    <figcaption class="images-caption">
                        <span>{{ item.caption }}</span>
                        <Button
                            v-if="
                                item.resourceinstanceid !== resourceInstanceId
                            "
                            as="a"
                            variant="link"
                            size="small"
                            :href="item.report_url"
                            :label="item.resource_name"
                        />
                    </figcaption>
                </figure>
            </template>
            <template #thumbnail="{ item }">
                <img
                    class="images-thumbnail"
                    :src="item.url"
                    :alt="item.alt_text"
                />
            </template>
        </Galleria>
        <Button
            v-if="nextCursor !== null"
            variant="link"
            size="small"
            :label="$gettext('Load more')"
            :loading="isLoadingMore"
            @click="loadMore"
        />
    </div>
</template>

<style scoped>
.images {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding: 1.6rem;
}

.images-empty {
    margin: 0;
    color: var(--p-text-muted-color);
    font-style: italic;
}

.images-item {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    inline-size: 100%;
    margin: 0;
}

.images-main {
    inline-size: 100%;
    max-block-size: 40rem;
    object-fit: contain;
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-hover-background);
}

.images-caption {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
    color: var(--p-text-muted-color);
    font-size: 1.4rem;
}

.images-thumbnail {
    inline-size: 6rem;
    block-size: 6rem;
    object-fit: cover;
    border-radius: var(--p-content-border-radius);
}
</style>
