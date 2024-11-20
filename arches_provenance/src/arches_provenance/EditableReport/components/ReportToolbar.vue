<script setup lang="ts">
import type { SectionContent } from "@/arches_provenance/EditableReport/types";
</script>

<template>
    <h3>{{ ($attrs.content as SectionContent).component }}</h3>
    <pre style="text-wrap: auto">{{
        ($attrs.content as SectionContent).config
    }}</pre>
</template>
