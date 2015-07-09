
var ComboCheckboxGroup = Ext.extend(Ext.form.CheckboxGroup, {
	/// where val is a comma separated string of values
	
    setValue: function(val){
		
		this.eachItem(function(item){ if(item.getXType()=="checkbox")item.setValue(false);})
		var checkedBoxes = val.split(",");
		for(var i = 0; i < checkedBoxes.length; i++)
		{
			box = this.getBox(checkedBoxes[i]); 
			if(box) box.setValue(true);
		}

	},
	fireChecked: function(){
        var arr = [];
        this.eachItem(function(item){
            if(item.checked){
                arr.push(item);
            }
        });
        this.display.setValue(this.getValue());
        this.fireEvent('change', this, arr);
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
	},
	onRender: function(ct, position){
		        if(!this.el){
		        	this.display = new Ext.form.TriggerField({
		        			anchor:'100%',
		        			visible: true,
		        			hidden:false,
		        			id:'disp',
		        			editable:false,
		        			onTriggerClick:function(){this.fireEvent('trigger')}
		        	});
		        	
		        	this.boxPanel = new Ext.Panel({
		        		anchor:'100%',
		        		
		        		width:200,
		        		cls: 'x-combo-list-inner',
		        		collapsed:true,
		        		layout : {
		        			type: 'form',
		        			labelSeparator: ''
		        			
		        		},
		        		hideLabels:true,
		        		defaults:{anchor:'100%'}
		        	});
		        	for(var x = 0; x < this.items.length; x++)
		        	{
		        		
		        		this.boxPanel.add(new Ext.form.Checkbox({
		        			boxLabel : this.items[x].boxLabel,
		        			id: this.items[x].name,
		        			name: this.items[x].name
		        		
		        		}));
		        	}
		        	
		        	this.panel = new Ext.Panel({
		        		renderTo: ct,
		        		border: false,
		        		items: [this.display, this.boxPanel],
		        		layout:'anchor'
		        	});
		        	
		        	
		        	
		        	this.display.on('trigger',function(){
		        		
		        		this.boxPanel.render();
		        		
		        		this.boxPanel.show();
		        		this.boxPanel.toggleCollapse(true);
		        			        		
		        	},this);		        	
		        			        	
		        	this.el = this.panel.getEl();

		            var fields = this.boxPanel.findBy(function(c){
		                return c.isFormField;
		            }, this);
		            
		            this.items = new Ext.util.MixedCollection();
		            
		            this.items.addAll(fields);
		            if(this.value)this.setValue(this.value);
		        }
		
		//ComboCheckboxGroup.superclass.onRender.call(this, ct, position);
	}
});

Ext.reg('combocheckboxgroup', ComboCheckboxGroup);

