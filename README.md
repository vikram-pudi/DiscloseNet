# DiscloseNet

DiscloseNet is a software for hosting a website to serve as a *public 
institute repository of academic research publications of the 
institute*. Its well-tested as it has been in use at [IIIT Hyderabad](http://web2py.iiit.ac.in/publications) for over a decade.

## Installation

To simply try out DiscloseNet, download [web2py source](https://mdipierro.pythonanywhere.com/examples/static/web2py_src.zip), extract it.
Then download [DiscloseNet](https://gitlab.com/vikrampudi/publications/-/archive/master/publications-master.zip),
extract it inside the web2py/applications folder. Rename the extracted 'publications-master' folder into
'publications' (for e.g.).

Then go into publications/private and edit appconfig.ini to configure it for your organization/institute.

Next, start web2py by going back into the web2py folder and run:

    python web2py.py -a ""

Finally, access your website at: http://127.0.0.1:8000/publications

To make your website accessible publicly like:

http://[your_web2py_server]/publications

you must deploy web2py publicly, perhaps behind a web-server like Apache. To do so,
see the *deployment chapter* of the [web2py book](http://web2py.com/book) for details on doing this.

## Details of the hosted website and its moderation

The website is designed so that _all_ visitors may view its content, 
which consists of research publications. Please observe the copyright 
notice that will appear on the website for this content:

*Copyright Notice:* The material presented here is to ensure timely 
dissemination of scholarly and technical work on a non-commercial 
basis. Copyright and all rights therein are retained by authors or by 
other copyright holders. All persons copying this information are 
expected to adhere to the terms and constraints invoked by each 
author's copyright. These works may not be reposted without the 
explicit permission of the copyright holder.

*Searching Content:* The content is easily searchable by centre 
(subject-area / department), content-type (book, thesis, etc.), author 
and date range. By default, for public visitors, the homepage shows the 
institute publications of the current year (may include last year as 
well, if this year has just started and does not have much content 
yet). The default view shows books, peer-reviewed publications 
(journal/conference) and technical reports of the institute. It does 
not show theses, which may be seen/searched separately.

*Adding Content:* The website enables designated institute admin 
personnel and/or faculty members to add content. The content consists 
of research publications, each of which can be either a book, journal 
paper, conference paper, technical report, or a PhD or master's 
thesis. Each publication consists of one or more authors. A thesis may 
have one or more advisors.

*Moderation:* The designated admin/faculty may add more authors into the 
system. For ease and efficiency, the institute may designate several 
admin, for e.g. one per department, and several or all faculty members 
to add content to the repository. To prevent arbitrary content from 
being posted, the institute may designate one or a few members as 
_moderators_. One admin person may serve as a thesis moderator, 
who will approve theses that are uploaded by other admin. A 
faculty-in-charge may serve as a publications moderator to ensure that 
technical reports uploaded meet a minimum standard set by the 
institute.

The centres/subject-areas can be changed by moderators. This is 
best done initially, at installation time, and is best not changed 
frequently, and arbitrarily after that, as it may make the subject-area 
of existing publications to become invalid.

*License:* DiscloseNet is released under the GPLv3 open source license. 
Additionally, you may not modify or remove the notices about 
DiscloseNet present on the help page of the website that is served by 
this software. More details of the license are in the file: LICENSE.

*Disclaimer:* The authors of DiscloseNet are not legally responsible 
for the hosting of this software on any domain, or for the material 
uploaded by users.
