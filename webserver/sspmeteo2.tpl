<!doctype html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SSPMeteo2</title>
    <link rel="icon" type="image/png" href="static/favicon.png" />
    <script src="static/gauge.min.js"></script>
</head>
<body style="font-family:arial;max-width:630px;margin:auto">
    <header style="background-color:#BABAB2; color:#444444;padding:15px 3px 3px 3px">
        <div style="text-align:center">Estación meteorológica SSPMeteo2 - Benifayó (SPAIN)</div>
        <div style="text-align:right"><small>by sersope</small></div>
    </header>
    <div style="background-color:#F0F0F0;padding:8px;border: 2px solid #BABAB2">
        <canvas id="temperatura"></canvas>
        <canvas id="humedad"></canvas>
        <canvas id="presion"></canvas>
        <canvas id="dir_vent"></canvas>
        <canvas id="vel_vent"></canvas>
        <canvas id="rac_vent"></canvas>
        <canvas id="lluvia_int"></canvas>
        <canvas id="lluvia_dia"></canvas>
        <div style="text-align:right"><small >{{datos[0]}}</small></div>
    </div>
    <script>

        setInterval(function() {
          location.reload();
        }, 300000);

        var ancho = 200;
        var alto = 200;
        //~ Temperatura
        var gauge_temp = new RadialGauge({
            renderTo: 'temperatura', width: ancho, height: alto, units: "°C", title: 'Temperatura',
            minValue: -20, maxValue: 60, majorTicks: ["-20","-10","0","10","20","30","40","50","60"], highlights: false,
            animateOnInit: true, colorTitle:"#444444", colorUnits:"#444444", borders:false,
            value:{{datos[1]}}
        }).draw();
        //~ Humedad
        var gauge_humedad = new RadialGauge({
            renderTo: "humedad",
            width: ancho, title: 'Humedad', height: alto, units: '%', colorTitle:"#444444", colorUnits:"#444444",
            minValue: 0, maxValue: 100, majorTicks: [0,10,20,30,40,50,60,70,80,90,100], highlights: false,
            animationRule: "linear", animateOnInit: true, animationDuration: 1500, borders:false,
            value:{{datos[3]}}
        }).draw();
        //~ Presion
        var gauge_presion = new RadialGauge({
            renderTo: "presion",
            width: ancho, title: 'Presión', height: alto, units: 'mbar', colorTitle:"#444444", colorUnits:"#444444",
            minValue: 950, maxValue: 1050, majorTicks: [950,960,970,980,990,1000,1010,1020,1030,1040,1050], highlights: false,
            animationRule: "linear", animateOnInit: true, animationDuration: 1500, borders:false,
            value:{{datos[6]}}
        }).draw();
        //~ Viento
        var gauge_dir_vent = new RadialGauge({
            renderTo: "dir_vent",
            width: ancho, height: alto, minValue: 0, maxValue: 360, colorTitle:"#444444", colorUnits:"#444444", strokeTicks: false, highlights: false,
            majorTicks: ["N","NE","E","SE","S","SW","W","NW","N"], minorTicks: 2, ticksAngle: 360, startAngle: 180,
            valueBox: false, title: 'Dir. viento', animationRule: "elastic", animateOnInit: true, animationDuration: 1500, borders:false,
            value:{{datos[11]}}
        }).draw();
        var gauge = new RadialGauge({
            renderTo: 'vel_vent',
            width: ancho, height: alto, units: "Km/h", title: "Vel. viento", minValue: 0, valueBox: true, maxValue: 160,
            majorTicks: [ "0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "110", "120", "130", "140"],
            strokeTicks: true, highlights:false, borders:false, colorTitle:"#444444", colorUnits:"#444444",
            animationDuration: 1500, animationRule: "linear", animationOnInit: true,
            value:{{datos[9]}}
        }).draw();
        var gauge = new RadialGauge({
            renderTo: 'rac_vent',
            width: ancho, height: alto, units: "Km/h", title: "Racha", minValue: 0, valueBox: true, maxValue: 160,
            majorTicks: [ "0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "110", "120", "130", "140"],
            strokeTicks: true, highlights:false, borders:false, colorTitle:"#444444", colorUnits:"#444444",
            animationDuration: 1500, animationRule: "linear", animationOnInit: true,
            value:{{datos[10]}}
        }).draw();
        // Lluvia
        var gauge = new RadialGauge({
            renderTo: 'lluvia_int',
            width: ancho, height: alto, units: "mm/h", title: "Intens. lluvia", minValue: 0, valueBox: true, maxValue: 60,
            majorTicks: [ "0", "10", "20", "30", "40", "50", "60"], colorTitle:"#444444", colorUnits:"#444444",
            strokeTicks: true, highlights:false, borders:false,
            animationDuration: 1500, animationRule: "linear", animationOnInit: true,
             value:{{datos[8]}}
       }).draw();
        var gauge_humedad = new RadialGauge({
            renderTo: "lluvia_dia",
            width: ancho, title: 'Lluvia diaria', height: alto, units: 'mm', colorTitle:"#444444", colorUnits:"#444444",
            minValue: 0, maxValue: 100, majorTicks: [0,10,20,30,40,50,60,70,80,90,100], highlights: false,
            animationRule: "linear", animateOnInit: true, animationDuration: 1500, borders:false,
            value:{{datos[7]}}
        }).draw();
    </script>
</body>
</html>

