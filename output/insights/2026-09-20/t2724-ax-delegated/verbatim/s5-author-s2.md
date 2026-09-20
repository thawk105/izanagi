## 作成した file と script (逐語)

approval record:

```json
{"approved_at":"2026-09-20T05:20:31Z","approver":"user (delegated to AI by user ruling 2026-09-20 13:2x JST; supersedes D2120 item 2(b) and D2174 item 4)","generation_sha256":"7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06","scope":"s8b-holdout"}
```

pointer record:

```json
{"approval_sha256":"3787d97beb698c650153167e91d85cfbe9b2da1d87b38068427163a696821f90","generation_number":1,"parent_active_sha256":null,"path":"output/s8b-freeze/holdout_freeze.v2.g1.json","sha256":"7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06"}
```

両 record の実ファイルに末尾改行はありません。path は次節の status に記載します。

[_t2724_write_approval.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-ax-s2/_t2724_write_approval.py) 全文:

```python
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

assert Path.cwd() == Path("/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-ax-s2")
gen = Path("output/s8b-freeze/holdout_freeze.v2.g1.json")
gen_sha = hashlib.sha256(gen.read_bytes()).hexdigest()
assert gen_sha == "7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06"
doc = {"generation_sha256": gen_sha,
       "approver": "user (delegated to AI by user ruling 2026-09-20 13:2x JST; supersedes D2120 item 2(b) and D2174 item 4)",
       "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "scope": "s8b-holdout"}
raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
path = Path("output/s8b-freeze/approvals") / (gen_sha + ".json")
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("xb") as f: f.write(raw)
print(path); print("approval_sha256=" + hashlib.sha256(raw).hexdigest())
```

[_t2724_write_pointer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-ax-s2/_t2724_write_pointer.py) 全文:

```python
import hashlib, json
from pathlib import Path

assert Path.cwd() == Path("/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-ax-s2")
gen_path = "output/s8b-freeze/holdout_freeze.v2.g1.json"
gen_sha = hashlib.sha256(Path(gen_path).read_bytes()).hexdigest()
assert gen_sha == "7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06"
approval_sha = hashlib.sha256((Path("output/s8b-freeze/approvals") / (gen_sha + ".json")).read_bytes()).hexdigest()
doc = {"generation_number": 1, "path": gen_path, "sha256": gen_sha,
       "parent_active_sha256": None, "approval_sha256": approval_sha}
raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
ptr_sha = hashlib.sha256(raw).hexdigest()
path = Path("output/s8b-freeze/active") / (ptr_sha + ".json")
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("xb") as f: f.write(raw)
print(path); print("pointer_sha256=" + ptr_sha)
```

両 script を指定 worktree root から `python3 -B <絶対 path>` で順次実行し、双方 rc=0 でした。

## 自己検証 (実測値)

`git rev-parse HEAD` は作成前後とも:

```text
4114cf51b40a482e5f25a081156d964dc57451c7
```

開始時 status は空。作成後の `git status --porcelain --untracked-files=all --ignore-submodules=none` は指定の4行だけでした:

```text
?? _t2724_write_approval.py
?? _t2724_write_pointer.py
?? output/s8b-freeze/active/577537e223ffa6930e2b983ae384780dc3e6fd7427d7c03009a81882aaf64653.json
?? output/s8b-freeze/approvals/7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06.json
```

`sha256sum` と `wc -c` の実測値:

| record | SHA-256 | bytes |
|---|---|---:|
| approval | `3787d97beb698c650153167e91d85cfbe9b2da1d87b38068427163a696821f90` | 264 |
| pointer | `577537e223ffa6930e2b983ae384780dc3e6fd7427d7c03009a81882aaf64653` | 265 |

`python3 -B -c` による検証は rc=0:

- approval keys は exact 4: `approved_at`, `approver`, `generation_sha256`, `scope`。
- `generation_sha256` は approval filename と一致。世代ファイルの再計算値も指定の `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06` と一致。
- `approved_at` は実行ホストの UTC 実時刻 `2026-09-20T05:20:31Z`。
- pointer keys は exact 5: `approval_sha256`, `generation_number`, `parent_active_sha256`, `path`, `sha256`。
- pointer 自身の SHA-256 は filename と一致。`approval_sha256` は読み直した approval bytes の SHA-256 と一致。
- `parent_active_sha256` は JSON `null`。
- 両 record の末尾 byte は `b'}'`。
- 現物 module の import、`_APPROVAL_RE` / `_ACTIVE_RE` の fullmatch、および `_load_canonical(raw, keys, what=...)` は双方成功。

`git diff --exit-code HEAD --` は出力なし・rc=0。既存 tracked file の変更はありません。G と X1′ の ancestry 確認もそれぞれ rc=0 でした。

## 未実施・限界

指示どおり add・commit・push、hook 変更、`resolve_active_generation` 呼び出しは行っていません。commit 後の批准 loader・履歴検証は親の作業として残ります。

## 総括

record 2 件と script 2 本の作成、および指定の自己検証を完了しました。既存 tracked file は不変で、親による A → X の commit に引き継げる状態です。