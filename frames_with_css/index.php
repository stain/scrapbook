<?php top("Emulating frames with CSS"); ?>
    <div class="abstract"> 
      <h2>Abstract</h2>
      <p>
      A way to emulate framesets using nothing but CSS. 
      Nice way to get fixed position menus and status bars
      without using tables or frameset. Works with Internet
      Explorer 5.x and 6.0, Opera 7.2, Netscape 7, Mozilla.
      </p>
    </div>

    <p>
    Presented here is one way of achieving the "frames" effect
    by just using CSS. Basically, three <code>div</code>-blocks
    are defined in the HTML, named <code>top</code>, <code>bottom</code>
    and <code>left</code>, and they are placed such on the page. The
    <code>left</code> bar fills the whole height, while the rest of the
    screen is splitted between <code>top</code> and the
    <code>bottom</code>. The proportions are defined in the CSS and
    might be changed at will, however, be careful to test such
    changes in Internet Explorer. Especially fixed-sizing on
    <code>top</code>/<code>bottom</code> confuses IE. This is a problem
    that should be worked out.
    </p>
    <p>
    You might be confused why this works, as it is normally impossible
    to define static elements (elements that are positioned according to
    the viewport) with Internet Explorer. However, the trick used here
    is to not have anything in <code>body</code> at all, then
    heights like <code>100%</code> will be the whole screen height, and
    nothing but that. 
    </p>
    <p>
     The technique is highly inspired by the examples at 
     <a href="http://devnull.tagsoup.com/fixed/">devnull.tagsoup</a>,
     and also by <a href="http://glish.com/css/">glish.com</a>. The
     technique used by Eric Bednarz in the  
     <a href="http://devnull.tagsoup.com/fixed/vertical.html">vertical</a>
     and <a 
     href="http://devnull.tagsoup.com/fixed/horizontal.html">horizontal</a>
     bar have the advantages of keeping the main text within the normal
     body, not creating any additional scroll bars and making keyboard 
     navigation easy. However, when I tried to simply combine these
     two to get both a horisontal and vertical bar, I could not
     succeed without getting serious bugs with IE. In addition, the
     full-height scrollbar confused a lot when I positioned the
     horizontal bar at the bottom. In addition, the full-height
     scrollbar confused a lot when I positioned the horizontal bar at
     the bottom.
    </p>
    <p>Another technique using Javascript to trick IE is presented by
       <a href="http://www.fu2k.org/alex/css/frames/">Alex</a>, called
       <em>Frames without frames</em>. Or you could just let IE degrade
       nicely to a "normal" webpage, as shown by 
       <a href="http://underscorebleach.net/content/jotsheet/2004/12/frames_with_css_layout">Tom Sherman</a>.
    <p>
     This frames technique is not suitable for all solutions, but
     might be if you're creating a web application, and it's important
     to keep relevant menu items, statistics and log entries on screen
     all the time. Check out the <a href="background">background</a> for
     why I developed this technique.
    </p>
    <p>
     You are free to use the <a href="source">source code</a> as
     you like, as long as you credit my and Bednarz's work. Also, check
     out the examples from the menu. If you like, you can take a look at
     the <a href="php">PHP</a> used for templating pages or download a whole
     <a href="frames_with_css.tar.gz">tar-ball</a> of these pages,
     including the PHP behind.
    </p>
