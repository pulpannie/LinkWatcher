import http from 'k6/http';
import { sleep, check } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';
import file from 'k6/x/file';
export const options = {
  // A number specifying the number of VUs to run concurrently.
  vus: 1,
  // A string specifying the total duration of the test run.
  duration: '1s',
};

// The function that defines VU logic.
//
// See https://grafana.com/docs/k6/latest/examples/get-started-with-k6/ to learn more
// about authoring k6 scripts.
//
export default async function() {
  const fd = new FormData();
  const fd1 = new FormData();
  fd.append('email', 'example@gmail.com');
  fd1.append('email', 'example@gmail.com');
  fd1.append('t_email', 'PII');
  fd.append('username', 'annie0808');
  fd.append('password1', 'pwd12345');
  fd.append('password2', 'pwd12345');
  fd.append('t_email', 'PII');

 
  let res = await http.asyncRequest(
  'POST', 'http://localhost:8000/delete-user/', fd1.body(), {headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd1.boundary},
}); 
  
  res = await http.asyncRequest('POST', 'http://localhost:8000/signup_view/', fd.body(), {headers: {'Content-Type': 'multipart/form-data; boundary=' + fd.boundary}, redirects: 0,
});
  let result = res.json();
  console.log(result);
  check(res, {
    'is status 302': (r) => r.status === 302,
  });
  file.writeString("data.json", JSON.stringify(result['hashes']), (error)=> {if(error){console.error(error)}});
  sleep(1);
}
