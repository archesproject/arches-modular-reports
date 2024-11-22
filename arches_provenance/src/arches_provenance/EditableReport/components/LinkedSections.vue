<script setup lang="ts">
import { ref, useTemplateRef } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Button from "primevue/button";

import type { Ref } from "vue";

const { $gettext } = useGettext();
const buttonSectionRef = useTemplateRef("buttonSectionRef");
const linkedSectionsRef = useTemplateRef("linked_sections");

interface LinkedSection {
    label: string;
    collapsed: Ref<boolean>;
}

async function scrollToSection(linked_section: LinkedSection): Promise<void> {
    linked_section.collapsed.value = false;

    const index = config.linked_sections.indexOf(linked_section);
    const section = linkedSectionsRef.value?.[index];

    if (section) {
        section.$el.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
        });
    }
}

function backToTop() {
    buttonSectionRef.value?.scrollIntoView({
        behavior: "smooth",
        block: "end",
    });
}

const config = {
    title: "Linked Section",
    linked_sections: [
        {
            label: "Names and Statements",
            collapsed: ref(false),
        },
        {
            label: "Section 2",
            collapsed: ref(false),
        },
        {
            label: "Section 3",
            collapsed: ref(false),
        },
        {
            label: "Section 4",
            collapsed: ref(false),
        },
    ],
};
</script>

<template>
    <div class="linked-section-outer-container">
        <div
            ref="buttonSectionRef"
            class="linked-section-button-container"
        >
            <Button
                v-for="linked_section in config.linked_sections"
                :key="linked_section.label"
                :label="linked_section.label"
                severity="secondary"
                variant="outlined"
                @click="scrollToSection(linked_section)"
            />
        </div>

        <div class="linked-section-container">
            <Panel
                v-for="linked_section in config.linked_sections"
                ref="linked_sections"
                :key="linked_section.label"
                :collapsed="linked_section.collapsed"
                :header="linked_section.label"
                toggleable
            >
                <template #icons>
                    <Button
                        class="back-to-top"
                        icon="pi pi-home"
                        severity="secondary"
                        variant="text"
                        :aria-label="$gettext('back to top')"
                        @click="backToTop()"
                    />
                </template>
                <div style="height: 600px"></div>
            </Panel>
        </div>
    </div>
</template>

<style scoped>
.linked-section-outer-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.linked-section-button-container {
    display: flex;
    justify-content: center;
    width: 100%;
    background-color: white;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    gap: 10px;
}

button.back-to-top {
    background-color: unset;
    color: gray;
    border: solid 1px white;
    border-radius: 7rem;
    width: 2.5rem;
    height: 2.5rem;
    padding: 10px;
}

:deep(.p-button-label),
:deep(.pi) {
    font-size: 1.4rem;
}
:deep(.p-panel-header) {
    padding: 10px 20px;
}
</style>
