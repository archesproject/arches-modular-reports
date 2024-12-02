<script setup lang="ts">
import type { SectionContent } from "@/arches_provenance/EditableReport/types";
</script>

<template>
    <h3>{{ ($attrs.component as SectionContent).component }}</h3>
    <pre style="text-wrap: auto">
        {{ ($attrs.component as SectionContent).config }}
    </pre>
</template>
