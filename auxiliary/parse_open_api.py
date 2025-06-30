# -*- coding: utf-8 -*-
import argparse
import json
from pathlib import Path

from loguru import logger
from prance import ResolvingParser
from slugify import slugify


class AsciiDocFile:
    def __init__(self, title: str, anchor: str):
        self._lines = [f"== [[{anchor}]]{title}\n"]
        self._anchor = anchor
        self._title = title

    def __str__(self):
        return "".join(self._lines)

    def __add__(self, other):
        if isinstance(other, str) or hasattr(other, "__str__"):
            self._lines.append(f"{str(other).strip()}\n\n")

        else:
            logger.error(f"Должно быть строкой, но получено {type(other).__name__}")

        return self

    def write(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        file_path: Path = directory.joinpath(f"{self._anchor}.adoc")
        file_path.write_text(str(self), encoding="utf-8")


def format_row(name, schema, required):
    desc = schema.get("description", "")
    default = schema.get("default")
    typ = schema.get("type", "object")
    required_flag = "M" if required else "O"
    if default:
        desc += f" (Default: {default})"
    return f"|{name}\n|{desc}\n|{typ}\n|{required_flag}\n\n"


def render_schema_table(schema):
    if not schema:
        return ""
    props = schema.get("properties", {})
    required = schema.get("required", [])
    rows = ""
    for name, meta in props.items():
        rows += format_row(name, meta, name in required)
    return rows


class RequestPart:
    def __init__(self, method: str, path: str, base_url: str, op: dict):
        self.method = method.upper()
        self.path = path
        self.base_url = base_url.rstrip("/")
        self.op = op

    def render(self):
        curl_lines = [
            f"curl -X '{self.method}' '{self.base_url}{self.path}' \\",
            "  -h 'Content-Type: application/json' \\"
        ]
        if "parameters" in self.op:
            for p in self.op["parameters"]:
                if p.get("in") == "header":
                    curl_lines.append(f"  -h '{p['name']}: <value>' \\")
        if "requestBody" in self.op:
            curl_lines.append("  -d '<json_body>'")
        return "=== Request\n[source,shell]\n----\n" + "\n".join(curl_lines) + "\n----"


class TablePart:
    def __init__(self, title: str, parameters: list, location: str):
        self.title = title
        self.parameters = parameters
        self.location = location

    def render(self):
        rows = ""
        for p in self.parameters:
            if p.get("in") == self.location:
                schema = p.get("schema", {})
                rows += format_row(p["name"], schema, p.get("required", False))
        if not rows:
            return ""
        return f"=== {self.title}\n[options=\"header\",width=\"100%\"]\n|===\n|Parameter |Description |Type |Optional/Mandatory\n{rows}|===\n"


class RequestBodyPart:
    def __init__(self, schema: dict):
        self.schema = schema

    def render(self):
        body = render_schema_table(self.schema)
        if not body:
            return ""
        return f"=== JSON Body\n[options=\"header\",width=\"100%\"]\n|===\n|Parameter |Description |Type |Optional/Mandatory\n{body}|===\n"


class ResponsePart:
    def __init__(self, responses: dict):
        self.responses = responses

    def render_success(self):
        success = self.responses.get("200") or self.responses.get("201")
        if not success:
            return ""
        schema = success.get("content", {}).get("application/json", {}).get("schema", {})
        table = render_schema_table(schema)
        return f"=== Response\n[options=\"header\",width=\"100%\"]\n|===\n|Parameter |Description |Type |Optional/Mandatory\n{table}|===\n" if table else ""

    def render_sample(self):
        success = self.responses.get("200") or self.responses.get("201")
        if not success:
            return ""
        content = success.get("content", {})
        for ctype in ("application/json",):
            example = content.get(ctype, {}).get("example")
            if example:
                return f"=== Sample\n[source,json]\n----\n{json.dumps(example, indent=2)}\n----"
        return ""

    def render_errors(self):
        errors = [f"* {code}:: {resp.get('description', '')}" for code, resp in self.responses.items() if code not in ("200", "201")]
        return f"=== Errors\n" + "\n".join(errors) if errors else ""


class ParsedEndpoint:
    def __init__(self, path: str, method: str, op: dict, base_url: str):
        self.path = path
        self.method = method
        self.op = op
        self.base_url = base_url
        self.slug = slugify(f"{method}-{path}")
        self.title = op.get("summary") or f"{method.upper()} {path}"

    def to_adoc(self) -> AsciiDocFile:
        req = RequestPart(self.method, self.path, self.base_url, self.op)
        all_params: list[str] = self.op.get("parameters", [])

        query_params: TablePart = TablePart("Query Parameters", all_params, "query")
        path_params: TablePart = TablePart("Path Parameters", all_params, "path")

        body_schema = self.op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        body = RequestBodyPart(body_schema)

        resp = ResponsePart(self.op.get("responses", {}))

        adoc = AsciiDocFile(self.title, self.slug)
        adoc += req.render()
        adoc += path_params.render()
        adoc += query_params.render()
        adoc += body.render()
        adoc += resp.render_success()
        adoc += resp.render_sample()
        adoc += resp.render_errors()
        return adoc


def parse_openapi(path: str) -> dict:
    parser = ResolvingParser(path)
    return parser.specification


def generate_index(endpoints: list[ParsedEndpoint], output_dir: Path):
    lines = ["= API Documentation Index\n\n"]
    for ep in sorted(endpoints, key=lambda e: e.slug):
        lines.append(f"* <<{ep.slug}>> {ep.title}")
    (output_dir / "_index.adoc").write_text("\n".join(lines), encoding="utf-8")


def main(input_file: str, out_dir: str, base_url: str):
    spec = parse_openapi(input_file)
    paths = spec["paths"]
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    endpoints = []
    for path, methods in paths.items():
        for method, op in methods.items():
            ep = ParsedEndpoint(path, method, op, base_url)
            adoc = ep.to_adoc()
            adoc.write(out_path)
            endpoints.append(ep)

    generate_index(endpoints, out_path)
    print(f"✅ Generated {len(endpoints)} endpoints and _index.adoc in {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="OpenAPI YAML or JSON file")
    parser.add_argument("-o", "--output-dir", default="out_adoc", help="Output directory")
    parser.add_argument("--base-url", default="http://localhost", help="Base URL for endpoints")

    args = parser.parse_args()
    main(args.input_file, args.output_dir, args.base_url)
