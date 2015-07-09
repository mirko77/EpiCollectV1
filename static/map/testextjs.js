// JavaScript Document

    Ext.onReady(function(){


        // NOTE: This is an example showing simple state management. During development,
        // it is generally best to disable state management as dynamically-generated ids
        // can change across page loads, leading to unpredictable results.  The developer
        // should ensure that stable state ids are set for stateful components in real apps.
        Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
        
       var viewport = new Ext.Viewport({
            layout:'border',
            items:[
                new Ext.BoxComponent({ // raw
                    region:'north',
                    el: 'north',
                    height:32
                }),{
                    region:'south',
                    contentEl: 'south',
                    split:true,
                    height: 100,
                    minSize: 100,
                    maxSize: 200,
                    collapsible: true,
                    title:'Time Slider',
                    margins:'0 0 0 0'
                }, {
                    region:'east',
                    title: 'East Side',
                    collapsible: true,
                    split:true,
                    width: 225,
                    minSize: 175,
                    maxSize: 400,
                    layout:'fit',
                    margins:'0 5 0 0',
                    items:
                      new Ext.TabPanel({
                           
                        //title:'Chat Pane1l',
                        html:'<div id=\"update_view\">You are currently viewing all data</div><br><div id =\"graphs\"></div>',
                        border:false,
                        iconCls:'settings'
                    		
                        })
                 },{
                region:'west',
                    id:'west-panel',
                    title:'Navigation ',
                    split:true,
                    width: 200,
                    minSize: 175,
                    maxSize: 400,
                    collapsible: true,
					
                    margins:'0 0 0 5',
                    layout:'accordion',
                    layoutConfig:{
                        animate:true
                    },
                    items: [{
                        contentEl: 'west',
                        title:'Data points',
                        border:false,
                        iconCls:'nav',
						autoScroll:true
                    },{
                        title:'Data Variables',
                        html:'Please choose a value -<br><br><b>Serogroup:</b><br><br> <form id=\"serogroupform\" name=\"serogroupform\"><select name=\"a\" id =\"a\"><option value=\"1\">1</option><option value=\"2\">2</option><option value=\"3\">3</option><option value=\"4\">4</option><option value=\"5\">5</option><option value=\"6\">6</option><option value=\"7\">7</option><option value=\"8\">8</option><option value=\"9\">9</option><option value=\"10\">10</option></select><input type=\"button\" onclick=\"turnoffserogroup();\" value=\"Submit\"></form><br><b>Resistant/Susceptible:</b><br><br> <form id=\"statusform\" name=\"statusform\"><select name=\"a\" id =\"a\"><option value=\"1\">Resistant</option><option value=\"2\">Susceptible</option></select><input type=\"button\" onclick=\"turnoffstatus();\" value=\"Submit\"></form><br><b>Estimated age(from-to)</b>:<br><br> <form id=\"variableform\" name=\"variableform\"><select name=\"a\" id =\"a\"><option value=\"1\"><1</option><option value=\"2\">1-5</option><option value=\"3\">>5</option></select><select name=\"b\" id =\"b\"><option value=\"1\"><1</option><option value=\"2\">1-5</option><option value=\"3\"><5</option></select><input type=\"button\" onclick=\"turnoffvariable();\" value=\"Submit\"></form><br><a href=\"javascript:showAll();\">show all</a> ',
                        border:false,
                        iconCls:'settings'
                    },{
                        title:'Chat Panel',
                        html:'<iframe src="http://talkgadget.google.com/talkgadget/client" scrolling="no" frameborder="0" style="overflow:hidden; width: 100%; height: 250px;"></iframe>',
                        border:false,
                        iconCls:'settings'
                    }
					
					
					]
                },
                new Ext.TabPanel({
                   deferredRender:false,
                    activeTab:0,
				xtype: 'gmappanel',
                region: 'center',
                   items:[{
                        contentEl:'center1',
                        title: 'Map Panel',
                        closable:false,
                        autoScroll:true
                    },{
                        contentEl:'center3',
                        title: 'Project Panel',
                        autoScroll:true
                    },{
                        contentEl:'center2',
                        title: 'Google Earth',
                        autoScroll:true
                    }]
                })
             ]
        });
    //    Ext.get("hideit").on('click', function() {
     //      var w = Ext.getCmp('west-panel');
    //       w.collapsed ? w.expand() : w.collapse(); 
    //    });
    });
	
	