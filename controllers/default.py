import datetime

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

#------- Controller function --------

def help():
    return dict()

@auth.requires_permission('create')
def add_author():
    nextlink = request.vars.nextlink or 'index'
    pubid = request.vars.pubid
    if pubid == None:
        return dict(mesg='First select a publication.')
    fields = []
    from gluon.sqlhtml import form_factory
    authorsQuery = (db.auth_membership.group_id == auth.id_group('author')) & \
                   (db.auth_membership.user_id == db.auth_user.id)
    #advisorsQuery = (db.auth_membership.group_id == auth.id_group('faculty')) & \
    #                (db.auth_membership.user_id == db.auth_user.id)
    fields.append(db.Field('new_author','integer',requires = IS_IN_DB(db(authorsQuery),
            'auth_user.id','%(first_name)s %(last_name)s'),required=True))
    n = db(db.author.pubid == pubid).count() + 1
    fields.append(db.Field('author_order','integer',requires=IS_IN_SET(range(1,n+1)),required=True,default=n))
    form = form_factory(*fields)
    if form.accepts(request.vars,session):
        recs = db(db.author.pubid == pubid).select(orderby=db.author.id)
        newrec = db.author.insert(pubid=pubid,personid=form.vars.new_author)
        allrecs = [i.id for i in recs]
        allrecs.append(newrec)
        allrecs.sort()
        curpos = allrecs.index(newrec)
        order = int(form.vars.author_order) - 1
        if order != curpos:
            while order != curpos:
                if order > curpos:
                    db.author[allrecs[curpos]] = dict(personid=db.author[allrecs[curpos+1]].personid)
                    curpos += 1
                else:
                    db.author[allrecs[curpos]] = dict(personid=db.author[allrecs[curpos-1]].personid)
                    curpos -= 1
            db.author[allrecs[curpos]] = dict(personid=form.vars.new_author)
        redirect(URL(r=request, f=nextlink))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def remove_author():
    nextlink = request.vars.nextlink or 'index'
    pubid = request.vars.pubid
    if pubid == None:
        return dict(mesg='First select a publication.')
    from gluon.sqlhtml import form_factory
    authorsQuery = (db.author.pubid == pubid) & (db.author.personid == db.auth_user.id)
    #advisorsQuery = (db.advisor.pubid == pubid) & (db.advisor.personid == db.auth_user.id)
    form = form_factory(db.Field('remove_author',requires = IS_IN_DB(db(authorsQuery),
            'auth_user.id','%(first_name)s %(last_name)s',multiple=True),
            comment='Use ctrl to select multiple',required=True))
    if form.accepts(request.vars,session):
        removed = 0
        if request.vars.remove_author:
            to_remove = request.vars.remove_author if isinstance(request.vars.remove_author, list) \
                                else [request.vars.remove_author]
            for i in to_remove:
                db((db.author.pubid==pubid)&(db.author.personid==i)).delete()
                removed += 1
        redirect(URL(r=request, f=nextlink))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def change_type():
    table = request.vars.table
    tid = request.vars.tid
    if table == None or tid == None:
        return dict(mesg='First select a publication properly.')
    validtables = ['article','inproceedings','techreport']
    if table not in validtables:
        return dict(mesg='This conversion is not implemented')
    newtable = None

    from gluon.sqlhtml import form_factory
    validtables.remove(table)
    form = form_factory(db.Field('new_type',requires = IS_IN_SET(validtables),required=True))
    if form.accepts(request.vars,session):
        rec = db(db[table].id == tid).select(db[table].ALL)[0]
        newtable = form.vars.new_type
        if db(db[newtable].title == rec.title).select():
            return dict(mesg='Title already exists in %s.' % newtable)
        newfields = {
            'pubid':rec.pubid,
            'title':rec.title,
            'xdate':rec.xdate,
            'abstract':rec.abstract,
            'subjectarea':rec.subjectarea,
            'num':rec.num,
            'icon':rec.icon,
            'pdf':rec.pdf,
            'ppt':rec.ppt,
            'pdfsource':rec.pdfsource,
            'programs':rec.programs,
            'xkey':rec.xkey}
        if table == 'inproceedings':
            if newtable == 'article':
                newfields['journal']=rec.conference
                newfields['firstpage']=rec.firstpage
                newfields['lastpage']=rec.lastpage
                newfields['journalurl']=rec.confurl
        if table == 'article':
            if newtable == 'inproceedings':
                newfields['conference']=rec.journal
                newfields['firstpage']=rec.firstpage
                newfields['lastpage']=rec.lastpage
                newfields['confurl']=rec.journalurl
        newrec = db[newtable].insert(**newfields)
        db(db[table].id == tid).delete()
        redirect(URL(r=request,f='view_publication/%s/%s'%(newtable,newrec)))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

def add_page(fname,i,type,authors):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    elements = []
    realauthor=authors
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate('/home/web2py/web2py/applications/research_centres/private/try.pdf')
    treepath = '/home/web2py/web2py/applications/research_centres/static/icon_abc.gif'
    ts = styles['Title']
    ts.fontSize = 15
    nc = styles['Normal']
    nc.alignment = 1
    i.num=-1
    if(i.subjectarea):	
    	centre = 'Centre for '+db.subject[i.subjectarea].name
    if type == 'book':
      elements.append(Paragraph(i.title, styles['Title']))
      if i.edition > 1:
          elements.append(Paragraph('Edition: %d<br />'%i.edition, styles['Normal']))
      elements.append(Paragraph('by', styles['Normal']))
      elements.append(Paragraph('<br />', styles['Normal']))
      elements.append(Paragraph('%s' % realauthor, styles['Normal']))
      elements.append(Paragraph('<br /><br /><br />', styles['Normal']))
      #elements.append(Paragraph('<br />%s<br /><br /><br />' % authors, styles['Normal']))
      if i.publisher:
          elements.append(Paragraph('<br />Publisher: %s<br />' % i.publisher, styles['Normal']))
      if i.volume:
          elements.append(Paragraph('<br />Volume: %s<br />' % i.volume, styles['Normal']))
      if i.series:
          elements.append(Paragraph('<br />Series: %s<br /><br />' % i.series, styles['Normal']))
      elements.append(Paragraph('<br />Book No: ABC/Bk/%d/%d<br /><br />' % (i.xdate.year,i.num),styles['Normal']))
      elements.append(Paragraph('<br /><br />', styles['Normal']))
      elements.append(Paragraph('<img src="%s" width="30" height="25" />'%treepath, styles['Normal']))
      
      if(i.subjectarea):	
	  elements.append(Paragraph(centre, styles['Normal']))
      elements.append(Paragraph(configuration.get('host.institute'), styles['Normal']))
      elements.append(Paragraph(i.xdate.strftime('%B %Y'), styles['Normal']))
    elif type == 'article':
      elements.append(Paragraph(i.title, styles['Title']))
      elements.append(Paragraph('by', styles['Normal']))
      elements.append(Paragraph('<br />', styles['Normal']))
      elements.append(Paragraph('%s' % realauthor, styles['Normal']))
      elements.append(Paragraph('<br /><br /><br />', styles['Normal']))
      #elements.append(Paragraph('<br />%s<br /><br /><br />' % authors, styles['Normal']))
      if i.journal:	 
	  elements.append(Paragraph('in', styles['Normal']))
      	  elements.append(Paragraph('<br /><i>%s</i>' % i.journal, styles['Normal']))
