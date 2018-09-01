# DiscloseNet

DiscloseNet is a software for hosting a website to serve as an 
institute repository of academic research publications of the 
institute.

## Installation

A system must be configured to host web2py applications. See the 
deployment chapter of the web2py book for details on doing this. It is available here:

http://web2py.com/book

Once web2py is hosted, this application may be extracted into the 
web2py/applications directory as a folder named 'publications' (for 
e.g.). Then go into publications/models directory and edit config.py to 
configure it for your organization/institute.

Finally, start web2py and access your website at: http://your_web2py_server/publications

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
of research publications, each of which can be either a book, a journal 
paper, a conference paper, a technical report, or a PhD or master's 
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

DiscloseNet is released under the GPLv3 open source license. 
Additionally, you may not modify or remove the notices about 
DiscloseNet present on the help page of the website that is served by 
this software. More details of the license are in the file: LICENSE.

*Disclaimer:* The authors of DiscloseNet are not legally responsible 
for the hosting of this software on any domain, or for the material 
uploaded by users.
