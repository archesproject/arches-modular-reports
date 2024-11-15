<script setup lang="ts">
import Panel from 'primevue/panel';

const _id = Date.now();

let config = {
    title: "Linked Section",
    linked_sections: [
        {   
            id: `1-${_id}`,
            label: "Names and Statements",
            content: "This is the content of section 1"
        },{
            id: `2-${_id}`,
            label: "Section 2",
        },{
            id: `3-${_id}`,
            label: "Section 3",
        },{
            id: `4-${_id}`,
            label: "Section 4",
        },
    ]
};

</script>

<template>
    <div class="linked-section-outer-container">
        <div class="linked-section-button-container" :id="`sectionheader-${_id}`">
            <a v-for="linked_section in config.linked_sections" :key="linked_section.id" :href="`#${linked_section.id}`" >{{ linked_section.label }}</a>
        </div>
    
        <div class="linked-section-container">
            <Panel v-for="linked_section in config.linked_sections"  :id="linked_section.id" :key="linked_section.id" toggleable>
                <template #header>
                    <div class="flex items-center gap-2">
                        <span class="font-bold">{{ linked_section.label }}</span>
                    </div>
                </template>
                <template #icons>
                    <a class="pi pi-home back-to-top" :href="`#sectionheader-${_id}`"></a>
                </template>
                <div style="height: 600px;"></div>
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
}

.linked-section-button-container a, a.back-to-top {
    display: inline-block;
    padding: 6px 10px;
    margin: 5px;
    text-decoration: none;
    color: white;
    background-color: #007BFF;
    border: 1px solid #007BFF;
    border-radius: 4px;
    text-align: center;
    cursor: pointer;
    align-content: center;
}

a.back-to-top {
    font-size: 1.5rem;
    background-color: unset;
    color: gray;
    border: unset;
    padding: 10px;
}

.linked-section-button-container a:hover {
    background-color: #0056b3;
    border-color: #0056b3;
}

</style>