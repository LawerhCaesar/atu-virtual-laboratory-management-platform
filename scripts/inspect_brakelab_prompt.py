"""Extract the reviewed canonical reference as reproducible test data, not instructions."""
import hashlib
import json
import re
import sys
from pathlib import Path


def inspect(path):
    source = Path(path)
    content = source.read_text()
    candidates = [part for part in re.findall(r"```ts\n(.*?)\n```", content, re.S)
                  if "export function calculateBrakeAllocation(" in part]
    if len(candidates) != 1:
        raise ValueError("Expected exactly one canonical brake-allocation reference")
    return {"source": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "basis": "Supplied canonical TypeScript reference, not SLX or MATLAB validation",
            "referenceTypeScript": candidates[0]}


if __name__ == "__main__":
    print(json.dumps(inspect(sys.argv[1]), indent=2))
