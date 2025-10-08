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

2. When your project is ready add "rest_framework", "arches_modular_reports", "arches_querysets", and "arches_component_lab" to INSTALLED_APPS **below** the name of your project:

    ```
    INSTALLED_APPS = (
        ...
        "my_project_name",
        "rest_framework",
        "arches_modular_reports",
        "arches_querysets",
        "arches_component_lab",
    )
    ```

3. Next ensure arches, arches_modular_reports are included as dependencies in package.json

    ```
    "dependencies": {
        "arches": "archesproject/arches#stable/7.6.12",
        "arches-modular-reports": "archesproject/arches-modular-reports#beta/1.0.0b0"
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

This document explains the structure and purpose of a JSON configuration used to define custom reports in Arches. It breaks down key components and their configuration properties to help you understand how to control the layout and display of resource data.

### Top-Level Structure

At a high level, the configuration defines a report with a name and a list of UI components that will be rendered in the report interface.

```json
{
  "name": "Untitled Report",
  "components": [ ... ]
}
```

Each entry in the `components` array defines a section of the report interface, such as the header, toolbar, tombstone (summary), or tabs.

---

### Key Components

#### `ReportHeader`

Displays the report title or descriptor. The descriptor can include references to node values by referencing the node_alias from within `<>` brackets.
Additionally, if a node in brackets contains more than 1 entry (eg: concept-list or resource-instance-list) then the number of those values can be limited via the `node_alias_options` property and a separator character can be specified.

```json
{
    "component": "ReportHeader",
    "config": {
        "descriptor": "<name_node> - born on <date_of_birth>",
        "node_alias_options": {
            "name_node": {
                "limit": 3,
                "separator": "|"
            }
        }
    }
}
```

---

#### `ReportToolbar`

Adds export buttons and list tools to the report.

```json
{
    "component": "ReportToolbar",
    "config": {
        "lists": true,
        "export_formats": ["csv", "json-ld", "json"]
    }
}
```

---

#### `ReportTombstone`

Displays a summary or key metadata for the resource.

```json
{
  "component": "ReportTombstone",
  "config": {
    "node_aliases": [],
    "custom_labels": {},
    "image_node_alias": null <-- unused
  }
}
```

---

#### `ReportTabs`

Defines tabs for organizing the main content of the report.

```json
{
  "component": "ReportTabs",
  "config": {
    "tabs": [ ... ]
  }
}
```

Each tab contains components — typically `LinkedSections` — that organize content into visual sections.

---

### LinkedSections and Subcomponents

#### `LinkedSections`

Used within tabs to group and render multiple content sections.

Each `section` has a name and an array of components like `DataSection` or `RelatedResourcesSection`.

---

#### `DataSection`

Displays a group of nodes from the main resource graph. DataSection objects can be grouped together under a common name within LinkedSection components. By default, top-level node groups will appear as individual sections each with its own DataSection in the "Data" tab. For cardinality-n tiles, reports can optionally be filtered to limit the tile(s) displayed in the report.

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

#### `RelatedResourcesSection`

Displays resources related to this resource instance based on the related resource graph slug. By default the resource instance name and relationship is displayed. Other nodes from that related resource can be displayed by adding entries in the "node_aliases" array and those node names can be overwritten with the "custom_labels" object.
RelatedResourcesSection objects can be grouped together under a common name within LinkedSection components.

```json
{
    "component": "RelatedResourcesSection",
    "config": {
        "graph_slug": "digital",
        "node_aliases": [],
        "custom_labels": {}
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
