<script setup lang="ts">
const { icon, message } = defineProps<{
    icon: string;
    message: string;
}>();
</script>

<template>
    <div class="report-placeholder">
        <i
            :class="icon"
            aria-hidden="true"
        />
        <span>{{ message }}</span>
    </div>
</template>

<style scoped>
.report-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.8rem;
    width: 100%;
    max-width: 48rem;
    margin-block: 3.2rem;
    margin-inline: auto;
    padding-block: 3.2rem;
    padding-inline: 2.4rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    text-align: center;
}

.report-placeholder i {
    font-size: 2.8rem;
    opacity: 0.35;
}
</style>