#      if i.volume:
#          elements.append(Paragraph(', <i>%s</i>' % i.volume, styles['Normal']))
#      if i.volume_number:
#          elements.append(Paragraph(', <i>%s</i>' % i.volume_number, styles['Normal']))
#      if i.firstpage:
#          elements.append(Paragraph(': %d' % i.firstpage, styles['Normal']))
#      if i.lastpage:
#          elements.append(Paragraph('-%d' % i.lastpage, styles['Normal']))
      elements.append(Paragraph('<br /><br />Report No: ABC/TR/%d/%d<br /><br />' % (i.xdate.year,i.num),styles['Normal']))
      elements.append(Paragraph('<br /><br />', styles['Normal']))
      elements.append(Paragraph('<img src="%s" width="30" height="25" />'%treepath, styles['Normal']))
      if i.subjectarea:      
	 elements.append(Paragraph(centre, styles['Normal']))
      elements.append(Paragraph(configuration.get('host.institute'), styles['Normal']))
      elements.append(Paragraph(i.xdate.strftime('%B %Y'), styles['Normal']))
    elif type == 'inproceedings':
      elements.append(Paragraph(i.title, styles['Title']))
      elements.append(Paragraph('by', styles['Normal']))
      elements.append(Paragraph('<br />', styles['Normal']))
      elements.append(Paragraph('%s' % realauthor, styles['Normal']))
      elements.append(Paragraph('<br /><br /><br />', styles['Normal']))
      
      #elements.append(Paragraph('<br />%s<br /><br /><br />' % authors, styles['Normal']))
      if i.conference:	      
	elements.append(Paragraph('in', styles['Normal']))
      	elements.append(Paragraph('<br /><i>%s</i>' % i.conference, styles['Normal']))
      if i.confabbr:
          elements.append(Paragraph('(<i>%s</i>)' % i.confabbr, styles['Normal']))
      #confurl = i.confurl
      if i.firstpage:
          elements.append(Paragraph(': %d' % i.firstpage, styles['Normal']))
      if i.lastpage:
          elements.append(Paragraph('-%d' % i.lastpage, styles['Normal']))
      if i.address:
          elements.append(Paragraph('<br /><br />%s<br />' % i.address, styles['Normal']))
      elements.append(Paragraph('<br /><br />Report No: ABC/TR/%d/%d<br /><br />' % (i.xdate.year,i.num), styles['Normal']))
      elements.append(Paragraph('<br /><br />', styles['Normal']))
      elements.append(Paragraph('<img src="%s" width="30" height="25" />'%treepath, styles['Normal']))
      if(i.subjectarea):	
	  elements.append(Paragraph(centre, styles['Normal']))
      elements.append(Paragraph(configuration.get('host.institute'), styles['Normal']))
      elements.append(Paragraph(i.xdate.strftime('%B %Y'), styles['Normal']))
    elif type == 'techreport':
      elements.append(Paragraph(i.title, styles['Title']))
      elements.append(Paragraph('by', styles['Normal']))
      elements.append(Paragraph('<br />', styles['Normal']))
      elements.append(Paragraph('%s' % realauthor, styles['Normal']))
      elements.append(Paragraph('<br /><br /><br />', styles['Normal']))     
      #elements.append(Paragraph('<br />%s<br /><br /><br />' % authors, styles['Normal']))
      elements.append(Paragraph('<br /><br />Report No: ABC/TR/%d/%d<br /><br />' % (i.xdate.year,i.num), styles['Normal']))
      elements.append(Paragraph('<br /><br />', styles['Normal']))
      elements.append(Paragraph('<img src="%s" width="30" height="25" />'%treepath, styles['Normal']))
      if(i.subjectarea):	
	  elements.append(Paragraph(centre, styles['Normal']))
      elements.append(Paragraph(configuration.get('host.institute'), styles['Normal']))
      elements.append(Paragraph(i.xdate.strftime('%B %Y'), styles['Normal']))
    doc.build(elements)
    if(i.pdf):	
    	newfinal_add(i.pdf)
		
