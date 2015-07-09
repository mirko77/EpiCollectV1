
        function getRequestParameter ( parameterName ) {
            var queryString = window.location.search.substring(1);
            var parameterName = parameterName + "=";
            if ( queryString.length > 0 ) {
                begin = queryString.indexOf ( parameterName );
                if ( begin != -1 ) {
                    begin += parameterName.length;
                    end = queryString.indexOf ( "&" , begin );
                    if ( end == -1 ) {
                        end = queryString.length
                    }
                    return unescape ( queryString.substring ( begin, end ) );
                }
            }
            return "";
        }
        
        var totalItems=0;
        var currentlyEditing=null;
        var lastEdited=null;
        var allIDs=null;
 
        $(function() {
            $(".formLineEdit").hide();
            
            //load XML, if any
            var projectKey=getRequestParameter("projectKey");
            if (!projectKey)
                projectKey="ahBlcGljb2xsZWN0c2VydmVycg8LEgdQcm9qZWN0GMXqAQw";
 
            var formKey=getRequestParameter("formKey");
            if (!formKey)
                formKey="";
 
            var formName=getRequestParameter("formName");
            var formVersion=getRequestParameter("formVersion");
            if (formKey.length>0 || (formName.length>0 && formVersion.length>0) || projectKey.length>0) {
                var loadURL = "/getForm.asp?projectKey="+projectKey+"&formkey="+formKey+"&formName="+formName+"&formVersion="+formVersion;
                $.ajax({
                    type: "GET",
                    url: loadURL,
                    dataType: "xml",
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var errorString = errorThrown ? errorThrown : textStatus;
                        if (XMLHttpRequest.responseText.indexOf("No form")!=0) //don't show an error if there's just no form
                            $("#error").text("Error: "+errorString);
                    },
                    success:  function (xml) {
                        //OK, we've got an XML document. Now to populate form name, version number, etc.,
                        //and most importantly, the existing inputs.
                        
                        var inputCount=0;
                        //dive down from document, to the root <xforms> element, to its children...
                        $(xml).children().children().each( function() {
                            if (this.tagName=="model") {
                                var formName=$(this).find("submission").attr("id");
                                $("input[name=formName]").val(formName);
 
                                var allowDownloadEdits=$(this).find("submission").attr("allowDownloadEdits");
                                if (allowDownloadEdits=="true")
                                    $("input[name=allowDownloadEdits]").attr("checked", true);
                                
                                var versionNumber=$(this).find("submission").attr("versionNumber");
                                setVersionNumbersFor(versionNumber);
                            }
                            else if (this.tagName=="input") {
                                var inputDiv='<div id="textInput'+(inputCount++)+'" dropped="true" class="formLine"';
                                inputDiv+=getInputFlagsFor($(this));
                                inputDiv+='><div class="label">';
                                inputDiv+=$(this).find("label").text();
                                inputDiv+='</div><div class="formInput"><input name="inputID" value="';
                                inputDiv+=$(this).attr("ref");
                                inputDiv+='" value="'+$(this).attr("ref");
                                inputDiv+='" /></div></div>';
                                $("#destination").append(inputDiv);
                            }
                            else if (this.tagName=="textarea") {
                                var inputDiv='<div id="longText'+(inputCount++)+'" dropped="true" class="formLine"';
                                inputDiv+=getInputFlagsFor($(this));
                                inputDiv+='><div class="label">';
                                inputDiv+=$(this).find("label").text();
                                inputDiv+='</div><div class="formInput"><textarea name="textarea">';
                                inputDiv+=$(this).attr("ref");
                                inputDiv+='</textarea></div></div>';
                                $("#destination").append(inputDiv);
                            }
                            else if ((this.tagName=="select1") || (this.tagName=="select")) {
                                var inputDiv='<div id="';
                                var isSelect1 = this.tagName=="select1";
                                if (isSelect1)
                                    inputDiv+='selectOne'+(inputCount++);
                                else
                                    inputDiv+='selectMultiple'+(inputCount++);
                                inputDiv+='" dropped="true" class="formLine"';
                                inputDiv+=getInputFlagsFor($(this));
                                inputDiv+='>';
 
                                var inputRef=$(this).attr("ref");
                                var doneFirst=false;
                                $(this).children().each( function() {
                                    if (!doneFirst) {
                                        inputDiv+='<div class="label">'+$(this).text()+'</div>';
                                        doneFirst=true;
                                    }
                                    else {
                                        inputDiv+='<div class="formInput">';
                                        if (isSelect1)
                                            inputDiv+='<input type="radio" name="'+inputRef+'" value="'
                                        else
                                            inputDiv+='<input type="checkbox" name="'+inputRef+'" value="'
                                        inputDiv+=$(this).find("value").text()+'" />';
                                        inputDiv+='<div class="optionLabel">'+$(this).find("label").text()+'</div></div>';
                                    }
                                });
                                inputDiv+='</div>';
                                $("#destination").append(inputDiv);
                            }
                        });
                    },
                }); //ajax call
            }
            
            //make divs created out of XML clickable
            var destClicked=false;
            $("#destination").mousedown( function() {
                if (!destClicked) { //only do this once, or it might get messy
                    $("#destination").children().each( function() {
                        $(this).bind("click", function() {
                            showEditDetailsFor($(this));
                        });
                    });
                }
                destClicked=true;
            });
            
            //set up drag-and-drop stuff
            $("#textInput").draggable(
                {   connectToSortable:'#destination',
                    cursor:'move',
                    helper:'clone',
                }
            );
            $("#longText").draggable(
                {   connectToSortable:'#destination',
                    cursor:'move',
                    helper:'clone',
                }
            );
            $("#selectMultiple").draggable(
                {   connectToSortable:'#destination',
                    cursor:'move',
                    helper:'clone',
                }
            );
            $("#selectOne").draggable(
                {   connectToSortable:'#destination',
                    cursor:'move',
                    helper:'clone',
                }
            );
            $("#destination").sortable(
                {
                    change: function(event, ui) {
                        ui.placeholder.css({visibility: 'visible', border : '2px solid yellow'});
                    },
                    start: function(event, ui) {
                        ui.placeholder.css({visibility: 'visible', border : '2px solid yellow'});
                        var tempID=ui.item.attr("id");
                        if (tempID.indexOf("_")==-1) {
                            tempID=tempID+"_"+totalItems++;
                            ui.item.attr({id:tempID});
                        }
                    },
                    stop: function(event, ui) {
                        //load element details, and ensure they'll show up again when this item is clicked
                        destClicked=true; //otherwise we wind up with double-calls
                        showEditDetailsFor(ui.item);
                        if (ui.item.attr("dropped")!="true") { //if this is the first time it's dropped
                            $(".formLineEdit").find("input[type!=submit]").val(""); //wipe any existing values in the edit fields
                            ui.item.bind("click", function() {
                                showEditDetailsFor(ui.item);
                            });
                        }
                        ui.item.attr("dropped","true");
                    },
                }
            );
            
            //respond to inputs in the edit-details column
            $("input[name=done]").mouseup( function() {
                saveCurrentInput();
            });
            $("input[name=delete]").mouseup( function() {
                var really = confirm ("Delete this element?")
                if (really) {
                    $("#"+currentlyEditing).remove();
                    $(".formLineEdit").hide();
                }
            });
            $("input[name=addSelectMultiOption]").mouseup( function() {
                optionClone=$("#selectMultiOption").clone();
                cloneRemoveButton = optionClone.find("input[name=removeSelectMultiOption]");
                cloneRemoveButton.bind("mouseup", function() {
                    $(this).parent().remove();
                });
                $("#selectMultiEdit").append(optionClone);
            });
            $("input[name=addSelectOneOption]").mouseup( function() {
                optionClone=$("#selectOneOption").clone();
                cloneRemoveButton = optionClone.find("input[name=removeSelectOneOption]");
                cloneRemoveButton.bind("mouseup", function() {
                    $(this).parent().remove();
                });
                $("#selectOneEdit").append(optionClone);
            });
  
            //respond to an element being made chartable or unchartable:
            //former case - make it numeric, disable numeric option, activate pie/bar options, set to pie
            //latter case - enable numeric option, disable pie/bar options
            $("input[name=chart]").change( function() {
                if ($("input[name=chart]").attr("checked")) {
                    if (currentlyEditing.indexOf("textInput")==0) {
                        $("input[name=numeric]").attr("checked", true);
                        $("input[name=numeric]").attr("disabled", true);
                    }
                    $("input[name=pie]").attr("disabled", false);
                    $("input[name=pie]").attr("checked", true);
                    $("input[name=bar]").attr("disabled", false);
                    $("input[name=bar]").attr("checked", false);
                }
                else {
                    if (currentlyEditing.indexOf("textInput")==0)
                        $("input[name=numeric]").attr("disabled", false);
                    $("input[name=pie]").attr("checked", false);
                    $("input[name=pie]").attr("disabled", true);
                    $("input[name=bar]").attr("checked", false);
                    $("input[name=bar]").attr("disabled", true);
                }
            });
 
            //ensure you've only ever got pie or bar
            $("input[name=pie]").change( function() {
                $("input[name=bar]").attr("checked", !$("input[name=pie]").attr("checked"));
            });
            $("input[name=bar]").change( function() {
                $("input[name=pie]").attr("checked", !$("input[name=bar]").attr("checked"));
            });
 
            //convert form to XML, validate, save
            $("input[name=saveForm]").mouseup( function() {
                saveCurrentInput();
                var xml="";
                allIDs=new Array();
                $("#success").text("");
                $("#error").text("");
                var error=validateID("Form Name", $("input[name=formName]").val());
                
                //iterate over the form lines, creating XML and/or recording errors
                $("#destination > .formLine").each( function() {
                    if ($(this).attr("id").indexOf("textInput")==0) {
                        var inputLabel = $(this).find(".label").text();
                        var inputID = $(this).find("input:first").val();
                        error+=validateID(inputLabel, inputID);
                        xml+='<input ref="'+inputID+'"'+getInputFlagsFor($(this))+'> <label>'+inputLabel+'</label> </input>\n';
                    }
                    else if ($(this).attr("id").indexOf("longText")==0) {
                        var inputLabel = $(this).find(".label").text();
                        var inputID = $(this).find("textarea").val();
                        error+=validateID(inputLabel, inputID);
                        xml+='<textarea ref="'+inputID+'"'+getInputFlagsFor($(this))+'> <label>'+inputLabel+'</label> </textarea>\n';
                    }
                    else if ($(this).attr("id").indexOf("selectMultiple")==0) {
                        var inputLabel = $(this).find(".label").text();
                        var inputID = $(this).find("input:first").attr("name");
                        error+=validateID(inputLabel, inputID);
                        xml+='<select ref="'+inputID+'"'+getInputFlagsFor($(this))+'> <label>'+inputLabel+'</label> ';
                        $(this).find("input").each( function() {
                            xml+='<item><label>'+$(this).next().text()+'</label><value>'+$(this).attr("value")+'</value></item> ';
                        });
                        xml+='</select>\n';
                    }
                    else if ($(this).attr("id").indexOf("selectOne")==0) {
                        var inputLabel = $(this).find(".label").text();
                        var inputID = $(this).find("input:first").attr("name");
                        error+=validateID(inputLabel, inputID);
                        xml+='<select1 ref="'+inputID+'"'+getInputFlagsFor($(this))+'> <label>'+inputLabel+'</label> ';
                        $(this).find("input").each( function() {
                            xml+='<item><label>'+$(this).next().text()+'</label><value>'+$(this).attr("value")+'</value></item> ';
                        });
                        xml+='</select1>\n';
                    }
                });
                
                //check XML for flag errors
                if (xml.indexOf('required="true" readonly="true"')>=0)
                    error+="\nA form element may not be simultaneously flagged as required and read-only."
                if (xml.indexOf(' title="true"') != xml.lastIndexOf(' title="true"'))
                    error+="\nA form may have only one title element."
                if (xml.indexOf(' subtitle="true"') != xml.lastIndexOf(' subtitle="true"'))
                    error+="\nA form may have only one subtitle element."
                if (xml.split('chart=').length>4)
                    error+="\nA form may have no more than three chartable elements."
 
                //done - now, either report errors, or upload XML
                if (error.length>0) {
                    $("#error").text("Error: "+error);
                }
                else {
                    //we're error-free, we've got the XML, now send it to server
                    
                    $.ajax({
                        async: false,
                        cache: false,
                        type: "POST",
                        url: "/buildForm.asp",
                        data: {
                            "projectKey" : "ahBlcGljb2xsZWN0c2VydmVycg8LEgdQcm9qZWN0GMXqAQw",
                            "formKey" : formKey,
                            "formName" : $("input[name=formName]").val(),
                            "formVersion" : $("select[name=formVersion]").val(),
                            "allowDownloadEdits" : $("input[name=allowDownloadEdits]").attr("checked"),
                            "inputXML" : xml,
                        },
                        dataType: "string",
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            $("#error").text("Error: "+errorThrown);
                        },
                        success:  function (string) {
                            if (string.indexOf("Error:")>=0)
                                $("#error").text(string);
                            else {
                                formKey=$.trim(string);
                                $("#success").text("Save successful - this form is ready for use.");
                            }
                        },
                    });
                    
                    //increment version number for future saves
                    setVersionNumbersFor($("select[name=formVersion]").val());
                }
            });
        });
        
        function saveCurrentInput() {
            if (currentlyEditing==null)
                return;
 
            if (currentlyEditing.indexOf("textInput")==0) {
                var labelText=$("input[name=textInputLabel]").val();
                var idText=$("input[name=textInputValue]").val();
                $("#"+currentlyEditing+" > .label").text(labelText);
                $("#"+currentlyEditing).find("input[name=inputID]").val(idText);
                setFlagAttributes($('#'+currentlyEditing));
            }
            else if (currentlyEditing.indexOf("longText")==0) {
                var labelText=$("input[name=longTextLabel]").val();
                var idText=$("input[name=longTextValue]").val();
                $("#"+currentlyEditing+" > .label").text(labelText);
                $("#"+currentlyEditing).find("textarea[name=textarea]").val(idText);
                setFlagAttributes($('#'+currentlyEditing));
            }
            else if (currentlyEditing.indexOf("selectMulti")==0) {
                //set label, remove existing inputs
                var labelText=$("input[name=selectMultiLabel]").val();
                $("#"+currentlyEditing+" > .label").text(labelText);
                $("#"+currentlyEditing).find(".formInput").remove();
                $("#"+currentlyEditing).find(".optionLabel").remove();
                $("#"+currentlyEditing).find("input[type=checkbox]").remove();
 
                //plug in new ones
                var idText=$("input[name=selectMultiValue]").val();
                editDiv=$("#selectMultiEdit");
                editDiv.find(".selectOption").each( function() {
                    var optionLabel=$(this).find("input[name=multiOptionLabel]").val();
                    var optionValue=$(this).find("input[name=multiOptionValue]").val();
                    var newOption = '<div class="formInput"><input type="checkbox" name="'+idText+'" value="'+optionValue+'" /><div class="optionLabel">'+optionLabel+'</div></div>';
                    if ($("#"+currentlyEditing).html().indexOf(newOption)==-1)
                        $("#"+currentlyEditing).append(newOption);
                    $("#"+currentlyEditing).html($("#"+currentlyEditing).html().replace("<br><br>","<br>")); // I really have no idea why this is necessary
                });
                setFlagAttributes($('#'+currentlyEditing));
            }
            else if (currentlyEditing.indexOf("selectOne")==0) {
                //set label, remove existing inputs
                var labelText=$("input[name=selectOneLabel]").val();
                $("#"+currentlyEditing+" > .label").text(labelText);
                $("#"+currentlyEditing).find(".formInput").remove();
                $("#"+currentlyEditing).find(".optionLabel").remove();
                $("#"+currentlyEditing).find("input[type=radio]").remove();
 
                //plug in new ones
                var idText=$("input[name=selectOneValue]").val();
                editDiv=$("#selectOneEdit");
                editDiv.find(".selectOption").each( function() {
                    var optionLabel=$(this).find("input[name=oneOptionLabel]").val();
                    var optionValue=$(this).find("input[name=oneOptionValue]").val();
                    var newOption = '<div class="formInput"><input type="radio" name="'+idText+'" value="'+optionValue+'" /><div class="optionLabel">'+optionLabel+'</div></div>'
                    if ($("#"+currentlyEditing).html().indexOf(newOption)==-1)
                        $("#"+currentlyEditing).append(newOption);
                    $("#"+currentlyEditing).html($("#"+currentlyEditing).html().replace("<br><br>","<br>")); // I really have no idea why this is necessary
                });
                setFlagAttributes($('#'+currentlyEditing));
            }
        }
 
        function showEditDetailsFor ( object ) {
            saveCurrentInput();
 
            currentlyEditing=object.attr("id");
            if (currentlyEditing==lastEdited)
                return;
 
            $(".formLineEdit").hide();
            setDetailFlagsFor(object);
            $("#inputOptions").show();
 
            if (object.attr("id").indexOf("textInput")==0) {
                var inputLabel = $.trim(object.find(".label").text());
                var inputID = object.find("input[name=inputID]").val();
                if (inputLabel!="Text Input" || object.find("input[name=inputID]").attr("name")!="inputID") {
                    $("#textInputEdit").find("input[name=textInputLabel]").val(inputLabel);
                    $("#textInputEdit").find("input[name=textInputValue]").val(inputID);
                }
                $("#textInputEdit").show();
                $("input[name=numeric]").attr("disabled", false);
                $("input[name=chart]").attr("disabled", false);
            }
            else if (object.attr("id").indexOf("longText")==0) {
                var inputLabel = $.trim(object.find(".label").text());
                var inputID = object.find("textarea:first").val();
                if (inputLabel!="Long Text" || inputID!="") {
                    $("#longTextEdit").find("input[name=longTextLabel]").val(inputLabel);
                    $("#longTextEdit").find("input[name=longTextValue]").val(inputID);
                }
                $("#longTextEdit").show();
                $("input[name=numeric]").attr("disabled", true);
                $("input[name=chart]").attr("disabled", true);
            }
            else if (object.attr("id").indexOf("selectMultiple")==0) {
                var inputLabel = $.trim(object.find(".label:first").text());
                var inputID = object.find("input:last").attr("name");
                if (inputLabel!="Select Multiple" || inputID!="selectMulti") {
                    $("#selectMultiEdit").find("input[name=selectMultiLabel]").val(inputLabel);
                    $("#selectMultiEdit").find("input[name=selectMultiValue]").val(inputID);
                    var blankOption=$("#selectMultiEdit > .selectOption:first");
                    $("#selectMultiEdit > .selectOption").remove();
                    var addedChild=false;
                    object.children(".formInput").each( function() {
                        optionClone=blankOption.clone();
                        var optionLabel=$(this).find(".optionLabel").text();
                        optionClone.find("input[name=multiOptionLabel]").val(optionLabel);
                        var optionValue=$(this).find("input:first").attr("value");
                        optionClone.find("input[name=multiOptionValue]").val(optionValue);
                        cloneRemoveButton = optionClone.find("input[name=removeSelectMultiOption]");
                        cloneRemoveButton.bind("mouseup", function() {
                            $(this).parent().remove();
                        });
                        $("#selectMultiEdit").append(optionClone);
                        addedChild=true;
                    });
                    if (!addedChild)
                        $("#selectMultiEdit").append(blankOption);
                } //don't show defaults
                $("#selectMultiEdit").show();
                $("input[name=numeric]").attr("disabled", true);
                $("input[name=chart]").attr("disabled", false);
            }
            else if (object.attr("id").indexOf("selectOne")==0) {
                var inputLabel = $.trim(object.find(".label:first").text());
                var inputID = object.find("input:last").attr("name");
                if (inputLabel!="Select One" || inputID!="selectOne") {
                    $("#selectOneEdit").find("input[name=selectOneLabel]").val(inputLabel);
                    $("#selectOneEdit").find("input[name=selectOneValue]").val(inputID);
                    var blankOption=$("#selectOneEdit > .selectOption:first");
                    $("#selectOneEdit > .selectOption").remove();
                    var addedChild=false;
                    object.children(".formInput").each( function() {
                        optionClone=blankOption.clone();
                        var optionLabel=$(this).find(".optionLabel").text();
                        optionClone.find("input[name=oneOptionLabel]").val(optionLabel);
                        var optionValue=$(this).find("input:first").attr("value");
                        optionClone.find("input[name=oneOptionValue]").val(optionValue);
                        cloneRemoveButton = optionClone.find("input[name=removeSelectOneOption]");
                        cloneRemoveButton.bind("mouseup", function() {
                            $(this).parent().remove();
                        });
                        $("#selectOneEdit").append(optionClone);
                        addedChild=true;
                    });
                    if (!addedChild)
                        $("#selectOneEdit").append(blankOption);
                } //don't show defaults
                $("#selectOneEdit").show();
                $("input[name=numeric]").attr("disabled", true);
                $("input[name=chart]").attr("disabled", false);
            }
            lastEdited=currentlyEditing;
        }
 
        // converts an object's flags into a XML (or HTML div) attribute string
        function getInputFlagsFor ( object ) {
            var flags='';
            if (object.attr("required")=="true")
                flags+=' required="true"';
            if (object.attr("readonly")=="true")
                flags+=' readonly="true"';
            if (object.attr("title")=="true")
                flags+=' title="true"';
            if (object.attr("subtitle")=="true")
                flags+=' subtitle="true"';
            if (object.tagName="input" && object.attr("numeric")=="true")
                flags+=' numeric="true"';
            if (object.attr("chart")=="pie")
                flags+=' chart="pie"';
            else if (object.attr("chart")=="bar")
                flags+=' chart="bar"';
            return flags;
        }
 
        function setDetailFlagsFor ( object ) {
            //clear any existing flags
            $("#inputOptions").find("input[name=required]").attr("checked",false);
            $("#inputOptions").find("input[name=readonly]").attr("checked",false);
            $("#inputOptions").find("input[name=title]").attr("checked",false);
            $("#inputOptions").find("input[name=subtitle]").attr("checked",false);
            $("#inputOptions").find("input[name=numeric]").attr("checked",false);
            $("#inputOptions").find("input[name=chart]").attr("checked",false);
            $("#inputOptions").find("input[name=pie]").attr("checked",false);
            $("#inputOptions").find("input[name=pie]").attr("disabled",true);
            $("#inputOptions").find("input[name=bar]").attr("checked",false);
            $("#inputOptions").find("input[name=bar]").attr("disabled",true);
 
            //reset them as appropriate
            if (object.attr("required")=="true")
                $("#inputOptions").find("input[name=required]").attr("checked",true);
            if (object.attr("readonly")=="true")
                $("#inputOptions").find("input[name=readonly]").attr("checked",true);
            if (object.attr("title")=="true")
                $("#inputOptions").find("input[name=title]").attr("checked",true);
            if (object.attr("subtitle")=="true")
                $("#inputOptions").find("input[name=subtitle]").attr("checked",true);
            if (object.attr("numeric")=="true")
                $("#inputOptions").find("input[name=numeric]").attr("checked",true);
 
            if (object.attr("chart")=="pie") {
                $("#inputOptions").find("input[name=chart]").attr("checked",true);
                $("#inputOptions").find("input[name=pie]").attr("checked",true);
            }
            else if (object.attr("chart")=="bar") {
                $("#inputOptions").find("input[name=chart]").attr("checked",true);
                $("#inputOptions").find("input[name=bar]").attr("checked",true);
            }
        }
 
        //set the element's attributes as per the checkboxes in the edit-details column
        function setFlagAttributes ( object ) {
            object.attr("required", $("#inputOptions").find("input[name=required]").attr("checked"));
            object.attr("readonly", $("#inputOptions").find("input[name=readonly]").attr("checked"));
            object.attr("title", $("#inputOptions").find("input[name=title]").attr("checked"));
            object.attr("subtitle", $("#inputOptions").find("input[name=subtitle]").attr("checked"));
            object.attr("numeric", $("#inputOptions").find("input[name=numeric]").attr("checked"));
            if ($("#inputOptions").find("input[name=chart]").attr("checked"))
                object.attr("chart",  $("#inputOptions").find("input[name=pie]").attr("checked") ? "pie" : "bar");
            else
                object.attr("chart",null);
        }
 
        function setVersionNumbersFor(existingNumber) {
            //handle version number - annoyingly tricky
            var floatVersion = parseFloat(existingNumber);
            if (!isNaN(floatVersion)) {
                versionNumber1=floatVersion+0.1;
                versionNumber2=parseInt(floatVersion)+1;
                if ((""+versionNumber1).length>5) {
                    versionNumber1=(""+versionNumber1).substr(0,5);
                    while (versionNumber1.charAt(versionNumber1.length-1)=="0"
                           && versionNumber1.charAt(versionNumber1.length-2)!=".") {
                        versionNumber1=versionNumber1.substr(0,versionNumber1.length-1);
                    }
                }
                $("select[name=formVersion]").find("option:first").attr("name",versionNumber1);
                $("select[name=formVersion]").find("option:first").text(versionNumber1);
                $("select[name=formVersion]").find("option:last").attr("name",versionNumber2+".0");
                $("select[name=formVersion]").find("option:last").text(versionNumber2+".0");
                $("select[name=formVersion]").val(versionNumber1);
            }
        }
 
        function validateID(label, id) {
            id=$.trim(id);
            if (id.length<=1)
                return "\nThe ID '"+id+"' for "+label+" is invalid: values must be at least 2 characters long.";
 
            if (id.length>1 && id.substr(0,2)=="ec")
                return "\nThe ID '"+id+"' for "+label+" is invalid: values beginning with 'ec' are reserved for the EpiCollect system.";
 
            var re=new RegExp("^[a-zA-Z0-9]*$");
            if (!re.test(id))
                return "\nThe ID '"+id+"' for "+label+" is invalid: only numbers and ASCII letters are permitted. No other characters (including spaces) are allowed.";
 
            if ($.inArray(id, allIDs)>=0)
                return "\nThe ID '"+id+"' for "+label+" is invalid: IDs must be unique within a form, and must not be the same as the form name.";
 
            allIDs.push(id);
            return "";
        }
