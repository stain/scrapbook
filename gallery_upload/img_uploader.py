#!/usr/bin/env python

"""Selects images from emails and submits them to a Gallery <http://gallery.sf.net/> site.

Any attachments with mime type image/ will be picked up.

Usage:

img_uploader.py < email

Ie. from procmailrc, catching all emails sent from spam@soiland.no (my
cellular phone sends emails from that address):

    # Images from the cell phone
    :0 c
    * ^From:.*spam@soiland.no
    | /usr/bin/python /home/stud/stain/src/img_uploader.py


Copyright (c) 2004-2005 Stian Soiland

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Author: Stian Soiland <stian@soiland.no>
URL: http://soiland.no/software/img_uploader
License: MIT
"""

import email
import sys
import re
import os
import tempfile

# gallery.py from http://garion.tzo.com/python/
import gallery

# Don't forget the trailing / in URL to your Gallery
URL="http://soiland.no/gallery/"
# A Gallery username with the right to add images. (no other
# rights are neccessary)
USERNAME="mobcam"  
PASSWORD="blapp"
# Which album to put images in
ALBUM="mobcam"

def get_images(message):
    images = []
    for submessage in message.walk():
        if not submessage.get_content_type().count("image/"):
            # only care about images 
            continue
        filename = submessage.get_filename()
        # Clean up possibly ugly filenames    
        filename = filename.lower()
        filename = re.sub(r"[^0-9a-z-_.]", r"", filename)
        filename = re.sub(r"_+", r"_", filename)
        filename = re.sub(r"_\.", r".", filename)
        if not filename:
            # Generate one, assume .jpg
            filename = "img%04i.jpg" % len(images)
        image = submessage.get_payload(decode=1)
        images.append((filename, image))
    return images        

def upload_image(filename, image):
    gal = gallery.Gallery(URL)    
    gal.login(USERNAME, PASSWORD)

    tempdir = tempfile.mktemp()
    os.mkdir(tempdir, 0700)
    fullpath = os.path.join(tempdir, filename)
    # write out to file since Gallery needs a file
    open(fullpath, "w").write(image)
    # strip file extension if any 
    caption = re.sub(r"\.[a-z]{3,4}$", "", filename)
    if not caption:
        caption = filename
    caption = caption.capitalize()
    gal.addItem(ALBUM, fullpath, caption)
   
if __name__ == "__main__":
    message = email.message_from_file(sys.stdin)
    images = get_images(message)
    if not images:
        sys.exit(0)
    
    for (filename, image) in images:
        upload_image(filename, image)
