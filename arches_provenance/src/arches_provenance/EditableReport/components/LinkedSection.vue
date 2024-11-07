<script setup lang="ts">
import Button from 'primevue/button';


let config = {
    title: "Linked Section",
    linked_sections: [
        {   
            id: "1",
            label: "Section 1",
        },{
            id: "2",
            label: "Section 2",
        },
    ]
};

</script>

<template>

    <div>
        <Button v-for="linked_section in config.linked_sections" :key="linked_section.id" :label="linked_section.label" :href="'#'+linked_section.id" />
        <a v-for="linked_section in config.linked_sections" :key="linked_section.id" :href="'#'+linked_section.id" >{{ linked_section.label }}</a>
    </div>

    <div>
        <section style="height:700px;" :id="linked_section.id" v-for="linked_section in config.linked_sections" :key="linked_section.id">
            <h2>{{ linked_section.label }}</h2>
        </section>
    </div>

</template>

<style scoped>
    html {
        scroll-behavior: smooth;
    }
</style>