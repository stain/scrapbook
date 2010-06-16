<?php
function findfile($location='',$fileregex='') {
   if (!$location or !is_dir($location) or !$fileregex) {
       return false;
   }
 
   $matchedfiles = array();
 
   $all = opendir($location);
   while ($file = readdir($all)) {
       if (is_dir($location.'/'.$file) and $file <> ".." and $file <> ".") {
//         $subdir_matches = findfile($location.'/'.$file,$fileregex);
//         $matchedfiles = array_merge($matchedfiles,$subdir_matches);
         unset($file);
       }
       elseif (!is_dir($location.'/'.$file)) {
         if (preg_match($fileregex,$file)) {
             array_push($matchedfiles,$location.'/'.$file);
         }
       }
   }
   closedir($all);
   unset($all);
   return $matchedfiles;
}
?>
