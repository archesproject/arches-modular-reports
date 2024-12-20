import ko from 'knockout';
import EditableReport from '@/arches_provenance/EditableReport/EditableReport.vue';
import createVueApplication from 'utils/create-vue-application';
import EditableReportTemplate from 'templates/views/report-templates/editable-report.htm';

import { definePreset } from '@primevue/themes';
import Aura from '@primevue/themes/aura';

const EditableReportPreset = definePreset(Aura, {
    semantic: {
        primary: {
            50: '{sky.50}',
            100: '{sky.100}',
            200: '{sky.200}',
            300: '{sky.300}',
            400: '{sky.400}',
            500: '{sky.500}',
            600: '{sky.600}',
            700: '{sky.700}',
            800: '{sky.800}',
            900: '{sky.900}',
            950: '{sky.950}'
        },
    },
    components: {
        toast: {
            summary: { fontSize: '1.5rem' },
            detail: { fontSize: '1.25rem' },
        },
    },
});

const EditableReportTheme = {
    theme: {
        preset: EditableReportPreset,
    },
};

ko.components.register('editable-report', {
    viewModel: function(params) {
        createVueApplication(EditableReport, EditableReportTheme).then(vueApp => {
            // handles the Graph Designer case of multiple mounting points on the same page
            const mountingPoints = document.querySelectorAll('.editable-report-mounting-point');
            const mountingPoint = mountingPoints[mountingPoints.length - 1];

            vueApp.provide('resourceInstanceId', params.report.report_json.resourceinstanceid);
            vueApp.mount(mountingPoint);
        });
    },
    template: EditableReportTemplate,
});
