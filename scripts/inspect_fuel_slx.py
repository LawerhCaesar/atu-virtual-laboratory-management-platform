"""Read-only SLX audit: never loads MATLAB, executes blocks or extracts files."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


def inspect(path):
    document = Path(path)
    result = {"source": document.name, "sha256": hashlib.sha256(document.read_bytes()).hexdigest(), "systems": {}}
    ignored = {"Position", "ZOrder", "BackgroundColor", "ForegroundColor", "FontSize", "NameLocation", "ContentPreviewEnabled", "DisplayOption", "Ports"}
    with ZipFile(document) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith("simulink/systems/") or not name.endswith(".xml"):
                continue
            xml = ET.fromstring(archive.read(name))
            blocks = []
            for block in xml.findall("Block"):
                if block.get("BlockType") in {"Display", "Scope"}:
                    continue
                blocks.append({"sid": block.get("SID"), "type": block.get("BlockType"), "name": block.get("Name"),
                    "parameters": {p.get("Name"): p.text for p in block.findall("P") if p.get("Name") not in ignored}})
            wires = [{"from": line.findtext('P[@Name="Src"]'), "to": [p.text for p in line.iter("P") if p.get("Name") == "Dst"]} for line in xml.findall("Line")]
            result["systems"][Path(name).stem] = {"blocks": blocks, "wires": wires}
        config = ET.fromstring(archive.read("simulink/configSet0.xml"))
        result["solver"] = {p.get("Name"): p.text for p in config.iter("P") if p.get("Name") in {"Solver", "SolverName", "SolverType", "FixedStep", "StopTime", "RelTol", "AbsTol"}}
    return result


if __name__ == "__main__":
    print(json.dumps(inspect(sys.argv[1]), indent=2))
