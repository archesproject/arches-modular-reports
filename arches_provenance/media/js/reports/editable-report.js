import ko from 'knockout';
import EditableReport from '@/arches_provenance/EditableReport/EditableReport.vue';
import createVueApplication from 'utils/create-vue-application';
import EditableReportTemplate from 'templates/views/report-templates/editable-report.htm';


ko.components.register('editable-report', {
    viewModel: function() {
        createVueApplication(EditableReport).then(vueApp => {
            // handles the Graph Designer case of multiple mounting points on the same page
            const mountingPoints = document.querySelectorAll('.editable-report-mounting-point');
            const mountingPoint = mountingPoints[mountingPoints.length - 1];
            
            vueApp.mount(mountingPoint);
        });
    },
    template: EditableReportTemplate,
});
