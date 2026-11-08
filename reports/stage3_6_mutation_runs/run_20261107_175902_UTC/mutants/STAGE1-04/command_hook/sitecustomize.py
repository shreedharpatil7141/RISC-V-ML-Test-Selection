import json, os, subprocess
_orig_run=subprocess.run
def _audit_run(*args, **kwargs):
    cmd=args[0] if args else kwargs.get("args")
    try:
        with open(os.environ["MUTATION_COMMAND_LOG"], "a", encoding="utf-8") as f:
            f.write(json.dumps({"command":cmd,"cwd":kwargs.get("cwd"),"shell":kwargs.get("shell",False)})+"\n")
    except Exception:
        pass
    return _orig_run(*args, **kwargs)
subprocess.run=_audit_run
