#!/usr/bin/env python3
"""Rebuild the beta.2.40 stability candidate from verified 2.39 JARs and class patches.

This code does NOT touch or sign the live update manifest.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import json, hashlib, sys

baseline=Path(sys.argv[1]); patch_path=Path(sys.argv[2]); dest=Path(sys.argv[3]); dest.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with ZipFile(patch_path) as patch:
    assert patch.testzip() is None
    manifest=json.loads(patch.read("manifest.json"))
    assert set(manifest)=={"1.20.1","1.21.1","1.21.4","1.21.11"}
    for v,record in manifest.items():
        source=baseline/f"DuckClientZ-{v}-1.5.28-beta.2.39.jar"
        assert sha(source)==record["baseline_sha256"],f"Unexpected 2.39 baseline: {v}"
        target=dest/f"DuckClientZ-{v}-1.5.28-beta.2.40.jar"
        changed=set(record["changed"])
        assert len(changed)>=25, f"Too few changes in {v}"
        with ZipFile(source) as old:
            assert old.testzip() is None
            oldnames=set(old.namelist())
            for cls in changed:
                assert f"{v}/{cls}" in patch.namelist(), f"Missing patch {v}/{cls}"
            with ZipFile(target,"w",ZIP_DEFLATED,compresslevel=6) as out:
                for entry in old.infolist():
                    content=patch.read(f"{v}/{entry.filename}") if entry.filename in changed else old.read(entry.filename)
                    out.writestr(entry,content)
                for cls in record["changed"]:
                    if cls not in oldnames:out.writestr(cls,patch.read(f"{v}/{cls}"))
        with ZipFile(target) as check,ZipFile(source) as old:
            assert check.testzip() is None
            names=check.namelist()
            assert len(names)==len(set(names))
            assert set(names)==set(old.namelist())|changed
            assert json.loads(check.read("fabric.mod.json"))["version"]=="1.5.28-beta.2.40"
            assert check.read("com/duckswords/modules/HitParticles.class")==old.read("com/duckswords/modules/HitParticles.class")
            assert check.read("com/duckswords/modules/TargetHud.class")==old.read("com/duckswords/modules/TargetHud.class")
            for cls in changed:
                assert check.read(cls)==patch.read(f"{v}/{cls}"),f"Incorrect patch {cls}"
            for cls in old.namelist():
                if cls not in changed: assert check.read(cls)==old.read(cls), f"Modified unexpected {cls}"
            assert check.read("assets/duckswords/storage.properties").decode().splitlines()[0]==f"minecraft={v}"
        print(f"PASS {v}: {target.name} ({target.stat().st_size} bytes, SHA256 {sha(target)})", flush=True)
print("All 4 candidates reconstructed with exact class contents and baseline hashes validated.")
