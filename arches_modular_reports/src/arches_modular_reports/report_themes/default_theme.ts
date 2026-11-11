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
        // Navy built around #092c8d (700): lighter steps mix in white,
        // darker steps mix in black.
        primary: {
            50: "#f0f2f8",
            100: "#dfe4f0",
            200: "#bfc8e1",
            300: "#93a2cd",
            400: "#6278b6",
            500: "#3552a2",
            600: "#1d3d96",
            700: "#092c8d",
            800: "#072371",
            900: "#061c5a",
            950: "#04143f",
        },
        colorScheme: {
            light: {
                primary: {
                    color: "{primary.700}",
                    contrastColor: "#ffffff",
                    hoverColor: "{primary.800}",
                    activeColor: "{primary.900}",
                },
                editor: {
                    panel: {
                        background: "{surface-50}",
                        headerBackground: "{surface-200}",
                    },
                },
            },
            dark: {
                // Aura's default ({primary.400}) is under 4.5:1 on the dark
                // surfaces with this navy, so dark mode steps up to 300.
                primary: {
                    color: "{primary.300}",
                    contrastColor: "{surface.900}",
                    hoverColor: "{primary.200}",
                    activeColor: "{primary.100}",
                },
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
            },
        },
    },
    css: compileGlobalCss(cssOverrides),
    components: {
        button: {
            root: {
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
        },
        tag: {
            root: {
                fontSize: "1.2rem",
                padding: "0.3rem 0.8rem",
                gap: "0.4rem",
            },
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
        // Select, MultiSelect and TreeSelect dropdowns render on <body>, so
        // these radii read variables that must be overridden at :root, not
        // on the report.
        multiselect: {
            root: {
                borderRadius:
                    "var(--resource-report-multiselect-border-radius, 0.2rem)",
            },
            overlay: {
                borderRadius:
                    "var(--resource-report-multiselect-border-radius, 0.2rem)",
            },
            option: {
                borderRadius:
                    "var(--resource-report-multiselect-border-radius, 0.2rem)",
            },
        },
        select: {
            root: {
                borderRadius:
                    "var(--resource-report-select-border-radius, 0.2rem)",
            },
            overlay: {
                borderRadius:
                    "var(--resource-report-select-border-radius, 0.2rem)",
            },
            option: {
                borderRadius:
                    "var(--resource-report-select-border-radius, 0.2rem)",
            },
        },
        treeselect: {
            root: {
                borderRadius:
                    "var(--resource-report-treeselect-border-radius, 0.2rem)",
            },
            overlay: {
                borderRadius:
                    "var(--resource-report-treeselect-border-radius, 0.2rem)",
            },
        },
        tree: {
            node: {
                borderRadius:
                    "var(--resource-report-treeselect-border-radius, 0.2rem)",
            },
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
