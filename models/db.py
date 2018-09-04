# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# AppConfig configuration made easy. Look inside private/appconfig.ini
# Auth is for authenticaiton and access control
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig
from gluon.tools import Auth

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.15.5":
    raise HTTP(500, "Requires web2py 2.15.5 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
configuration = AppConfig()

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(configuration.get('db.uri'),
             pool_size=configuration.get('db.pool_size'),
             migrate_enabled=configuration.get('db.migrate'),
             check_reserved=['all'])
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = [] 
if request.is_local and not configuration.get('app.production'):
    response.generic_patterns.append('*')

# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = 'bootstrap4_inline'
response.form_label_separator = ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=configuration.get('host.names'))

# -------------------------------------------------------------------------
# create all tables needed by auth, maybe add a list of extra fields
# -------------------------------------------------------------------------
auth.settings.extra_fields['auth_user'] = [
    db.Field('homepage', length=256, default='', requires = [IS_EMPTY_OR(IS_URL())]),
    db.Field('mailserver', length=128, default='', comment='Leave blank to allow this website to manage your password'),
    db.Field('organization', 'string',length=256, default=configuration.get('host.institute')) #field needed for adjunct faculty
]

#t = auth.settings.table_user
#t.last_name.requires = IS_NOT_EMPTY()
#t.email.requires = [IS_EMPTY_OR(IS_EMAIL()), IS_NOT_IN_DB(db, 'auth_user.email')]
#t.homepage.requires = [IS_NULL_OR(IS_URL())]

auth.define_tables(username=False, signature=False)

#-- following lines added by Vikram
#from gluon.contrib.login_methods.cas_auth import CasAuth
#auth.settings.login_form=CasAuth()
#auth.settings.login_form.settings( globals(), urlbase = "https://login.abc.edu/cas" )
#-- end of this batch of lines added by Vikram

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else configuration.get('smtp.server')
mail.settings.sender = configuration.get('smtp.sender')
mail.settings.login = configuration.get('smtp.login')
mail.settings.tls = configuration.get('smtp.tls') or False
mail.settings.ssl = configuration.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled.append('register')
auth.settings.create_user_groups = False # no need to create separate group for each user

# -------------------------------------------------------------------------  
# read more at http://dev.w3.org/html5/markup/meta.name.html               
# -------------------------------------------------------------------------
response.meta.author = configuration.get('app.author')
response.meta.description = configuration.get('app.description')
response.meta.keywords = configuration.get('app.keywords')
response.meta.generator = configuration.get('app.generator')
response.show_toolbar = configuration.get('app.toolbar')

# -------------------------------------------------------------------------
# your http://google.com/analytics id                                      
# -------------------------------------------------------------------------
response.google_analytics_id = configuration.get('google.analytics_id')

# -------------------------------------------------------------------------
# maybe use the scheduler
# -------------------------------------------------------------------------
if configuration.get('scheduler.enabled'):
    from gluon.scheduler import Scheduler
    scheduler = Scheduler(db, heartbeat=configuration.get('scheduler.heartbeat'))

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------
oldURL = URL
def URL(*f, **d):
    d['url_encode'] = False
    return oldURL(*f, **d)

db.define_table('subject',
    db.Field('name','string',length=256),
    db.Field('abbr','string',length=64),
)

db.define_table('publication', # abstract base type for book, thesis, etc.
    db.Field('title','string',length=256), )

typenames = ['Books','Journal Papers','Conference Papers','Technical Reports','Masters Theses','PhD Theses']
typenames2 = ['Book','Journal Paper','Conference Paper','Technical Report','Masters Thesis','PhD Thesis']
typetables = ['book','article','inproceedings','techreport','mastersthesis','phdthesis']
thesistypes = ['mastersthesis','phdthesis']

db.define_table('pubrelations',
    db.Field('fromId',db.publication,requires = IS_IN_DB(db,'publication.id','%(title)s')),
    db.Field('toId',db.publication,requires = IS_IN_DB(db,'publication.id','%(title)s')),
    db.Field('relation','integer',requires = IS_INT_IN_RANGE(0,3)), # 0 = basedon, 1 = supercedes, 2 = longer, 3 = citation
    
)

db.define_table('comments',
    db.Field('pubid',db.publication,requires = IS_IN_DB(db,'publication.id','%(title)s')),
    db.Field('personid',db.auth_user,requires = IS_IN_DB(db,'auth_user.id','%(first_name)s %(last_name)s')),
    db.Field('xcomment','text',requires=IS_NOT_EMPTY()) #changed name to xcomment as comment is a reserved SQL keyword
)

