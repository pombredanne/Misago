from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from jinja2 import TemplateNotFound
import math
from misago.forms import Form
from misago.forms.layouts import *
from misago.messages import Message, BasicMessage
from misago.search import SearchException

"""
Class widgets
"""
class BaseWidget(object):
    """
    Admin Widget abstract class, providing widgets with common or shared functionality
    """
    admin = None
    id = None
    fallback = None
    name = None
    help = None
    notfound_message = None
    
    def __new__(cls, request, **kwargs):
        obj = super(BaseWidget, cls).__new__(cls)
        if not obj.name:
            obj.name = obj.get_name()
        if not obj.help:
            obj.help = obj.get_help()
        return obj(request, **kwargs)
    
    def get_token(self, token):
        return '%s_%s_%s' % (self.id, token, str('%s.%s' % (self.admin.model.__module__, self.admin.model.__name__)))
        
    def get_url(self):
        return reverse(self.admin.get_action_attr(self.id, 'route'))
    
    def get_name(self):
        return self.admin.get_action_attr(self.id, 'name')
    
    def get_help(self):
        return self.admin.get_action_attr(self.id, 'help')
    
    def get_id(self):
        return 'admin_%s' % self.id
         
    def get_templates(self, template):
        return ('%s/%s/%s.html' % (str(self.admin.model.__module__).split('.')[1], str(self.admin.route).lower(), template),
                '%s/%s.html' % (str(self.admin.model.__module__).split('.')[1], template),
                'admin/%s.html' % template)
            
    def get_fallback_url(self, request):
        return reverse(self.fallback)
        
    def get_target(self, request, model):
        pass
    
    def get_target_name(self, model):
        try:
            return model.__dict__[self.target_name]
        except AttributeError:
            return None
        
    def get_and_validate_target(self, request, target):
        try:
            model = self.admin.model.objects.select_related().get(pk=target)
            self.get_target(request, model)
            return model
        except self.admin.model.DoesNotExist:
            request.messages.set_flash(BasicMessage(self.notfound_message), 'error', self.admin.id)
        except ValueError as e:
            request.messages.set_flash(BasicMessage(e.args[0]), 'error', self.admin.id)
        return None


