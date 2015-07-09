var elevator;

var EcCheckboxGroup = Ext.extend(Ext.form.CheckboxGroup, {
	setValue:function(val){
		this.eachItem(function(item){ if(item.getXType()=="checkbox")item.setValue(false);})
		if (!val) return;
		var checkedBoxes = val.split(",");
		for(var i = 0; i < checkedBoxes.length; i++)
		{
			box = this.getBox(checkedBoxes[i]); 
			if(box) box.setValue(true);
		}
	},
	getValue:function()
	{	
		var res = "";
		this.eachItem(function(box)
		{
			if(box.getValue() && box.getXType()=="checkbox")
			{
				res += (res == "" ? "" : ",") + box.name;
			}
		});
		return res;
	}
});

var EcEntryWindow = function(conf, imageUrl)
{
	 EcEntryWindow.superclass.constructor.call(this, conf);
	 this.imageUploadUrl = imageUrl;
}

Ext.extend(EcEntryWindow, Ext.Window, {
	closeAction:'hide',
	buttons:[{text:'Save'},{text:'Cancel'}],
	title: 'Add/edit Entry',
	width: Ext.getBody().getWidth() * 0.75,
	height: Ext.getBody().getHeight() * 0.75,
	modal: true,
	fPanel: {},
	resizable: false,
	imageUploadUrl: '',
	project: '',
	setEntry: function(rec) //
	{
		this.entry = rec;
	},
	mapPanel: new Ext.Panel({
		title:'Location', 
		anchor:'100% 50%',
		layout: 'absolute',
		items:[
		       new Ext.form.TextField({
		    	   id:'geoSearch',
		    	   name:'geoSearch',
		    	   x:0,y:0,
		    	   width: 300
		       }),
		       new Ext.Button({
		    	   text:'search',
		    	   x:305, y: 0,
		    	   width:80
		    	   
		       }),
		       new Ext.Panel({
		    	   anchor: '100% 100%',
		    	   x: 0,
		    	   y:25,
		    	   xtype: 'gmappanel',
		    	   html: '<div id="gmap" style="width: 100%; height: 100%" ></div>',
		    	   
		})]
	}),
	imagePanel: {},
	entry: false, //Ext.data.Record
	form: [],
	layout: 'column',
	map: {},
	marker:{},
	getParams: function()
	{
		params = this.fPanel.getForm().getFieldValues();
		for(var i =0; i < this.form.length; i++)
		{
			if(this.form[i].type == "select")
			{
				params[this.form[i].name] = this.fPanel.get(this.form[i].name).getValue();
			}
		}
		return params;
	},
	render: function(ele)
	{
		
		this.fPanel = new Ext.form.FormPanel({
			autoScroll: true,
			title:'Entry Details', 
			url:'/saveEntryWeb',
			method:'POST',
			anchor:'100% 100%',
			labelAlign: 'left',
			labelSeparator: ' ',
			padding: 5,
			defaults: {
		        // applied to each contained item
		        anchor:'90% right',
		        msgTarget: 'side'
		    }
		});
		for(var i =0; i < this.form.length; i++)
		{
			var ctrl;
			var conf = {
					id: this.form[i].name,
					name: this.form[i].name,
					fieldLabel: this.form[i].label,
					allowBlank: !this.form[i].required,
					validationEvent:'blur'
			};
			switch(this.form[i].type)
			{
				case 'input':
					if(this.form[i].numeric)
						conf.regex = /^[0-9]*$/;
						conf.regexText = 'The value of this field must be numeric';
					ctrl = new Ext.form.TextField(conf);
					break;
				case 'select':
					
					conf.items = [];
					conf.vertical = true;
					conf.columns = 1;
					for (var j = 0; j < this.form[i].options.length; j++)
					{
						conf.items.push({name:this.form[i].options[j].value, boxLabel:this.form[i].options[j].label})
					}
					ctrl = new EcCheckboxGroup(conf);
					break;
				case 'select1':
					var data = [];
					conf.forceSelection = true;
					for (var j = 0; j < this.form[i].options.length; j++)
					{
						data.push([this.form[i].options[j].value, this.form[i].options[j].label])
					}
					conf.typeAhead= true,
					conf.triggerAction= 'all',
					conf.lazyRender=true,
					conf.mode= 'local',
					conf.store= new Ext.data.ArrayStore({
				        id: 0,
				        fields: [
				            'value',
				            'label'
				        ],
				        data: data
				    }),
				    conf.valueField= 'value',
				    conf.displayField= 'label'
					conf.mode = 'local';
					
					ctrl = new Ext.form.ComboBox(conf);
					break;
				case 'textarea':
					ctrl = new Ext.form.TextArea(conf);
					break;
			}
			this.fPanel.add(ctrl);
			ctrl.clearInvalid();
		}
		this.fPanel.add(new Ext.form.TextField({
			id:'latitude',
			fieldLabel:'Latitude',
			name:'latitude',
			value: '0',
			readOnly: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'longitude',
			fieldLabel:'Longitude',
			name:'longitude',
			value: '0',
			readOnly: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'altitude',
			fieldLabel:'Altitude',
			name:'altitude',
			value: '0',
			readOnly: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'photo',
			fieldLabel:'photoPath',
			name:'photo',
			readOnly: true,
			hidden: true,
			hideLabel:true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'key',
			fieldLabel:'Key',
			name:'key',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'dateCreated',
			fieldLabel:'Date created',
			name:'dateCreated',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'deviceId',
			fieldLabel:'Device Id',
			name:'deviceId',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'entryId',
			fieldLabel:'Entry Id',
			name:'entryId',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'lastEdited',
			fieldLabel:'Last Edited',
			name:'lastEdited',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'timeUploaded',
			fieldLabel:'Time Uploaded',
			name:'timeUploaded',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'enterpriseName',
			fieldLabel:'Enterprise Name',
			name:'enterpriseName',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		this.fPanel.add(new Ext.form.TextField({
			id:'projectName',
			fieldLabel:'Project Name',
			name:'projectName',
			readOnly: true,
			hidden: true,
			hideLabel: true
		}));
		
		this.imagePanel = new Ext.FormPanel({
			title:'Entry Image', 
			url:this.imageUploadUrl,
			anchor:'100% 50%',
			fileUpload: true,
			items:[
				{
				    xtype: 'fileuploadfield',
				    id: 'form-file',
				    emptyText: 'Select an image',
				    fieldLabel: 'Photo',
				    name: 'photo-path',
				    buttonText: '',
				    buttonCfg: {
				        iconCls: 'upload-icon'
				    }
				    
				},
				{
					xtype:'panel',
					id:'newPhoto'
				}
			]
		});
		this.imagePanel.items.get(0).on('fileselected', function(){
			
			this.imagePanel.getForm().submit({
				params: this.getParams(),
				success:function(form, action)
				{
					if(action.result != "")
					{
						Ext.getCmp('newPhoto').update('<img src="/displayImage/' + action.result.msg + '" alt="new Photo" height="100%" width="50%" />');
						//update form URL
						form.url = action.result.newUrl;
						Ext.getCmp('photo').setValue(action.result.msg);
					}
				}
			}
		)}, this);
			
		EcEntryWindow.superclass.render.call(this, ele);
		
		this.add([{columnWidth: 0.5,border:false, layout:'anchor', height: this.getInnerHeight(),autoScroll: true},{columnWidth: 0.5,border:false, layout:'anchor', height: this.getInnerHeight()}]);
		
		this.items.get(0).add(this.fPanel);
		this.items.get(1).add(this.mapPanel);
		this.items.get(1).add(this.imagePanel);
		this.buttons[0].on('click', function(){
			if(this.fPanel.getForm().isValid()){
				this.fPanel.getForm().submit({
					params:this.getParams(),
					success: function(form, action)
					{
						Ext.getCmp('popup').fireEvent('saved', null);
						Ext.getCmp('popup').hide();
					}
				});
			}
			else
			{
				Ext.MessageBox.alert("Please check your data", "The data you have entered does not match the rules for this form, please correct the data and try again.");
			}
		}, this);
		this.buttons[1].on('click', function(){
			this.hide();
		}, this);
		this.mapPanel.items.get(1).on('click', function()
				{
			req = { address: Ext.getCmp('geoSearch').getValue() };
			var gCoder = new google.maps.Geocoder();
			gCoder.geocode(req, function(results,status)
			{
				if (status == google.maps.GeocoderStatus.OK) {
						Ext.getCmp('popup').map.setCenter(results[0].geometry.location);
						Ext.getCmp('popup').map.setZoom(10);
						Ext.getCmp('popup').marker.setPosition(results[0].geometry.location);
						Ext.getCmp('latitude').setValue(results[0].geometry.location.lat());
						Ext.getCmp('longitude').setValue(results[0].geometry.location.lng());
						elevator.getElevationForLocations({'locations' : [results[0].geometry.location]}, function(results, status) {
							if(results[0])
							{
								Ext.getCmp('altitude').setValue(results[0].elevation);
							}
						});
				}else{}
			});
		}, this)
	},
	onShow:function(){
		mApi = google.maps;
		this.map = new mApi.Map(document.getElementById('gmap'),{ 
			  zoom: 0,
		      center: new mApi.LatLng(0,0),
		      mapTypeId: mApi.MapTypeId.ROADMAP
		 });
		
		this.marker = new mApi.Marker({
			position: new mApi.LatLng(0,0),
			map: this.map,
			draggable: true
		});
		elevator = new google.maps.ElevationService();
		mApi.event.addListener(this.map, 'click',function(ev){
			Ext.getCmp('popup').marker.setPosition(ev.latLng);
			Ext.getCmp('latitude').setValue(ev.latLng.lat());
			Ext.getCmp('longitude').setValue(ev.latLng.lng());
			elevator.getElevationForLocations({'locations' : [ev.latLng]}, function(results, status) {
				if(results[0])
				{
					Ext.getCmp('altitude').setValue(results[0].elevation);
				}
			});

		});
		mApi.event.addListener(this.marker, 'dragend',function(ev){
			
			Ext.getCmp('latitude').setValue(ev.latLng.lat());
			Ext.getCmp('longitude').setValue(ev.latLng.lng());
			elevator.getElevationForLocations({'locations' : [ev.latLng]}, function(results, status) {
				if(results[0])
				{
					Ext.getCmp('altitude').setValue(results[0].elevation);
				}
			});

		});
		
		if(this.entry)
		{
			//alert(this.entry.data["latitude"]);
			this.marker.setPosition(new google.maps.LatLng(this.entry.data["latitude"], this.entry.data["longitude"]));
			this.map.setCenter(new google.maps.LatLng(this.entry.data["latitude"], this.entry.data["longitude"]));
			this.map.setZoom(12);
			this.marker.setMap(this.map);
			Ext.getCmp('newPhoto').update('<img src="' +  this.entry.data["photo"]+ '" alt="new Photo" height="100%" width="50%" />');
			Ext.getCmp('form-file').setValue(this.entry.data["photo"].replace("showImageWithKey?imageKey=", ""));
			for(var c = 0; c < this.fPanel.items.length; c++)
			{
				cmp = this.fPanel.items.get(c);
				if(cmp.setValue)
					cmp.setValue(this.entry.data[cmp.id]);
				else
					alert(cmp.name);
			}
			Ext.getCmp('photo').setValue(this.entry.data["photo"].replace("showImageWithKey?imageKey=", ""));
		}else{
			
			for(var c = 0; c < this.fPanel.items.length; c++)
			{
				cmp = this.fPanel.items.get(c);
				if(cmp.setValue)
					cmp.setValue(null);
				else
					alert(cmp.name);
			}
			var dat=new Date();
			dat.setHours(dat.getUTCHours());
			
			this.fPanel.get('longitude').setValue(0);
			this.fPanel.get('latitude').setValue(0);
			this.fPanel.get('altitude').setValue(0);
			this.fPanel.get('deviceId').setValue(navigator.userAgent);
			this.fPanel.get('entryId').setValue(dat.getTime().toString());
			this.fPanel.get('dateCreated').setValue(dat.format('Y-m-d H:i:s.u'));
			Ext.getCmp('newPhoto').update('');
			Ext.getCmp('form-file').setValue('');
			this.marker.setPosition(new google.maps.LatLng(0,0));
			this.map.setCenter(new google.maps.LatLng(0,0));
			this.marker.setMap(this.map);
		}
		Ext.getCmp('projectName').setValue(this.project);
		Ext.QuickTips.init();
		
	}
});