db.define_table('author',
    db.Field('pubid',db.publication,requires = IS_IN_DB(db,'publication.id','%(title)s')),
    db.Field('personid',db.auth_user,requires = IS_IN_DB(db,'auth_user.id','%(first_name)s %(last_name)s')), 
)
db.executesql('CREATE INDEX IF NOT EXISTS author_idx ON author (pubid);')

db.define_table('advisor',
    db.Field('pubid',db.publication,requires = IS_IN_DB(db,'publication.id','%(title)s')),
    db.Field('personid',db.auth_user,requires = IS_IN_DB(db,'auth_user.id','%(first_name)s %(last_name)s')), 
)

db.define_table('book',
    db.Field('pubid',db.publication),
    db.Field('title','string',length=256,required=True,label='Title*',unique=True),
    db.Field('xdate','date',requires=IS_DATE(),label='Date*'), # for conf paper, this date is the first day of conference
    db.Field('publisher','string',length=256,required = True,label='Publisher*'),
    db.Field('abstract','text'),
    db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s')),
    db.Field('num','integer',label='Number',default=-1), # techreport serial number
    db.Field('pdf','upload',label='PDF'),
    db.Field('ppt','upload',label='Presentation',comment='ppt, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('pdfsource','upload',label='PDF Source',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('programs','upload',comment='tgz, zip, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('icon','upload'),
    db.Field('xkey','string',label='Key',length=64,comment = 'Bibtex key for citations'),
    db.Field('edited','boolean',comment='Is this book edited or authored? Edited means different authors for each chapter and an editor acts as a coordinator.'),
    db.Field('volume','string',length=64),
    db.Field('series','string',length=64),
    db.Field('edition','integer',requires = IS_NULL_OR(IS_INT_IN_RANGE(1,100000))),
    db.Field('bookurl','string',length=256,requires = IS_NULL_OR(IS_URL())),
    db.Field('uploaded_by','string'),
    db.Field('upload_date','date',requires=IS_DATE()), 
)

#book.pdfsource.requires = IS_NOT_EMPTY()    
   

db.define_table('article', # journal article
    db.Field('pubid',db.publication),
    db.Field('title','string',length=256,required=True,label='Title*',unique=True),
    db.Field('xdate','date',requires=IS_DATE(),label='Date*'), # for conf paper, this date is the first day of conference
    db.Field('abstract','text'),
    db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s')),
    db.Field('num','integer',label='Number',default=-1), # techreport serial number
    db.Field('pdf','upload',requires = IS_UPLOAD_FILENAME(extension='pdf'),label='PDF*'),
    db.Field('ppt','upload',label='Presentation',comment='ppt, etc.',authorize=lambda row: auth.is_logged_in()),
    #db.Field('pdfsource','upload',label='PDF Source*',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in(),requires=IS_NOT_EMPTY()),
    db.Field('pdfsource','upload',label='PDF Source',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('programs','upload',comment='tgz, zip, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('icon','upload'),
    db.Field('xkey','string',label='Key',length=64,comment = 'Bibtex key for citations'),
    db.Field('journal','string',length=256,required = True),
    db.Field('volume','string',length=64),
    db.Field('volume_number','string',length=64),
    db.Field('firstpage','integer',required = False,requires = IS_NULL_OR(IS_INT_IN_RANGE(1,100000))),
    db.Field('lastpage','integer',required = False,requires = IS_NULL_OR(IS_INT_IN_RANGE(1,100000))),
    db.Field('journalurl','string',length=256,requires = IS_NULL_OR(IS_URL())),
    db.Field('uploaded_by','string'),
    db.Field('upload_date','date',requires=IS_DATE()), 
)

#article.pdfsource.requires = IS_NOT_EMPTY()

db.define_table('inproceedings', # conference paper
    db.Field('pubid',db.publication),
    db.Field('title','string',length=256,required=True,label='Title*',unique=True),
    db.Field('xdate','date',label='Conference Start Date*',requires=IS_DATE()), # for conf paper, this date is the first day of conference
    db.Field('enddate','date',label='Conference End Date',required=False,requires = IS_NULL_OR(IS_DATE())),
    db.Field('conference','string',length=256,required=True,label='Conference*'),
    db.Field('confabbr','string',length=64),
    db.Field('abstract','text'),
    db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s')),
    db.Field('num','integer',label='Number',default=-1), # techreport serial number
    db.Field('pdf','upload',requires = IS_UPLOAD_FILENAME(extension='pdf'),label='PDF*'),
    db.Field('ppt','upload',label='Presentation',comment='ppt, etc.',authorize=lambda row: auth.is_logged_in()),
    #db.Field('pdfsource','upload',label='PDF Source*',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in(),requires=IS_NOT_EMPTY()),
    db.Field('pdfsource','upload',label='PDF Source',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('programs','upload',comment='tgz, zip, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('icon','upload'),
    db.Field('xkey','string',label='Key',length=64,comment = 'Bibtex key for citations'),
    db.Field('booktitle','string',length=256),
    db.Field('firstpage','integer',requires = IS_NULL_OR(IS_INT_IN_RANGE(1,100000))),
    db.Field('lastpage','integer',requires = IS_NULL_OR(IS_INT_IN_RANGE(1,100000))),
    db.Field('address','string',length=256),
    db.Field('confurl','string',length=256,requires = IS_NULL_OR(IS_URL())),
    db.Field('uploaded_by','string'),
    db.Field('upload_date','date',requires=IS_DATE()), 
    db.Field('publicationregion',requires=IS_IN_SET(('International','National'))), 
    db.Field('field',requires=IS_IN_SET(('CSE','ECE','CIVIL','CNS'))), 
)

#inproceedings.pdfsource.requires = IS_NOT_EMPTY()

db.define_table('techreport', # technical report
    db.Field('pubid',db.publication),
    db.Field('title','string',length=256,required=True,label='Title*',unique=True),
    db.Field('xdate','date',requires=IS_DATE(),label='Date*'), # for conf paper, this date is the first day of conference
    db.Field('abstract','text'),
    db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s')),
    db.Field('num','integer',label='Number',default=-1), # techreport serial number
    db.Field('pdf','upload',requires = IS_UPLOAD_FILENAME(extension='pdf'),label='PDF*'),
    db.Field('ppt','upload',label='Presentation',comment='ppt, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('pdfsource','upload',label='PDF Source',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in()),
    #db.Field('pdfsource','upload',label='PDF Source*',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in(),requires=IS_NOT_EMPTY()),
    db.Field('programs','upload',comment='tgz, zip, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('icon','upload'),
    db.Field('xkey','string',label='Key',length=64,comment = 'Bibtex key for citations'),
    db.Field('uploaded_by','string'),
    db.Field('upload_date','date',requires=IS_DATE()), 
)

#techreport.pdfsource.requires = IS_NOT_EMPTY()

db.define_table('mastersthesis', # masters thesis
    db.Field('pubid',db.publication),
    db.Field('title','string',length=256,required=True,label='Title*',unique=True),
    db.Field('xdate','date',requires=IS_DATE(),label='Date*'), # for conf paper, this date is the first day of conference
    db.Field('abstract','text'),
    db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s')),
    db.Field('num','integer',label='Number',default=-1), # techreport serial number
    db.Field('pdf','upload',requires = IS_UPLOAD_FILENAME(extension='pdf'),label='PDF*'),
    db.Field('ppt','upload',label='Presentation',comment='ppt, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('pdfsource','upload',label='PDF Source*',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in(),requires=IS_NOT_EMPTY()),
    db.Field('programs','upload',comment='tgz, zip, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('icon','upload'),
    db.Field('xkey','string',label='Key',length=64,comment = 'Bibtex key for citations'),
    db.Field('thesisurl','string',length=256,requires = IS_NULL_OR(IS_URL())),
    db.Field('uploaded_by','string'),
    db.Field('upload_date','date',requires=IS_DATE()), 
)

#mastersthesis.pdfsource.requires = IS_NOT_EMPTY()
    
db.define_table('phdthesis', # phd thesis
    db.Field('pubid',db.publication),
    db.Field('title','string',length=256,required=True,label='Title*',unique=True),
    db.Field('xdate','date',requires=IS_DATE(),label='Date*'), # for conf paper, this date is the first day of conference
    db.Field('abstract','text'),
    db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s')),
    db.Field('num','integer',label='Number',default=-1), # techreport serial number
    db.Field('pdf','upload',requires = IS_UPLOAD_FILENAME(extension='pdf'),label='PDF*'),
    db.Field('ppt','upload',label='Presentation',comment='ppt, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('pdfsource','upload',label='PDF Source*',comment='latex, doc, etc.',authorize=lambda row: auth.is_logged_in(),requires=IS_NOT_EMPTY()),
    db.Field('programs','upload',comment='tgz, zip, etc.',authorize=lambda row: auth.is_logged_in()),
    db.Field('icon','upload'),
    db.Field('xkey','string',label='Key',length=64,comment = 'Bibtex key for citations'),
    db.Field('thesisurl','string',length=256,requires = IS_NULL_OR(IS_URL())),
    db.Field('uploaded_by','string'),
    db.Field('upload_date','date',requires=IS_DATE()), 
)
#phdthesis.pdfsource.requires = IS_NOT_EMPTY()
db.author.personid.widget = SQLFORM.widgets.autocomplete(
     request, db.auth_user.first_name, limitby=(0,10), min_length=2)

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)
