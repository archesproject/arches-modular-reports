# Welcome to Arches Modular Reports!

Arches Modular Reports is an Arches Application that provides an alternate and more modular way to present and configure reports in Arches. 


Please see the [project page](http://archesproject.org/) for more information on the Arches project.


## Installation

If you are installing Arches Modular Reports for the first time, **we strongly recommend** that you install it as an Arches application into a existing (or new) project. Running Arches Modular Reports as a standalone project can provide some convienience if you are a developer contributing to the Arches Modular Reports project but you risk conflicts when upgrading to the next version of Arches Modular Reports.  

### If installing for development
Clone the arches-modular-reports repo and checkout the latest `dev/x.x.x` or any other branch you may be interested in. 
Navigate to the `arches-modular-reports` directory from your terminal and run:
 ```
pip install -e .
 ```

`Important`: Installing the arches-modular-reports app will install Arches as a dependency. This may replace your current install of Arches with a version from PyPi. If you've installed Arches for development using the `--editable` flag, you'll need to reinstall Arches using the `--editable` flag again after installing arches-modular-reports

### If installing for deployment, run:
```
pip install arches-modular-reports
```


## Project Configuration

1. If you don't already have an Arches project, you'll need to create one by following the instructions in the Arches [documentation](http://archesproject.org/documentation/).

2. When your project is ready add "arches_modular_reports", "arches_querysets", and "arches_component_lab" to INSTALLED_APPS **below** the name of your project:
    ```
    INSTALLED_APPS = (
        ...
        "my_project_name",
        "arches_modular_reports",
        "arches_querysets",
        "arches_component_lab"
    )
    ```

3. Next ensure arches, arches_modular_reports, dayjs, @primevue/forms, and @primeuix/themes are included as dependencies in package.json
    ```
    "dependencies": {
        "arches": "archesproject/arches#stable/7.6.12",
        "arches-modular-reports": "archesproject/arches-modular-reports#main",
        "dayjs": "^1.11.13",
        "@primevue/forms": "4.3.3",
        "@primeuix/themes": "1.0.1"
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

5. Start your project
    ```
    python manage.py runserver
    ```

6. Next cd into your project's app directory (the one with package.json) install and build front-end dependencies:
    ```
    npm install
    npm run build_development
    ```