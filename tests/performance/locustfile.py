"""
Locust load testing for Nanonets OCR API.

Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""
import os
import io
import random
from locust import HttpUser, task, between, events
from PIL import Image


class OCRUser(HttpUser):
    """Simulated user for load testing OCR API."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Called when a simulated user starts."""
        self.api_key = os.getenv("API_KEY", "test_key_12345")
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }
        # Create test images
        self._test_images = self._create_test_images()

    def _create_test_images(self):
        """Create test images for load testing."""
        images = []

        # Small image (100x100)
        img_small = Image.new('RGB', (100, 100), color='white')
        buf_small = io.BytesIO()
        img_small.save(buf_small, format='PNG')
        buf_small.seek(0)
        images.append(("small", buf_small.getvalue()))

        # Medium image (500x500)
        img_medium = Image.new('RGB', (500, 500), color='white')
        buf_medium = io.BytesIO()
        img_medium.save(buf_medium, format='PNG')
        buf_medium.seek(0)
        images.append(("medium", buf_medium.getvalue()))

        # Large image (1000x1000)
        img_large = Image.new('RGB', (1000, 1000), color='white')
        buf_large = io.BytesIO()
        img_large.save(buf_large, format='PNG')
        buf_large.seek(0)
        images.append(("large", buf_large.getvalue()))

        return images

    @task(10)
    def health_check(self):
        """Check API health endpoint."""
        with self.client.get(
            "/api/v1/health",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def ready_check(self):
        """Check API readiness endpoint."""
        with self.client.get(
            "/api/v1/ready",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Ready check failed: {response.status_code}")

    @task(3)
    def process_small_image(self):
        """Process a small test image."""
        self._process_image("small")

    @task(2)
    def process_medium_image(self):
        """Process a medium test image."""
        self._process_image("medium")

    @task(1)
    def process_large_image(self):
        """Process a large test image."""
        self._process_image("large")

    @task(3)
    def process_image_v2(self):
        """Process image with API v2 (structured output)."""
        self._process_image_v2("small")

    @task(2)
    def classify_document(self):
        """Classify document type."""
        image_data = self._test_images[0][1]  # small image
        files = {
            "file": ("test.png", io.BytesIO(image_data), "image/png")
        }
        with self.client.post(
            "/api/v1/classify",
            files=files,
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code in [200, 422]:
                response.success()
            else:
                response.failure(f"Classify failed: {response.status_code}")

    @task(2)
    def detect_language(self):
        """Detect document language."""
        image_data = self._test_images[0][1]
        files = {
            "file": ("test.png", io.BytesIO(image_data), "image/png")
        }
        with self.client.post(
            "/api/v1/detect-language",
            files=files,
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code in [200, 422]:
                response.success()
            else:
                response.failure(f"Detect language failed: {response.status_code}")

    @task(1)
    def get_structured_output(self):
        """Get fully structured output."""
        image_data = self._test_images[1][1]  # medium image
        files = {
            "file": ("test.png", io.BytesIO(image_data), "image/png")
        }
        with self.client.post(
            "/api/v1/structured",
            files=files,
            headers={"X-API-Key": self.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Structured failed: {response.status_code}")

    def _process_image(self, size: str):
        """Process an image of the given size."""
        # Find image by size
        image_data = None
        for name, data in self._test_images:
            if name == size:
                image_data = data
                break

        if not image_data:
            return

        files = {
            "file": (f"test_{size}.png", io.BytesIO(image_data), "image/png")
        }
        data = {
            "output_format": "json",
            "max_tokens": 1024
        }

        with self.client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers={"X-API-Key": self.api_key},
            catch_response=True,
            name=f"/api/v1/ocr [{size}]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"OCR failed: {response.status_code}")

    def _process_image_v2(self, size: str):
        """Process an image with API v2."""
        image_data = None
        for name, data in self._test_images:
            if name == size:
                image_data = data
                break

        if not image_data:
            return

        files = {
            "file": (f"test_{size}.png", io.BytesIO(image_data), "image/png")
        }
        data = {
            "max_tokens": 1024
        }

        with self.client.post(
            "/api/v1/v2/ocr",
            files=files,
            data=data,
            headers={"X-API-Key": self.api_key},
            catch_response=True,
            name=f"/api/v1/v2/ocr [{size}]"
        ) as response:
            if response.status_code == 200:
                # Verify v2 response structure
                try:
                    json_resp = response.json()
                    if "api_version" in json_resp and json_resp["api_version"] == "2.0":
                        response.success()
                    else:
                        response.failure("Invalid v2 response structure")
                except Exception:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"OCR v2 failed: {response.status_code}")

    @task(2)
    def get_models(self):
        """Get list of available models."""
        with self.client.get(
            "/api/v1/models",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get models failed: {response.status_code}")

    @task(1)
    def get_metrics(self):
        """Get Prometheus metrics."""
        with self.client.get(
            "/api/v1/metrics",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics failed: {response.status_code}")


class AuthenticatedOCRUser(HttpUser):
    """User that tests authentication flows."""

    wait_time = between(2, 5)

    @task(3)
    def test_invalid_auth(self):
        """Test with invalid API key."""
        with self.client.get(
            "/api/v1/health",
            headers={"X-API-Key": "invalid_key"},
            catch_response=True
        ) as response:
            # Should still work for health (or return 401)
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def test_no_auth(self):
        """Test without any authentication."""
        with self.client.get(
            "/api/v1/health",
            catch_response=True
        ) as response:
            # Health should work without auth
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"No auth failed: {response.status_code}")

    @task(1)
    def test_rate_limit(self):
        """Attempt to trigger rate limiting."""
        for _ in range(10):
            self.client.get("/api/v1/health")


class BatchProcessingUser(HttpUser):
    """User that tests batch processing."""

    wait_time = between(5, 10)

    def on_start(self):
        """Setup for batch user."""
        self.api_key = os.getenv("API_KEY", "test_key_12345")
        self.headers = {"X-API-Key": self.api_key}

    @task
    def submit_batch(self):
        """Submit a batch processing job."""
        # Create multiple test images
        files = []
        for i in range(3):
            img = Image.new('RGB', (200, 200), color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            files.append(
                ("files", (f"batch_{i}.png", buf.getvalue(), "image/png"))
            )

        with self.client.post(
            "/api/v1/ocr/batch",
            files=files,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202, 404]:
                response.success()
            else:
                response.failure(f"Batch failed: {response.status_code}")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, **kwargs):
    """Log request metrics."""
    pass  # Can add custom logging here


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("Load test completed.")
