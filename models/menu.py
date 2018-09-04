# coding: utf8

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.title = '%s Publications' % configuration.get('host.institute')
response.subtitle = ' '

if not auth.is_logged_in():
    response.menu_auth = [
       [T('Help'), False, URL(request.application,'default','help')],
       [T('Login'), False, auth.settings.login_url]
    ]

    response.menu = [
        ['Thesis', True, URL(request.application,'default','index?type=Masters Theses&type=PhD Theses'), []],
        ['Publications', True, URL(request.application,'default','index?type=Journal Papers&type=Conference Papers&type=Technical Reports'), []],
        ['Books', True, URL(request.application,'default','index?type=Books'), []],
        ['All', True, URL(request.application,'default','index?type=Journal Papers&type=Conference Papers&type=Technical Reports&type=Books&type=Masters Theses&type=PhD Theses'), []]]
else:
    response.menu_auth = [
        [T('Help'), False, URL(request.application,'default','help')],
        ['Logout '+auth.user.email.split('@')[0], False, URL(request.application,'default','user/logout')],
        [T('Edit Profile'), False, URL(request.application,'default','user/profile')]]
    if not auth.user.mailserver:
        response.menu_auth.append([T('Change Password'), False,
            URL(request.application,'default','user/change_password')])

    if auth.has_membership(auth.id_group('moderator')):
        response.menu_mod = [
            ['Manage Subject Areas', False, URL(request.application,'default','subjects'), []],
            ['Change User Permissions', False, URL(request.application,'default','update_membership'), []],
            ['Match Duplicate Persons', False, URL(request.application,'default','match_duplicate_persons'), []]]

    if auth.has_permission('create'):
        response.menu_edit = [['Add Person', False, URL(request.application,'default','add_person'),[]]]
        response.menu.append(['My Pending Works', True, URL(request.application,'default','pending'), []])
        for i in range(len(typenames)):
            response.menu_edit.append(['Add '+typenames2[i], False,
                URL(request.application,'default','add_publication/%s'%typetables[i]),[]])

    if auth.has_membership(auth.id_group('moderator')):
        response.menu_mod.append( 
            ['Approve Pending Publications', False, URL(request.application,'default','moderator_page'), []])

    response.menu = [
        ['Thesis', True, URL(request.application,'default','index?type=Masters Theses&type=PhD Theses'), []],
        ['Publications', True, URL(request.application,'default','index?type=Journal Papers&type=Conference Papers&type=Technical Reports'), []],
        ['Books', True, URL(request.application,'default','index?type=Books'), []],
        ['All', True, URL(request.application,'default','index?type=Journal Papers&type=Conference Papers&type=Technical Reports&type=Books&type=Masters Theses&type=PhD Theses'), []]]
