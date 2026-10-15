<script setup lang="ts">
const { icon, message } = defineProps<{
    icon: string;
    message: string;
}>();
</script>

<template>
    <div class="report-placeholder">
        <div class="report-placeholder-message">
            <i
                :class="icon"
                aria-hidden="true"
            />
            <span>{{ message }}</span>
        </div>
    </div>
</template>

<style scoped>
.report-placeholder {
    display: flex;
    justify-content: center;
    padding-block: 3.2rem;
    padding-inline: 1.6rem;
}

.report-placeholder-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.8rem;
    inline-size: 100%;
    max-inline-size: 48rem;
    padding-block: 3.2rem;
    padding-inline: 2.4rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    text-align: center;
}

.report-placeholder-message i {
    font-size: 2.8rem;
    opacity: 0.35;
}
</style>
