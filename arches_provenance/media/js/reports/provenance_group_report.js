define([
    'jquery',
    'underscore',
    'arches', 
    'knockout',
    'models/graph',
    'viewmodels/card',
    'viewmodels/tile',
    'viewmodels/provisional-tile',
    'bindings/datatable', 
    'js-cookie',
    'templates/views/report-templates/provenance_group_report.htm'
], function($, _, arches, ko, GraphModel, CardViewModel, TileViewModel, ProvisionalTileViewModel, datatable, Cookies, provenanceGroupReportTemplate) {
    return ko.components.register('provenance_group_report', {
        viewModel: function(params) {
            params.configKeys = [];
            var self = this;

            const resourceid = params.report.report_json?.resourceinstanceid;
            const resourceName = params.report.report_json?.displayname;

            const nameNodegroupdId = "5bc65fd2-bb18-11ea-85a6-3af9d3b32b71";
            const nationalityNodegroupId = "a5cff5a3-e317-11eb-ba14-0a9473e82189";
            const typeOfGroupNodegroupId = "7275d2fe-2a65-11ec-b195-0a9473e82189";
            const statementNodegroupId = "9285a4ba-bb18-11ea-85a6-3af9d3b32b71";
            const externalIdentifierNodegroupId = "f5930746-bb18-11ea-85a6-3af9d3b32b71";
            const subGroupNodegroupId = "df216a34-bb18-11ea-85a6-3af9d3b32b71";
            const labelNodegroupId = "97f15d22-bb18-11ea-85a6-3af9d3b32b71";
            const contactNodegroupId = "ace43c39-f43b-11eb-ba14-0a9473e82189";
            const groupFormationNodegroupId = "c6dc61cc-bb18-11ea-85a6-3af9d3b32b71";
            const groupDissolutionNodegroupId = "c0a136c4-bba0-11ea-ad92-3af9d3b32b71";
            const groupEstablishmentNodegroupId =  "7c586770-eac9-11eb-ba14-0a9473e82189";
            const groupProfessionalActivityNodegroupId = "0c3baef0-e323-11eb-ba14-0a9473e82189";
            const groupIdentifierAssignmentNodegroupId = "42b0db83-e319-11eb-ba14-0a9473e82189";
            const sourceReferenceNodegroupId = "30e30626-c798-11ea-b94e-3af9d3b32b71";

            this.sojournNameNodegroupId = '7c586764-eac9-11eb-ba14-0a9473e82189';
            this.sojournStatementNodegroupId = '7c58675b-eac9-11eb-ba14-0a9473e82189';
            this.sojournStatementNameNodegroupId = '7c58675e-eac9-11eb-ba14-0a9473e82189';
            this.sojournTimespanNodegroupId = '7c58676a-eac9-11eb-ba14-0a9473e82189';
            this.sojournTimespanNameNodegroupId = '7c586758-eac9-11eb-ba14-0a9473e82189';
            this.sojournTimespanStatementNodegroupId = '7c586755-eac9-11eb-ba14-0a9473e82189';
            this.sojournTimespanStatementNameNodegroupId = '7c58676d-eac9-11eb-ba14-0a9473e82189';
            this.sojournTimespanDurationNodegroupId = '7c586761-eac9-11eb-ba14-0a9473e82189';
            this.sojournTimespanDurationNameNodegroupId = '7c586767-eac9-11eb-ba14-0a9473e82189';

            this.groupFormationStatementNodegroupId = 'c6dc7090-bb18-11ea-85a6-3af9d3b32b71';
            this.groupFormationStatementNameNodegroupId = 'c6dc734c-bb18-11ea-85a6-3af9d3b32b71';
            this.groupFormationNameNodegroupId = 'c6dc75f4-bb18-11ea-85a6-3af9d3b32b71';
            this.groupFormationTimespanNodegroupId = '32fdfc1d-e324-11eb-ba14-0a9473e82189';
            this.groupFormationTimespanNameNodegroupId = '32fdfc20-e324-11eb-ba14-0a9473e82189';
            this.groupFormationTimespanStatementNodegroupId = '32fdfc1a-e324-11eb-ba14-0a9473e82189';
            this.groupFormationTimespanStatementNameNodegroupId = '32fdfc14-e324-11eb-ba14-0a9473e82189';
            this.groupFormationTimespanDurationNodegroupId = '32fdfc17-e324-11eb-ba14-0a9473e82189';
            this.groupFormationTimespanDurationNameNodegroupId = '32fdfc11-e324-11eb-ba14-0a9473e82189';

            this.groupDissolutionNameNodegroupId = 'c0a1247c-bba0-11ea-ad92-3af9d3b32b71';
            this.groupDissolutionStatementNodegroupId = 'c0a121b6-bba0-11ea-ad92-3af9d3b32b71';
            this.groupDissolutionStatementNameNodegroupId = 'c0a129b8-bba0-11ea-ad92-3af9d3b32b71';
            this.groupDissolutionTimespanNodegroupId = 'c77b5163-17bf-11ec-b193-0a9473e82189';
            this.groupDissolutionTimespanNameNodegroupId = 'c77b5166-17bf-11ec-b193-0a9473e82189';
            this.groupDissolutionTimespanStatementNodegroupId = 'c77b5160-17bf-11ec-b193-0a9473e82189';
            this.groupDissolutionTimespanStatementNameNodegroupId = 'c77b515a-17bf-11ec-b193-0a9473e82189';
            this.groupDissolutionTimespanDurationNodegroupId = 'c77b515d-17bf-11ec-b193-0a9473e82189';
            this.groupDissolutionTimespanDurationNameNodegroupId = 'c77b5157-17bf-11ec-b193-0a9473e82189';

            this.professionalActivitynameNodegroupId = '0c3baed8-e323-11eb-ba14-0a9473e82189';
            this.professionalActivitystatementNodegroupId = '0c3baed5-e323-11eb-ba14-0a9473e82189';
            this.professionalActivitystatementNameNodegroupId = '0c3baeed-e323-11eb-ba14-0a9473e82189';
            this.professionalActivityTimespanNodegroupId = '0c3baee7-e323-11eb-ba14-0a9473e82189';
            this.professionalActivityTimespanNameNodegroupId = '0c3baeea-e323-11eb-ba14-0a9473e82189';
            this.professionalActivityTimespanStatementNodegroupId = '0c3baee1-e323-11eb-ba14-0a9473e82189';
            this.professionalActivityTimespanStatementNameNodegroupId = '0c3baee4-e323-11eb-ba14-0a9473e82189';
            this.professionalActivityTimespanDurationNodegroupId = '0c3baede-e323-11eb-ba14-0a9473e82189';
            this.professionalActivityTimespanDurationNameNodegroupId = '0c3baedb-e323-11eb-ba14-0a9473e82189';

            this.identifierDataAssignmentNodegroupId = '42b0db6b-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentNameNodegroupId = '42b0db7a-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentTimespanNodegroupId = '42b0db80-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentTimespanNameNodegroupId = '42b0db77-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentTimespanStatementNodegroupId = '42b0db74-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentTimespanStatementNameNodegroupId = '42b0db71-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentTimespanDurationNodegroupId = '42b0db7d-e319-11eb-ba14-0a9473e82189';
            this.identifierDataAssignmentTimespanDurationNameNodegroupId = '42b0db6e-e319-11eb-ba14-0a9473e82189';

            self.nationality = ko.observable();
            self.typeOfGroup = ko.observable();
            self.externalIdentifierUrl = ko.observable();
            self.externalIdentifierLabel = ko.observable();
            self.sourceReference = ko.observable();
            self.subgroup = ko.observable();
            self.label = ko.observable();
            self.statementData = ko.observableArray();
            self.groupFormationData = ko.observable();
            self.groupDissolutionData = ko.observable();
            self.groupEstablishmentData = ko.observable();
            self.groupProfessionalActivityData = ko.observable();
            self.groupIdentifierAssignmentData = ko.observable();
            self.proActivity = ko.observable();
            self.relatedResourceConfigs = ko.observableArray();
            self.nameRowData = ko.observable();
            self.externalIdentifierData = ko.observable();
            
            let selectedElement = null;
            self.handleMouseover = function(data, evt){
                if(selectedElement){
                    $(selectedElement).removeClass("hovered");
                }
                selectedElement = evt.currentTarget;
                if(evt.type == "mouseover"){
                    $(evt.currentTarget).addClass("hovered");
                }
            };
            
            // graphids of all graphs in provenance/the ones that can be related to Groups
            self.relatedResourceGraphs = {
                "Activity":"734d1558-bfad-11ea-a62b-3af9d3b32b71",
                // "Bidding":"21d83275-e88f-11ea-9fb6-0a1706e75f30",
                "Digital Object":"0044f7da-b4b6-11ea-84f7-3af9d3b32b71",
                "Event":"7c2205b2-baee-11ea-81b2-3af9d3b32b71",
                "Exhibition Concept":"2a7fb09a-bfa5-11ea-a62b-3af9d3b32b71",
                "Group":"d6774bfc-b4b4-11ea-84f7-3af9d3b32b71",
                "Person":"9ffb6fcc-b4b4-11ea-84f7-3af9d3b32b71",
                "Physical Object":"1810d182-b4b5-11ea-84f7-3af9d3b32b71",
                "Place":"f6e89030-b4b4-11ea-84f7-3af9d3b32b71",
                "Provenance Activity":"3d461890-b4b5-11ea-84f7-3af9d3b32b71",
                "Set":"bdba56bc-b4b5-11ea-84f7-3af9d3b32b71",
                "Textual Work":"6dad61aa-b4b5-11ea-84f7-3af9d3b32b71",
                "Visual Work":"933ee880-b4b5-11ea-84f7-3af9d3b32b71"
            };

            // Tile Editor

            this.resourceId = ko.observable();
            this.card = ko.observable();
            this.tile = ko.observable();
            this.displayname = ko.observable();
            this.showTileEditor = ko.observable(false);
            this.complete = params.complete || ko.observable();
            this.loading = params.loading || ko.observable(false);
            this.currentObservable = ko.observable();
            this.currentNodegroupId = ko.observable();
            this.mainTileId = ko.observable();

            this.onSaveSuccess = () => {
                self.getComplexBranchData(self.currentObservable(), self.currentNodegroupId(), self.mainTileId());
                self.showTileEditor(false);
                $('#name-summary-table').DataTable().ajax.reload();
            };
            this.onDeleteSuccess = () => {
                self.getComplexBranchData(self.currentObservable(), self.currentNodegroupId(), self.mainTileId());
                self.showTileEditor(false);
            };
            this.onSaveError = () => {};
            this.onDeleteError = () => {};

            const handlers = {
                'after-update': [],
                'tile-reset': []
            };
            this.on = function(eventName, handler) {
                if (handlers[eventName]) {
                    handlers[eventName].push(handler);
                }
            },

            this.close = function() {
                self.showTileEditor(false);
            };

            this.editTile = function(tileid, nodegroupid, parenttileid) {
                const url = tileid ?
                    `${arches.urls.provenance_editor}?tileid=${tileid}` :
                    `${arches.urls.provenance_editor}?nodegroupid=${nodegroupid}&resourceid=${resourceid}&parenttileid=${parenttileid}`;
                $.getJSON(url).then(function(data) {
                    console.log(data);
                    self.resourceId(data.resourceid);
                    self.displayname(data.displayname);
                    const createLookup = function(list, idKey) {
                        return _.reduce(list, function(lookup, item) {
                            lookup[item[idKey]] = item;
                            return lookup;
                        }, {});
                    };
                    const card = data.cards.find(card=>card.nodegroup_id == data.tile.nodegroup_id);
                    const graphModel = new GraphModel({
                        data: {
                            nodes: data.nodes,
                            nodegroups: data.nodegroups,
                            edges: []
                        },
                        datatypes: data.datatypes
                    });
                    self.reviewer = data.userisreviewer;
                    self.provisionalTileViewModel = new ProvisionalTileViewModel({
                        tile: self.tile,
                        reviewer: data.userisreviewer
                    });
    
                    self.widgetLookup = createLookup(
                        data.widgets,
                        'widgetid'
                    );
                    self.cardComponentLookup = createLookup(
                        data['card_components'],
                        'componentid'
                    );
                    self.nodeLookup = createLookup(
                        graphModel.get('nodes')(),
                        'nodeid'
                    );
    
                    self.card(new CardViewModel({
                        card: card,
                        graphModel: graphModel,
                        tile: data.tile,
                        resourceId: self.resourceId,
                        displayname: self.displayname,
                        handlers: handlers,
                        cards: data.cards,
                        tiles: data.tiles,
                        provisionalTileViewModel: self.provisionalTileViewModel,
                        cardwidgets: data.cardwidgets,
                        userisreviewer: data.userisreviewer,
                        loading: self.loading
                    }));

                    data.tile.noDefaults = true;
                    self.tile(new TileViewModel({
                        tile: data.tile,
                        card: self.card(),
                        graphModel: graphModel,
                        resourceId: self.resourceId,
                        displayname: self.displayname,
                        handlers: handlers,
                        userisreviewer: data.userisreviewer,
                        provisionalTileViewModel: self.provisionalTileViewModel,
                        loading: self.loading,
                        cardwidgets: data.cardwidgets,
                    }));
                    self.showTileEditor(true);
                });
            };
    
            // End of Tile Editor

            // Node Editor
            self.cardwidgetWidgetConfig = ko.observable();
            self.widgetWidgetConfig = ko.observable();
            self.nodeWidgetConfig = ko.observable();
            self.widgetTileid = ko.observable();
            let currentNodeBeingEdited;
            self.currentNodeValue = ko.observable();
            self.originalNodeValue = ko.observable();
            self.loadedWidget = ko.observable(false);

            self.openNodeEditor = function(){ 
                $('#cardinality1EditorModal').modal('show');
            }
            
            self.closeNodeEditor = function(){ 
                $('#cardinality1EditorModal').modal('hide');
            }

            self.buildStrObject = str => {
                return {[arches.activeLanguage]: {
                    'value': str,
                    'direction': arches.activeLanguageDir
                }};
            };

            self.getWidget = async(rawNodeValue, cardData) => {
                try {
                    self.loadedWidget(false);
                    currentNodeBeingEdited = cardData; // store current card data to update on save

                    const nodeid = rawNodeValue['@node_id'];
                    const tileid = rawNodeValue['@tile_id'];
                    self.widgetTileid(tileid);

                    // get widget config
                    let response = await fetch(`${arches.urls.provenance_editor}?nodeid=${nodeid}`);
                    let result = await response.json();
                    self.cardwidgetWidgetConfig(result.cardwidget);
                    self.widgetWidgetConfig(result.widget);
                    self.nodeWidgetConfig(result.node);

                    // get current value of node via tile
                    let tile = await fetch(arches.urls.api_tiles(tileid));
                    let tiledata = await tile.json();
                    self.currentNodeValue(tiledata.data[nodeid]);
                    self.originalNodeValue(self.currentNodeValue());

                    self.loadedWidget(true);
                } catch(error) {
                    console.error('Error:', error);
                };
            };

            

            self.saveNodeValue = async function() {
                this.loading(true);
                let formData = new FormData();
                formData.append('nodeid', self.nodeWidgetConfig().nodeid);
                // formData.append('data', self.currentNodeValue());
                if (self.widgetWidgetConfig().name === 'text-widget') {
                    formData.append('data', JSON.stringify(self.currentNodeValue()));
                } else {
                    formData.append('data', self.currentNodeValue());
                } 
                formData.append('resourceinstanceid', params.resourceinstanceid);
                formData.append('tileid', self.widgetTileid());

                let postNewNode = await fetch(arches.urls.api_node_value, {
                    method: 'POST',
                    credentials: 'include',
                    body: formData,
                    headers: {
                        "X-CSRFToken": Cookies.get('csrftoken')
                    }
                }).then(function(response) {
                    if(response.ok){
                        return response.json();
                    }
                }).then(function(data){
                    if (data.parenttile_id){ // if tile is a child tile, use parent tileid
                        self.getComplexBranchData(currentNodeBeingEdited, data.nodegroup_id, data.parenttile_id);
                    } else {
                        self.getComplexBranchData(currentNodeBeingEdited, data.nodegroup_id, data.tileid);
                    }
                    self.closeNodeEditor();
                });
                this.loading(false);
            };

            // End of Node Editor

            self.resourceName = resourceName;

            // helper function for getting to the template
            self.getValue = function(obj, attrs, missingValue='') {
                try {
                    return attrs.reduce(function index(obj, i) {return obj[i];}, obj) || missingValue;
                } catch(e) {
                    return missingValue;
                }
            };



        // ----------------- begin name table definition --------------------------

            // create name table columns and name table tableconfig object
            const nameColumns = [
                {"title": "Name", "orderable": true, targets: 0, "name": "5bc66298-bb18-11ea-85a6-3af9d3b32b71", "data": "name.name_content.@display_value", "defaultContent": ""},
                {"title": "Type", "orderable": true, targets: 0, "name": "5bc66360-bb18-11ea-85a6-3af9d3b32b71", "data": "name.name_type.@display_value", "defaultContent": ""},
                {"title": "Source", "orderable": false, targets: 0, "data": "name.name_source_reference.@display_value", "defaultContent": ""},
                {"title": "", "orderable": false, targets: 0, "data": "tileid", "defaultContent": "", "autowidth": false, "width": "10px",
                    "render": function() {
                        var t = "<button type='button' class='btn' style='font-weight:bold; font-size:large; width:5px;' data-toggle='modal' data-target='#nameModal'>+</button>";
                        return t;
                    } 
                },
            ];

            // create name table tableconfig object using columns defined above
            self.nameTableConfig = {
                tableName: 'name',
                paging: true,
                searching: true,
                scrollY: "250px",
                columns: nameColumns,
                searchDelay: 400,
                order: [],
                processing: true,
                serverSide: true,
                scroller: true,
                deferRender: true,
                errMode: 'Ignore',
                ajax: {
                    url: arches.urls.provenance_report + '?resourceid=' + resourceid + '&nodegroupid=' + nameNodegroupdId,
                    dataSrc: function(json) {
                        for (el of json.data) {
                            for (const [key, value] of Object.entries(el['name'])) {
                                if (typeof value === 'object' && !value.hasOwnProperty('@display_value')) {
                                    value['@display_value'] = '';
                                }
                            }
                        }
                        return json.data;
                    }
                },
            };

        // ----------------- end name table definition --------------------------



        // ----------------- begin source reference table definition --------------------------

            // create source reference table columns and source reference table tableconfig object
            const sourceReferenceColumns = [
                {"title": "Source Reference", "orderable": true, targets: 0, "data": "reference", "name": "name", "defaultContent": "",
                    "render": function(data) {
                        var t = `<a href='/report/${data.resourceinstanceid}' target='_blank' style="color:blue;">${data.name}</a>`
                        return t;
                    }
                },
            ];

            self.sourceReferenceTableConfig = {
                tableName: 'sourceReferences',
                paging: true,
                searching: true,
                scrollY: "250px",
                columns: sourceReferenceColumns,
                searchDelay: 400,
                order: [],
                processing: true,
                serverSide: true,
                scroller: true,
                deferRender: true,
                errMode: 'Ignore',
                ajax: {
                    url: arches.urls.provenance_source_references + '?resourceid=' + resourceid + '&nodegroupid=' + sourceReferenceNodegroupId,
                    dataSrc: function(json) {
                        return json.data
                    }
                },
            };

        // ----------------- end source reference table definition --------------------------



        // ----------------- begin summary table definitions --------------------------

            // create table configs for tables with columns at different levels of graph
            // name (string) - name of the table config. will be appended with 'TableConfig'
            // columns (array) - datatables columns array
            // nodegroupId (string) - nodegroupid of the branch you would like to get data for
            // nodes (array) - nodeids of the specific nodes you would like to get data for from within the branch
            self.createSummaryTableConfig = function(name, columns, nodegroupId, nodes) {
                self[name + "TableConfig"] = {
                    paging: true,
                    searching: true,
                    scrollY: "250px",
                    // scrollY: 20,
                    columns: columns,
                    searchDelay: 400,
                    order: [],
                    processing: true,
                    serverSide: true,
                    scroller: true,
                    deferRender: true,
                    errMode: 'Ignore',
                    ajax: {
                        url: arches.urls.provenance_summary_table + '?' + new URLSearchParams ({
                            resourceid: resourceid,
                            nodegroupid: nodegroupId,
                            nodes: nodes
                        }),
                        dataSrc: function(json) {
                            return json.data;
                        }
                    },
                };
            };

            const professionalActivityColumns  = [
                {"title": "Location", "orderable": true, targets: 0, "data": "related_resource", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return "<a href=/report/" + data.relatedresourceinstanceid + " target=_blank style='color:blue;'>" + data.name.en.value + "</a>";
                        }
                        else {
                            return '';
                        }
                    } 
                },
                {"title": "Time Span", "orderable": true, targets: 0, "data": "child_nodegroups.0c3baee7-e323-11eb-ba14-0a9473e82189.0.child_nodegroups.0c3baeea-e323-11eb-ba14-0a9473e82189.0.0c3baef5-e323-11eb-ba14-0a9473e82189", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return JSON.parse(data).en.value;
                        }
                        else {
                            return '';
                        }
                    }
                },
                {"title": "Type", "orderable": true, targets: 0, "data": "0c3baefb-e323-11eb-ba14-0a9473e82189", "defaultContent": ""},
                {"title": "", "orderable": false, targets: 0, "data": "tileid", "defaultContent": "", "autowidth": false, "width": "10px",
                    "render": function(data) {
                        var t = "<button type='button' class='btn' style='font-weight:bold; font-size:large; width:5px;' data-toggle='modal' data-target='#professionalActivityModal'>+</button>";
                        return t;
                    } 
                },
            ];

            const establishmentColumns  = [
                {"title": "Location", "orderable": true, targets: 0, "data": "related_resource", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return "<a href=/report/" + data.relatedresourceinstanceid + " target=_blank style='color:blue;'>" + data.name.en.value + "</a>";
                        }
                        else {
                            return '';
                        }
                    }    
                },
                {"title": "Time Span", "orderable": true, name: "7c5867a1-eac9-11eb-ba14-0a9473e82189", targets: 0, "data": "child_nodegroups.7c58676a-eac9-11eb-ba14-0a9473e82189.0.child_nodegroups.7c586758-eac9-11eb-ba14-0a9473e82189.0.7c5867a1-eac9-11eb-ba14-0a9473e82189", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return JSON.parse(data).en.value;
                        }
                        else {
                            return '';
                        }
                    }
                },
                {"title": "Type", "orderable": true, targets: 0, "data": "7c58678a-eac9-11eb-ba14-0a9473e82189", "defaultContent": ""},
                {"title": "", "orderable": false, targets: 0, "data": "tileid", "defaultContent": "", "autowidth": false, "width": "10px",
                    "render": function(data) {
                        var t = "<button type='button' class='btn' style='font-weight:bold; font-size:large; width:5px;' data-toggle='modal' data-target='#establishmentModal'>+</button>";
                        return t;
                    } 
                },
            ];

            const identifierAssignmentColumns  = [
                {"title": "Name", "orderable": true, targets: 0, "data": "related_resource.name", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return data.en.value;
                        }
                        else {
                            return '';
                        }
                    }
                },
                {"title": "Type", "orderable": true, targets: 0, "data": "42b0db9e-e319-11eb-ba14-0a9473e82189", "defaultContent": ""},
                {"title": "Data Assigner", "orderable": true, targets: 0, "data": "child_nodegroups.42b0db6b-e319-11eb-ba14-0a9473e82189.0.42b0db8c-e319-11eb-ba14-0a9473e82189", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return JSON.parse(data).en.value;
                        }
                        else {
                            return '';
                        }
                    }
                },
                {"title": "", "orderable": false, targets: 0, "data": "tileid", "defaultContent": "", "autowidth": false, "width": "10px",
                    "render": function(data) {
                        var t = "<button type='button' class='btn' style='font-weight:bold; font-size:large; width:5px;' data-toggle='modal' data-target='#identifierModal'>+</button>";
                        return t;
                    } 
                },
            ];

            self.createSummaryTableConfig('professionalActivity', professionalActivityColumns, groupProfessionalActivityNodegroupId, ['0c3baf01-e323-11eb-ba14-0a9473e82189', '0c3baefb-e323-11eb-ba14-0a9473e82189', '0c3baef5-e323-11eb-ba14-0a9473e82189']);
            self.createSummaryTableConfig('establishment', establishmentColumns, groupEstablishmentNodegroupId, ['e5f12154-17c1-11ec-b193-0a9473e82189', '7c5867a1-eac9-11eb-ba14-0a9473e82189', '7c58678a-eac9-11eb-ba14-0a9473e82189']);
            self.createSummaryTableConfig('identifierAssignemnt', identifierAssignmentColumns, groupIdentifierAssignmentNodegroupId, ['42b0dbab-e319-11eb-ba14-0a9473e82189', '42b0db9e-e319-11eb-ba14-0a9473e82189', '42b0db8c-e319-11eb-ba14-0a9473e82189']);
            
        // ----------------- end summary table defitions --------------------------
        
        

        // ----------------- begin get simple branch data --------------------------

            // helper function to get values for a given nodegroup
            // generally used to get a single value from a cardinality "1" node/ndoegroup
            // cardData (ko.observable) - observable that will hold the final data
            // nodegroupid (string) - nodegroupid of the branch you are interested in
            // path (array) - path to data in the label_based_graph return
            self.getSimpleBranchData = function(cardData, nodegroupid, path) {
                const searchParams = new URLSearchParams({
                    resourceid: resourceid,
                    nodegroupid: nodegroupid
                });
                fetch(`${arches.urls.provenance_report}?${searchParams}`)
                    .then (response => response.json())
                    .then(result => {
                        if (result.data.length != 0) {
                            cardData(path.reduce(function index(result, i) {return result[i];}, result));
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            };

            // get values for all cardinality "1" nodegroups
            // self.getSimpleBranchData(self.typeOfGroup, typeOfGroupNodegroupId, ['data', '0', 'type', '@display_value']);
            // self.getSimpleBranchData(self.nationality, nationalityNodegroupId, ['data', '0', 'nationality', '@display_value']);
            self.getSimpleBranchData(self.sourceReference, sourceReferenceNodegroupId, ['data', '0', 'source_reference', 'instance_details']);
            self.getSimpleBranchData(self.subgroup, subGroupNodegroupId, ['data', '0', 'member_of_group', '@display_value']);
            self.getSimpleBranchData(self.label, labelNodegroupId, ['data', '0', '_label', '@display_value']);

        // ----------------- end get simple branch data --------------------------



        // ----------------- begin get complex branch data --------------------------

            // helper function to get values for a given nodegroup
            // generally used to get all the data of a deeply nested branch (ie formation, dissolution, etc)
            // cardData (ko.observable) - observable that will hold the final data
            // nodegroupid (string) - nodegroupid of the branch we are interested in
            // tileid (string) - optional tileid of the specific tile you would like to get data for
            self.getComplexBranchData = function(cardData, nodegroupid, tileid='') {
                const searchParams = new URLSearchParams ({
                    resourceid: resourceid,
                    nodegroupid: nodegroupid,
                    tileid: tileid
                });
                fetch(`${arches.urls.provenance_report}?${searchParams}`)
                    .then (response => response.json())
                    .then(result => {
                        cardData(result.data);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            };

            // get complex branch data
            self.getComplexBranchData(self.typeOfGroup, typeOfGroupNodegroupId);
            self.getComplexBranchData(self.nationality, nationalityNodegroupId);
            self.getComplexBranchData(self.externalIdentifierData, externalIdentifierNodegroupId);
            self.getComplexBranchData(self.groupFormationData, groupFormationNodegroupId);
            self.getComplexBranchData(self.groupDissolutionData, groupDissolutionNodegroupId);
            self.getComplexBranchData(self.statementData, statementNodegroupId);

        // ----------------- end get complex branch data --------------------------
        
        

        // ----------------- begin get related resources data --------------------------

            // create datatable table config object for related resource tables based on passed in params
            // name (string)- this will be appeneded with TableConfig to define the table config
            // resourcegraphto (string) - the graphid of the related resource graph you would like to create a table for
            self.createRelatedResourceConfig = function(name, resourcegraphto) {
                self[name + "RelatedTableConfig"] = {
                    tableName: name,
                    paging: true,
                    searching: true,
                    scrollY: "250px",
                    columns: [
                        {"title": "Related Resource", "orderable": true, targets: 0, "name": "name", "data": 'resourceinstance_to',
                            "render": function(data) {
                                return "<a href=/report/" + data.resourceid + " target=_blank style='color:blue;'>" + data.displayname + "</a>";
                            }
                        },
                        {"title": "Relationship Type", "orderable": true, targets: 0, "name": "relationshiptype", "data": "relationshiptype",
                            "render": function(data) {
                                if (data != null) {
                                    return "<a href=" + data + " target=_blank style='color:blue;'>" + data + "</a>";
                                }
                                else {
                                    return "No relationship type defined.";
                                }
                            }
                        }
                    ],
                    searchDelay: 400,
                    order: [],
                    processing: true,
                    serverSide: true,
                    scroller: true,
                    deferRender: true,
                    language: {
                        emptyTable: "No related " + name + " resources."
                    },
                    errMode: 'Ignore',
                    ajax: {
                        url: arches.urls.provenance_related_resources + '?' + new URLSearchParams ({
                            resourceid: resourceid,
                            resourcegraphto: resourcegraphto
                        }),
                        dataSrc: function(json) {
                            return json.related_resources;
                        }
                    },
                };
                return self[name + "RelatedTableConfig"];
            };

            // iterate over list of related resource graphids and create related resource table config objects
            for (var el in self.relatedResourceGraphs) { 
                self.relatedResourceConfigs.push(self.createRelatedResourceConfig(el, self.relatedResourceGraphs[el]));
            }

        // ----------------- end get related resources data --------------------------


            $('#formation-summary-table tbody').on( 'click', 'button', function() {
                self.currentObservable(self.groupFormationData);
                self.currentNodegroupId(groupFormationNodegroupId);
                self.mainTileId('');
            } );

            $('#dissolution-summary-table tbody').on( 'click', 'button', function() {
                self.currentObservable(self.groupDissolutionData);
                self.currentNodegroupId(groupDissolutionNodegroupId);
                self.mainTileId('');
            } );

            // jquery logic for buttons that expose modals
            $('#professional-activity-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#professional-activity-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.getComplexBranchData(self.groupProfessionalActivityData, groupProfessionalActivityNodegroupId, data.tileid);
                self.currentObservable(self.groupProfessionalActivityData);
                self.currentNodegroupId(groupProfessionalActivityNodegroupId);
                self.mainTileId(data.tileid);
            } );

            $('#establishment-activity-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#establishment-activity-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.getComplexBranchData(self.groupEstablishmentData, groupEstablishmentNodegroupId, data.tileid);
                self.currentObservable(self.groupEstablishmentData);
                self.currentNodegroupId(groupEstablishmentNodegroupId);
                self.mainTileId(data.tileid);
            } );

            $('#identifier-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#identifier-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.getComplexBranchData(self.groupIdentifierAssignmentData, groupIdentifierAssignmentNodegroupId, data.tileid);
                self.currentObservable(self.groupIdentifierAssignmentData);
                self.currentNodegroupId(groupIdentifierAssignmentNodegroupId);
                self.mainTileId(data.tileid);
            } );

            $('#name-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#name-summary-table').DataTable();
                var data = table.row($(this).parents('tr') ).data();
                self.nameRowData(data);
            } );

            // jquery logic for closing modals
            $('#closeformationmodal').click(function() {
                $('#formationModal').modal('hide');
            });
            
            $('#closedissolutionmodal').click(function() {
                $('#dissolutionModal').modal('hide');
            });
            
            $('#closeestablishmentmodal').click(function() {
                $('#establishmentModal').modal('hide');
            });
            
            $('#closepreofessionalActivitymodal').click(function() {
                $('#professionalActivityModal').modal('hide');
            });
            
            $('#closeindentifiermodal').click(function() {
                $('#identifierModal').modal('hide');
            });
            
            $('#closenamemodal').click(function() {
                $('#nameModal').modal('hide');
            });

            $('#closeCardinality1EditorModal').click(function() {
                $('#cardinality1EditorModal').modal('hide');
            });
            
            // suppress error that pops up when tables fail to load. This information can still be found in developer tools
            $.fn.dataTable.ext.errMode = 'ignore';
        },
        template: provenanceGroupReportTemplate
    });
});