def newfinal_add(fil):
	from pyPdf import PdfFileWriter, PdfFileReader
	import os
	k = fil
	if k:
		k = fil
	else:
		return
	if k.endswith(".pdf"):
		k = fil;
	else:
		return;

   	if k=="article.pdf.acbdc115-641b-495c-b6cc-9172308c4031.pdf" or k =="inproceedings.pdf.47efe0d0-4d62-46ff-9df7-64bd84d4b2ff.pdf" or k=="article.pdf.8680807f363b8b25.323030355f362e706466.pdf" or k=="article.pdf.9432a67306009058.746573742e706466.pdf" or k=="inproceedings.pdf.f20c57ee-71c7-4765-ae6b-c7b4b29a3f00.pdf" or k=="article.pdf.86e41d5baa08609f.323030355f352e706466.pdf" or k=="inproceedings.pdf.e0af031d-cea6-4f08-9139-d317139a6164.pdf" or k=="article.pdf.2f8864c2-fbdb-4eb8-ad0b-f02fec5555a3.pdf" or k=="article.pdf.27f0296c-140a-4771-ace6-48f4a8fad265.pdf" or k=="inproceedings.pdf.e7e82961-fa0a-485c-acf4-cf32884e400b.pdf" or k=="inproceedings.pdf.861674cc-3f1e-4e13-8dfa-daa856416a63.pdf" or k=="inproceedings.pdf.4c56a6de-20d4-4361-a843-1fa3c9dfe8cf.pdf" or k=="article.pdf.646add64-60f2-4b25-abe1-917cf411135b.pdf" or k=="inproceedings.pdf.cf608009-aa32-4226-b24f-9c47aadeea64.pdf" or k=="article.pdf.98c1af722d3d0a87.746573742e706466.pdf" or k=="inproceedings.pdf.a22e0d3a-aa17-4364-b2f4-33bbeb1843e6.pdf" or k=="inproceedings.pdf.d53f90df-022c-445d-809b-3c44b0b955ac.pdf" or k=="inproceedings.pdf.d7e16329-b8e0-4225-91ae-5ed19e1a9fc6.pdf" or k=="inproceedings.pdf.85d3d0c0-fc4c-45a2-9734-669f4b04566b.pdf" or k=="article.pdf.e1b0aa5d-df85-4ec3-80ca-e212481c55b5.pdf" or k=="inproceedings.pdf.81eb71de8e239b72.323030355f322e706466.pdf" or k=="inproceedings.pdf.054a0e1c-4ca3-4dc4-b97b-30b14d26521f.pdf":
		return;	
	k1 ="/home/web2py/web2py/applications/research_centres/uploads/" + k;
    	k = "/home/web2py/web2py/applications/research_centres/private/uploadbackup/" + k;
	#os.system ("cp %s %s" % (k , "document1.pdf"))

	output = PdfFileWriter()
	input1 = PdfFileReader(file(k1, "rb"))
	#output = PdfFileReader(file("document1.pdf", "wb"))
	input2 = PdfFileReader(file("/home/web2py/web2py/applications/research_centres/private/try.pdf", "rb"))

	i = input1.getNumPages();

	#output.setPageSize
	output.addPage(input2.getPage(0));
	for j in range(0,i):
		output.addPage(input1.getPage(j));

	outputStream = file("/home/web2py/web2py/applications/research_centres/private/document-output.pdf", "wb")
#	outputStream = file(k1, "wb")
	output.write(outputStream)
	outputStream.close()
	os.system ("cp %s %s" % ("/home/web2py/web2py/applications/research_centres/private/document-output.pdf" ,k1 ))
        return 

@auth.requires_permission('create')
def publication_form(): 
    now=datetime.datetime.now()
    table = request.args(0)
    authors = request.vars.author or []
    advisors = request.vars.advisor or []
    if not isinstance(authors, list): authors = [authors]
    if not isinstance(advisors, list): advisors = [advisors]

    #if not (auth.is_logged_in() and db(((db.auth_membership.user_id == auth.user.id)|(db.area.delegated_to == auth.user.id)|(db.area.admin == auth.user.id))).select()):
    #    return dict(mesg = 'Permission denied')

    pubid = db.publication.insert(title='')
    pubfield = db[table].pubid
    pubfield.readable = pubfield.writable = False
    pubfield.default = pubid
    numfield = db[table].num
    numfield.readable = numfield.writable = False
#below lines are added by me(saikiran) to store the uplaod time and uploadeder name
    uploadfield = db[table].uploaded_by
    uploadfield.readable = uploadfield.writable = False
    uploadfield.default = auth.user.email+' '+'('+auth.user.first_name + ' ' + auth.user.last_name+')'
    datefield = db[table].upload_date
    datefield.readable = datefield.writable = False
    datefield.default = now
    form = SQLFORM(db[table])
    if form.accepts(request.vars,session):
        for i in authors:
            db.author.insert(pubid=pubid, personid=i)
        for i in advisors:
            db.advisor.insert(pubid=pubid, personid=i)
        mail.settings.sender=configuration.get('smtp.sender')
        authors_str = ''
        for i in authors:
            x = db(db.auth_user.id == i).select()[0]
            if authors_str:
                authors_str += ', %(first_name)s %(last_name)s' % x
            else:
                authors_str = '%(first_name)s %(last_name)s' % x
        advisors_str = ''
        for i in advisors:
            x = db(db.auth_user.id == i).select()[0]
            if advisors_str:
                advisors_str += ', %(first_name)s %(last_name)s' % x
            else:
                advisors_str = '%(first_name)s %(last_name)s' % x
        if table not in thesistypes:
            #add_page(form.vars.pdf,form.vars,table,authors_str)
            pass
        mesg_to = configuration.get('host.thesis_moderator') if table in thesistypes else configuration.get('host.techreports_moderator')
        message = '''
Title: %s
Authors: %s
''' % (form.vars.title, authors_str)
        if advisors_str: message = '%sAdvisors: %s\n' % (message, advisors_str)
        message = '''%s
Abstract: %s

To approve, visit: http://%s/research_centres/publications/moderator_page
''' % (message, form.vars.abstract, configuration.get('host.domain'))
        mail.send(mesg_to, subject='New publication added on portal', message=message)

        msg = '''Dear User,

              %s is successfully added to portal, it will be available for public once the Chair, Publication Committee approves.
'''%(table)
        mail.send(auth.user.email,subject='You have uploaded a new publication on portal',message=msg)
        session.flash = 'Uploaded. It will be displayed after approval.'
        redirect(URL(r=request, f='index'))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def pub_authors_form():
    table = request.args(0)
    num_authors = request.vars.num_authors
    num_advisors = request.vars.num_advisors
    num_authors = int(num_authors)
    num_advisors = int(num_advisors) if num_advisors else 0

    fields = []
    from gluon.sqlhtml import form_factory

    authorsQuery = (db.auth_membership.group_id == auth.id_group('author')) & \
                   (db.auth_membership.user_id == db.auth_user.id)
    advisorsQuery = (db.auth_membership.group_id == auth.id_group('faculty')) & \
                    (db.auth_membership.user_id == db.auth_user.id)
    for j in xrange(num_authors):
        fields.append(db.Field('author'+str(j),'string',requires = IS_IN_DB(db(authorsQuery),
            'auth_user.id','%(first_name)s %(last_name)s'),label='Author %d*'%(j+1),required=True))
    for j in xrange(num_advisors):
        fields.append(db.Field('advisor'+str(j),'string',requires = IS_IN_DB(db(advisorsQuery),
            'auth_user.id','%(first_name)s %(last_name)s'),label='Advisor %d*'%(j+1),required=True))
    form = form_factory(*fields)
    if form.accepts(request.vars,session):
        s = ''
        sep = '?'
        for i in xrange(num_authors):
            s += '%sauthor=%s' % (sep,form.vars['author'+str(i)])
            sep = '&'
        for i in xrange(num_advisors):
            s += '%sadvisor=%s' % (sep,form.vars['advisor'+str(i)])
            sep = '&'
        redirect(URL(r=request, f='publication_form/%s%s' % (table,s)))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def add_publication():
    table = request.args(0)
    fields = []
    from gluon.sqlhtml import form_factory
    fields.append(db.Field('num_authors','integer',label='Number of Authors',required=True,default=1))
    if table in ['mastersthesis', 'phdthesis']:
        fields.append(db.Field('num_advisors','integer',label='Number of Advisors',required=True,default=1))
    form = form_factory(*fields)
    if form.accepts(request.vars,session):
        if table in ['mastersthesis', 'phdthesis']:
            redirect(URL(r=request, f='pub_authors_form/%s?num_authors=%s&num_advisors=%s' % (table,form.vars.num_authors,form.vars.num_advisors)))
        else:
            redirect(URL(r=request, f='pub_authors_form/%s?num_authors=%s' % (table,form.vars.num_authors)))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def pending():
    #types = range(len(typenames)-2) # default page doesn't have theses listed
    types = range(len(typenames))
    if request.vars.type:
        if isinstance(request.vars.type, list):
            types = [typenames.index(x) for x in request.vars.type if x in typenames]
            request.vars.type = None
        else:
            types = [typenames.index(request.vars.type)]
    pubs = {}
    authors = {}
    advisors = {}
    authorids = {}
    advisorids = {}
    for t in types:
        table = db[typetables[t]]
        query = (table.num == -1)
        thisauthorq = (db.author.personid == auth.user.id) & (table.pubid == db.author.pubid)
        query = thisauthorq & query
        #thisadvisorq = (db.advisor.personid == auth.user.id) & (table.pubid == db.advisor.pubid)
        #query = thisadvisorq & query
        pubs[t] = db(query).select(table.ALL,orderby=~table.xdate)
        thispubs = set([x.pubid for x in pubs[t]])
        get_authors(authors, authorids, table, thispubs)
        if typetables[t] in thesistypes:
            get_advisors(advisors, advisorids, table, thispubs)
    papers = []
    for y in [1,2,3]: # journals, conference papers, techreports
        if y in pubs: papers.extend(pubs[y])
        pubs[y]=None
    papers.sort(lambda a,b: (b.xdate.year-a.xdate.year) or (b.num-a.num))
    pubs[1] = papers
    return dict(pubs=pubs, authors=authors, advisors=advisors)

