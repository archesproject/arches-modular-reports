<script setup lang="ts">
import { onMounted, ref, useTemplateRef } from "vue";
import { useGettext } from "vue3-gettext";
import Panel from "primevue/panel";
import Button from "primevue/button";

import {
    importComponents,
    uniqueId,
} from "@/arches_modular_reports/ModularReport/utils.ts";

import type {
    ComponentLookup,
    CollapsibleSection,
    SectionContent,
} from "@/arches_modular_reports/ModularReport/types";

const componentLookup: ComponentLookup = {};
const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const { $gettext } = useGettext();

const buttonSectionRef = useTemplateRef<HTMLElement>("buttonSectionRef");
const linkedSectionsRef = useTemplateRef<HTMLElement[]>("linked_sections");
const linkedSections = ref<CollapsibleSection[]>([]);

function scrollToSection(linked_section: CollapsibleSection): void {
    const sectionElement = linkedSectionsRef.value!.find((el) => {
        const panelRoot = el.closest(".p-panel");
        const headerText = panelRoot
            ?.querySelector(".p-panel-header")
            ?.textContent?.trim();
        return headerText === linked_section.name;
    });

    if (sectionElement) {
        linked_section.collapsed = false;

        const panelRoot = sectionElement.closest(".p-panel") as HTMLElement;
        if (panelRoot) {
            panelRoot.scrollIntoView({
                behavior: "smooth",
                block: "start",
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

onMounted(async () => {
    await importComponents(component.config.sections, componentLookup);

    for (const section of component.config.sections) {
        linkedSections.value.push({
            name: section.name,
            components: section.components.map((child: SectionContent) => ({
                ...child,
                config: { ...child.config, id: uniqueId(child) },
            })),
            collapsed: false,
        });
    }
});
</script>

<template>
    <div class="linked-section-outer-container">
        <div
            ref="buttonSectionRef"
            class="linked-section-button-container"
        >
            <Button
                v-for="linked_section in linkedSections"
                :key="linked_section.name"
                :label="linked_section.name"
                variant="link"
                as="a"
                @click="scrollToSection(linked_section)"
            />
        </div>

        <div class="linked-section-container">
            <Panel
                v-for="linked_section in linkedSections"
                :key="linked_section.name"
                :collapsed="linked_section.collapsed"
                toggleable
                :header="$gettext('toggle section')"
                @toggle="linked_section.collapsed = !linked_section.collapsed"
            >
                <template #header>
                    <h3>{{ linked_section.name }}</h3>
                </template>
                <template #icons>
                    <Button
                        class="back-to-top"
                        icon="pi pi-arrow-circle-up"
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
                        :is="componentLookup[child.component]?.component"
                        v-for="child in linked_section.components"
                        :key="componentLookup[child.component]?.key"
                        :component="child"
                        :resource-instance-id
                    />
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
    width: 100%;
    padding: 10px 0px;
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

:deep(button.back-to-top span.pi) {
    font-size: 1.2rem;
}

.linked-section-container .p-panel:not(:last-child) {
    margin-bottom: 1.5rem;
}

.linked-section-container h3 {
    margin: 10px 0px;
}

@media print {
    .linked-section-button-container {
        display: none;
    }
}
</style>
