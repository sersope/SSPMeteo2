<!doctype html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SSPMeteo2</title>
    <link rel="icon" type="image/png" href="static/favicon.png" />
    <script src="static/raphael-2.1.4.min.js"></script>
    <script src="static/justgage.js"></script>
</head>
<body style="font-family:arial;max-width:630px;margin:auto">
    <header style="background-color:#BABAB2; color:#444444;padding:15px 3px 3px 3px">
        <div style="text-align:center">Francisco Climent - Benifayó (SPAIN)</div>
        <div style="text-align:right"><small>sspmeteo2 by sersope</small></div>
    </header>
    <div style="background-color:#F0F0F0;padding:8px;border: 2px solid #BABAB2">
        <table>
            <tr>
                <td> <div id="gTemp" style="width:200px; height:160px"></div> </td>
                <td> <div id="gHume" style="width:200px; height:160px"></div> </td>
                <td> <div id="gPres" style="width:200px; height:160px"></div> </td>
            </tr>
            <tr>
                <td> <div id="gVven" style="width:200px; height:160px"></div> </td>
                <td> <div id="gRach" style="width:200px; height:160px"></div> </td>
                <td> <div id="gDven" style="width:200px; height:160px"></div> </td>
            </tr>
            <tr>
                <td> <div id="gLluvh" style="width:200px; height:160px"></div> </td>
                <td> <div id="gLluvd" style="width:200px; height:160px"></div> </td>
            </tr>
        </table>
        <div style="text-align:right"><small >{{status}}</small></div>
    </div>
    <script>
        new JustGage({id: "gTemp",  value: {{datos['temp']}}, symbol: " ºC", min: 0, max: 40, label: "Temperatura"});
        new JustGage({id: "gHume",  value: {{datos['humi']}}, symbol: " %", min: 0, max: 100, label: "Humedad"});
        new JustGage({id: "gPres",  value: {{datos['pres']}}, symbol: " mb", min: 950, max: 1050, label: "Presión"});
        new JustGage({id: "gDven",  value: {{datos['dven']}}, symbol: " º", min: 0, max: 359, label: "Dir. viento", donut:true});
        new JustGage({id: "gVven",  value: {{datos['vven']}}, symbol: " km/h", min: 0, max: 100, label: "Vel. viento"});
        new JustGage({id: "gRach",  value: {{datos['vrac']}}, symbol: " km/h", min: 0, max: 100, label: "Rachas"});
        new JustGage({id: "gLluvh", value: {{datos['lluh']}}, symbol: " mm/h", min: 0, max: 100, label: "Intensidad lluvia"});
        new JustGage({id: "gLluvd", value: {{datos['llud']}}, symbol: " mm", min: 0, max: 100, label: "Lluvia diaria"});
    </script>
</body>
</html>