#@auth.requires_membership('moderator')
@auth.requires_permission('create')
def update_publication(): #changed from crud to sqlform: todo: test
    table = request.args(0)
    pid = request.args(1)
    pubfield = db[table].pubid
    pubfield.readable = pubfield.writable = False
    numfield = db[table].num
    numfield.readable = numfield.writable = False
    rec = db(db[table].id == pid).select()[0]
    if rec.pdf:
        db[table].pdf.writable = False
    form = SQLFORM(db[table], pid, deletable = False)
    if form.accepts(request.vars, session):
        redirect(URL(r=request,f='view_publication/%s/%s'%(table,pid)))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def add_person():
    db.auth_user.password.comment = 'A password for this website'
    form = SQLFORM(db.auth_user)
    if form.accepts(request.vars, session):
        redirect(URL(r=request, f='update_membership?id=%s' % form.vars.id))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_permission('create')
def update_membership():
    user_id = request.vars.id
    fields = []
    from gluon.sqlhtml import form_factory
    if not user_id: # if no user_id given, then get it by showing a form
        fields.append(db.Field('user',db.auth_user,required=True,
            requires = IS_IN_DB(db,'auth_user.id','%(first_name)s %(last_name)s')))
        form = form_factory(*fields)
        if form.accepts(request.vars,session):
            redirect(URL(r=request, f='update_membership?id=%s' % form.vars.user))
        elif form.errors:
            response.flash='Errors in form'
        return dict(form=form)

    group = dict((group.role,group.id) for group in db(db.auth_group.id > 0).select())
    roles = {}
    if (auth.has_membership(group['faculty']) or auth.has_membership(group['admin'])) and not auth.has_membership(group['moderator'],user_id):
        roles.update((group[x],x) for x in ['faculty','author'])
        if not auth.has_membership(group['faculty']):
            roles.update((group[x],x) for x in ['admin'])
    if auth.has_membership(group['moderator']):
        roles.update((group[x],x) for x in ['moderator'])
        roles.update((group[x],x) for x in ['faculty','author','admin'])
    if not roles: redirect(URL(r=request, f='index'))

    cur_roles = db(db.auth_membership.user_id == user_id).select(db.auth_membership.group_id)
    cur_roles = [x.group_id for x in cur_roles]
    form = form_factory(
        db.Field('groups', requires=IS_IN_SET(roles,multiple=True), default=cur_roles, widget=SQLFORM.widgets.checkboxes.widget))
    if form.accepts(request.vars,session):
        db(db.auth_membership.user_id == user_id).delete() #remove existing memberships
        if request.vars.groups == None:
            newgroups = []
        else:
            newgroups = request.vars.groups if isinstance(request.vars.groups,list) else [request.vars.groups]
        for group_id in newgroups: #add updated memberships
            auth.add_membership(user_id=user_id, group_id=group_id)
        redirect(URL(r=request, f='index'))
    return dict(form=form)

#7. List publications (all, by type, by centre, by advisor, by year): everyone
def get_advisors(advisornames, advisorids, table, pubs): # this is needed by the actual function below
    advisorq = (table.pubid == db.advisor.pubid) & (db.advisor.personid == db.auth_user.id)
    advisors = db(table.pubid.belongs(pubs) & advisorq).select(db.advisor.id,
        db.advisor.pubid,db.auth_user.first_name,db.auth_user.last_name,orderby=db.advisor.id,distinct=True)
    for i in advisors:
        if i.advisor.pubid not in advisornames:
            advisornames[i.advisor.pubid] = []
            advisorids[i.advisor.pubid] = []
        advisornames[i.advisor.pubid].append('%(first_name)s %(last_name)s' % i.auth_user)
        advisorids[i.advisor.pubid].append(i.advisor.id)

