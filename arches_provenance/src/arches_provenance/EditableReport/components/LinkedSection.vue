<script setup lang="ts">
import Panel from "primevue/panel";
import Button from "primevue/button";

const _id = Date.now();

let config = {
    title: "Linked Section",
    linked_sections: [
        {
            id: `1-${_id}`,
            label: "Names and Statements",
            content: "This is the content of section 1",
        },
        {
            id: `2-${_id}`,
            label: "Section 2",
        },
        {
            id: `3-${_id}`,
            label: "Section 3",
        },
        {
            id: `4-${_id}`,
            label: "Section 4",
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
                as="a"
                :href="`#${linked_section.id}`"
                :label="linked_section.label"
                severity="secondary"
                variant="outlined"
            />
        </div>

        <div class="linked-section-container">
            <Panel
                v-for="linked_section in config.linked_sections"
                :id="linked_section.id"
                :key="linked_section.id"
                toggleable
            >
                <template #header>
                    <div class="flex items-center gap-2">
                        <span class="font-bold">{{
                            linked_section.label
                        }}</span>
                    </div>
                </template>
                <template #icons>
                    <Button
                        class="back-to-top"
                        as="a"
                        :href="`#sectionheader-${_id}`"
                        icon="pi pi-home"
                        severity="secondary"
                        variant="text"
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

a.back-to-top {
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
</style>