class ListWidget(BaseWidget):
    """
    Items list widget
    """
    actions =[]
    columns = []
    sortables = {}
    default_sorting = None
    search_form = None
    is_filtering = False
    pagination = None
    template = 'list'
    hide_actions = False
    table_form_button = _('Go')
    empty_message = _('There are no items to display')
    empty_search_message = _('Search has returned no items')
    nothing_checked_message = _('You have to select at least one item.')
    prompt_select = False
    
    def get_item_actions(self, request, item):
        """
        Provides request and item, should return list of tuples with item actions in following format:
        (id, name, help, icon, link)
        """
        return []
    
    def action(self, icon=None, name=None, url=None, post=False, prompt=None):
        """
        Function call to make hash with item actions
        """
        if prompt:
            self.prompt_select = True
        return {
                'icon': icon,
                'name': name,
                'url': url,
                'post': post,
                'prompt': prompt,
                }
        
    def get_search_form(self, request):
        """
        Build a form object with items search
        """
        return self.search_form
            
    def set_filters(self, model, filters):
        """
        Set filters on model using filters from session
        """
        return None
    
    def get_table_form(self, request, page_items):
        """
        Build a form object with list of all items fields
        """
        return None
    
    def table_action(self, request, page_items, cleaned_data):
        """
        Handle table form submission, return tuple containing message and redirect link/false
        """
        return None
    
    def get_actions_form(self, page_items):
        """
        Build a form object with list of all items actions
        """
        if not self.actions:
            return None # Dont build form
        form_fields = {}
        list_choices = []
        for action in self.actions:
            list_choices.append((action[0], action[1]))
        form_fields['list_action'] = forms.ChoiceField(choices=list_choices)
        list_choices = []
        for item in page_items:
            list_choices.append((item.pk, None))
        form_fields['list_items'] = forms.MultipleChoiceField(choices=list_choices,widget=forms.CheckboxSelectMultiple)
        return type('AdminListForm', (Form,), form_fields)
        
    def get_sorting(self, request):
        """
        Return list sorting method.
        A list with three values:
        - Field we use to sort over
        - Sorting direction
        - order_by() argument
        """
        sorting_method = None
        if request.session.get(self.get_token('sort')) and request.session.get(self.get_token('sort'))[0] in self.sortables:
            sorting_method = request.session.get(self.get_token('sort'))
            
        if request.GET.get('sort') and request.GET.get('sort') in self.sortables:
            new_sorting = request.GET.get('sort')
            sorting_dir = int(request.GET.get('dir')) == 1
            sorting_method = [
                    new_sorting,
                    sorting_dir,
                    new_sorting if sorting_dir else '-%s' % new_sorting
                   ]
            request.session[self.get_token('sort')] = sorting_method
            
        if not sorting_method:
            if self.sortables:
                new_sorting = self.sortables.keys()[0]
                if self.default_sorting in self.sortables:
                    new_sorting = self.default_sorting
                sorting_method = [
                        new_sorting,
                        self.sortables[new_sorting] == True,
                        new_sorting if self.sortables[new_sorting] else '-%s' % new_sorting
                       ]
            else:
                sorting_method = [
                        id,
                        True,
                        '-id'
                       ]
        return sorting_method
    
    def sort_items(self, request, page_items, sorting_method):
        return page_items.order_by(sorting_method[2])
    
    def get_pagination_url(self, page):
        return reverse(self.admin.get_action_attr(self.id, 'route'), kwargs={'page': page})
    
    def get_pagination(self, request, total, page):
        """
        Return list pagination.
        A list with three values:
        - Offset for ORM slicing
        - Length of slice
        - no. of prev page (or -1 for first page)
        - no. of next page (or -1 for last page)
        - Current page
        - Pages total
        """
        if not self.pagination or total < 0:
            # Dont do anything if we are not paging
            return None
        
        # Set basic pagination, use either Session cache or new page value
        pagination = {'start': 0, 'stop': 0, 'prev': -1, 'next': -1}
        if request.session.get(self.get_token('pagination')):
            pagination['start'] = request.session.get(self.get_token('pagination'))
        page = int(page)
        if page > 0:
            pagination['start'] = (page - 1) * self.pagination
            
        # Set page and total stat
        pagination['page'] = int(pagination['start'] / self.pagination) + 1
        pagination['total'] = int(math.ceil(total / float(self.pagination)))
            
        # Fix too large offset
        if pagination['start'] > total:
            pagination['start'] = 0
            
        # Allow prev/next?
        if total > self.pagination:
            if pagination['page'] > 1:
                pagination['prev'] = pagination['page'] - 1
            if pagination['page'] < pagination['total']:
                pagination['next'] = pagination['page'] + 1
                
        # Set stop offset
        pagination['stop'] = pagination['start'] + self.pagination
        return pagination
    
    def __call__(self, request, page=0):
        """
        Use widget as view
        """
        # Get basic list attributes
        if request.session.get(self.get_token('filter')):
            self.is_filtering = True
            items_total = self.set_filters(self.admin.model.objects, request.session.get(self.get_token('filter'))).count()
        else:
            items_total = self.admin.model.objects.count()
        sorting_method = self.get_sorting(request)
        paginating_method = self.get_pagination(request, items_total, page)
        
        # List items
        items = self.admin.model.objects
        
        # Filter items?
        if request.session.get(self.get_token('filter')):
            items = self.set_filters(items, request.session.get(self.get_token('filter')))
        else:
            items = items.all()
                   
        # Sort them
        items = self.sort_items(request, items, sorting_method);
        
        # Set pagination
        if self.pagination:
            items = items[paginating_method['start']:paginating_method['stop']]
        
        # Prefetch related?
        if self.prefetch_related:
            items = self.prefetch_related(items)
            
        # Default message
        message = request.messages.get_message(self.admin.id)
        
        # See if we should make and handle search form
        search_form = None
        SearchForm = self.get_search_form(request)
        if SearchForm:
            if request.method == 'POST':
                # New search
                if request.POST.get('origin') == 'search':
                    search_form = SearchForm(request.POST, request=request)
                    if search_form.is_valid():
                        search_criteria = {}
                        for field, criteria in search_form.cleaned_data.items():
                            if len(criteria) > 0:
                                search_criteria[field] = criteria
                        if not search_criteria:
                            message = BasicMessage(_("No search criteria have been defined."))
                        else:
                            request.session[self.get_token('filter')] = search_criteria
                            return redirect(self.get_url())
                    else:
                        message = BasicMessage(_("Search form contains errors."))
                    message.type = 'error'
                else:
                    search_form = SearchForm(request=request)
                    
                # Kill search
                if request.POST.get('origin') == 'clear' and self.is_filtering and request.csrf.request_secure(request):
                    request.session[self.get_token('filter')] = None
                    request.messages.set_flash(BasicMessage(_("Search criteria have been cleared.")), 'info', self.admin.id)
                    return redirect(self.get_url())
            else:
                if self.is_filtering:
                    search_form = SearchForm(request=request, initial=request.session.get(self.get_token('filter')))
                else:
                    search_form = SearchForm(request=request)
        
        # See if we sould make and handle tab form
        table_form = None
        TableForm = self.get_table_form(request, items)
        if TableForm:
            if request.method == 'POST' and request.POST.get('origin') == 'table':
                table_form = TableForm(request.POST, request=request)
                if table_form.is_valid():
                    message, redirect_url = self.table_action(request, items, table_form.cleaned_data)
                    if redirect_url:
                        request.messages.set_flash(message, message.type, self.admin.id)
                        return redirect(redirect_url)
                else:
                    message = Message(request, table_form.non_field_errors()[0])
                    message.type = 'error'
            else:
                table_form = TableForm(request=request)
        
        # See if we should make and handle list form
        list_form = None
        ListForm = self.get_actions_form(items)
        if ListForm:
            if request.method == 'POST' and request.POST.get('origin') == 'list':
                list_form = ListForm(request.POST, request=request)
                if list_form.is_valid():
                    try:
                        form_action = getattr(self, 'action_' + list_form.cleaned_data['list_action'])
                        message, redirect_url = form_action(request, items, list_form.cleaned_data['list_items'])
                        if redirect_url:
                            request.messages.set_flash(message, message.type, self.admin.id)
                            return redirect(redirect_url)
                    except AttributeError:
                        message = BasicMessage(_("Action requested is incorrect."))
                else:
                    if 'list_items' in list_form.errors:
                        message = BasicMessage(self.nothing_checked_message)
                    elif 'list_action' in list_form.errors:
                        message = BasicMessage(_("Action requested is incorrect."))
                    else:
                        message = Message(request, list_form.non_field_errors()[0])
                message.type = 'error'
            else:
                list_form = ListForm(request=request)
                
        # Render list
        return request.theme.render_to_response(self.get_templates(self.template),
                                                {
                                                 'admin': self.admin,
                                                 'action': self,
                                                 'request': request,
                                                 'url': self.get_url(),
                                                 'message': message,
                                                 'sorting': self.sortables,
                                                 'sorting_method': sorting_method,
                                                 'pagination': paginating_method,
                                                 'list_form': FormLayout(list_form) if list_form else None,
                                                 'search_form': FormLayout(search_form) if search_form else None,
                                                 'table_form': FormFields(table_form).fields if table_form else None,
                                                 'items': items,
                                                 'items_total': items_total,
                                                },
                                                context_instance=RequestContext(request));
                                                
