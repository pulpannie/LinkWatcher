Boundary = "----1234567890"
CRLF = "\r\n"
BodyBoundary = "--" .. Boundary
LastBoundary = "--" .. Boundary .. "--"
Username_meta = 'Content-Disposition: form-data; name="username"'
Username_content = "annie1"
Password1_meta = 'Content-Disposition: form-data; name="password1"'
Password1_content = "password1"
Password2_meta = 'Content-Disposition: form-data; name="password2"'
Password2_content = "password1"
t_email_meta = 'Content-Disposition: form-data; name="t_email"'
t_email_data = 'PII'
Email_meta = 'Content-Disposition: form-data; name="email"'
Email_data = 'example@gmail.com'
ContentType = 'Content-Type: text/plain'

method = "POST"
headers = {}
headers["Content-Type"] = "multipart/form-data; boundary=" .. Boundary
body = BodyBoundary .. CRLF .. Username_meta .. CRLF .. ContentType .. CRLF .. CRLF .. Username_content .. CRLF ..  BodyBoundary .. CRLF .. Email_meta .. CRLF .. ContentType .. CRLF .. CRLF .. Email_data .. CRLF .. BodyBoundary .. CRLF .. Password1_meta .. CRLF .. ContentType .. CRLF .. CRLF .. Password1_content .. CRLF .. BodyBoundary .. CRLF .. Password2_meta .. CRLF .. ContentType .. CRLF .. CRLF .. Password1_content .. CRLF .. BodyBoundary .. CRLF .. t_email_meta .. CRLF .. ContentType .. CRLF .. CRLF .. t_email_data .. CRLF .. LastBoundary 

body1 = BodyBoundary .. CRLF .. Email_meta .. CRLF .. ContentType .. CRLF .. CRLF .. Email_data .. CRLF .. BodyBoundary .. CRLF .. t_email_meta .. CRLF .. ContentType .. CRLF .. CRLF .. t_email_data .. CRLF .. LastBoundary

local r = {}
r[1] = wrk.format(method, "/delete-user/", headers, body1)
r[2] = wrk.format(method, "/signup/", headers, body)

req = table.concat(r)

request = function()
	return req
end
