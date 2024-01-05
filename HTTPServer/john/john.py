from typing import Any, List, Final, Callable, Dict, Tuple
from urllib.parse import urlparse, parse_qs

__all__: Final[List[str]] = ["John"]


class John:
    def __init__(self):
        self.routes = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}}

    def route(self, method: str, path: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            parsed_path = self.parse_path(path)
            self.routes[method][
                tuple(parsed_path)
            ] = func  # Convert parsed_path to tuple here
            return func

        return decorator

    def parse_path(self, path: str) -> List[Tuple[str, bool]]:
        parts = path.lstrip("/").split("/")
        parsed_path = []

        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                parsed_path.append((part[1:-1], True))
            else:
                parsed_path.append((part, False))
        return parsed_path

    def match_path(
        self, route_path: List[Tuple[str, bool]], actual_path: List[str]
    ) -> Dict[str, Any]:
        if len(route_path) != len(actual_path):
            return {}

        params = {}
        for route_part, actual_part in zip(route_path, actual_path):
            route_segment, is_variable = route_part
            if is_variable:
                params[route_segment] = actual_part
            elif route_segment != actual_part:
                return {}

        return params

    def get(self, path: str) -> Callable:
        return self.route("GET", path)

    def post(self, path: str) -> Callable:
        return self.route("POST", path)

    def put(self, path: str) -> Callable:
        return self.route("PUT", path)

    def delete(self, path: str) -> Callable:
        return self.route("DELETE", path)

    def dispatch(self, method: str, url: str) -> Any:
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip("/")
        if method in self.routes:
            for route_path in self.routes[method]:
                parsed_route_path = list(route_path)
                parsed_actual_path = path.split("/")
                print(parsed_route_path, parsed_actual_path)
                match = self.match_path(parsed_route_path, parsed_actual_path)
                print(match)
                if match:
                    query_params = parse_qs(parsed_url.query)
                    print(route_path)
                    return self.routes[method][route_path](**match, **query_params)
        return "404 Not Found"


app = John()


@app.get("/monkey")
def money():
    return "helloe world"


@app.get("/monkey/gay/{monkey}")
def get_hitler(monkey):
    return monkey + " is gay."


print(app.dispatch("GET", "/monkey/gay/hittyler"))
print(app.routes)


routes = {}
