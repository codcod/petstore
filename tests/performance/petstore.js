import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  scenarios: {
    smoke: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 10 },
        { duration: "30s", target: 10 },
        { duration: "10s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<200"],
  },
};

export default function () {
  const health = http.get(`${BASE_URL}/api/health`);
  check(health, { "health 200": (r) => r.status === 200 });

  const index = http.get(`${BASE_URL}/`);
  check(index, { "index 200": (r) => r.status === 200 });

  const name = `k6-pet-${__VU}-${__ITER}`;
  const created = http.post(`${BASE_URL}/pets/new`, {
    name,
    category: "Dogs",
    tags: "friendly,loud",
    photo_urls: "",
    status: "available",
  });
  check(created, { "create 200": (r) => r.status === 200 });

  const idPattern = new RegExp(
    `<span class="name">${name}</span>.*?hx-delete="/pets/(\\d+)"`,
    "s",
  );
  const match = created.body.match(idPattern);
  const petId = match && match[1];

  if (petId) {
    const get = http.get(`${BASE_URL}/pets/${petId}/detail`);
    check(get, { "get 200": (r) => r.status === 200 });

    const edit = http.get(`${BASE_URL}/pets/${petId}/detail/edit`);
    check(edit, { "edit form 200": (r) => r.status === 200 });

    const updated = http.put(`${BASE_URL}/pets/${petId}/detail/edit`, {
      name: `k6-pet-${__VU}-${__ITER}`,
      category: "Cats",
      tags: "calm",
      photo_urls: "",
      status: "sold",
    });
    check(updated, { "update 200": (r) => r.status === 200 });

    const deleted = http.del(`${BASE_URL}/pets/${petId}`);
    check(deleted, { "delete 200": (r) => r.status === 200 });
  }

  sleep(1);
}
