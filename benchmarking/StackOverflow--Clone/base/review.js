import http from 'k6/http';
import { sleep, check } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';
import file from 'k6/x/file';

export const options = {
  // A number specifying the number of VUs to run concurrently.
  vus: 1,
  // A string specifying the total duration of the test run.
  duration: '60s',
};

// The function that defines VU logic.
//
// See https://grafana.com/docs/k6/latest/examples/get-started-with-k6/ to learn more
// about authoring k6 scripts.
//

export default function() {
  const fd = new FormData();
  fd.append('username', 'annie0808');
  fd.append('slug', '1');
  fd.append('title', 'this sucks');
  fd.append('body', 'why did you make this product?');
  
  const res = http.post('http://localhost:8000/review/', fd.body(), {headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd.boundary}, redirects: 0, 
});
  check(res, {
    'is status 302': (r) => r.status === 302,
  });
  sleep(1);
}