def get_authors(authornames, authorids, table, pubs): # this is needed by the actual function below
    authorq = (db.auth_user.id == db.author.personid) & (table.pubid == db.author.pubid)
    authors = db(table.pubid.belongs(pubs) & authorq).select(db.author.id,
        db.author.pubid,db.auth_user.first_name,db.auth_user.last_name,db.auth_user.email,orderby=db.author.id,distinct=True)
    for i in authors:
        if i.author.pubid not in authornames:
            authornames[i.author.pubid] = []
            authorids[i.author.pubid] = []
#below lines are added by me(sai kiran) to get email id's of authors for moderators
	if auth.user_id>0 and i.auth_user.email and auth.has_membership(auth.id_group('moderator')):
            authornames[i.author.pubid].append('%(first_name)s %(last_name)s (%(email)s)' % i.auth_user) 
	else:
            authornames[i.author.pubid].append('%(first_name)s %(last_name)s' % i.auth_user)
        authorids[i.author.pubid].append(i.author.id)

def view_publication():
    table = request.args(0)
    id = request.args(1)
    type = typetables.index(table)
    query = (db[table].id == id)
    rows = db(query).select()
    authors = {}
    authorids = {}
    advisors = {}
    advisorids = {}
    get_authors(authors, authorids, db[table], [x.pubid for x in rows])
    actual_authorids = []
#below lines are added by me(saikiran) to get a comment box for moderators
    uploadfield = db.comments.pubid
    uploadfield.readable = uploadfield.writable = False
    uploadfield.default = rows[0].pubid
    datefield = db.comments.personid
    datefield.readable = datefield.writable = False
    datefield.default = auth.user_id 
    form = SQLFORM(db.comments)
    if rows[0].pubid in authorids:
        actual_authorids = [db.author[i].personid for i in authorids[rows[0].pubid]]
    get_advisors(advisors, advisorids, db[table], [x.pubid for x in rows])
    if form.accepts(request.vars,session):
        redirect(URL(r=request, f='index'))
    return dict(record=rows[0], type=type, authors=authors, authorids=actual_authorids, advisors=advisors,form=form)

#@cache(request.env.path_info, cache_model=cache.ram, time_expire=5000)
def get_default_results():
    types = range(len(typenames)-2) # default page doesn't have theses listed
    pubs = {}
    authors = {}
    advisors = {}
    authorids = {}
    advisorids = {}
    default_start_date = datetime.date(datetime.date.today().year-1,1,1)
    for t in types:
        table = db[typetables[t]]
        query = (table.xdate >= default_start_date) & (table.num != -1)
        pubs[t] = db(query).select(table.ALL,orderby=~table.xdate)
        thispubs = set([x.pubid for x in pubs[t]])
        get_authors(authors, authorids, table, thispubs)
        if typetables[t] in thesistypes:
            get_advisors(advisors, advisorids, table, thispubs)
    return (pubs,authors,advisors)

def index_showtypes():
    types = range(len(typenames)-2) # default page doesn't have theses listed
    if request.vars.type:
        if isinstance(request.vars.type, list):
            types = [typenames.index(x) for x in request.vars.type]
        else:
            types = [typenames.index(request.vars.type)]

    from gluon.sqlhtml import form_factory
    fields = []
    authorsQuery = (db.auth_membership.group_id == auth.id_group('author')) & (db.auth_membership.user_id == db.auth_user.id)
    advisorsQuery = (db.auth_membership.group_id == auth.id_group('faculty')) & (db.auth_membership.user_id == db.auth_user.id)
    fields.append(db.Field('subjectarea',db.subject,requires = IS_EMPTY_OR(IS_IN_DB(db,'subject.id','%(name)s')),label='Subject'))
    fields.append(db.Field('type',requires = IS_EMPTY_OR(IS_IN_SET(typenames))))
    fields.append(db.Field('author','string',label='Author',requires = IS_EMPTY_OR(IS_IN_DB(db(authorsQuery),'auth_user.id','%(first_name)s %(last_name)s'))))
    if typetables.index('mastersthesis') in types or typetables.index('phdthesis') in types:
        fields.append(db.Field('advisor','string',label='Advisor',requires = IS_EMPTY_OR(IS_IN_DB(db(advisorsQuery),'auth_user.id','%(first_name)s %(last_name)s'))))
    default_start_date = datetime.date(datetime.date.today().year-1,1,1)
    fields.append(db.Field('start_date','date', requires = IS_DATE(), default=default_start_date))
    fields.append(db.Field('end_date','date', requires = IS_DATE(), default=datetime.date.today()))
    form = form_factory(*fields)
    form.accepts(request.vars,session,keepvalues = True)
    if form.errors:
        response.flash='Errors in form'

    if not form.vars.start_date:
        form.vars.start_date = default_start_date
    if not form.vars.end_date:
        form.vars.end_date = datetime.date.today()
    #if not (form.vars.type or (form.vars.start_date!=default_start_date) or form.vars.end_date or
    #        form.vars.subjectarea or form.vars.author or form.vars.advisor):
    #    (pubs,authors,advisors) = get_default_results()
    #    return dict(form=form, pubs=pubs, authors=authors, advisors=advisors)

    pubs = {}
    authors = {}
    advisors = {}
    authorids = {}
    advisorids = {}
    for t in types:
        table = db[typetables[t]]
        query = (table.num != -1)
        if form.vars.start_date:
            query = (table.xdate >= form.vars.start_date) & query
        if form.vars.end_date:
            query = (table.xdate <= form.vars.end_date) & query
        if form.vars.subjectarea:
            query = (table.subjectarea == form.vars.subjectarea) & query
        if form.vars.author:
            thisauthorq = (db.author.personid == form.vars.author) & (table.pubid == db.author.pubid)
            query = thisauthorq & query
        if form.vars.advisor:
            thisadvisorq = (db.advisor.personid == form.vars.advisor) & (table.pubid == db.advisor.pubid)
            query = thisadvisorq & query
        pubs[t] = db(query).select(table.ALL,orderby=~table.xdate)
        thispubs = set([x.pubid for x in pubs[t]])
        get_authors(authors, authorids, table, thispubs)
        if typetables[t] in thesistypes:
            get_advisors(advisors, advisorids, table, thispubs)
    return dict(form=form, pubs=pubs, authors=authors, advisors=advisors)

