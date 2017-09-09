<html>
<head>
	<link rel="stylesheet" href="styles.css">
</head>
<body>

<?php

$servername = "localhost";
$username = "videovote";
$password = "Bagwell107";
$dbname = "test";

$conn = new mysqli($servername, $username, $password, $dbname);
if($conn->connect_error) {
	die("Connection failed: " . $conn->connect_error);
}

$sql = "SELECT video_id, votes, multiplier, play_date, (votes*multiplier) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY score LIMIT 10;";
$result = $conn->query($sql);
$c = 0;



while($row = $result->fetch_assoc()){

	$url = 'http://img.youtube.com/vi/'. $row["video_id"] .'/mqdefault.jpg';
	$votes = $row["votes"];
	$mult = $row["multiplier"];

	
	$content = file_get_contents("http://youtube.com/get_video_info?video_id=". $row["video_id"]);
	parse_str($content, $ytarr);
	$title =  $ytarr['title'];
	

	print('
		<div class="set">
			<div class="num">' . $c . '</div>
			<div class="title">'. $title .'</div>
			<img class="vid" src="'. $url .'"></img>
			<div class="info">
				<div class="votes">'. $votes .'</div>
				<div class="powers">'. $mult .'%</div>
			</div>
		</div>
	');

	$c = $c + 1;

}

$conn->close();

?>


</body>
</html>

