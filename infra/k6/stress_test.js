/**
 * k6 Stress Test - Find breaking point
 * Run: k6 run stress_test.js --env BASE_URL=https://api.yourdomain.com
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m',  target: 100 },
    { duration: '5m',  target: 100 },
    { duration: '2m',  target: 200 },
    { duration: '5m',  target: 200 },
    { duration: '2m',  target: 300 },
    { duration: '5m',  target: 300 },
    { duration: '5m',  target: 0 },    // recovery
  ],
  thresholds: {
    http_req_duration: ['p(99)<5000'],
    http_req_failed:   ['rate<0.10'],
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  const ok = check(res, { 'status 200': (r) => r.status === 200 });
  errorRate.add(!ok);
  sleep(1);
}
