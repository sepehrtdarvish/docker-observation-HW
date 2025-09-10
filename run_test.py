import requests
import time
import threading
import random
import sys
from datetime import datetime
from typing import Optional

BASE_URL = "http://localhost:9000"
DURATION = 60


class LoadTester:
    def __init__(self, base_url: str = BASE_URL, duration: int = DURATION):
        self.base_url = base_url
        self.duration = duration
        self.start_time = None
        self.threads = []

    def check_app_running(self) -> bool:
        print("Checking if the Flask app is running...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("Flask app is running!")
                return True
            else:
                print(f"Error: Flask app returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error: Flask app is not running at {self.base_url}")
            print(f"Error details: {e}")
            print("Please start the app first with: docker-compose up")
            return False

    def test_hello(self) -> None:
        while time.time() - self.start_time < self.duration:
            try:
                requests.get(f"{self.base_url}/", timeout=5)
                time.sleep(0.1)
            except requests.exceptions.RequestException:
                pass
        print("Hello endpoint completed")

    def test_add_item(self) -> None:
        while time.time() - self.start_time < self.duration:
            try:
                timestamp = int(time.time())
                key = f"test_key_{timestamp}_{random.randint(1000, 9999)}"
                value = f"test_value_{timestamp}"

                payload = {"key": key, "value": value}
                requests.post(f"{self.base_url}/items", json=payload, timeout=5)
                time.sleep(0.2)
            except requests.exceptions.RequestException:
                pass
        print("Add item endpoint completed")

    def test_get_item(self) -> None:
        for i in range(1, 6):
            try:
                payload = {"key": f"load_test_key_{i}", "value": f"load_test_value_{i}"}
                requests.post(f"{self.base_url}/items", json=payload, timeout=5)
            except requests.exceptions.RequestException:
                pass

        while time.time() - self.start_time < self.duration:
            try:
                key_num = random.randint(1, 5)
                requests.get(
                    f"{self.base_url}/items/load_test_key_{key_num}", timeout=5
                )
                time.sleep(0.1)
            except requests.exceptions.RequestException:
                pass
        print("Get item endpoint completed")

    def test_list_items(self) -> None:
        while time.time() - self.start_time < self.duration:
            try:
                requests.get(f"{self.base_url}/items", timeout=5)
                time.sleep(0.3)
            except requests.exceptions.RequestException:
                pass
        print("List items endpoint completed")

    def test_cache_miss(self) -> None:
        while time.time() - self.start_time < self.duration:
            try:
                timestamp = int(time.time())
                random_key = f"cache_miss_{timestamp}_{random.randint(1000, 9999)}_{random.randint(1000, 9999)}"
                requests.get(f"{self.base_url}/items/{random_key}", timeout=5)
                time.sleep(0.5)
            except requests.exceptions.RequestException:
                pass
        print("Cache miss endpoint completed")

    def run_load_test(self) -> None:
        print(f"Starting load test for {self.duration} seconds...")
        print(f"Base URL: {self.base_url}")
        print()

        if not self.check_app_running():
            sys.exit(1)

        self.start_time = time.time()

        print("\nStarting parallel load test...")

        test_functions = [
            self.test_hello,
            self.test_add_item,
            self.test_get_item,
            self.test_list_items,
            self.test_cache_miss,
        ]

        for test_func in test_functions:
            thread = threading.Thread(target=test_func)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

        for thread in self.threads:
            thread.join()

        print("\nLoad test completed!")


def main():
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library is not installed.")
        print("Please install it with: pip install requests")
        sys.exit(1)

    tester = LoadTester()
    tester.run_load_test()


if __name__ == "__main__":
    main()
