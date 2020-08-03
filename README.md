ddencode
========

A simple frontend for [ffmpeg](http://ffmpeg.org/) to encode a
sequence of image files to a h.264 mp4 video file.

Note that ffmpeg is a powerful and full-featured encoding program, and
it includes native support for encoding a sequence of images to a
video file.

The purpose of this frontend is to apply sensible default options, to
avoid exposing the user to the complicated option syntax of ffmpeg,
and to allow the frame images to have non-sequential names (which the
ffmpeg image2 plugin does not support).

Example
-------

`ddencode.py -r 30 -b 8000k -m framelist.txt -o video.mp4`

Read a list of filenames from `framelist.txt` and use 2-pass encoding
to make 8000kbit/s 30fps h.264 video file `video.mp4`.

Comments, questions, bug reports
--------------------------------

Send to: david@dumas.io
