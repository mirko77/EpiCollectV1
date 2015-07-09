function validateLength1(v) {															   
	if(v.length == 0)
	{
		return true;				
	}
	if(v.length==348)
	{		
		return true;
	}
	else
	{
		return "length must be 348"
	}
}

function validateLength2(v){
	if(v.length == 0) 
	{
		return true;
	}
	if(v.length==351)
	{
		return true;
	}
	else
	{
		return "length must be 351"
	}
}
function validateLength3(v){
	if(v.length == 0) 
	{
		return true;
	}
	if(v.length==552)
	{
		return true;
	}
	else
	{
		return "length must be 552"
	}
}
function validateLength4(v){
	if(v.length == 0) 
	{
		return true;
	}
	if(v.length==492)
	{
		return true;
	}
	else
	{
		return "length must be 492"
	}
}
function validateLength6(v) {
	if(v.length == 0) 
	{
		return true;
	}
	if(v.length==516)
	{
		return true;
	}
	else
	{
		return "length must be 516"
	}
}
function validateLength7(v){
	if(v.length == 0) 
	{
		return true;
	}
	if(v.length==378)
	{
		return true;
	}
	else
	{
		return "length must be 378"
	}
}
function validateLength8(v){
	if(v.length == 0) 
	{
		return true;
	}
	if(v.length==426)
	{
		return true;
	}
	else
	{
		return "length must be 426"
	}
}

function validateDna(v) {
	//		return v.length == 0 ||  /^[actgACTG]+$/.test(v)
			
	v=v.replace(/\s+/g,'');
	
	if(v.length == 0) 
					
	return true;
	var regex =/^[actgACTG]+$/;
	if(regex.test(v)){
		return true;
	}
	else
	{
		return "DNA Sequence must only contain A, C, T and G";	
	}
}
function validateDayOfMonth(v){
	v = Number(v);
	if(v <= 31 && v > 0)
	{
		return true;		
	}
	else
	{
		return this.fieldLabel + " of month must be between 1 and 31";	
	}
}

function validateMonth(v){
	if((v.length == 0 || (!isNaN(v) && !/^\s+$/.test(v))) && (v>0 && v <= 12))
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " must be a number between 1 and 12";
	}
}

function validateYear(v){
	if( (v.length == 0 || (!isNaN(v) && /^\d{4}$/.test(v) && v <= new Date().getFullYear())) )
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " must be a four digit number and not in the future.";
	}
}

function validateNumber(v) {
	if( v.length == 0 || (!isNaN(v) && !/^\s+$/.test(v)))
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " be a number";
	}
}

function validateDate(v){
		if(v < new Date())
		{
				
				return true;		
		}
		else
		{
				return this.fieldLabel + " must be in the past.";
		}
}

function validateDigits(v) {
	if(v.length == 0 ||  !/[^\d]/.test(v))
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " must contain only digits";	
	}
}

function validateDecimal(v) {
	if( v.length == 0 ||  /^-?\d+(\.\d+)?$/.test(v))
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " must contain a decimal number";
	}
}
function validateAlpha(v){
	if( v.length == 0 ||  /^[a-zA-Z]+$/.test(v))
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " must contain only letters.";
	}
}
function validateAlphanum(v) {
		if(v.length == 0 ||  !/\W/.test(v))
		{
			return true;
		}
		else
		{
			return this.fieldLabel + " must only contain letters and numbers";
		}
	}

function validateEmail(v) {
	if( v.length == 0 || /\w{1,}[@][\w\-]{1,}([.]([\w\-]{1,})){1,3}$/.test(v))
	{
		return true;
	}
	else
	{
		return "Email must be in the format user@domain.com";
	}
}
function validateUrl(v) {
	if(v.length == 0 || /^(http|https|ftp):\/\/(([A-Z0-9][A-Z0-9_-]*)(\.[A-Z0-9][A-Z0-9_-]*)+)(:(\d+))?\/?/i.test(v))
	{
		return true;
	}
	else
	{
		return this.fieldLabel + " must be a full URL i.e. http://www.example.com";
	}
}
function validateDateAu(v) {
		if(v.length == 0) return true;
		var regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
		if(!regex.test(v)) return false;
		var d = new Date(v.replace(regex, '$2/$1/$3'));
		return ( parseInt(RegExp.$2, 10) == (1+d.getMonth()) ) && 
			(parseInt(RegExp.$1, 10) == d.getDate()) && 
			(parseInt(RegExp.$3, 10) == d.getFullYear() );
		}
function validateCurrencyDollar(v) {
			// [$]1[##][,###]+[.##]
			// [$]1###+[.##]
			// [$]0.##
			// [$].##
			return v.length == 0 ||  /^\$?\-?([1-9]{1}[0-9]{0,2}(\,[0-9]{3})*(\.[0-9]{0,2})?|[1-9]{1}\d*(\.[0-9]{0,2})?|0(\.[0-9]{0,2})?|(\.[0-9]{1,2})?)$/.test(v)
}

function validateLatitude(v){
	if(v.match(/^-?[0-9]+(\.[0-9]+)?$/g) && Number(v) >= -90 && Number(v) <= 90)
		return true;
	else
		return("Latitude must be a decimal number between -90 and 90");
}
function validateLongitude(v){
	if( v.match(/^-?[0-9]+(\.[0-9]+)?$/g) && Number(v) >= -180 && Number(v) <= 180)
		return true;
	else
		return(this.fieldLabel + " must be a decimal number between -180 and 180");
}
	
function isLeapYear(year)
{
	year = Number(year);
	return year % 400 == 0 || (year % 4 == 0 && year % 100 != 0);
}

function validateSelection(v)
{
	if(this.isXType('combo')){
		return (this.selectedIndex >= 0 ? true : ("<b>" +this.fieldLabel + "</b> must be a value from the list"));
	}
	else
	{
		return this.value ? true : ( this.fieldLabel + " must have a value");
	}
}

function validateSelectionOrNull(v)
{
	if(this.isXType('combobox')){
		return (this.selectedIndex >= 0 || (this.selectedIndex == -1 &&!this.value) ? true : (this.fieldLabel + " must be a value from the list or nothing"));
	}
	else
	{
		return true;
	}
}