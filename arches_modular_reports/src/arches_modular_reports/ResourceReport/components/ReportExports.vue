<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { buildExportUrl } from "@/arches_modular_reports/ResourceReport/api.ts";

import type { ExportFormat } from "@/arches_modular_reports/ResourceReport/types.ts";

const EXPORT_FORMATS: ExportFormat[] = ["json-ld", "json", "csv"];

const { $gettext } = useGettext();
const reportData = useReportData();

const exportFormatLabels: Record<ExportFormat, string> = {
    "json-ld": $gettext("JSON-LD"),
    json: $gettext("JSON"),
    csv: $gettext("CSV"),
};

function exportAriaLabel(exportFormat: ExportFormat): string {
    return $gettext(
        "Export as %{exportFormat}",
        {
            exportFormat: exportFormatLabels[exportFormat],
        },
        true,
    );
}
</script>

<template>
    <nav
        class="report-exports"
        :aria-label="$gettext('Export')"
    >
        <Button
            v-for="exportFormat in EXPORT_FORMATS"
            :key="exportFormat"
            class="report-exports-link"
            as="a"
            variant="link"
            size="small"
            target="_blank"
            rel="noopener"
            :href="
                buildExportUrl(
                    reportData.resource.resourceinstanceid,
                    exportFormat,
                )
            "
            :label="exportFormatLabels[exportFormat]"
            :aria-label="exportAriaLabel(exportFormat)"
        />
    </nav>
</template>

<style scoped>
.report-exports {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.report-exports .report-exports-link {
    --p-button-label-font-weight: 600;
    padding: 0;
    border: none;
    font-size: 1.2rem;
    line-height: 1.2;
}

.report-exports .report-exports-link :deep(.p-button-label) {
    text-decoration: underline;
    text-underline-offset: 0.2rem;
}

.report-exports .report-exports-link:not(:disabled):hover {
    color: var(--p-primary-hover-color);
}
</style>
