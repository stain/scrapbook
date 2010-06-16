function setup()
{
    loop();
}

function debug(msg) {
    document.getElementById('debug').innerText += msg;
}

function loop() {
    fetchMpetreData();
    // Every 20th second
    window.setTimeout("loop()", 20000);
}

function fetchMpetreData() {
    xmlhttp = new XMLHttpRequest();
    url = "http://rita.nrk.no/community/klanen/xml/flashData.php";
    xmlhttp.open("GET", url);
    xmlhttp.onload = function(e) {
            var splitted = xmlhttp.responseText.split("&");
            var values = new Array();
            for (var i in splitted) {
                var str = splitted[i];
                var sp = str.split("=");
                var key = sp[0];
                var value = sp[1];
                values[key] = value;
            }
	        document.getElementById('artist').innerText = values['Artist'];
	        document.getElementById('song').innerText = values['Laat'];
	        document.getElementById('next_artist').innerText = values['NesteArtist'];
	        document.getElementById('next_song').innerText = values['NesteLaat'];
    }
    xmlhttp.send(null);
        /*if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {*/
        /*}*/
}
