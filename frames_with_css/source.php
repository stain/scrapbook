<?php top("Source code"); ?>

<p>
To use the frames technique, the document must be structued to contain
three <code>div</code>s, with classes <code>top</code>, <code>bottom</code>
and <code>left</code>. Their position should be obvious from the class
names.  Due to a scaling bug in IE, at least each of <code>bottom</code>
and <code>top</code> should directly beneath contain another
<code>div</code> with class <code>inner</code>.
</p>
<p>
Again, due to Internet Explorer, the XML preamble and a proper
<code>DOCTYPE</code> header must be included at the top of the file.
This is to triger what's called 
<a 
href="http://msdn.microsoft.com/library/en-us/dnie60/html/cssenhancements.asp">standard compliant mode</a>. 
If nothing works in IE, and everything works in everything else, this is
probably what you've done wrong. Also see an article on this subject
by <a
href="http://gutfeldt.ch/matthias/articles/doctypeswitch.html">Matthias
Gutfeldt</a>.
</p>
<p>Finally, some more workarounds for IE is needed, and trickily
included with a IE-only <code>if</code>-statement within the HTML.</p>

<p>
Two CSS files are needed, <a href="fixed.css">fixed.css</a>
and <a href="fixed_ie.css">fixed_ie.css</a>.
</p>

<h2>Example HTML</h2>
<pre>
&lt;?xml version="1.0" lang="en" ?&gt;
&lt;!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"&gt;
&lt;html lang="en"&gt;
   &lt;head&gt;
     &lt;title&gt;Emulating frames with CSS&lt;/title&gt;
 
     &lt;!-- Make a 'frameset' with three parts. --&gt;
     &lt;link rel="stylesheet" type="text/css" 
           media="screen" href="fixed.css" /&gt;
     &lt;!--[if IE]&gt;
     &lt;link rel="stylesheet" type="text/css" 
           media="screen" href="fixed_ie.css" /&gt;
     &lt;![endif]--&gt;
   &lt;/head&gt;
   &lt;body&gt;

     &lt;div class="left"&gt;
       Menu &lt;br /&gt;
       Link1 &lt;br /&gt;
       link2
     &lt;/div&gt;  

     &lt;div class="top"&gt;
       &lt;div class="inner"&gt;
         .. text to be in the top part
       &lt;/div&gt;
     &lt;/div&gt;

     &lt;div class="bottom"&gt;
       &lt;div class="inner"&gt;
         .. text to be in the bottom part
       &lt;/div&gt;
     &lt;/div&gt;

   &lt;/body&gt;
&lt;/html&gt;  
</pre>

<p>If you want to support a printout version without some of your
elements, include another stylesheet within <code>&lt;head&gt;</code>
like this:</p>
<pre>
     &lt;link rel="stylesheet" type="text/css" 
           media="print" href="print.css" /&gt;
</pre>

<p>Note that you don't have to undo the framing, as this is done
only for <code>media="screen"</code>.  You might want to "undo" 
other styling operations, but it would be easier to likewise have a
seperate <code>screen.css</code> with <code>media="screen"</code> for
screen-specific details, like link background colors. Here's an example
of a <code>print.css</code> that changes fonts and disables the
<code>left</code> and <code>bottom</code> parts of the page:
</p>
<pre>
body {
    font-family: "Times New Roman", times, serif;
    font-size: 10pt;
}
div.left {
    display: none;
}
div.bottom {
    display: none;
}
</pre>
<p>
  Also look at the <a href="php">PHP</a> tricks used for generating
  these pages, including a trick for auto-generating the menu.
</p>
