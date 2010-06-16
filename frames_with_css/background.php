<?php top("Background for using css"); ?>

    <p>
      Defining static areas of the webpage without using frames
      or tables. Typical examples could be menu bar to the left, 
      status area at the bottom, common header, shopping cart at the
      bottom, advertiesment on the top, etc.
    </p>
    <p>
      The background for making this CSS was that I were going
      to create a web interface for a user management database, and
      needed to keep certain elements available on the screen all the
      time, like menus, log entries and statistics.
    </p>
    <h2>Frames</h2>
    <p>
      The problem with using frames is that doing so messes up:
    </p>
    <dl>
      <dt>URLs and bookmarks</dt>
        <dd>It is impossible to bookmark or send an URL to a 
            page within a frameset. It is only possible to
            give to the frontpage. Carefully picking out the
            address to a subframe yields an address to an 
            incomplete page, missing essential stuff as 
            navigation.
        </dd>

      <dt>Back/forward buttons</dt>
        <dd>Within a frameset, the back/forward buttons in the
            user's browser never behave as expected. It might be
            impossible to go back to a location, and users are
            confused.
            
      <dt>Printing</dt>      
        <dd>Printing a frameset page almost never work
            properly. Information is doomed to be lost in the
            paper margins, and lots of paper is 
            wasted on printing empty menu frames.
            
      <dt>Serverside code</dt>
        <dd>You might think that frames at least make it easy on the
            server side. You only need to keep the menu one place, 
            relative menu links will always work, and so on. It turns
            out to be the other way around. In most web solutions
            some kind of backend is used, that generates the HTML
            code, responds to user requests, and so.
            <p>
            The trouble with framesets in such an environment is
            when you need to update more than one frame at once. A 
            link or form button can only change one of the frames (or
            the whole frameset), and which one needs to be decided up
            front when placing the link.
            </p>
            <p>
            This makes it rather difficult to perform some request, 
            return the new data in the upper frame, at the same time
            update the "current open branch" in the left frame menu and
            in addition update the statistics in the lower frame. To do
            this you would either need to activate some ugly javascript,
            or reload the whole frameset and passing by arguments 
            to bring up the correct subpages. 
            </p>
        </dd>
    </dl>
    <h2>Tables</h2>
    <p>So I've given up frames, and so has most of the rest of the
       world, luckily. What about tables, then? Here's the problems with
       using tables.
    </p>
    <dl>
    <dt>Easy to get pixel oriented</dt>
      <dd>Designers using HTML tables tend to limit everything down
          to the pixel level. Dirty tricks are done to achieve "full
          size", breaking HTML standards to make browsers like Internet
          Explorer behave decent. Everything is carefully laid out,
          changing anything later might break the whole design. 
          It is easy to create pages dependent on a certain window
          resolution, or at least some minimum width.

    <dt>Still no printing</dt>
      <dd>Printing a table oriented page still wastes a lot of paper.
          Table designs <em>can</em> be made relative to screen size,
          and therefore making the page printable without loosing
          information in the margins. However, the printouts include
          menu items, headers and other items that are of no use
          on the printout.
      </dd>
    
    <dt>Not seperating code from design</dt>
      <dd>The webdesign is contained in the HTML, so changing 
          the design means changing the HTML. Following the 
          principle of seperating code from design means one
          needs to carefully use template systems to make it
          able to change the design later on. 
    </dl>
    
    <dt>Not fixable on screen</dt>
      <dd>While one might argue that it's simpler for users to
          only have one window to scroll, table-based pages
          have the problem that all forms of navigation 
          disappear as soon as the user scrolls down. Things can't
          stay on screen.  This leads to a lot of scrolling up and down
          just to get going.
      </dd>   

   <h2>CSS</h2>
   <p>
     So why CSS then? What is it all about?
   </p>
   <dl>
     <dt>Seperating code and design</dt>
       <dd>HTML code can be kept straight and simple, and almost at a
           strict markup level, suitable for search engines.
           This makes it easy to change the design at any point,
           in addition to making it easier to <em>write</em> the
           HTML code.
       </dd>    
     <dt>Giving the user a choice</dt>
       <dd>Some browsers (Opera, Mozilla) gives the user a choice
           to change the stylesheet of a page on the fly. This is
           good for people with bad vision who is interested in the
           plain text, and with simple, structured HTML, the 
           information will still be visible even though the 
           design is gone. PDAs might not have CSS support, but by
           structuring the HTML, the information will be
           easy to get anyway.
           </dd>

     <dt>Thinking shapes, not details</dt>
       <dd>Using CSS makes it easier to think relative and
           general, not caring about precise pixel values and
           accurate positioning. This makes web pages available
           to a wide variety of screen resolution and font sizes.
       </dd>    

     <dt>Keeping things in place</dt>
       <dd>Using the 'frames technique' discussed on these pages, 
           it is possible to keep navigational items fixed on 
           screen while giving the user a choice to scroll the
           main document. This is specially important to web
           applications users stay in for hours a day.
       </dd>

     <dt>Easy for the user</dt>
       <dd>Using single pages without framesets makes back/forward
       buttons and bookmarking work as intended. URLs can be made
       easy to type and give away. </dd>
     
     <dt>Easy on the serverside</dt>
       <dd>While using this technique forces you to include
           the navigational items in each HTML page, this is
           something that is simple with most publishing tools
           today. Avoiding frames makes it easy to create 
           seperate URLs and processing requests.
       </dd>     
     
     <dt>Printable</dt>
       <dd>Using CSS lets you present different stylesheets
           according to the output media.  Seperate
           <code>print</code>-stylesheets could disable
           printing of menu items, and navigational positioning
           of boxes could be kept at a <code>screen</code>-level
           only. Try to print this page for an example!
       </dd>    
   </dl>
   <h2>Problems</h2>
     <p>
       There <em>are</em> however some problems with the 
       presented CSS frames technique that are worth to be mentioned.
       </p>
       <dl>
         <dt>Internet Explorer</dt>
           <dd>As hard as CSS designers try, Internet Explorer
               always has some difficult bug that messes things
               up. In this case, I've tried to counteract
               most of the IE behavour, but still some bugs resist.
               For instance, at specific font sizes, a maximized IE
               window might hide the scrollbar. The scrollbars might not
               be properly aligned with the margins. 
           </dd>    
         <dt>Keyboard issues</dt>  
           <dd> As the trick in  our technique is to set
           <code>body</code> 100% high, and then use 
           seperate <code>div</code>-blocks with their own
           scroll bars, normal scrolling keys might not 
           always work. Users might have to click inside a
           'window' to make it active before scrolling.
           </dd>

         <dt>Usability issues</dt>
           <dd>Users might be confused by if some parts stay 
               at rest while scrolling. This is most appearent
               when keeping the bottom part at rest while scrolling
               the top part. (a stationary header is more normal and
               don't confuse that much.)
           </dd>   
         
         <dt>HTML-error sensitivity</dt>
           <dd>Errors in the HTML, like an extra or missing 
           closing tag <code>&lt;/div&gt;</code>, might mess up
           the whole design as part of the <code>bottom</code>
           suddenly becomes a part of <code>top</code> and such. This
           could be avoided in most cases by keeping the static parts
           in the upper part of the generated HTML code, so that errors
           only affect the dynamic (scrolling) part.
           </dd>
       </dl>
