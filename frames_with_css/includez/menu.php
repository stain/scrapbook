<?php
include_once("utils.php");
$url = "http://www.soiland.no/frames_with_css/"; 
?>
<?php
 global $SCRIPT_FILENAME;
 foreach(findfile('.', '/.php$/') as $file) {
     $file = preg_replace("/.php$/", "", $file);
     $file = preg_replace(",.*/,", "", $file);
     if ($file == "index") {
         continue;
     }
     $name = ucfirst($file);
     $name = preg_replace("/_/", " ", $name);
     if (preg_match("/$file/", $SCRIPT_FILENAME)) {
         echo "<a class='current' href='$url$file'>$name</a>\n";
     } else {
         echo "<a href='$url$file'>$name</a>\n";
     }
 }
 
?>