#@cache(request.env.path_info, time_expire=86400, cache_model=cache.ram)
def index():
    if db(db.auth_user).isempty():
        loadgroups()
        passwd = 'admin'
        passwd = db.auth_user.password.requires[0](passwd)[0]
        #passwd = db.auth_user.password.requires(passwd)[0]
        #passwd = CRYPT()(passwd)[0]
        uid1 = db.auth_user.insert(email=configuration.get('host.techreports_moderator'), last_name=configuration.get('host.techreports_moderator').split('@')[0], password=passwd)
        uid2 = db.auth_user.insert(email=configuration.get('host.thesis_moderator'), last_name=configuration.get('host.thesis_moderator').split('@')[0], password=passwd)
        pub_moderator_grp = auth.id_group('moderator')
        db.auth_membership.insert(user_id=uid1, group_id=pub_moderator_grp) #moderator
        db.auth_membership.insert(user_id=uid2, group_id=pub_moderator_grp) #moderator
        session.flash = 'Added moderators. Now login from menu with password "admin" and then change your password.'
        redirect(URL(r=request, f='index'))
    elif auth.is_logged_in() and auth.has_membership(auth.id_group('moderator')) and db(db.subject).isempty():
        response.flash = 'No subject areas. Define using menu on left.'

    if not request.vars.author and not request.vars.advisor and auth.is_logged_in() and auth.has_membership(auth.id_group('author')):
        session.flash = response.flash
        redirect(URL(r=request, f='index?author=%d'%auth.user.id))
    for f,v in request.get_vars.iteritems(): #give priority to post_vars over get_vars
        if v and f in request.post_vars and request.post_vars[f]:
            request.vars[f] = request.post_vars[f]
    A = request.vars.author #form.vars.author
    if A:
        if isinstance(A, list):
            A = A[-1]
            request.vars.author = A
    if A == '': A = None

    types = range(len(typenames)-2) # default page doesn't have theses listed
    if request.vars.type:
        if isinstance(request.vars.type, list):
            types = [typenames.index(x) for x in request.vars.type if x in typenames]
            request.vars.type = None
        else:
            types = [typenames.index(request.vars.type)]

    #from gluon.sqlhtml import form_factory
    fields = []
    authorsQuery = (db.auth_membership.group_id == auth.id_group('author')) & (db.auth_membership.user_id == db.auth_user.id)
    advisorsQuery = (db.auth_membership.group_id == auth.id_group('faculty')) & (db.auth_membership.user_id == db.auth_user.id)
    fields.append(db.Field('subjectarea',db.subject,requires = IS_EMPTY_OR(IS_IN_DB(db,'subject.id','%(name)s',zero='Any')),label='Subject',default=request.vars.subjectarea))
    fields.append(db.Field('type',requires = IS_EMPTY_OR(IS_IN_SET(typenames,zero='Any')),default=request.vars.type))
    fields.append(db.Field('author','string',label='Author',
        requires = IS_EMPTY_OR(IS_IN_DB(db(authorsQuery),'auth_user.id','%(first_name)s %(last_name)s', zero='Any')),
        default=A))#,widget=SQLFORM.widget.autocomplete(request,db.author.id ))
    if typetables.index('mastersthesis') in types or typetables.index('phdthesis') in types:
        fields.append(db.Field('advisor','string',label='Advisor',requires = IS_EMPTY_OR(IS_IN_DB(db(advisorsQuery),'auth_user.id','%(first_name)s %(last_name)s',zero='Any')),default=request.vars.advisor))
    if request.vars.start_date:
       default_start_date = datetime.datetime.strptime(request.vars.start_date,'%Y-%m-%d').date()
    else:
       default_start_date = datetime.date(datetime.date.today().year-1,1,1)
    fields.append(db.Field('start_date','date', requires = IS_DATE(), default=default_start_date))
    if request.vars.end_date:
       default_end_date = datetime.datetime.strptime(request.vars.end_date,'%Y-%m-%d').date()
    else:
       default_end_date = datetime.date.today()
    fields.append(db.Field('end_date','date', requires = IS_DATE(), default=default_end_date))
    form = SQLFORM.factory(*fields, formstyle='table3cols')
    form.accepts(request.vars)
    if form.errors:
        response.flash='Errors in form'

    if not form.vars.start_date:
        form.vars.start_date = default_start_date
    if not form.vars.end_date:
        form.vars.end_date = datetime.date.today()

    #if not (form.vars.type or (form.vars.start_date!=default_start_date) or form.vars.end_date or
    #        form.vars.subjectarea or form.vars.author or form.vars.advisor):
    #    (pubs,authors,advisors) = get_default_results()
    #    return dict(form=form, pubs=pubs, authors=authors, advisors=advisors)

    pubs = {}
    authors = {}
    advisors = {}
    authorids = {}
    advisorids = {}
    for t in types:
        table = db[typetables[t]]
        query = (table.num != -1)
        if form.vars.start_date:
            query = (table.xdate >= form.vars.start_date) & query
        if form.vars.end_date:
            query = (table.xdate <= form.vars.end_date) & query
        if request.vars.subjectarea:
            query = (table.subjectarea == request.vars.subjectarea) & query
        if A:
            thisauthorq = (db.author.personid == A) & (table.pubid == db.author.pubid)
            query = thisauthorq & query
        if form.vars.advisor:
            thisadvisorq = (db.advisor.personid == form.vars.advisor) & (table.pubid == db.advisor.pubid)
            query = thisadvisorq & query
        pubs[t] = db(query).select(table.ALL,orderby=~table.xdate)
        thispubs = set([x.pubid for x in pubs[t]])
        get_authors(authors, authorids, table, thispubs)
        if typetables[t] in thesistypes:
            get_advisors(advisors, advisorids, table, thispubs)
    papers = []
    for y in [1,2,3]: # journals, conference papers, techreports
        if y in pubs: papers.extend(pubs[y])
        pubs[y]=None
    papers.sort(lambda a,b: (b.xdate.year-a.xdate.year) or int(b.num-a.num))
    pubs[1] = papers
    return dict(form=form, pubs=pubs, authors=authors, advisors=advisors)

def nextnumber(year, types):  #e.g. ABC/TR/2009/84
    'returns the next number in series for numbering publications'
    max = 0
    for t in types:
        e = db[t].num.max()
        maxq = db(db[t].xdate.year() == year).select(e)
        maxqval = maxq[0][e]
        typemax = int(maxqval) if maxqval else 0
        if typemax > max:
            max = typemax
    return max+1

