<%
Dim appEngineUrl
Dim objXmlHttp
Dim formBody
Dim strXML

appEngineUrl="http://epicollectserver.appspot.com/buildForm"

Set objWinHttp = Server.CreateObject("WinHttp.WinHttpRequest.5.1")
objWinHttp.Open "POST", appEngineUrl, False
objWinHttp.SetRequestHeader "Content-Type", "application/x-www-form-urlencoded"

formBody = ""
For Each key in Request.Form
 formBody = formBody & key
 formBody = formBody & "="
 formBody = formBody & Server.URLEncode(Request.Form(key))
 formBody = formBody & "&"
Next 

objWinHttp.Send formBody

strHTML = objWinHttp.responseText
Response.Write strHTML
Set objWinHttp = Nothing
%>
