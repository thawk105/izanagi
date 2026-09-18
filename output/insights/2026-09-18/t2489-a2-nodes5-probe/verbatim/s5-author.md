## 総括

[paper_story_a2_certification.v2.json:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree/orchestrator/campaign/paper_story_a2_certification.v2.json:132) の `scheduler.nodes` を `1` → `5` に変更しました。他のバイトは不変です。他ファイルの作成・編集、テスト、commit は行っていません。

`load_policy()` は成功。workload は `rr5` / `rr50` のままです（戻り値はタプル）。

実走コマンドと出力（いずれも終了コード0）：

```console
$ git diff --stat
 orchestrator/campaign/paper_story_a2_certification.v2.json | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

$ git diff
diff --git a/orchestrator/campaign/paper_story_a2_certification.v2.json b/orchestrator/campaign/paper_story_a2_certification.v2.json
index c0ace8db7..9d98ed2dd 100644
--- a/orchestrator/campaign/paper_story_a2_certification.v2.json
+++ b/orchestrator/campaign/paper_story_a2_certification.v2.json
@@ -129,7 +129,7 @@
   "scheduler": {
     "project": "SFC",
     "queue": "gen_S",
-    "nodes": 1,
+    "nodes": 5,
     "walltime": "06:00:00",
     "job_body": "tools/pegasus/paper_story_a2_certification.sh"
   }
```

```console
$ python3 -B -m orchestrator.campaign.paper_story_a2_certification --help
usage: paper_story_a2_certification.py [-h] [--policy PATH]
                                       {exact-qsub,compute-preflight,preregister,record-request-id,durabilize-qsub-diagnostics,run-workload,finalize-raw,finish-group,record-submission,record-completion,record-acquisition,collect}
                                       ...

Paper-story A-2 exact-workload certification protocol. The module deliberately
keeps the experiment values in the adjacent versioned policy. Code here
validates bindings, collects one create-only outer attempt, publishes a
bounded tracked result, and exposes the exact qsub primitive used by the
login-side fan-out submitter.

positional arguments:
  {exact-qsub,compute-preflight,preregister,record-request-id,durabilize-qsub-diagnostics,run-workload,finalize-raw,finish-group,record-submission,record-completion,record-acquisition,collect}

options:
  -h, --help            show this help message and exit
  --policy PATH         select one of the two canonical repository
                        certification policies
```

読込確認も追加実行しました。

```console
$ python3 -B - <<'PY'
from orchestrator.campaign import paper_story_a2_certification as a2
p = a2.load_policy()
print(p.document["scheduler"])
print(a2.workload_ids(p))
PY
{'project': 'SFC', 'queue': 'gen_S', 'nodes': 5, 'walltime': '06:00:00', 'job_body': 'tools/pegasus/paper_story_a2_certification.sh'}
('rr5', 'rr50')
```

```console
$ sha256sum orchestrator/campaign/paper_story_a2_certification.v2.json
f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c  orchestrator/campaign/paper_story_a2_certification.v2.json
```

追加のバイト比較：

```console
$ python3 -B - <<'PY'
from pathlib import Path
import subprocess
path = 'orchestrator/campaign/paper_story_a2_certification.v2.json'
before = subprocess.check_output(['git', 'show', 'HEAD:' + path])
after = Path(path).read_bytes()
assert after == before.replace(b'    "nodes": 1,', b'    "nodes": 5,', 1)
print('PASS: HEAD bytes differ only by scheduler.nodes 1 -> 5')
PY
PASS: HEAD bytes differ only by scheduler.nodes 1 -> 5
```

所有外への波及の静的列挙：

- scheduler を使う投入処理は5ノード指定になります。実際の投入は未実行です。
- policy bytes の SHA-256 は変わりますが、`load_policy()` は拒否しませんでした。
- 指定された `orchestrator/tests/test_paper_story_a2_certification.py` 付近の policy SHA-256 pin 2箇所は更新・実行していません。**wave branch に入れないため回帰しない**という運用上の扱いです。この tree でのテスト成功を示すものではありません。
- `walltime`、`queue`、`project`、`job_body`、A-6 policy は変更していません。