from django.test import Client
import json

c = Client()
print("=========SENDING DELETE REQUEST===========")
response = c.post('/delete-user/', {"email": "hyokyung@gmail.com", "t_email":"PII"})
print(response.status_code)
print(response.content)


print("=========SENDING REGISTER REQUEST==========")
response = c.post('/signup/', {"username": "annie", "email":"hyokyung@gmail.com", "password1":"password", "password2":"password", "t_email":"PII"})
print("TEST RESPONSE:", response.status_code)
print("TEST RESPONSE:", response.content)
content = json.loads(response.content)
print("=========SENDING LOGIN REQUEST=============")
response = c.post('/login/', {"username": "annie", "password":"password", "t_username":"Linked", "t_password":"Linked", "h_username":content['hashes']['self.request.POST.username'], "h_password":content['hashes']['self.request.POST.password1']})
print("TEST RESPONSE:", response.status_code)
print("TEST RESPONSE:", response.content)

print("=========SENDING ORDER REQUEST=============")
response = c.post('/order/', {"username": "annie", "slug":"1", "t_username": "Linked", "t_password":"Linked","h_username":content['hashes']['self.request.POST.username']})
print("ORDER RESPONSE:", response.status_code, response.content)

print("=========SENDING REVIEW REQUEST===========")
response = c.post('/review/', {"username":"annie", "slug":"1", "title":"This sucks", "body":"Why did you make this product.","t_username":"Linked","h_username":content['hashes']['self.request.POST.username']})
print("REVIEW RESPONSE:", response.status_code, response.content)
