import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  json: true
});

const execute = async (method, resource, data) => {
  // inject the accessToken for each request
  //   let accessToken = await Vue.prototype.$auth.getAccessToken();
  let accessToken = process.env.ACCESS_TOKEN;
  return client({
    method,
    url: resource,
    data: data,
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  })
    .then(req => {
      return req.data;
    })
    .catch(error => {
      /* eslint-disable-next-line */
      // TODO: needs to decide where errors are going to logged but for now just printing them to console
      console.log(error);
    });
};

export const get = async options => execute('get', options.resource, null);