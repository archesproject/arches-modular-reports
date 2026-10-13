import { definePreset } from "@openvue/themes";
import Aura from "@openvue/themes/aura";

import { compileGlobalCss } from "@/arches_modular_reports/utils.ts";

const cssOverrides = {
    // examples of how to override styles in modular report components
    // ".section-table-header h4": {
    //     padding: "0 2rem !important",
    //     "font-size": "1.5rem !important",
    // },
    // ".linked-section-container": {
    //     margin: "0 1.5rem !important",
    // },
    // ".linked-section-container .p-panel-header h3": {
    //     "font-size": "2.5rem !important",
    // },
    // ".linked-section-button-container .p-button-label": {
    //     color: "#1857e5",
    // },
    // ".p-card-content h2": {
    //     "font-size": "3rem !important",
    // },
    // ".node-container strong": {
    //     "font-size": "1.7rem !important",
    // },
    // "button.p-tab": {
    //     "font-size": "1.6rem !important",
    // },
    // ".p-tabpanels": {
    //     "background-color": "#e9ebed",
    // },
    // ".data-container": {
    //     border: "0",
    //     margin: "0 4.5rem 3rem !important",
    //     "grid-template-columns": "repeat(4, 1fr) !important",
    // },
    ".p-button:not(.p-button-sm):not(.p-button-lg), .p-inputtext, .p-select-options, .p-select-label, .p-select-overlay, .p-toast-detail":
        {
            "font-size": "1.4rem !important",
        },
    ".p-toast-summary": {
        "font-size": "1.6rem !important",
    },
    ".p-toast-message-icon": {
        "margin-top": "0.6rem !important",
    },
    ".p-icon": {
        width: "1.2rem !important",
        height: "1.2rem !important",
    },
    ".p-dialog-title": {
        "font-size": "1.8rem !important",
    },
};

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
            50: "{teal.50}",
            100: "{teal.100}",
            200: "{teal.200}",
            300: "{teal.300}",
            400: "{teal.400}",
            500: "{teal.500}",
            600: "{teal.600}",
            700: "{teal.700}",
            800: "{teal.800}",
            900: "{teal.900}",
            950: "{teal.950}",
        },
        colorScheme: {
            light: {
                primary: {
                    color: "{primary.600}",
                    contrastColor: "#ffffff",
                    hoverColor: "{primary.700}",
                    activeColor: "{primary.800}",
                },
                editor: {
                    panel: {
                        background: "{surface-50}",
                        headerBackground: "{surface-200}",
                    },
                },
                resourceReport: {
                    strip: {
                        background: "{surface.200}",
                    },
                    caption: {
                        background: "{surface.100}",
                    },
                    aside: {
                        background: "{surface.50}",
                    },
                },
            },
            dark: {
                surface: {
                    0: "#ffffff",
                    50: "{slate.50}",
                    100: "{slate.100}",
                    200: "{slate.200}",
                    300: "{slate.300}",
                    400: "{slate.400}",
                    500: "{slate.500}",
                    600: "{slate.600}",
                    700: "{slate.700}",
                    800: "{slate.800}",
                    900: "{slate.900}",
                    950: "{slate.950}",
                },
                editor: {
                    panel: {
                        background: "transparent",
                        headerBackground: "transparent",
                    },
                },
                resourceReport: {
                    strip: {
                        background: "{surface.950}",
                    },
                    caption: {
                        background: "{surface.950}",
                    },
                    aside: {
                        background: "{surface.950}",
                    },
                },
            },
        },
    },
    css: compileGlobalCss(cssOverrides),
    components: {
        button: {
            paddingX: "1.2rem",
            paddingY: "0.8rem",
            sm: {
                fontSize: "1.3rem",
                paddingX: "1rem",
                paddingY: "0.5rem",
            },
            lg: {
                fontSize: "1.8rem",
                paddingX: "1.4rem",
                paddingY: "1rem",
            },
        },
        tag: {
            fontSize: "1.2rem",
            padding: "0.3rem 0.8rem",
            gap: "0.4rem",
        },
        datatable: {
            rowToggleButton: {
                size: "2.5rem",
            },
            colorScheme: {
                light: {
                    headerCell: {
                        background: "{surface-50}",
                        hoverBackground: "{surface-200}",
                    },
                },
                dark: {
                    headerCell: {
                        background: "{surface-800}",
                        hoverBackground: "{surface-700}",
                    },
                },
            },
        },
        tree: {
            colorScheme: {
                light: {
                    node: {
                        hoverBackground: "{surface-200}",
                        selectedBackground: "{surface-200}",
                    },
                },
                dark: {
                    node: {
                        hoverBackground: "{surface-600}",
                        selectedBackground: "{surface-600}",
                    },
                },
            },
        },
    },
});

export default {
    theme: {
        ...DEFAULT_THEME.theme,
        preset: ModularReportPreset,
    },
};
