from django.conf import settings
from django.contrib.messages.storage import default_storage
from django.utils.deprecation import MiddlewareMixin
from collections import defaultdict
import json
from django.utils import link_tee
import time

mapping = defaultdict()
mapping["/signup/ POST"] = "Entry function: SignUpView.post"
mapping["/delete-user/ POST"] = "/delete-user/ POST"
mapping["/login/ POST"] = "Entry function: LoginView.post"
mapping["/order/ POST"] = "Entry function: AddOrderView.post"
mapping["/review/ POST"] = "Entry function: AddReview.post"
mapping["/ GET"] = "Entry function: base"
class MessageMiddleware(MiddlewareMixin):
    """
    Middleware that handles temporary messages.
    """
    def current_milli_time(self):
        return round(time.time() * 1000)
    def process_request(self, request):
        request._messages = default_storage(request)

    def process_response(self, request, response):
        """
        Update the storage backend (i.e., save the messages).

        Raise ValueError if not all messages could be stored and DEBUG is True.
        """
        # A higher middleware layer may return a request which does not contain
        # messages storage, so make no assumption that it will be there.
        if hasattr(request, '_messages'):
            unstored_messages = request._messages.update(response)
            if unstored_messages and settings.DEBUG:
                raise ValueError('Not all temporary messages could be stored.')\
        #link-TEE message
        #start = self.current_milli_time()
        tmp = {}
        for key, item in request.POST.items():
            tmp["self.request.POST." + key] = item
        #response.content = json.dumps(tmp)
        #print("MESSAGES", response.content)
        #link-TEE response
        
        path_method = request.path + " " +request.method
        # print("=======")
        # print("RESPONSE:")
        # print("=======")
        f = open('/home/annie/django-ecommerce/django-ecommerce/output2.json')
        data = json.load(f)
        if tmp:
            if response.content:
                #print("response.content:", response.content)
                content = json.loads(response.content)
            else:
                content = {}
            content['data'] = tmp
            content['hashes'] = defaultdict(list)
            content['tags'] = defaultdict()
            hashes = content['hashes']
            tags = content['tags']
            for entry_function, sinks in data['direct_dataflow'].items():
                if path_method in mapping and entry_function == mapping[path_method]:
                    for sink in sinks:                            
                        #check if sink of json file matches sink being processed
                        if "redirect" in sink['sink']['label']:
                            for field_name, field_sources in sink['fields'][0].items():
                                field = field_name.split(".")[1:]
                                f = field[0]
                                for i in field[1:]:
                                    f += "." + i
                                field = f
                                for field_source in field_sources:
                                    for hash_key in link_tee.hashes:
                                        if field_source['field'] == "self.request.POST":
                                            if field_source['field'] in hash_key:
                                                for item in link_tee.hashes[hash_key]:
                                                    hashes[hash_key].append(item)
                                        else:
                                            source = field_source['path'] + "." + str(field_source['line_number']) 
                                            f_split = field_source['field'].split(".")
                                            if len(f_split) == 1:
                                                source += "." + f_split[0]
                                            else:
                                                for i in field_source['field'].split(".")[1:]:
                                                    source += "." + i
                                            if source in hash_key:
                                                for item in link_tee.hashes[hash_key]:
                                                    if item not in hashes[field]:
                                                        hashes[field].append(item)
                                    for tag_key in link_tee.tags:
                                        if source in tag_key: 
                                            tags[field] = link_tee.tags[tag_key]
            for key, item in content['data'].items():
                if 'self.request.POST' in key:
                    tmp = link_tee.hashes[key]
                    if tmp:
                        for i in tmp:
                            hashes[key].append(i)
                    if key in link_tee.tags:
                        tags[key] = link_tee.tags[key]
            response.content = json.dumps(content)
            #print("response: ", response.content)
            # end = self.current_milli_time()
            # duration = end - start
            # print("[response duration]", duration)
        return response

