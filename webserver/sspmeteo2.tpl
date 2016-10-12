<!doctype html>
<html>
<head>
    <title>SSPMeteo2</title>
    <script src="static/gauge.min.js"></script>
</head>
<body>
    <header style="background-color:#BABAB2; color:#444444; font-family:arial;">
        <h1>SSPMeteo</h1>
        <h2>Estación meteorológica</h2>
    </header>
    <canvas id="temperatura"></canvas>
    <canvas id="humedad"></canvas>
    <canvas id="presion"></canvas>
    <canvas id="dir_vent"></canvas>
    <br>
    <small style="text-align:right">Datos actualizados a las {{datos[0]}}</small>
<!--
    <button onclick="myFunction()">Reload page</button>
-->

    <script>
        
        setInterval(function() {
          location.reload();
        }, 300000);

        //~ Temperatura
        var gauge_temp = new RadialGauge({
            renderTo: 'temperatura', width: 250, height: 250, units: "°C", title: 'Temperatura',
            minValue: -20, maxValue: 60, majorTicks: ["-20","-10","0","10","20","30","40","50","60"], highlights: false,
            animateOnInit: true,
            value:{{datos[1]}}
        }).draw();
        //~ Presión
        var gauge_humedad = new RadialGauge({
            renderTo: "humedad",
            width: 250, title: 'Humedad', height: 250, units: '%',
            minValue: 0, maxValue: 100, majorTicks: [0,10,20,30,40,50,60,70,80,90,100], highlights: false,
            animationRule: "linear", animateOnInit: true, animationDuration: 1500,
            value:{{datos[2]}}
        }).draw();
        //~ Humedad
        var gauge_presion = new RadialGauge({
            renderTo: "presion",
            width: 250, title: 'Presión', height: 250, units: 'mbar',
            minValue: 950, maxValue: 1050, majorTicks: [950,960,970,980,990,1000,1010,1020,1030,1040,1050], highlights: false,
            animationRule: "linear", animateOnInit: true, animationDuration: 1500,
            value:{{datos[4]}}
        }).draw();
        //~ Direccion del viento
        var gauge_dir_vent = new RadialGauge({
            renderTo: "dir_vent",
            width: 250, height: 250, minValue: 0, maxValue: 360,
            majorTicks: ["N","NE","E","SE","S","SW","W","NW","N"], minorTicks: 2, ticksAngle: 360, startAngle: 180, strokeTicks: false, highlights: false,
            valueBox: false, title: 'Dirección del viento', animationRule: "elastic", animateOnInit: true, animationDuration: 1500,
            value:{{datos[9]}}
        }).draw();

    </script>
</body>
</html>

