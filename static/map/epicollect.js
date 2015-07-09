// JavaScript Document

function ShowGraphs(a,b,c) {


//map.closeInfoWindow();


//document.getElementById('progress').style.display = "block";

//new Ajax.Updater('resultset', 'http://spneumoniae.mlst.net/earth/maps/byst1.asp?country='+country, { method: 'get' });


{
		var url1 = 'http://www.spatialepidemiology.net/epicollect/demo/graphs.asp?a='+a+'&b='+b+'&c='+c+'';
		////var pars = 'someParameter=ABC';
		
		var myAjax1 = new Ajax.Updater(
					'graphs', 
					url1, 
					{
						method: 'get', 
					    onComplete: showResponseGraphs
					});
		
	}

function showResponseGraphs(req1) {
//document.getElementById('showstcountries').innerHTML = req1.responseText;
//document.getElementById('progress').style.display = "none";
//document.getElementById('returntomap').style.display = "block";
//Overlayfirst.show();



}
   
function reportErrorGraphs(request1) {alert('Sorry. There was an error.');}
}