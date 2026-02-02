import ko from 'knockout';
import ModularReport from '@/arches_modular_reports/ModularReport/ModularReport.vue';
import createVueApplication from 'utils/create-vue-application';
import ModularReportTemplate from 'templates/views/report-templates/modular-report.htm';
import { fetchGraphSlugFromId } from '@/arches_modular_reports/ModularReport/api.ts';
import ModularReportTheme from '@/arches_modular_reports/report_themes/default_theme.ts';


ko.components.register('modular-report', {
    viewModel: async function(params) {

        let graphSlug = params.report.graph?.slug || params.report.report_json.graph_slug;
        const resourceInstanceId = params.report.report_json.resourceinstanceid;
        const reportConfigSlug = params.report.report_json.report_config_slug;
        const reportThemePath = params.report.report_json.report_theme;

        if (reportThemePath && reportThemePath !== "") {
            // uncomment the next section once dynamic imports of .ts files work with webpack

            // const cleanedReportThemePath = reportThemePath.replace(/\.[^/.]+$/, '');
            // try {
            //     // strip file extension if present
            //     ModularReportTheme = (await import(`@/${cleanedReportThemePath}.ts`)).default;
            // } catch (error) {
            //     console.error(`Failed to load report theme: @/${cleanedReportThemePath}.ts`, error);
            // }
        }

        if (!graphSlug) {
            // fetch graph slug from graph id this can happen when viewing the 
            // report from the "details" section of search
            const graphId = params.report.graph?.id || params.report.report_json.graph_id;
            const data = await fetchGraphSlugFromId(graphId);
            graphSlug = data.graph_slug;
        }

        createVueApplication(ModularReport, ModularReportTheme, { graphSlug, resourceInstanceId, reportConfigSlug }).then(vueApp => {
            // handles the Graph Designer case of multiple mounting points on the same page
            const mountingPoints = document.querySelectorAll('.modular-report-mounting-point');
            const mountingPoint = mountingPoints[mountingPoints.length - 1];

            // handles the Resource Editor case of navigating from report doesn't unmount the previous app
            if (window.archesModularReportVueApp) {
                window.archesModularReportVueApp.unmount();
            }
            window.archesModularReportVueApp = vueApp;

            vueApp.mount(mountingPoint);
        });
    },
    template: ModularReportTemplate,
});
