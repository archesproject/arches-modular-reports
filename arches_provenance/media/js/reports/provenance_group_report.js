define([
    'arches', 
    'knockout', 
    'bindings/datatable', 
    'templates/views/report-templates/provenance_group_report.htm'
], function(arches, ko, datatable, provenanceGroupReportTemplate) {
    return ko.components.register('provenance_group_report', {
        viewModel: function(params) {
            params.configKeys = [];
            var self = this;
            // define params for custom report here
            // ReportViewModel.apply(this, [params]);

            const resourceid = params.report.report_json.resourceinstanceid;
            const resourceName = params.report.report_json.displayname;

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

            self.cardwidget = ko.observable();
            self.widget = ko.observable();
            self.node = ko.observable();
            self.newValue = ko.observable();
            self.showModal = ko.observable(false);
            
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

            self.resourceName = resourceName;

            self.getValue = function(obj, attrs, missingValue='') {
                try {
                    return attrs.reduce(function index(obj, i) {return obj[i];}, obj) || missingValue;
                } catch(e) {
                    return missingValue;
                }
            };
                        
            self.createTableConfig = function(name, columns, nodegroupId) {
                self[name + "TableConfig"] = {
                    tableName: name,
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
                        url: arches.urls.provenance_report + '?resourceid=' + resourceid + '&nodegroupid=' + nodegroupId,
                        dataSrc: function(json) {
                            for (el of json.data) {
                                for (const [key, value] of Object.entries(el[name])) {
                                    if (typeof value === 'object' && !value.hasOwnProperty('@display_value')) {
                                        value['@display_value'] = '';
                                    }
                                }
                            }
                            if (name === 'source_reference') {
                                return json.data[0].source_reference.instance_details
                            }
                            else {
                                return json.data;
                            }
                        }
                    },
                };
            };

            // helper function to get values for a given nodegroup
            self.getSimpleBranchData = function(nodegroupid, path, cardData) {
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

            // helper function to get values for a given nodegroup
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

            // helper function to get widgets 
            // self.getWidget = async(value, nodeid) => {
            self.getWidget = async(nodeid, value) => {
                try {
                    self.showModal(false);

                    let response = await fetch(`${arches.urls.provenance_editor}?nodeid=${nodeid}`);
                    let result = await response.json();
                    
                    console.log(result);
                    self.cardwidget(result.cardwidget);
                    self.widget(result.widget);
                    self.node(result.node);
                    self.newValue(value);

                    self.showModal(true);
                } catch(error) {
                    console.error('Error:', error);
                };
            };
            
            // create columns for each table
            const nameColumns = [
                {"title": "Name", "orderable": true, targets: 0, "name": "5bc66298-bb18-11ea-85a6-3af9d3b32b71", "data": "name.name_content.@display_value", "defaultContent": ""},
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

            const sourceReferenceColumns = [
                {"title": "Source Reference", "orderable": true, targets: 0, "data": "reference", "name": "name", "defaultContent": "",
                    "render": function(data) {
                        var t = `<a href='/report/${data.resourceinstanceid}' target='_blank' style="color:blue;">${data.name}</a>`
                        return t;
                    }
                },
            ];
            
            const contactColumns = [
                {"title": "Point of Contact", "orderable": false, targets: 0, "data": "contact_point.contact_point_content.@display_value", "defaultContent": ""},
                {"title": "Type of Contact", "orderable": false, targets: 0, "data": "contact_point.contact_point_type.@display_value", "defaultContent": ""},
                // {"title": "Statement Source", "orderable": false, targets: 0, "data": "contact_point.contact_point_label.@display_value", "defaultContent": ""},
            ];

            const professionalActivityColumns  = [
                {"title": "Location", "orderable": true, targets: 0, "data": "0c3baf01-e323-11eb-ba14-0a9473e82189", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return JSON.parse(data).en.value;
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
                {"title": "Location", "orderable": true, targets: 0, "data": "e5f12154-17c1-11ec-b193-0a9473e82189", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return JSON.parse(data).en.value;
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
                {"title": "Name", "orderable": true, targets: 0, "data": "42b0dbab-e319-11eb-ba14-0a9473e82189", "defaultContent": "",
                    "render": function(data) {
                        if (data) {
                            return JSON.parse(data).en.value;
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

            // create all table configs using columns defined above
            self.createTableConfig('name', nameColumns, nameNodegroupdId);
            // self.createTableConfig('contact_point', contactColumns, contactNodegroupId);

            self.sourceReferenceTableConfig = {
                tableName: 'sourceReferences',
                paging: true,
                searching: true,
                scrollY: "250px",
                // scrollY: 20,
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

            // create table configs for tables with columns at different levels of graph
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
            
            // get values for all cardinality "1" nodegroups
            // self.getSimpleBranchData(typeOfGroupNodegroupId, ['data', '0', 'type'], self.typeOfGroup);
            // self.getSimpleBranchData(nationalityNodegroupId, ['data', '0', 'nationality', '@display_value'], self.nationality);
            // self.getSimpleBranchData(sourceReferenceNodegroupId, ['data', '0', 'source_reference', 'instance_details'], self.sourceReference);
            // self.getSimpleBranchData(subGroupNodegroupId, ['data', '0', 'member_of_group', '@display_value'], self.subgroup);
            // self.getSimpleBranchData(labelNodegroupId, ['data', '0', '_label', '@display_value'], self.label);

            self.getComplexBranchData(self.typeOfGroup, typeOfGroupNodegroupId);
            self.getComplexBranchData(self.nationality, nationalityNodegroupId);
            // self.getComplexBranchData(self.sourceReference, sourceReferenceNodegroupId);
            // self.getComplexBranchData(self.subgroup, subGroupNodegroupId);
            // self.getComplexBranchData(self.label, labelNodegroupId);
            
           
            
            // these had to be separated because of the datatype
            // self.getSimpleBranchData(externalIdentifierNodegroupId, ['data', '0', 'exact_match', 'url'], self.externalIdentifierUrl);
            // self.getSimpleBranchData(externalIdentifierNodegroupId, ['data', '0', 'exact_match', 'url_label'], self.externalIdentifierLabel);
            
            self.getComplexBranchData(self.externalIdentifierData, externalIdentifierNodegroupId);

            // get complex branch data
            self.getComplexBranchData(self.groupFormationData, groupFormationNodegroupId);
            self.getComplexBranchData(self.groupDissolutionData, groupDissolutionNodegroupId);
            self.getComplexBranchData(self.statementData, statementNodegroupId);
            
            self.createRelatedResourceConfig = function(name, resourcegraphto) {
                self[name + "RelatedTableConfig"] = {
                    tableName: name,
                    paging: true,
                    searching: true,
                    scrollY: "250px",
                    // scrollY: 20,
                    columns: [
                        {"title": "Related Resource", "orderable": true, targets: 0, "name": "name", "data": 'resourceinstance_to',
                            "render": function(data) {
                                return "<a href=/report/" + data.resourceid + " target=_blank>" + data.displayname + "</a>";
                            }
                        },
                        {"title": "Relationship Type", "orderable": true, targets: 0, "name": "relationshiptype", "data": "relationshiptype",
                            "render": function(data) {
                                if (data != null) {
                                    return "<a href=" + data + " target=_blank>" + data + "</a>";
                                }
                                else {
                                    return "No relationship type defined.";
                                }
                            }
                        }
                    // {"title": "Identifier Content", "orderable": false, targets: 0, "data": "identifier.identifier_content.@display_value"},
                    // {"title": "Statement Source", "orderable": false, targets: 0, "data": "identifier.identifier_type.@display_value"},
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

            for (var el in self.relatedResourceGraphs) { 
                self.relatedResourceConfigs.push(self.createRelatedResourceConfig(el, self.relatedResourceGraphs[el]));
            }

            self.createSummaryTableConfig('professionalActivity', professionalActivityColumns, groupProfessionalActivityNodegroupId, ['0c3baf01-e323-11eb-ba14-0a9473e82189', '0c3baefb-e323-11eb-ba14-0a9473e82189', '0c3baef5-e323-11eb-ba14-0a9473e82189']);
            self.createSummaryTableConfig('establishment', establishmentColumns, groupEstablishmentNodegroupId, ['e5f12154-17c1-11ec-b193-0a9473e82189', '7c5867a1-eac9-11eb-ba14-0a9473e82189', '7c58678a-eac9-11eb-ba14-0a9473e82189']);
            self.createSummaryTableConfig('identifierAssignemnt', identifierAssignmentColumns, groupIdentifierAssignmentNodegroupId, ['42b0dbab-e319-11eb-ba14-0a9473e82189', '42b0db9e-e319-11eb-ba14-0a9473e82189', '42b0db8c-e319-11eb-ba14-0a9473e82189']);



            $('#professional-activity-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#professional-activity-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.getComplexBranchData(self.groupProfessionalActivityData, groupProfessionalActivityNodegroupId, data.tileid);
            } );

            $('#establishment-activity-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#establishment-activity-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.getComplexBranchData(self.groupEstablishmentData, groupEstablishmentNodegroupId, data.tileid);
            } );

            $('#identifier-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#identifier-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.getComplexBranchData(self.groupIdentifierAssignmentData, groupIdentifierAssignmentNodegroupId, data.tileid);
            } );

            $('#name-summary-table tbody').on( 'click', 'button', function() {
                var table = $('#name-summary-table').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                self.nameRowData(data);
            } );

            $.fn.dataTable.ext.errMode = 'ignore';

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

            $('#closeSummaryRoleModal').click(function() {
                $('#summaryRoleModal').modal('hide');
            });

            $('#closenationalityModal').click(function() {
                $('#nationalityModal').modal('hide');
            });

            $('#closeoverallDatesModal').click(function() {
                $('#overallDatesModal').modal('hide');
            });

            console.log(self);
            // console.log(params);

            self.getWidget(typeOfGroupNodegroupId);
        },
        template: provenanceGroupReportTemplate
    });
});