@auth.requires_membership('moderator')
@cache(request.env.path_info, time_expire=86400, cache_model=cache.disk)
def statistics():
    types = range(len(typenames)-2) # default page doesn't have theses listed
    #default_start_date = datetime.date(datetime.date.today().year-1,1,1)
    authors = {}
    for t in types:
        table = db[typetables[t]]
        #query = (table.xdate >= default_start_date) & (table.num != -1)
        query = (table.num != -1)
        count = db.auth_user.id.count()
        for row in db(query & (table.pubid == db.author.pubid) & (db.author.personid == db.auth_membership.user_id) & (db.auth_membership.group_id == auth.id_group('faculty')) & (db.author.personid == db.auth_user.id)&(db.auth_user.id<100)).select(db.auth_user.first_name, db.auth_user.last_name, db.auth_user.id, count, groupby=db.auth_user.email):
            if row.auth_user.id not in authors:
                authors[row.auth_user.id] = (row.auth_user.first_name, row.auth_user.last_name, {})
            authors[row.auth_user.id][2][t] = row[count]
    for t in range(len(typenames)-2,len(typenames)): #thesis types
        table = db[typetables[t]]
        #query = (table.xdate >= default_start_date) & (table.num != -1)
        query = (table.num != -1)
        count = db.auth_user.id.count()
        for row in db(query & (table.pubid == db.advisor.pubid) & (db.advisor.personid == db.auth_user.id)&(db.auth_user.id<100)).select(db.auth_user.first_name, db.auth_user.last_name, db.auth_user.id, count, groupby=db.auth_user.email):
            if row.auth_user.id not in authors:
                authors[row.auth_user.id] = (row.auth_user.first_name, row.auth_user.last_name, {})
            authors[row.auth_user.id][2][t] = row[count]
    return dict(authors=authors)

@auth.requires_membership('moderator')
def moderator_page():
    authors = {}
    advisors = {}
    authorids = {}
    advisorids = {}
    pubs = {}
    form = FORM(INPUT(_type="submit",_value="SUBMIT"))
    form.append(INPUT(_type="checkbox",_name='delete'))
    types = range(len(typenames))
    for t in types:
        table = db[typetables[t]]
        query = (table.num == -1)
        pubs[t] = db(query).select(table.ALL,orderby=~table.xdate)
        for i in pubs[t]:
            form.append(INPUT(_type="checkbox",_name=str(i.pubid)))
        thispubs = [x.pubid for x in pubs[t]]
        get_authors(authors, authorids, table, thispubs)
        if typetables[t] in thesistypes:
            get_advisors(advisors, advisorids, table, thispubs)

    if form.accepts(request.vars, formname='confirm'):
        n = 0
        if form.vars['delete'] == 'on':
            for t in types:
                for i in pubs[t]:
                    if form.vars[str(i.pubid)] == 'on':


                        if i.pubid in authorids:
                            for j in authorids[i.pubid]:
                                db(db.author.id == j).delete()
                        if i.pubid in advisorids:
                            for j in advisorids[i.pubid]:
                                db(db.advisor.id == j).delete()
                        db(db[typetables[t]].id == i.id).delete()
                        db(db.publication.id == i.pubid).delete()
                        n += 1
            response.flash = "%d pending publication(s) deleted" % n
            redirect(URL(r=request, f='moderator_page'))
        else:
            for t in types:
                for i in pubs[t]:
                    if form.vars[str(i.pubid)] == 'on':
                        row=db(db[typetables[t]].id == i.id).select()
                        email=row[0].uploaded_by.split(' ')[0] 
                        name=row[0].title

                        msg = '''Dear User,

                 Publication Committee has approved your %s,%s.
'''%(name,typetables[t])
                        mail.send(email,subject='Approved your Publication',message=msg)
                        types_for_num = []
                        if typetables[t] in thesistypes:
                            types_for_num = thesistypes
                        elif typetables[t] == 'book':
                            types_for_num = ['book']
                        else:
                            types_for_num = list(set(typetables)-set(['book'])-set(thesistypes))
                        db(db[typetables[t]].id == i.id).update(num=nextnumber(i.xdate.year,types_for_num))
                        n += 1
            response.flash = "%d pending publication(s) confirmed" % n
            redirect(URL(r=request, f='moderator_page'))
    elif form.errors:
        response.flash="form is invalid"
    return dict(pubs=pubs, authors=authors, advisors=advisors)

@auth.requires_membership('moderator')
def renumber_subject():
    'created for maintenance purpose. dont run casually!!!'
    fields = []
    from gluon.sqlhtml import form_factory
    fields.append(db.Field('subjectarea',db.subject,requires = IS_IN_DB(db,'subject.id','%(name)s'),label='Centre'))
    fields.append(db.Field('num','integer'))
    form = form_factory(*fields)
    if form.accepts(request.vars,session):
        sid = form.vars.subjectarea
        newnum = form.vars.num
        for i in ['book','article','inproceedings','techreport','mastersthesis','phdthesis']:
            db(db[i].subjectarea == sid).update(subjectarea=newnum)
        response.flash = 'Done.'
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_membership('moderator')
def change_centre():
    'created for maintenance purpose. dont run casually!!!'
    rows = {}
    for i in ['book','article','inproceedings','techreport','mastersthesis','phdthesis']:
        rows[i] = db((db.author.personid == 40) & (db[i].pubid == db.author.pubid) & 
           (db[i].subjectarea == 3)).select(db[i].id)
        for j in rows[i]:
           db(db[i].id == j.id).update(subjectarea=4) 
    return rows

@auth.requires_membership('moderator')
def rm_duplicates():
    'created for maintenance purpose. dont run casually!!!'
    table = db.auth_membership
    fields = ['user_id', 'group_id']
    #table = db.auth_user
    #fields = ['email', 'first_name','last_name','password','homepage','mailserver','organization']
    table_fields = [table[f] for f in fields]
    rows = db(table.id > 0).select(*table_fields,distinct=True)
    keyed = hasattr(table,'_primarykey')
    deleted = 0
    kept = 0
    for row in rows:
        query = (table.id > 0)
        for f in fields: query = query & (table[f] == row[f])
        r = db(query).select()
        if len(r) <= 1: continue
        firstone = True
        kept_id = None
        for record in r:
            #--- keep first record
            if firstone:
                firstone = False
                kept_id = record.id
		kept += 1
                continue

            #--- update reference fields of other referencing records to point to kept record
            #--- this part is copied from gluon/sqlhtml.py in SQLFORM::__init__()
            for (rtable, rfield) in table._referenced_by:
                #--- form query to find referencing records
                if keyed:
                    rfld = table._db[rtable][rfield]
                    #query = urllib.quote(str(rfld == record[rfld.type[10:].split('.')[1]]))
                    ref_query = (rfld == record[rfld.type[10:].split('.')[1]])
                else:
                    #query = urllib.quote(str(table._db[rtable][rfield] == record.id))
                    ref_query = (table._db[rtable][rfield] == record.id)
                #--- actually update referencing records
                update_dict = { rfield : kept_id }
                db(ref_query).update(**update_dict)

            #--- delete the other referencing records
            db(table.id == record.id).delete()
            deleted += 1
    response.flash = 'Deleted %d records. Kept %d records.' % (deleted,kept)
    return dict()

