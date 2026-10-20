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

A report config is a name and a list of components. The default config has one component, `ResourceReport`:

```json
{
    "name": "Default",
    "components": [
        {
            "component": "arches_modular_reports/ResourceReport/ResourceReport",
            "config": {
                "header": { ... },
                "workspaces": [ ... ]
            }
        }
    ]
}
```

Labels are a string or an object keyed by language, e.g. `{"en": "Report"}`.

Configs are validated against the graph on save: only `header` and `workspaces` are allowed, folios must be top-level nodegroups, summaries must name nodes that hold a value, related models must be resource models, and image sources must be `file-list` nodes. Folios and summary entries the user can't read are removed when the report loads.

---

### `header`

```json
"header": {
    "summary": [{ "node_alias": "description_content", "label": null }],
    "export_formats": ["json-ld", "json", "csv"],
    "lifecycle_severities": { "<lifecycle state id>": "warn" }
}
```

-   `summary`: nodes shown under the resource name (first value only). `label` overrides the node label.
-   `export_formats`: any of `json-ld`, `json` and `csv`.
-   `lifecycle_severities`: optional tag colours by lifecycle state id: `info`, `success`, `warn`, `danger`, `secondary` or `contrast`.

---

### `workspaces`

Each workspace is a tab at the top of the report.

```json
{
    "id": "report",
    "component": "ReportWorkspace",
    "label": { "en": "Report" },
    "description": { "en": "A curated summary of this resource's data" },
    "config": { ... }
}
```

-   `ReportWorkspace`: the report itself, see below.
-   `DataWorkspace`: every nodegroup in a tree, with an editor. Editors only.
-   `GraphWorkspace`: placeholder.

Any other `component` is loaded by path, e.g. `my_app/Report/CustomWorkspace`, and gets `workspaceConfig` and `reportData` props.

---

### `ReportWorkspace`

```json
"config": {
    "tabs": [
        {
            "label": { "en": "Overview" },
            "sections": [
                {
                    "label": { "en": "Identification" },
                    "icon": "pi pi-tag",
                    "folios": [{ "nodegroup_alias": "names" }]
                }
            ]
        }
    ],
    "home": {
        "summary": [{ "node_alias": "name_content", "label": null }],
        "drawer": [ ... ]
    }
}
```

-   `tabs`: each tab has `sections`, each section has `folios`. Section `label` and `icon` are optional.
-   `folios`: a top-level nodegroup. Child nodegroups render inside it.
-   `home.summary`: the Key Data Summary. Clicking a label jumps to its folio.
-   `home.drawer`: panels that open over the Key Data Summary.

#### Drawer panels

```json
{
    "component": "RelatedResourcesPanel",
    "label": { "en": "Related Resources" },
    "icon": "pi pi-link",
    "config": { "graphs": ["person", "place"] }
}
```

-   `EditHistoryPanel`: edit history. Editors only.
-   `ImagesPanel`: images from `file-list` nodes. `config.images` is a list of `{"model": "<graph slug>", "node": "<node alias>"}`. Sources on other models show images from related resources.
-   `RelatedResourcesPanel`: related resources by model. `config.graphs` lists the models, in order.
-   `ManagePanel`: copy, delete and print.

---

## Regenerating the default report configuration

The default config is generated from the graph: visible top-level nodegroups as folios, summaries from the descriptors, and panels for related models. Regenerate it after upgrading or changing a graph:

```bash
python manage.py report_configs generate --slug default --overwrite
```

`--graph <graph slug>` limits it to one graph. `--overwrite` replaces existing configs, including your edits, and asks first.

---

## Other report components

Other configs, like search result details, can use `DataSection`.

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
