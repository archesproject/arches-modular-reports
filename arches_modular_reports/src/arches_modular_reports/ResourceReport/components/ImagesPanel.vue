<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Galleria from "openvue/galleria";
import Message from "openvue/message";
import Skeleton from "openvue/skeleton";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { fetchResourceImages } from "@/arches_modular_reports/ResourceReport/api.ts";
import { PANEL_COUNT_EVENT } from "@/arches_modular_reports/ResourceReport/constants.ts";

import type {
    ComponentNode,
    DrawerPanelCount,
    ImagesPanelConfig,
    ResourceImage,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const VISIBLE_THUMBNAIL_COUNT = 5;
const THUMBNAIL_STRIP_INLINE_SIZE = `${VISIBLE_THUMBNAIL_COUNT * 6.8}rem`;

const { component } = defineProps<{
    component: ComponentNode<ImagesPanelConfig>;
}>();

const emit = defineEmits<{
    (event: typeof PANEL_COUNT_EVENT, panelCount: DrawerPanelCount): void;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const images = ref<ResourceImage[]>([]);
const nextCursor = ref<string | null>(null);
const isLoading = ref(true);
const isLoadingMore = ref(false);
const activeIndex = ref(0);
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
        activeIndex.value = 0;
        emit(PANEL_COUNT_EVENT, {
            count: imagesPage.images.length,
            hasMore: imagesPage.next_cursor !== null,
        });
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
            v-model:active-index="activeIndex"
            :value="images"
            :num-visible="VISIBLE_THUMBNAIL_COUNT"
            :show-thumbnails="images.length > 1"
        >
            <template #item="{ item }">
                <figure class="images-item">
                    <img
                        class="images-main"
                        loading="lazy"
                        :src="item.url"
                        :alt="item.alt_text"
                    />
                    <figcaption class="images-caption">
                        <template
                            v-if="
                                item.resourceinstanceid !== resourceInstanceId
                            "
                        >
                            <span>
                                {{
                                    $gettext(
                                        "Related %{model}:",
                                        { model: item.graph_name },
                                        true,
                                    )
                                }}
                            </span>
                            <Button
                                as="a"
                                variant="link"
                                size="small"
                                :href="item.report_url"
                                :label="item.resource_name"
                            />
                        </template>
                        <span v-else>{{ item.caption }}</span>
                        <Button
                            class="images-full-size"
                            as="a"
                            variant="link"
                            size="small"
                            icon="pi pi-external-link"
                            icon-pos="right"
                            target="_blank"
                            rel="noopener"
                            :href="item.url"
                            :label="$gettext('Open full size')"
                            :aria-label="
                                $gettext('Open full size image in a new tab')
                            "
                        />
                        <div
                            v-if="images.length > 1"
                            class="images-navigation"
                        >
                            <Button
                                icon="pi pi-chevron-left"
                                variant="text"
                                severity="secondary"
                                size="small"
                                :aria-label="$gettext('Previous image')"
                                :disabled="activeIndex === 0"
                                @click="activeIndex -= 1"
                            />
                            <Button
                                icon="pi pi-chevron-right"
                                variant="text"
                                severity="secondary"
                                size="small"
                                :aria-label="$gettext('Next image')"
                                :disabled="activeIndex === images.length - 1"
                                @click="activeIndex += 1"
                            />
                        </div>
                    </figcaption>
                </figure>
            </template>
            <template #thumbnail="{ item }">
                <img
                    class="images-thumbnail"
                    alt=""
                    loading="lazy"
                    :src="item.url"
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
    container-type: inline-size;
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
    border-radius: 0.2rem;
    background: var(--p-content-hover-background);
}

.images-caption {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem;
    padding-block: 0.5rem;
    padding-inline: 1rem;
    color: var(--p-text-muted-color);
    font-size: 1.4rem;
}

.images-caption .p-button-link {
    padding-inline: 0;
}

.images-navigation {
    display: flex;
    gap: 0.2rem;
    margin-inline-start: auto;
}

.images :deep(.p-galleria-thumbnail-items) {
    flex-shrink: 0;
    inline-size: v-bind(THUMBNAIL_STRIP_INLINE_SIZE);
}

.images-thumbnail {
    inline-size: 6rem;
    block-size: 6rem;
    object-fit: cover;
    border-radius: 0.2rem;
}

@container (min-inline-size: 80rem) {
    .images-main {
        max-block-size: 64rem;
    }
}
</style>
