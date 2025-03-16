local Boundary = "----1234567890"
local ContentDisposition = 'Content-Disposition: form-data; name="username"'
local ContentBody = "annie1"
local BodyBoundary = "--" .. Boundary
local LastBoundary = "--" .. Boundary .. "--"
local CRLF = "\r\n"
local ContentDisposition2 = 'Content-Disposition: form-data; name="slug"'
local ContentBody2 = "1"
local ContentType = 'Content-Type: text/plain'

method = "POST"
headers = {}
headers["Content-Type"] = "multipart/form-data; boundary=" .. Boundary
bodies = BodyBoundary .. CRLF .. ContentDisposition .. CRLF .. ContentType .. CRLF .. CRLF .. ContentBody .. CRLF ..  BodyBoundary .. CRLF .. ContentDisposition2 .. CRLF .. ContentType .. CRLF .. CRLF .. ContentBody2 .. CRLF .. LastBoundary 

request = function()
	return wrk.format(method, "/order/", headers, bodies)
end

--response = function(status, header, body)
--	print("status"..status.."\n"..header.."\n"..body.."\n------------------")
--end
