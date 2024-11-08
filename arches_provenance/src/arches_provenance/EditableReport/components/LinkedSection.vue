<script setup lang="ts">
import Button from 'primevue/button';
import Panel from 'primevue/panel';


let config = {
    title: "Linked Section",
    linked_sections: [
        {   
            id: "1",
            label: "Section 1",
            content: "This is the content of section 1"
        },{
            id: "2",
            label: "Section 2",
        },{
            id: "3",
            label: "Section 3",
        },{
            id: "4",
            label: "Section 4",
        },
    ]
};

</script>

<template>

    <div class="linked-section-outer-container">
        <div class="linked-section-button-container">
            <a v-for="linked_section in config.linked_sections" :key="linked_section.id" :href="'#'+linked_section.id" >{{ linked_section.label }}</a>
        </div>
    
        <div class="linked-section-container">
            <!-- <section style="height:700px;" :id="linked_section.id" v-for="linked_section in config.linked_sections" :key="linked_section.id">
                <h2>{{ linked_section.label }}</h2>
            </section> -->


            <Panel toggleable :id="linked_section.id" v-for="linked_section in config.linked_sections" :key="linked_section.id">
                <template #header>
                    <div class="flex items-center gap-2">
                        <span class="font-bold">{{ linked_section.label }}</span>
                    </div>
                </template>
                <template #icons>
                    <Button icon="pi pi-home" severity="secondary" rounded text/>
                </template>
                <div style="height: 600px;"></div>

            </Panel>


        </div>
    </div>

</template>

<style scoped>
.linked-section-outer-container {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.linked-section-button-container {
    display: flex;
    justify-content: center;
    /* gap: 5px;
    position: absolute;
    top: 0; */
    width: 100%;
    background-color: white;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.linked-section-button-container a {
    display: inline-block;
    padding: 10px 20px;
    margin: 5px;
    text-decoration: none;
    color: white;
    background-color: #007BFF;
    border: 1px solid #007BFF;
    border-radius: 4px;
    text-align: center;
    cursor: pointer;
}

.linked-section-button-container a:hover {
    background-color: #0056b3;
    border-color: #0056b3;
}

.linked-section-container {
    scroll-behavior: smooth;
    overflow: scroll;
    height: 600px;
}
</style>