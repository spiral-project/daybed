<html>
<head>
<script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
<script src="https://login.persona.org/include.js" type="text/javascript"></script>
<script type="text/javascript">${request.persona_js}</script>
</head>
<body>
<h1>Welcome on Daybed, ${user['name']}</h1>

Your API token is <code>${user['apitoken']}</code>
${request.persona_button}
</body>
</html>
