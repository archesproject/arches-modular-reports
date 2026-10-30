# Welcome to Arches Modular Reports!

Arches Modular Reports is an Arches Application that provides an alternate and more modular way to present and configure reports in Arches.

Please see the [project page](http://archesproject.org/) for more information on the Arches project.

## Installation

If you are installing Arches Modular Reports for the first time, **we strongly recommend** that you install it as an Arches application into an existing (or new) project. Running Arches Modular Reports as a standalone project can provide some convenience if you are a developer contributing to the Arches Modular Reports project but you risk conflicts when upgrading to the next version of Arches Modular Reports.

### If installing for development

Clone the arches-modular-reports repo and checkout the latest `dev/x.x.x` or any other branch you may be interested in.
Navigate to the `arches-modular-reports` directory from your terminal and run the following commands:

```
pip install -e . --group dev
pre-commit install

```

`Important`: Installing the arches-modular-reports app will install Arches as a dependency. This may replace your current install of Arches with a version from PyPi. If you've installed Arches for development using the `--editable` flag, you'll need to reinstall Arches using the `--editable` flag again after installing arches-modular-reports.

### If installing for deployment, run:

```
pip install arches-modular-reports
```

## Project Configuration

1. If you don't already have an Arches project, you'll need to create one by following the instructions in the Arches [documentation](http://archesproject.org/documentation/).

2. When your project is ready add "rest_framework", "arches_modular_reports", "arches.extensions.querysets", and "arches.extensions.vue_components" to INSTALLED_APPS **below** the name of your project. The querysets and vue_components applications ship inside arches as of 8.2.0, so there is nothing extra to install:

    ```
    INSTALLED_APPS = (
        ...
        "my_project_name",
        "rest_framework",
        "arches_modular_reports",
        "arches.extensions.querysets",
        "arches.extensions.vue_components",
    )
    ```

3. Next ensure arches, arches_modular_reports are included as dependencies in package.json

    ```
    "dependencies": {
        "arches": "archesproject/arches#dev/8.2.0",
        "arches-modular-reports": "archesproject/arches-modular-reports#dev/2.1.0"
    }
    ```

4. Update urls.py to include the arches-modular-reports urls

    ```
    urlpatterns = [
        ...
    ]

    urlpatterns.append(path("", include("arches_modular_reports.urls")))

    # Ensure Arches core urls are superseded by project-level urls
    urlpatterns.append(path("", include("arches.urls")))

    ```

5. Run migrations

    ```
    python manage.py migrate
    ```

6. Start your project

    ```
    python manage.py runserver
    ```

7. Next cd into your project's app directory (the one with package.json) install and build front-end dependencies:
    ```
    npm install
    npm run build_development
    ```

## Setting up a graph to use the Modular Reports Template

Once you've installed the Arches Modular Report Application into your project you'll notice a new report template available called "Modular Report Template".

1. Select a Graph in the graph designer that you'd like to use with the new modular reports.

2. Navigate to the "Cards" tab, select the root node and select the "Modular Report Template" from the Report Configuration section on the right.

3. Next go to the [admin page](https://arches.readthedocs.io/en/stable/administering/django-admin-ui/) and login.

4. Click on the "+ Add" button next to the item called "Report configs" under the "Arches Modular Reports" section.

5. You'll be presented with a large "Config" section that should only contain empty curly brackets "{}". Below that is a text field with the word "default" - do not change this for a default report setup. The slug is used for situations where multiple report configurations are needed for different custom reports. Below that is a dropdown with a listing of graphs available in your project. Select the graph you chose earlier in step 1 and then click the button that says "Save and continue editing".

6. Notice that the "Config" section is populated with a default configuration.

7. If you view a report of the type of graph set up to use the new template you should notice that it is now using the new report template and has a different appearance.

---

## Editing the structure of the report configuration

Every level of a report config is a component: a `component` path and the `config` that runs it. The path names a Vue component under an app's `src` folder and is loaded when the report needs it. A component's children are lists of components inside its config, usually under `components`.

```json
{
    "name": "Default",
    "components": [
        {
            "component": "arches_modular_reports/ResourceReport/ResourceReport",
            "config": {
                "components": [ ... ]
            }
        }
    ]
}
```

`ResourceReport` loads the resource and renders its `components` in order. With `"config": {}` it renders an empty report. Nothing below it is fixed: a report can have tabs or none, one pane or two, sections or a plain list of folios.

Labels are a string or an object keyed by language, e.g. `{"en": "Report"}`. A missing child list means no children. A component that is missing config it needs shows an error where it would appear.

Configs are validated against the graph on save, without looking at component names:

-   every component has exactly `component` (a string) and `config` (an object)
-   `nodegroup_alias` names a node in one of the graph's nodegroups
-   `node_alias` names a node that holds a value
-   `graphs` lists resource models, and `images` lists `file-list` nodes
-   inside a config with `graph_slug`, aliases belong to that other graph and are not checked

When the report loads, nodegroups and summary entries the user can't read are removed. A section, stack or tab set that loses all its folios is removed too.

---

### The default config

```json
{
    "component": "arches_modular_reports/ResourceReport/components/WorkspaceTabs",
    "config": {
        "banner": [
            { "component": ".../ReportHeader", "config": { "summary": [] } }
        ],
        "components": [
            {
                "component": ".../SplitPane",
                "config": {
                    "label": { "en": "Report" },
                    "description": { "en": "A curated summary of this resource's data" },
                    "main": [
                        {
                            "component": ".../ReportTabs",
                            "config": {
                                "components": [
                                    {
                                        "component": ".../ReportStack",
                                        "config": {
                                            "label": { "en": "Overview" },
                                            "components": [
                                                { "component": ".../FieldFolio", "config": { "nodegroup_alias": "object_type" } },
                                                { "component": ".../ReportFolio", "config": { "nodegroup_alias": "names" } },
                                                { "component": ".../MapFolio", "config": { "nodegroup_alias": "production", "node_alias": "production_location_geo" } }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ],
                    "aside": [
                        { "component": ".../EditorPanel/EditorPanel", "config": {} },
                        { "component": ".../ReportDrawer", "config": { "components": [ ... ], "panels": [ ... ] } }
                    ]
                }
            },
            { "component": ".../SplitPane", "config": { "label": { "en": "Data" }, "requires_edit": true, "main": [ ... ], "aside": [ ... ] } },
            { "component": ".../ReportPlaceholder", "config": { "label": { "en": "Graph" }, "icon": "pi pi-sitemap", "message": { "en": "Graph view — coming soon" } } }
        ]
    }
}
```

`...` stands for `arches_modular_reports/ResourceReport/components`. The config's last top-level component is `EditListTray`.

---

### Layout components

Paths are under `arches_modular_reports/ResourceReport/components/`.

-   `WorkspaceTabs`: the tab strip at the top of the report. Each of its `components` is a tab, named by its `label`, with its `description` shown under the strip. `banner` lists components shown under the strip above every tab.
-   `ReportTabs`: tabs inside a pane, with a tab bar that stays in view while the pane scrolls. Each of its `components` is a tab, named by its `label`.
-   `SplitPane`: `main` and `aside` lists side by side. Without an `aside`, `main` takes the full width.
-   `ReportStack`: its `components` in a column.
-   `ReportSection`: a heading (`label`, optional `icon`) over its `components`.
-   `ReportDrawer`: its `components`, with `panels` as buttons that open over them.

A tab or drawer panel with `"requires_edit": true` is hidden from people who can't edit the resource.

### Content components

-   `ReportHeader`: the resource name, lifecycle state and transitions, and JSON-LD, JSON and CSV exports. `summary` lists nodes shown under the name, each `{"node_alias": ..., "label": ...}`.
-   `KeyDataSummary`: `summary` in the same form. Clicking a label jumps to its folio, switching tabs if needed.
-   `ReportFolio`: `nodegroup_alias`. One card per entry, with child nodegroups inside it.
-   `FieldFolio`: `nodegroup_alias`. One row: label, value and its Edit, Delete or Add.
-   `MapFolio`: `nodegroup_alias` and `node_alias`, the geometry node. The map first, then the entry's other fields and child nodegroups, with a pager when there are several entries.
-   `EditorPanel/EditorPanel`: the edit form. It covers the area it's placed in while an entry is being edited. Edit, Add and Delete only appear when the report has one.
-   `EditListTray`: pending edits, with Apply and Cancel. Hidden when nothing is pending.
-   `DataBrowser/DataBrowser`: every nodegroup in a tree, with a filter.
-   `ReportPlaceholder`: an `icon` and a `message`.
-   Drawer panels, each with a `label` and `icon`: `EditHistoryPanel`; `ImagesPanel`, whose `images` lists `{"model": "<graph slug>", "node": "<node alias>"}` sources; `RelatedResourcesPanel`, whose `graphs` lists models in order; `ManagePanel` for copy, delete and print.

### Custom components

Any other path is loaded the same way, e.g. `my_app/Report/CustomPanel`. A component receives one prop, `component` (its own `{component, config}`), and reads the resource, permissions and editing state with `useReportData()` from `arches_modular_reports/ResourceReport/composables/useReportData.ts`.

---

## Regenerating the default report configuration

The default config is generated from the graph. Each visible top-level nodegroup becomes a folio: a `MapFolio` when it has a geometry node, a `FieldFolio` when it holds a single value and has no child nodegroups, and a `ReportFolio` otherwise. Summaries come from the descriptors and the drawer's panels from related models. Regenerate it after upgrading or changing a graph:

```bash
python manage.py report_configs generate --slug default --overwrite
```

`--graph <graph slug>` limits it to one graph. `--overwrite` replaces existing configs, including your edits, and asks first.

---

## Other report components

`DataSection` is kept for hosts that provide the state it injects, such as arches-search's search result details. It no longer works inside `ModularReport`.

### `DataSection`

Displays a group of nodes from the main resource graph. For cardinality-n tiles, reports can optionally be filtered to limit the tile(s) displayed in the report.

```json
{
    "component": "DataSection",
    "config": {
        "node_aliases": ["color"],
        "custom_labels": {},
        "nodegroup_alias": "physical_characteristics",
        "custom_card_name": "Physical Description"
    }
}
```

OR

```json
{
    "component": "DataSection",
    "config": {
        "node_aliases": ["color", "status_date", "status_type"],
        "filters": [{
              "alias": "status_date"
              "value": "2024-12-31",
              "field_lookup": "lt"
        },{
            "alias": "status_type",
            "value": "dd48ae2d-025a-4d62-978b-be35e106e6e9",
            "field_lookup": "0__uri__icontains"
        }],
        "custom_labels": {},
        "nodegroup_alias": "physical_characteristics",
        "custom_card_name": "Physical Description"
    }
}
```

---

### Common Configuration Properties

#### `node_aliases`

-   **Type:** `array`
-   **Description:** A list of node aliases that specify which nodes to display in a component.

---

#### `custom_labels`

-   **Type:** `object`
-   **Description:** A dictionary used to override default labels for fields. Each key is a `node_alias`, and each value is the custom label to display.

```json
"custom_labels": {
  "color_primary": "Primary Color",
  "material_label_1": "Composition"
}
```

---

#### `custom_card_name`

-   **Type:** `string` or `null`
-   **Description:** Overrides the default title shown on a data card (section). If not set, the system uses the label from the associated card.

```json
"custom_card_name": "Physical Description"
```

---

#### `nodegroup_alias`

-   **Type:** \`string\*\*
-   **Description:** The alias of a **node group** — the node that groups child nodes beneath it. Each node group is represented in the UI as a **Card**, which has a label used by default as the section title. You can override that label with `custom_card_name`.

```json
"nodegroup_alias": "physical_characteristics"
```
