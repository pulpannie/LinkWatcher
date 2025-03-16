local Boundary = "----1234567890"
local ContentDisposition = 'Content-Disposition: form-data; name="username"'
local ContentBody = "annie"
local BodyBoundary = "--" .. Boundary
local LastBoundary = "--" .. Boundary .. "--"
local CRLF = "\r\n"
local ContentDisposition2 = 'Content-Disposition: form-data; name="password"'
local ContentBody2 = "password"
local ContentType = 'Content-Type: text/plain'

wrk.method = "POST"
wrk.headers["Content-Type"] = "multipart/form-data; boundary=" .. Boundary
wrk.body = BodyBoundary .. CRLF .. ContentDisposition .. CRLF .. ContentType .. CRLF .. CRLF .. ContentBody .. CRLF ..  BodyBoundary .. CRLF .. ContentDisposition2 .. CRLF .. ContentType .. CRLF .. CRLF .. ContentBody2 .. CRLF .. LastBoundary 
