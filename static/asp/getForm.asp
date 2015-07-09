<%
Dim appEngineUrl
Dim objXmlHttp
Dim strXML

appEngineUrl="http://epicollectserver.appspot.com/getForm?"
For Each key in Request.QueryString
 appEngineUrl = appEngineUrl & key
 appEngineUrl = appEngineUrl & "="
 appEngineUrl = appEngineUrl & Request.QueryString(key)
 appEngineUrl = appEngineUrl & "&"
Next 

'Set objXmlHttp = Server.CreateObject("Msxml2.ServerXMLHTTP")
Set objXmlHttp = Server.CreateObject("WinHttp.WinHttpRequest.5.1")
objXmlHttp.open "GET", appEngineUrl
objXmlHttp.send

Response.ContentType = "text/XML"
strXML = objXmlHttp.responseText
Response.Write strXML
Set objXmlHttp = Nothing
%>
