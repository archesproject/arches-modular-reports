<script setup lang="ts">
import { defineAsyncComponent, onMounted, useTemplateRef } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Button from "primevue/button";

import type {
    NamedSection,
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const componentLookup: { [key: string]: string } = {};
const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const { $gettext } = useGettext();
const buttonSectionRef = useTemplateRef("buttonSectionRef");
const linkedSectionsRef = useTemplateRef("linked_sections");

function scrollToSection(linked_section: NamedSection): void {
    const sections = linkedSectionsRef.value;

    const section = sections?.find((section) => {
        const props = section?.$props as { header?: string };
        return props.header === linked_section.name;
    });

    if (section) {
        if (section.d_collapsed) {
            section.toggle();
        }
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

onMounted(async () => {
    component.config.sections.forEach((section: NamedSection) => {
        section.components.forEach((component: SectionContent) => {
            if (!componentLookup[component.component]) {
                componentLookup[component.component] = defineAsyncComponent(
                    () =>
                        import(
                            `@/arches_provenance/EditableReport/components/${component.component}.vue`
                        ),
                );
            }
        });
    });
});
</script>

<template>
    <div class="linked-section-outer-container">
        <div
            ref="buttonSectionRef"
            class="linked-section-button-container"
        >
            <Button
                v-for="linked_section in component.config.sections"
                :key="linked_section.name"
                :label="linked_section.name"
                severity="secondary"
                variant="outlined"
                @click="scrollToSection(linked_section)"
            />
        </div>

        <div class="linked-section-container">
            <Panel
                v-for="linked_section in component.config.sections"
                ref="linked_sections"
                :key="linked_section.name"
                :collapsed="false"
                :header="linked_section.name"
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
                <component
                    :is="
                        componentLookup[linked_section.components[0].component]
                    "
                    :key="linked_section.name"
                    :config="linked_section.components[0].config"
                    :resource-instance-id
                />
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
    flex-wrap: wrap;
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
