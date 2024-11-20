<script setup lang="ts">
import { ref } from "vue";

import Panel from "primevue/panel";
import Button from "primevue/button";

const _id = Date.now();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function scrollToSection(linked_section: { [key: string]: any }) {
    linked_section.collapsed.value = false;
    document
        .getElementById(linked_section.id)
        ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function backToTop() {
    document
        .getElementById(`sectionheader-${_id}`)
        ?.scrollIntoView({ behavior: "smooth", block: "end" });
}

let config = {
    title: "Linked Section",
    linked_sections: [
        {
            id: `1-${_id}`,
            label: "Names and Statements",
            content: "This is the content of section 1",
            collapsed: ref(false),
        },
        {
            id: `2-${_id}`,
            label: "Section 2",
            collapsed: ref(false),
        },
        {
            id: `3-${_id}`,
            label: "Section 3",
            collapsed: ref(false),
        },
        {
            id: `4-${_id}`,
            label: "Section 4",
            collapsed: ref(false),
        },
    ],
};
</script>

<template>
    <div class="linked-section-outer-container">
        <div
            :id="`sectionheader-${_id}`"
            class="linked-section-button-container"
        >
            <Button
                v-for="linked_section in config.linked_sections"
                :key="linked_section.id"
                :label="linked_section.label"
                severity="secondary"
                variant="outlined"
                @click="scrollToSection(linked_section)"
            />
        </div>

        <div class="linked-section-container">
            <Panel
                v-for="linked_section in config.linked_sections"
                :id="linked_section.id"
                :key="linked_section.id"
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
                        aria-label="back to top"
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
