import ko from 'knockout';
import EditableReport from '@/arches_provenance/EditableReport/EditableReport.vue';
import createVueApplication from 'utils/create-vue-application';
import EditableReportTemplate from 'templates/views/report-templates/editable-report.htm';

import { definePreset } from '@primevue/themes';
import Aura from '@primevue/themes/aura';

const EditableReportPreset = definePreset(Aura, {
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
    viewModel: function() {
        createVueApplication(EditableReport, EditableReportTheme).then(vueApp => {
            // handles the Graph Designer case of multiple mounting points on the same page
            const mountingPoints = document.querySelectorAll('.editable-report-mounting-point');
            const mountingPoint = mountingPoints[mountingPoints.length - 1];
            
            vueApp.mount(mountingPoint);
        });
    },
    template: EditableReportTemplate,
});
