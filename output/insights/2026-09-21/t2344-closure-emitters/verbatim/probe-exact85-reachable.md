# 親が repo 外で実行した script の逐語 (`probe_exact85_reachable.py`)

```python
"""DW-O13: exact-85 grammar が実環境で到達可能か (production の capture 経路が exact-85 の authority を出すか) を、
campaign を起動せずに確かめる。wave 木 (HEAD 5efd69367、clean) の production module を import し、
contract_loader_binding.capture_contract_loader_binding() を 1 回呼んで、blob map の key 列を調べる。
書き込みはしない (lock も campaign も作らない)。出力: exact85-reachable.json
"""
import json
import subprocess
import sys

W = "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters"
J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
sys.path.insert(0, W)
from orchestrator.campaign import campaign_lock, contract_loader_binding  # noqa: E402

head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=W, capture_output=True, text=True, check=True).stdout.strip()
status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=W,
                        capture_output=True, text=True, check=True).stdout
binding = contract_loader_binding.capture_contract_loader_binding()
keys = list(binding.contract_loader_blob_sha256s)
tuple85 = list(campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS)
out = {
    "head": head,
    "tracked_dirty": status.splitlines(),
    "binding_commit": binding.contract_loader_commit,
    "key_count": len(keys),
    "keys_equal_declared_order": keys == tuple85,
    "keys_equal_sorted": keys == sorted(tuple85),
    "declared_count": len(tuple85),
    "module_file": contract_loader_binding.__file__,
}
json.dump(out, open(J + "/exact85-reachable.json", "w"), indent=2)
print(json.dumps(out, indent=2))
```
