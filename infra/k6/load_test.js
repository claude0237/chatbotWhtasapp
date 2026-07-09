/**
 * k6 Load Test - ChatBot SaaS API
 * Run: k6 run load_test.js --env BASE_URL=https://api.yourdomain.com
 */
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_EMAIL = __ENV.TEST_EMAIL || 'load@test.com';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'loadtest123';

// Custom metrics
const errorRate = new Rate('errors');
const apiResponseTime = new Trend('api_response_time');

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // ramp up
    { duration: '1m',  target: 50 },   // steady load
    { duration: '30s', target: 100 },  // spike
    { duration: '1m',  target: 50 },   // back to normal
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% of requests < 2s
    http_req_failed:   ['rate<0.05'],   // error rate < 5%
    errors:            ['rate<0.05'],
  },
};

let authToken = null;

export function setup() {
  // Login once and share token
  const res = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
  }), { headers: { 'Content-Type': 'application/json' } });

  if (res.status !== 200) {
    console.error(`Login failed: ${res.status} ${res.body}`);
    return { token: null };
  }
  return { token: res.json('access_token') };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`,
  };

  group('Health Check', () => {
    const res = http.get(`${BASE_URL}/health`);
    check(res, { 'health OK': (r) => r.status === 200 });
    apiResponseTime.add(res.timings.duration);
  });

  sleep(0.5);

  group('Notifications', () => {
    const res = http.get(`${BASE_URL}/notifications`, { headers });
    const ok = check(res, {
      'notifications 200': (r) => r.status === 200,
      'is array': (r) => Array.isArray(r.json()),
    });
    errorRate.add(!ok);
    apiResponseTime.add(res.timings.duration);
  });

  sleep(0.3);

  group('Unread count', () => {
    const res = http.get(`${BASE_URL}/notifications/unread-count`, { headers });
    check(res, { 'unread count 200': (r) => r.status === 200 });
  });

  sleep(1);
}

export function teardown(data) {
  console.log(`Load test complete. Token used: ${data.token ? 'yes' : 'no'}`);
}