class FormWidget(BaseWidget):
    """
    Form page widget
    """
    template = 'form'
    submit_button = _("Save Changes")
    form = None
    layout = None
    target_name = None
    original_name = None
    submit_fallback = False
    
    def get_url(self, request, model):
        return reverse(self.admin.get_action_attr(self.id, 'route'))
    
    def get_form(self, request, model):
        return self.form
    
    def get_form_instance(self, form, request, model, initial, post=False):
        if post:
            return form(request.POST, request=request, initial=self.get_initial_data(request, model))
        return form(request=request, initial=self.get_initial_data(request, model))
    
    def get_layout(self, request, form, model):
        if self.layout:
            return self.layout
        return form.layout
    
    def get_initial_data(self, request, model):
        return {}
    
    def submit_form(self, request, form, model):
        """
        Handle form submission, ALWAYS return tuple with model and message
        """
        pass
    
    def __call__(self, request, target=None, slug=None):
        # Default message
        message = request.messages.get_message(self.admin.id)

        # Fetch target?
        model = None
        if target:
            model = self.get_and_validate_target(request, target)
            self.original_name = self.get_target_name(model)
            if not model:
                return redirect(self.get_fallback_url(request))
        original_model = model
        
        # Get form type to instantiate
        FormType = self.get_form(request, target)
        
        #Submit form
        if request.method == 'POST':
            form = self.get_form_instance(FormType, request, model, self.get_initial_data(request, model), True)
            if form.is_valid():
                model, message = self.submit_form(request, form, model)
                if message.type != 'error':
                    request.messages.set_flash(message, message.type, self.admin.id)
                    # Redirect back to right page
                    try:
                        if 'save_new' in request.POST and self.get_new_url:
                            return redirect(self.get_new_url(request, model))
                    except AttributeError:
                        pass
                    try:
                        if 'save_edit' in request.POST and self.get_edit_url:
                            return redirect(self.get_edit_url(request, model))
                    except AttributeError:
                        pass
                    try:
                        if self.get_submit_url:
                            return redirect(self.get_submit_url(request, model))
                    except AttributeError:
                        pass
                    return redirect(self.get_fallback_url(request))
            else:
                message = Message(request, form.non_field_errors()[0])
                message.type = 'error'
        else:
            form = self.get_form_instance(FormType, request, model, self.get_initial_data(request, model))
            
        # Render form
        return request.theme.render_to_response(self.get_templates(self.template),
                                                {
                                                 'admin': self.admin,
                                                 'action': self,
                                                 'request': request,
                                                 'url': self.get_url(request, model),
                                                 'fallback': self.get_fallback_url(request),
                                                 'message': message,
                                                 'target': self.get_target_name(original_model),
                                                 'target_model': original_model,
                                                 'form': FormLayout(form, self.get_layout(request, form, target)),
                                                },
                                                context_instance=RequestContext(request));

                                        
class ButtonWidget(BaseWidget):
    """
    Button Action Widget
    This widget handles most basic and common type of admin action - button press:
    - User presses button on list (for example "delete this user!")
    - Widget checks if request is CSRF-valid and POST
    - Widget optionally chcecks if target has been provided and action is allowed at all
    - Widget does action and redirects us back to fallback url
    """
    def __call__(self, request, target=None, slug=None):
        # Fetch target?
        model = None
        if target:
            model = self.get_and_validate_target(request, target)
            if not model:
                return redirect(self.get_fallback_url(request))
        original_model = model
            
        # Crash if this is invalid request
        if not request.csrf.request_secure(request):
            request.messages.set_flash(BasicMessage(_("Action authorization is invalid.")), 'error', self.admin.id)
            return redirect(self.get_fallback_url(request))
        
        # Do something
        message, url = self.action(request, model)
        request.messages.set_flash(message, message.type, self.admin.id)
        if url:
            return redirect(url)
        return redirect(self.get_fallback_url(request))
        
    def action(self, request, target):
        """
        Action to be executed when button is pressed
        Define custom one in your Admin action.
        It should return response and message objects 
        """
        pass