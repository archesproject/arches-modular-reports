<script setup lang="ts">
import { onMounted, ref, useTemplateRef } from "vue";
import { useGettext } from "vue3-gettext";
import Panel from "primevue/panel";
import Button from "primevue/button";

import {
    importComponents,
    uniqueId,
} from "@/arches_provenance/EditableReport/utils.ts";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const componentLookup: ComponentLookup = {};
const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const { $gettext } = useGettext();

const buttonSectionRef = useTemplateRef<HTMLElement>("buttonSectionRef");
const linkedSectionsRef = useTemplateRef<HTMLElement[]>("linked_sections");
const collapsedSections = ref<Record<string, boolean>>({});

function scrollToSection(linked_section: NamedSection): void {
    const sections = linkedSectionsRef.value;

    const sectionElement = sections?.find((el) => {
        const panelRoot = el.closest(".p-panel");
        const headerText = panelRoot
            ?.querySelector(".p-panel-header")
            ?.textContent?.trim();
        return headerText === linked_section.name;
    });

    if (sectionElement) {
        if (collapsedSections.value[linked_section.name]) {
            collapsedSections.value[linked_section.name] = false;
        }

        const panelRoot = sectionElement.closest(".p-panel") as HTMLElement;
        if (panelRoot) {
            panelRoot.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }
    }
}

function backToTop() {
    buttonSectionRef.value?.scrollIntoView({
        behavior: "smooth",
        block: "end",
    });
}

onMounted(() => importComponents(component.config.sections, componentLookup));
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
                :key="linked_section.name"
                :collapsed="collapsedSections[linked_section.name]"
                :header="linked_section.name"
                toggleable
                @toggle="
                    collapsedSections[linked_section.name] =
                        !collapsedSections[linked_section.name]
                "
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

                <div
                    ref="linked_sections"
                    class="panel-content"
                >
                    <component
                        :is="componentLookup[child.component]"
                        v-for="child in linked_section.components"
                        :key="uniqueId(child)"
                        :config="child.config"
                        :resource-instance-id
                    />
                    <div style="height: 600px"></div>
                </div>
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
    background-color: var(--p-content-background);
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
