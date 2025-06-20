import ko from 'knockout';
import ModularReport from '@/arches_modular_reports/ModularReport/ModularReport.vue';
import createVueApplication from 'utils/create-vue-application';
import ModularReportTemplate from 'templates/views/report-templates/modular-report.htm';

import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';


// TODO: when dropping support for 7.6, just import from arches 8.
const DEFAULT_THEME = {
    theme: {
        // preset: ArchesPreset,
        options: {
            prefix: "p",
            darkModeSelector: ".arches-dark",
            cssLayer: false,
        },
    },
};

// TODO: when dropping support for 7.6, extend ArchesPreset.
const ModularReportPreset = definePreset(Aura, {
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
        datatable: {
            rowToggleButton: {
                size: '2.5rem',
            },
            colorScheme: {  
                light: { 
                    header: {
                        cell: {
                            background: '{surface-50}',
                            hover: {
                                background: '{surface-200}'
                            }
                        }
                    }
                },
                dark: {
                    header: {
                        cell: {
                            background: '{surface-800}',
                            hover: {
                                background: '{surface-700}'
                            }
                        }
                    }
                }
            }
        },
        // TODO: arches v8: provided by default.ts, remove
        splitter: {
            handle: {
                background: "{surface.500}",
            },
        },
        toast: {
            summary: { fontSize: '1.5rem' },
            detail: { fontSize: '1.25rem' },
        },
        tabs: {
            colorScheme: {  
                light: {
                    tabpanel: {
                        background: '{surface-100}',
                    }
                },
                dark: {
                    tabpanel: {
                        background: '{surface-800}',
                    }
                }
            }
        },
        card: {
            colorScheme: {  
                light: {
                    background: '{surface-100}'
                },
                dark: {
                    background: '{surface-800}'
                }
            }
        },
        // custom button tokens and additional style
        button: {
            extend: {
                baseButton: {
                    fontSize: '1.4rem',
                }
            },
            colorScheme: {  
                light: { 
                    primary: {
                        color: '{primary-700}',
                    },
                    link: {  
                        hoverColor: '{button-text-plain-color}',  
                        color: '{button-primary-color}',  
                    },  
                    outlined: {  
                        primary: { 
                            color: '{button-primary-color}', 
                        },
                    },
                },  
                dark: {  
                    link: {  
                        hoverColor: '{button-text-plain-color}',  
                    },
                    outlined: {  
                        primary: {
                            hover:{  
                                color: '{primary-700}', // this doesn't work, but should based on primevue docs
                                background: '{button-text-plain-color}',  
                            },      
                        }
                    }
                },  
            },  
            css: ({ dt }) => `
                .p-button {
                    font-size: ${dt('base.button.font.size')};
                }
            `
        }
    },
});

const ModularReportTheme = {
    theme: {
        ...DEFAULT_THEME.theme,
        preset: ModularReportPreset,
    },
};

ko.components.register('modular-report', {
    viewModel: function(params) {
        createVueApplication(ModularReport, ModularReportTheme).then(vueApp => {
            // handles the Graph Designer case of multiple mounting points on the same page
            const mountingPoints = document.querySelectorAll('.modular-report-mounting-point');
            const mountingPoint = mountingPoints[mountingPoints.length - 1];

            // handles the Resource Editor case of navigating from report doesn't unmount the previous app
            if (window.archesModularReportVueApp) {
                window.archesModularReportVueApp.unmount();
            }
            window.archesModularReportVueApp = vueApp;

            vueApp.provide("graphSlug", params.report.graph.slug);
            vueApp.provide('resourceInstanceId', params.report.report_json.resourceinstanceid);
            vueApp.mount(mountingPoint);
        });
    },
    template: ModularReportTemplate,
});
