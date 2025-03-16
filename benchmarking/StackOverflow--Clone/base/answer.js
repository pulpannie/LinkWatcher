import http from 'k6/http';
import { sleep, check } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';
//import file from 'k6/x/file';

export const options = {
  // A number specifying the number of VUs to run concurrently.
  vus: 1,
  // A string specifying the total duration of the test run.
  iterations: 100,
};

// The function that defines VU logic.
//
// See https://grafana.com/docs/k6/latest/examples/get-started-with-k6/ to learn more
// about authoring k6 scripts.
//

export default function() {
  const fd = new FormData();
  fd.append('username', 'annie0808');
  fd.append('pk', '1');
  fd.append('body', 'this is such an easy question, why did you not use google and ask it here?? I am flagging this post as it is repetitive!!!!!!!!!');
  fd.append('is_wiki_answer', '');
  
  const res = http.post('http://localhost:8000/answer/', fd.body(), {headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd.boundary}, redirects: 0, 
});
  //console.log(res);
  check(res, {
    'is status 302': (r) => r.status === 302,
  });
  sleep(1);
}
