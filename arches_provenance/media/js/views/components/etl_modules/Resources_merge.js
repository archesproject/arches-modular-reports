define([
    'knockout',
    'jquery',
    'uuid',
    'arches',
    'templates/views/components/etl_modules/Resources_merge.htm',
    'viewmodels/alert-json',
], function(ko, $, uuid, arches, baseStringEditorTemplate, JsonErrorAlertViewModel) {
    const ViewModel = function(params) {
        const self = this;

        // Observables
        this.editHistoryUrl = `${arches.urls.edit_history}?transactionid=${ko.unwrap(params.selectedLoadEvent)?.loadid}`;
        this.load_details = params.load_details ?? {};
        this.itemToAdd = ko.observable();
        this.resourceBase = ko.observable();
        this.loadId = params.loadId || uuid.generate();
        this.showStatusDetails = ko.observable(false);
        this.text = ko.observable();  // Corrected
        this.formData = new FormData();
        this.moduleId = params.etlmoduleid;
        this.itemToAdd = ko.observable(''); // Observable for the input field
        this.mergeResources = ko.observableArray([]);
        this.dropdownnodes = ko.observableArray();
        this.InfoBase = ko.observable(false);
        this.flagMessage = ko.observable(false);
        this.flagInfo = ko.observable(false);
        this.showSamePreview = ko.observable(false);
        this.showPreview = ko.observable(false);
        this.showresult = ko.observable(false);
        this.showPreviewwrite = ko.observable(false);
        this.showPreviewTalbewrite = ko.observable(false);
        this.message = ko.observable();
        //loading status
        this.selectedLoadEvent = params.selectedLoadEvent || ko.observable();
        this.statusDetails = this.selectedLoadEvent()?.load_description?.split("|");

        this.formatTime = params.formatTime;
        this.timeDifference = params.timeDifference;
        
        self.isValidUuid = function(value) {
            const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
            return uuidRegex.test(value);
        };
        this.BaseResource = () => {
            if ( this.mergeResources().includes(this.resourceBase())){
                this.mergeResources.remove(this.resourceBase());
            };
            self.flagMessage(false);
            self.InfoBase(true);
            self.showresult(false);
        };

        this.addResource = () => {
            if (this.itemToAdd() && this.isValidUuid(this.itemToAdd())) {
                // Check if the item already exists in the array
                if (!this.mergeResources().includes(this.itemToAdd()) && !this.resourceBase().includes(this.itemToAdd())) {
                    this.mergeResources.push(this.itemToAdd()); 
                    this.itemToAdd('');
                    self.flagMessage(false);
                    self.flagInfo(true)
                    self.showresult(false);
                    self.showPreview(true);
                    self.showSamePreview(false);
                }else{
                    self.showSamePreview(true);
                }
                
            }
        };
        
        // Function to delete a resource from the list
        this.deleteResource = (item) => {
            this.mergeResources.remove(item); // Remove the selected item from the observable array
        };

        this.addAllFormData = () => {
            if (self.mergeResources()) {
                self.formData = new FormData();
                self.formData.append('mergeResources', self.mergeResources());
                self.formData.append('resourceBase', self.resourceBase());
            }
        };

        this.displayInformation = function() {
            
            self.addAllFormData();      
            self.submit('Merge_information').then(data => {
                // Ensure self.text is updated as an observable
                self.dropdownnodes.removeAll();
                self.flagMessage(false);
                if(data.result.info=='Yes'){
                    self.showPreviewwrite(true);
                    self.showresult(true);
                    self.showPreviewTalbewrite(true);
                    for (var i = 0; i < data.result.data.length; i++){
                        self.dropdownnodes.push(data.result.data[i]);
                    }
                    
                }
                else{
                    self.showresult(false);
                    self.flagMessage(true);
                    self.message(data.result.info_message);
                }
            });
        };

        this.write = function() {
            
            self.showPreviewTalbewrite(false);
            self.addAllFormData();
            params.activeTab("import");
            self.submit('write').then(data => {
            }).fail( function(err) {
                self.alert(
                    new JsonErrorAlertViewModel(
                        'ep-alert-red',
                        err.responseJSON["data"],
                        null,
                        function(){}
                    )
                );
            });
        };
        
        this.submit = function(action) {
            self.formData.append('action', action);
            self.formData.append('load_id', self.loadId);
            self.formData.append('module', self.moduleId);
            return $.ajax({
                type: "POST",
                url: arches.urls.etl_manager,
                data: self.formData,
                cache: false,
                processData: false,
                contentType: false,
            });
        };
        
    }

    // Register the component
    ko.components.register('Resources_merge', {
        viewModel: ViewModel,
        template: baseStringEditorTemplate,
    });

    // Return ViewModel
    return ViewModel;
});