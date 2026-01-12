import json
import os
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: render_asl.py <env.json> <input.asl.json> <output.json>", file=sys.stderr)
        return 2

    env_path, in_path, out_path = sys.argv[1:]

    with open(env_path, "r", encoding="utf-8") as f:
        env = json.load(f)

    with open(in_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace ${KEY} placeholders.
    # If env value is a list/dict, we inject as JSON (no quotes).
    # If env value is a scalar, we inject as string.
    for k, v in env.items():
        token = "${" + k + "}"
        if token not in content:
            continue
        if isinstance(v, (list, dict)):
            content = content.replace(token, json.dumps(v))
        else:
            content = content.replace(token, str(v))

    # Validate final JSON.
    json.loads(content)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
