import random
from locust import HttpUser, between, task


class CatalogUser(HttpUser):
    """Simulates users browsing a book catalog via GET /books/."""

    wait_time = between(1, 3)

    @task(5)
    def browse_all(self):
        with self.client.get(
            "/books/",
            name="GET /books/ [default]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                body = resp.json()
                if "items" in body and "total" in body:
                    resp.success()
                else:
                    resp.failure("Unexpected response shape")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(3)
    def browse_paginated(self):
        limit = random.choice([5, 10, 20])
        page = random.randint(0, 8)
        with self.client.get(
            f"/books/?limit={limit}&offset={page * limit}",
            name="GET /books/ [paginated]",
            catch_response=True,
        ) as resp:
            resp.success() if resp.status_code == 200 else resp.failure(f"HTTP {resp.status_code}")

    @task(2)
    def browse_sorted_year(self):
        with self.client.get(
            "/books/?sort_by=year",
            name="GET /books/ [sort_by=year]",
            catch_response=True,
        ) as resp:
            resp.success() if resp.status_code == 200 else resp.failure(f"HTTP {resp.status_code}")

    @task(2)
    def browse_by_status(self):
        status = random.choice(["free", "on_loan"])
        with self.client.get(
            f"/books/?status={status}",
            name="GET /books/ [status filter]",
            catch_response=True,
        ) as resp:
            resp.success() if resp.status_code == 200 else resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def browse_combined(self):
        status = random.choice(["free", "on_loan"])
        sort = random.choice(["title", "year"])
        limit = random.choice([5, 10])
        with self.client.get(
            f"/books/?status={status}&sort_by={sort}&limit={limit}&offset=0",
            name="GET /books/ [combined]",
            catch_response=True,
        ) as resp:
            resp.success() if resp.status_code == 200 else resp.failure(f"HTTP {resp.status_code}")
