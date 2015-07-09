function contactForm(userId, location)
{
         var myEmail = new Ext.form.TextField({
                  allowBlank:false,
                  id:'sender',
                  fieldLabel: 'My Email',
                  width:250,
                  validator: function(val){
                           return (val.match(/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6}$/i) != null);
                  }
         });
         
         var subject = new Ext.form.ComboBox({
                  allowBlank:false,
                  blankText:"You must chose a type of comment.",
                  editable:false,
                  emptyText: "Please select...",
                  forceSelection:true,
                  triggerAction: 'all',
                  lazyRender:true,
                  id:'feedbackType',
                  fieldLabel: 'Type of message',
                  store:[
                      ['1', 'Comment'],
                      ['2', 'Question'],
                      ['3', 'Bug report']
                  ],
                  width:250
         });
         
         var message = new Ext.form.TextArea({
                  allowBlank:false,
                  id:'message',
                  fieldLabel: 'Message',
                  width:250
         });
         
         var emform = new Ext.form.FormPanel({
                        baseParams:{
                            subject:window.location.href + " " + navigator.userAgent
                        },
                        buttonAlign:'center',
                        url:'sendFeedback.asp',
                        items:[
                            myEmail,
                            subject,
                            message
                        ]
                  });
         
              
         
         
         emform.addButton('Send',function(){
                  try{
                           if(emform.getForm().isValid()){
                                    emform.getForm().submit({
                                             params:{
                                                      msgType:subject.getValue()       
                                             },
                                             success:function(frm, action){
                                                      try{
                                                      popup.close();
                                                      }catch(err){Ext.MessageBox.alert('Error', err);}
                                             },
                                             failure:function(frm, action){
                                                      try{
                                                      alert(action.result.msg);
                                                      }catch(err){Ext.MessageBox.alert('Error', err);}
                                             }
                                             
                                    });
                           }
                           else
                           {
                                    Ext.MessageBox.alert('Please fill in all the form fields', 'Please enter values in all the fields');
                           }
                  }catch(err){Ext.MessageBox.alert('Error', err);}
         });
         emform.addButton('Cancel',function(){
                  popup.hide();
                  popup.destroy();
         });
         var popup = new Ext.Window({
                  
                  buttonAlign:'center',
                  buttons:[],
                  title: 'Leave feedback',
                  items:[emform],
                  padding:5,
                  layout:{
                           type:'form',
                           defaultMargins:{
                                    left: 5,
                                    right: 5,
                                    top: 5,
                                    bottom:5
                           }
                  },
                  width:400,
                  height:350
                  
         });
         popup.show();
         
        /* Recaptcha.create("6LfRMwkAAAAAAD6qcT9W2yobmjPlhzvX1hj-Uufx", "captcha", {
                  theme: "white",
                  callback: Recaptcha.focus_response_field,
                  lang: "en"
          });*/
}
