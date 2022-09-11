from common.app import api_restaurant_server, HOST, PORT
import requests
import threading
import time
import os


class APIRestaurantClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.result = None
        self.exit_flag = False
        self.days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    def _start_server(self):
        api_restaurant_server.run(host=self.host, port=self.port)

    def _get_api_request(self, url):
        status = 404
        content = None
        while status != 200 and not self.exit_flag:
            data = requests.get(url=f"{self.base_url}/{url}/")
            status = data.status_code
            if status == 200:
                content = data.json()
                self.exit_flag = True

        self.result = content

    def get_api_request_by_threading(self, api_request, max_wait=5):
        run_thread = threading.Thread(target=self._start_server)
        get_thread = threading.Thread(target=self._get_api_request, args=[api_request])
        s = time.time()
        run_thread.setDaemon(True)
        get_thread.setDaemon(True)
        run_thread.start()
        get_thread.start()
        while not self.exit_flag and time.time() - s < max_wait:
            pass
        assert self.result is not None, f"No data given from url {self.base_url}/{[api_request]}/"
        self.save_shifts(self.result)
        get_thread.join()
        run_thread.join()
        return self.result

    def save_shifts(self, shifts_data:dict):
        base_path = os.sep.join(os.path.abspath(os.curdir).split(os.sep)[:-2])
        csv_path = os.path.join(os.path.join(base_path, "results"))
        if not os.path.isdir(csv_path):
            os.makedirs(csv_path)
        csv_path = os.path.join(csv_path, "shifts.csv")
        with open(csv_path, "w") as file:
            file.write("Day, Opening Hours\n")
            for day in self.days:
                value = shifts_data[day]
                if value is None:
                    opening_hours_str = "closed"
                elif not isinstance(value, list):
                    opening_hours_str = "No Data"
                else:
                    frm = value[0]
                    to = value[1]
                    if 'type' not in frm or 'h' not in frm or 'type' not in to or 'h' not in to:
                        opening_hours_str = "No Data"
                    else:
                        opening_hours_str = f"from {frm['h']} {frm['type']} to {to['h']} {to['type']}"
                file.write(f"{day}, {opening_hours_str}\n")
        print(f"Saved Successfully Human-Readable Shifts Results in {csv_path}")


if __name__ == "__main__":
    api_restaurant_obj = APIRestaurantClient(HOST, PORT)
    timeout = 5
    shifts = api_restaurant_obj.get_api_request_by_threading("shifts", max_wait=timeout)
