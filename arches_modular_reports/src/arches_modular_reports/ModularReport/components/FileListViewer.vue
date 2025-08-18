<script setup lang="ts">
import { computed, ref } from "vue";
import { Image, Galleria } from "primevue";

import type { FileReference } from "@/arches_component_lab/datatypes/file-list/types";

const props = defineProps<{
    fileData: FileReference[];
}>();

const imageData = computed(() => {
    return props.fileData.map((fileReference) => {
        return {
            thumbnailImageSrc: `${fileReference.url}?thumbnail=true`,
            itemImageSrc: `${fileReference.url}`,
            alt: fileReference.altText,
            title: fileReference.title,
            attribution: fileReference.attribution,
            description: fileReference.description,
        };
    });
});

const showThumbnails = computed(() => {
    return imageData.value && imageData.value.length > 1;
});

const activeIndex = ref(0);
const activeMetadata = ref(imageData.value[0]);
function changeIndex(number: number) {
    activeMetadata.value = imageData.value[number];
}
</script>

<template>
    <Galleria
        v-model:active-index="activeIndex"
        :value="imageData"
        :show-thumbnails="showThumbnails"
        :show-item-navigators="true"
        container-class="galleria-container"
        @update:active-index="changeIndex"
    >
        <template #item="slotProps">
            <div class="item-container">
                <div class="header">{{ slotProps.item.title }}</div>
                <a
                    :href="slotProps.item.itemImageSrc"
                    target="_blank"
                >
                    <Image
                        class="mainImage"
                        :src="slotProps.item.thumbnailImageSrc"
                        :alt="slotProps.item.alt"
                    />
                </a>
            </div>
        </template>
        <template
            v-if="showThumbnails"
            #thumbnail="slotProps"
        >
            <Image
                class="thumbnailImage"
                :src="slotProps.item.thumbnailImageSrc"
                :alt="slotProps.item.alt"
                :header="slotProps.item.title"
            />
        </template>
        <template #caption="slotProps">
            <div class="description">{{ slotProps.item.description }}</div>
            <div class="attribution">{{ slotProps.item.attribution }}</div>
        </template>
    </Galleria>
</template>

<style scoped>
:deep(.mainImage) {
    display: flex;
    justify-content: center;
    align-items: center;
}

:deep(.mainImage img) {
    max-width: 100%;
}

:deep(.thumbnailImage img) {
    max-height: 5rem;
}

div.header {
    display: flex;
    justify-content: center;
    padding: 0.5rem;
}

.galleria-container {
    max-width: 30rem;
}

.item-container {
    display: flex;
    flex-direction: column;
}

div.description {
    padding: 0.25rem;
}

div.attribution {
    text-align: end;
    font-size: 1rem;
}
</style>
