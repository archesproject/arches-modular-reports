import ko from 'knockout';
import EditableReport from '@/arches_provenance/EditableReport/EditableReport.vue';
import createVueApplication from 'utils/create-vue-application';
import EditableReportTemplate from 'templates/views/report-templates/editable-report.htm';


ko.components.register('editable-report', {
    viewModel: function() {
        // querySelectorAll() handles the Graph Designer case of multiple mounting points on the same page
        for (let mountingPoint of document.querySelectorAll('.editable-report-mounting-point')) {
            createVueApplication(EditableReport).then(vueApp => {
                vueApp.mount(mountingPoint);
            });
        }
    },
    template: EditableReportTemplate,
});