@auth.requires_membership('moderator')
def query():
    table = db.publication
    rows = db(table.id == 1).select()
    record = rows[0]
    keyed = hasattr(table,'_primarykey')
    ref_rows = []
    for (rtable, rfield) in table._referenced_by:
        if keyed:
            rfld = table._db[rtable][rfield]
            #query = urllib.quote(str(rfld == record[rfld.type[10:].split('.')[1]]))
            ref_query = (rfld == record[rfld.type[10:].split('.')[1]])
        else:
            #query = urllib.quote(str(table._db[rtable][rfield] == record.id))
            ref_query = (table._db[rtable][rfield] == record.id)
        refs = db(ref_query).select()
        ref_rows.append(refs)
    return dict(rows=rows, ref_rows=ref_rows)

@auth.requires_membership('moderator')
def query2():
    author_pubids = set([i.pubid for i in db(db.author.pubid > 0).select(db.author.pubid)])
    pubids = set([i.id for i in db(db.publication.id > 0).select(db.publication.id)])
    return dict(extra_pubids=author_pubids-pubids, no_authors=pubids-author_pubids)

@auth.requires_membership('moderator')
def match_duplicate_persons():
    fields = []
    from gluon.sqlhtml import form_factory
    fields.append(db.Field('person_1','integer',requires = IS_IN_DB(db,'auth_user.id','%(first_name)s %(last_name)s (%(email)s)'),
                    required=True,comment='Keep this person'))
    fields.append(db.Field('person_2','integer',requires = IS_IN_DB(db,'auth_user.id','%(first_name)s %(last_name)s (%(email)s)'),
                    required=True,comment='Copy & remove this person'))
    form = form_factory(*fields)
    if form.accepts(request.vars,session):
        uid1 = form.vars.person_1
        uid2 = form.vars.person_2
        for i in db(db.auth_membership.user_id == uid2).select():
            if not db((db.auth_membership.user_id == uid1) & (db.auth_membership.group_id == i.group_id)).select():
                db.auth_membership.insert(user_id=uid1, group_id=i.group_id)
        db(db.author.personid == uid2).update(personid=uid1)
        db(db.advisor.personid == uid2).update(personid=uid1)
        db(db.auth_membership.user_id == uid2).delete()
        db(db.auth_event.user_id == uid2).update(user_id=uid1)
        db(db.comments.personid == uid2).update(personid=uid1)
        db(db.author.personid == uid2).update(personid=uid1)
        db(db.advisor.personid == uid2).update(personid=uid1)
        db(db.auth_user.id == uid2).delete()
        session.flash = 'Done. Deleted.'
        redirect(URL('match_duplicate_persons'))
    elif form.errors:
        response.flash='Errors in form'
    return dict(form=form)

@auth.requires_membership('moderator')
def subjects():
    grid=SQLFORM.grid(db.subject, searchable=False, csv=False, details=False)
    return locals()

@auth.requires_membership('moderator')
def remove_dangling_pubs():
    to_remove = []
    for i in db(db.publication.id > 0).select(db.publication.id):
        if db(db.book.pubid == i.id).select() or \
           db(db.article.pubid == i.id).select() or \
           db(db.inproceedings.pubid == i.id).select() or \
           db(db.techreport.pubid == i.id).select() or \
           db(db.mastersthesis.pubid == i.id).select() or \
           db(db.phdthesis.pubid == i.id).select():
              continue
        to_remove.append(i.id)
        db(db.publication.id == i.id).delete()
    return dict(removed = to_remove)

@auth.requires_membership('moderator')
def show_dangling_centres():
    dangling_centres = []
    for i in db(db.subject.id > 0).select(db.subject.id,db.subject.name):
        if db(db.book.subjectarea == i.id).select() or \
           db(db.article.subjectarea == i.id).select() or \
           db(db.inproceedings.subjectarea == i.id).select() or \
           db(db.techreport.subjectarea == i.id).select() or \
           db(db.mastersthesis.subjectarea == i.id).select() or \
           db(db.phdthesis.subjectarea == i.id).select():
              continue
        dangling_centres.append((i.id,i.name))
    return dict(dangling_centres  = dangling_centres)

def loadgroups():
    if not db(db.auth_group.role == 'moderator').select():
        if not db(db.auth_group.role == 'moderator').select():
            moderator = auth.add_group(role='moderator', description='Can authorize pending publications')
        if not db(db.auth_group.role == 'faculty').select():
            faculty = auth.add_group(role='faculty', description='Can be an advisor, add pending publications')
        if not db(db.auth_group.role == 'admin').select():
            admin = auth.add_group(role='admin', description='Can add pending publications')
        if not db(db.auth_group.role == 'author').select():
            author = auth.add_group(role='author', description='Can be an author')
        auth.add_permission(moderator,'create')
        auth.add_permission(moderator,'update')
        auth.add_permission(moderator,'delete')
        auth.add_permission(faculty,'create')
        auth.add_permission(admin,'create')

def drop_tables():
    #are you sure you want to do this?
    if not request.is_local: raise HTTP(400)
    for t in ['publication','book','article','inproceedings','techreport','mastersthesis','phdthesis','author','advisor',
        'comments','pubrelations','auth_user','auth_group', 'auth_membership', 'auth_permission', 'auth_event']:
        db[t].drop()
    #db.subject.drop()

def truncate_all_tables():
    if not request.is_local: raise HTTP(400)
    for t in ['auth_user', 'auth_membership', 'auth_event', 'auth_cas', 'publication', 'pubrelations', 'comments',
        'author', 'advisor', 'book', 'article', 'inproceedings', 'techreport', 'mastersthesis', 'phdthesis']:
        db[t].truncate()
    return dict(mesg='Done.')
