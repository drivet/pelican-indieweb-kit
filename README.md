# Pelican Indieweb Kit

This project provides some of the pieces required to make a [pelican][1] based website/blog more [indieweb][2] friendly. 
It consists of several components:

* A Flask application providing [webmention][3], [micropub and media server][4] endpoints.
* A collection of pelican plugins to send and show webmentions in general, and to interface with [bridgy][5] in particular.
* A pelican theme designed to display the different types of posts one might expect of an indieweb site, as well as webmentions.

The material in the project is very much geared towards my own personal website (https://desmondrivet.com) and not much
effort was put into generalizing it.  That being said, if you want to make your own website more indieweb friendly, you 
may find inspiration here, especially if you:

* Use pelican (obviously)
* Store your site code on github but host it somewhere else
* Use a push-to-deploy system to publish new posts

[1]: https://blog.getpelican.com/
[2]: https://indieweb.org/
[3]: https://www.w3.org/TR/webmention/
[4]: https://www.w3.org/TR/micropub/
[5]: https://brid.gy/
