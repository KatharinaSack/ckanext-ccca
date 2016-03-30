import cgi
import paste.fileapp
import mimetypes
import json
import logging
import os
import ckan.model as model
import ckan.logic as logic
import pylons.config as config
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.plugins as p
from ckan.common import request, c, g, response
import ckan.lib.uploader as uploader
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.dictization as dictization
from pylons.i18n.translation import _, ungettext
import ckan.lib.i18n as i18n
from ckan.controllers.package import PackageController

import ckan.lib.navl.dictization_functions as dict_fns

from urlparse import urlparse
from posixpath import basename, dirname

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

log = logging.getLogger(__name__)

class PackageContributeOverride(p.SingletonPlugin, PackageController):
    
    def new_metadata(self, id, data=None, errors=None, error_summary=None, template=None):
        #package_type = self._get_package_type(id)
        save_action = request.params.get('save')
        if not data:
            data = data or clean_dict(dictization_functions.unflatten(
                tuplize_dict(parse_params(request.POST))))
            # we don't want to include save as it is part of the form
 #           if 'save' in data:
#                del data['save']
            #resource_id = data['id']
            #del data['id']
            
        errors = errors or {}
        error_summary = error_summary or {}
    
        package_type = self._get_package_type(id)
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

        if context['save']:
            return self._save_edit(id, context, package_type=package_type)
        
        try:
            c.pkg_dict = get_action('package_show')(context, {'id': id})
            context['for_edit'] = True
            context['form_style'] = 'edit'
            old_data = get_action('package_show')(context, {'id': id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            if data:
                old_data.update(data)
            data = old_data
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound:
            abort(404, _('Dataset not found'))
            
       # vars['pkg_name'] = id
        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
            pkg_dict['package_id'] = id
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access('resource_create', context, pkg_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a resource for this package'))

        package_type = pkg_dict['type'] or 'dataset'
        
        if save_action == 'go-metadata':
            #return self._save_edit(id, context, package_type=package_type)
            data_dict = get_action('package_show')(context, {'id': id})
            get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
            redirect(h.url_for(controller='package',
                                   action='read', id=id))
        else:
            vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type': package_type}
            vars['pkg_name'] = id
            # required for nav menu
            vars['pkg_dict'] = pkg_dict
            vars['stage'] = ['complete', 'complete', 'active']
            vars['form_style'] = 'edit'
            if not template:
                template = 'package/ccca_new_metadata.html'
            return render(template, extra_vars=vars)
    
    def metadata(self, id, data=None, errors=None, error_summary=None):
        return self.new_metadata(id, data, {}, {}, 'package/ccca_metadata.html')
        
    '''        
        try:
            check_access('package_update', context, data_dict)
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('User %r not authorized to edit %s') % (c.user, id))
        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)
        

        try:
            c.pkg_dict = get_action('package_show')(context, {'id': id})
            context['for_edit'] = True
            context['form_style'] = 'edit'
            old_data = get_action('package_show')(context, {'id': id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            if data:
                old_data.update(data)
            data = old_data
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound:
            abort(404, _('Dataset not found'))
            
        package_type = c.pkg_dict['type'] or 'dataset'
         
        if save_action == 'go-metadata':
            return self._save_edit(id, context, package_type=package_type)
            data_dict = get_action('package_show')(context, {'id': id})
            get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
            redirect(h.url_for(controller='package',
                                   action='read', id=id))
        else:
           
#        self._setup_template_variables(context, {'id': id},
 #                                      package_type=package_type)
            data['id'] = id
            vars = {'data': data, 
                    'errors': {},
                    'error_summary': {}, 
                    'action': 'edit',
                    'resource_form_snippet': self._resource_form(package_type),
                    'dataset_type': package_type, 
                    'form_style': 'edit'
                    }      
            # required for nav menu
            c.pkg_dict['id'] = id
            vars['pkg_dict'] = c.pkg_dict
            return render('package/ccca_metadata.html',
                          extra_vars=vars)
            '''
          
    def new_resource(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or clean_dict(dictization_functions.unflatten(
                tuplize_dict(parse_params(request.POST))))
            if type(data['id']) is list:
                del data['id']
                
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}
            
            # we don't want to include save as it is part of the form
            del data['save']
            resource_id = None
            if 'id' in data and data['id']:
                resource_id = data['id']
                del data['id']
            
            if data['upload_type'] == 'sftp':
                data['id'] = request.params.get('id')
                get_action('resource_update')(context, data)
                if save_action == 'go-md_edit':
                    # go to final stage of add dataset
                    redirect(h.url_for('dataset_new_metadata', id=id))
                else: 
                    redirect(h.url_for(controller='package',
                                   action='read', id=id))
                
 
            
            # see if we have any data that we are trying to save
            data_provided = False
            for key, value in data.iteritems():
                if ((value or isinstance(value, cgi.FieldStorage))
                    and key != 'resource_type'):
                    data_provided = True
                    break

            if not data_provided and save_action != "go-dataset-complete":
                if save_action == 'go-dataset':
                    # go to final stage of adddataset
                    redirect(h.url_for(controller='package',
                                       action='edit', id=id))
                # see if we have added any resources
                try:
                    data_dict = get_action('package_show')(context, {'id': id})
                except NotAuthorized:
                    abort(401, _('Unauthorized to update dataset'))
                except NotFound:
                    abort(404,
                      _('The dataset {id} could not be found.').format(id=id))
                if not len(data_dict['resources']):
                    # no data so keep on page
                    msg = _('You must add at least one data resource')
                    # On new templates do not use flash message
                    if g.legacy_templates:
                        h.flash_error(msg)
                        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))
                    else:
                        errors = {}
                        error_summary = {_('Error'): msg}
                        return self.new_resource(id, data, errors, error_summary)
                # we have a resource so let them add metadata
                #redirect(h.url_for(controller='package',
                #                   action='new_metadata', id=id))
                vars['pkg_dict'] = pkg_dict
                template = 'package/metadata.html'
                return render(template, extra_vars=vars)

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new_resource(id, data, errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to create a resource'))
            except NotFound:
                abort(404,
                    _('The dataset {id} could not be found.').format(id=id))

            if save_action == 'go-metadata' or save_action == 'go-dataset-complete':
                ## here's where we're doing the route override
                data_dict = get_action('package_show')(context, {'id': id})

		######## 	USGINModels File Validation 	#######
		## Before activate dataset, validate files of all resources for dataset has usgin structure ##

		isUsginUsed = False#p.toolkit.get_action('is_usgin_structure_used')(context, data_dict)

		#if dataset doesn't use usgin structure then no need for usginModel file validation
		if isUsginUsed is True:

                    resources = data_dict.get('resources', [])
		    messages = {'result': []}
		    validationProcess = True

                    for resource in resources:
			#Bugfix: skip all resources created by ckan, e.g (geoserver wfs, wms ...) on add resource (after dataset is created)
			if save_action == 'go-dataset-complete':
			    protocol = resource.get('protocol', None)
			    if protocol is not None:
				continue
			
                        result = p.toolkit.get_action('usginmodels_validate_file') (context, {'resource_id': resource.get('id', None),
                                                                                'package_id': id,
                                                                                'resource_name': resource.get('name', None)})

		        valid = result.get('valid', None)
			message = result.get('message', None)
		        if valid is False or ( valid is True and message ):
			    #validation process has failed
			    validationProcess = False
			    #Link to download the corrected data from usginmodels
			    link = p.toolkit.url_for('custom_resource_download', id=id, resource_id=result.get('resourceId', None))
			    resourceId = resource.get('id', None)
			    resourceUrl = resource.get('url', None)
			    fileName = None

  			    if resourceUrl:
	         		parseObject = urlparse(resourceUrl)
			    	fileName = basename(parseObject.path)

			    try:
			        get_action('resource_delete')(context, {'id': resource.get('id', None)})
			    except:
			        #deleting non existing resource
			        continue

			    if not message:
                                message = [_("An error occurred while saving the data, please try again.")]

			    messages['result'].append({
                                'resource': result.get('resourceName', ''),
                                'valid': valid,
                                'messages': message,
                                'link': link,
                                'resourceId': resourceId,
				'fileName': fileName,
                            })

		    #if at least one resource file validation is failed, redirect user to new_resource page with error message
		    if not validationProcess:
			html = "The file(s) provided might have changes to be applied or might have failed the validation. For more details, please click <a href='#' class='btn btn-info btn-small openUSGINModelValidationMessage' style='color:white !important'>here</a>"
			# </div><div> HACK template (close alert div) and open div
			html = html + "</div><div>" + render('usginmodels/modalValidationMessages.html', messages)
			h.flash_error(html, True)

		        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))
		### END USGINModels File Validation ###

	    if save_action == 'go-metadata' or save_action == 'go-dataset-complete':
		data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
                
                # this is the original route
                # go to final stage of add dataset
                """vars['pkg_dict'] = pkg_dict
                template = 'package/metadata.html'
                return render(template, extra_vars=vars)
             """
            elif save_action == 'go-md_edit':
                # go to final stage of add dataset
                redirect(h.url_for('dataset_new_metadata', id=id))
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            else:
                # add more resources
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        vars['pkg_name'] = id
        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj
        }
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
            pkg_dict['package_id'] = id
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access('resource_create', context, pkg_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a resource for this package'))

        package_type = pkg_dict['type'] or 'dataset'

        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        vars['resource_form_snippet'] = self._resource_form(package_type)
        template = 'package/new_resource_not_draft.html'
        if pkg_dict['state'] == 'draft':
            vars['stage'] = ['complete', 'active']
            template = 'package/new_resource.html'
        elif pkg_dict['state'] == 'draft-complete':
            vars['stage'] = ['complete', 'active', 'complete']
            template = 'package/new_resource.html'
        return render(template, extra_vars=vars)

    def resource_edit(self, id, resource_id, data=None, errors=None,
                      error_summary=None):
        if request.method == 'POST' and not data:
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']

            context = {'model': model, 'session': model.Session,
                       'api_version': 3, 'for_edit': True,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to edit this resource'))
            
	    ########        USGINModels File Validation     #######
            pkg_dict = get_action('package_show')(context, {'id': id})

            isUsginUsed = False # p.toolkit.get_action('is_usgin_structure_used')(context, pkg_dict)

            #if dataset doesn't use usgin structure then no need for usginModel file validation
            if isUsginUsed is True:

                messages = {'result': []}
                validationProcess = True

                result = p.toolkit.get_action('usginmodels_validate_file') (context, {'resource_id': resource_id,
                                                                        'package_id': id,
                                                                        'resource_name': data.get('name', None)})

                valid = result.get('valid', None)
		message = result.get('message', None)
                if valid is False or ( valid is True and message ):
                    #validation process has failed
                    validationProcess = False
		    link = p.toolkit.url_for('custom_resource_download', id=id, resource_id=resource_id)
		    resourceUrl = data.get('url', None)
                    fileName = None

                    if resourceUrl:
                        parseObject = urlparse(resourceUrl)
                        fileName = basename(parseObject.path)

                    try:
                        get_action('resource_delete')(context, {'id': resource_id})
                    except:
                        #deleting non existing resource
                        pass

		    if not message:
                                message = [_("An error occurred while saving the data, please try again.")]

		    messages['result'].append({
                                'resource': result.get('resourceName', ''),
                                'valid': valid,
                                'messages': message,
                                'link': link,
                                'resourceId': resource_id,
				'fileName': fileName,
                            })

                    html = "The file(s) provided might have changes to be applied or might have failed the validation. For more details, please click <a href='#' class='btn btn-info btn-small openUSGINModelValidationMessage' style='color:white !important'>here</a>"
                    # </div><div> HACK template (close alert div) and open div
                    html = html + "</div><div>" + render('usginmodels/modalValidationMessages.html', messages)
                    h.flash_error(html, True)

                #if the resource file updated not valid then we delete this resource and redirect user to add new resource
                if not validationProcess:
                    redirect(h.url_for(controller='package',
                                       action='new_resource', id=id))

            ### END USGINModels File Validation ###

	    redirect(h.url_for(controller='package', action='resource_read',
                               id=id, resource_id=resource_id))

        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        pkg_dict = get_action('package_show')(context, {'id': id})
        if pkg_dict['state'].startswith('draft'):
            # dataset has not yet been fully created
            resource_dict = get_action('resource_show')(context, {'id': resource_id})
            fields = ['url', 'resource_type', 'format', 'name', 'description', 'id']
            data = {}
            for field in fields:
                data[field] = resource_dict[field]
            return self.new_resource(id, data=data)
        # resource is fully created
        try:
            resource_dict = get_action('resource_show')(context, {'id': resource_id})
        except NotFound:
            abort(404, _('Resource not found'))
        c.pkg_dict = pkg_dict
        c.resource = resource_dict
        # set the form action
        c.form_action = h.url_for(controller='package',
                                  action='resource_edit',
                                  resource_id=resource_id,
                                  id=id)
        if not data:
            data = resource_dict

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'resource_form_snippet': self._resource_form(package_type),
                'error_summary': error_summary, 'action': 'new'}
        return render('package/resource_edit.html', extra_vars=vars)
    
    # resource_download() also checking 'resource access' field that we added
    def resource_download(self, id, resource_id, filename=None):
        """
        Provides a direct download by either redirecting the user to the url
        stored or downloading an uploaded file directly.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        
        if request.method == 'POST':
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.POST))))

        try:
            rsc = get_action('resource_show')(context, {'id': resource_id})
            get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read resource %s') % id)

        if rsc.get('url_type') == 'upload':
            upload = uploader.ResourceUpload(rsc)
            filepath = upload.get_path(rsc['id'])
            fileapp = paste.fileapp.FileApp(filepath)
            try:
                status, headers, app_iter = request.call_application(fileapp)
            except OSError:
                abort(404, _('Resource data not found'))
            response.headers.update(dict(headers))
            content_type, content_enc = mimetypes.guess_type(
                rsc.get('url', ''))
            if content_type:
                response.headers['Content-Type'] = content_type
            response.status = status
            return app_iter
        elif not 'url' in rsc:
            abort(404, _('No download is available'))
        redirect(rsc['url'])
         
    #Custom resource download corrected data, resource_id only for generating the path to the file
    def resource_download_corrected_data(self, id, resource_id):
        """
        Provides a direct download by either redirecting the user to the url stored
         or downloading an uploaded file directly.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

	result = p.toolkit.get_action('get_file_path')(context, {'resourceId': resource_id, 'suffix': '_CorrectedData'})
	filePath = result.get('path', None)

        if os.path.isfile(filePath):
            #upload = uploader.ResourceUpload(rsc)
            #filepath = upload.get_path(rsc['id'])
            fileapp = paste.fileapp.FileApp(filePath)

            try:
               status, headers, app_iter = request.call_application(fileapp)
            except OSError:
               abort(404, _('Resource data not found'))
            response.headers.update(dict(headers))
            #content_type, content_enc = mimetypes.guess_type(rsc.get('url',''))
            #if content_type:
	    #It's CSV, because this method can be only access when a usgin model doesn't validate a CSV File
            response.headers['Content-Type'] = 'text/csv'
	    response.headers['Content-Disposition'] = 'attachment; filename="%s"' % 'correctedData.csv'
            response.status = status
            return app_iter

        abort(404, _('No download is available'))
