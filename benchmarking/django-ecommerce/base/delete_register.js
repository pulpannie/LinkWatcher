import http from 'k6/http';
import { sleep, check } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';
export const options = {
  // A number specifying the number of VUs to run concurrently.
  vus: 1,
  // A string specifying the total duration of the test run.
  duration: '2s',
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
  fd.append('username', 'annie0808');
  fd.append('password1', 'password');
  fd.append('password2', 'password');
 
  let res = await http.asyncRequest(
  'POST', 'http://localhost:8000/delete-user/', fd1.body(), {headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd1.boundary},
}); 
  
  res = await http.asyncRequest('POST', 'http://localhost:8000/signup/', fd.body(), {headers: {'Content-Type': 'multipart/form-data; boundary=' + fd.boundary},
});
  //console.log(res);
  check(res, {
    'is status 200': (r) => r.status === 200,
  });
  sleep(1);
}
