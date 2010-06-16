<?php 
function top($title="Emulating frames with CSS", $css="style.css") {
  print "<?xml version='1.0' lang='en' ?>\n"; ?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
<?php echo"<title>$title</title>\n"; ?>
 
    <!-- Make a 'frameset' with three parts. -->
    <link rel="stylesheet" type="text/css" href="fixed.css" 
          media="screen" />
    <!--[if IE]>
    <link rel="stylesheet" type="text/css" 
          media="screen" href="fixed_ie.css" />
    <![endif]-->

    <!-- Our normal styling, font, colors, etc.  -->
    
<?php echo "<link rel='stylesheet' type='text/css' href='$css' />\n"; ?>
    <link rel="stylesheet" type="text/css" 
          media="print" href="print.css" />
</head><body>

<div class="left">
<div class="inner">  
 <h2>Menu</h2>
 <div class="menu">
 <?php
   global $SCRIPT_FILENAME;
   if (preg_match("/index.php$/", $SCRIPT_FILENAME)) {
     echo "<a class='current' href='/frames_with_css/'>Frontpage</a>\n";
   } else {
     echo "<a href='/frames_with_css/'>Frontpage</a>\n";
   }
   ?>
<?php include("menu.php"); ?>   
   <a href="simple">Simple example</a>
   <a href="scroll">Scroll example</a>
 </div>
</div>
</div>


<div class="top">
<div class="inner">
<?php echo "<h1>$title</h1>\n"; ?>
<div class="content">

<?php
// I know this is truly lame to include code like this.
}
?>


