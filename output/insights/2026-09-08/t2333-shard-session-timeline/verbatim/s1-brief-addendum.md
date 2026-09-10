# 段 1 brief の追補 — 親が段 2 の間に実測した値

これらは親が自分で測った値である。**一般化が過ぎていないか、測り方が間違っていないかを攻撃せよ。**

## 実測 1 — 受入台帳の被覆率余裕は 7 node しかない

`orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
は `covered / collection >= 0.90` を要求する (同 file 712 行)。

親の測り方: worktree で `python3 -B -m pytest --collect-only -q orchestrator/tests` を走らせて
`orchestrator/tests/` で始まり `::` を含む行を node と数え、
`orchestrator/tests/acceptance_duration_ledger.json` の `duration_seconds_by_nodeid` の
key 集合と積を取った。

結果: collection = 21569、ledger = 19521、covered = 19419、被覆率 = 90.031990%。
`covered / (21569 + k) >= 0.90` を解くと **k <= 7**。

つまり新しい test node を 8 件以上足すとこの gate が赤になる。plan は 12 件以上 (parametrize 分を
数えるともっと多い) を足す計画である。したがって実装は `acceptance_duration_ledger.json` へ
新 node id を足し `nodeid_count` も更新する必要がある — と親は判断している。

**攻撃せよ:** この測り方は権威の test が使う `consumer_keys` と同じものを数えているか。
test は probe (`_COVERAGE_PROBE_ENV`) が書く `rows` の `consumer` key を使う (同 700〜707 行)。
親の素朴な collect 行の数え方と食い違うなら、余裕 7 という数字は誤りである。

## 実測 2 — xdist 越しに `TestReport.start` / `stop` は残る

親の測り方: `_pytest.reports._report_to_json` の実装を読み、`d = report.__dict__.copy()` で
instance 属性を丸ごと複製していることを確認した。pytest 9.1.1、xdist 3.8.0。

**攻撃せよ:** 復元側 (`_report_from_json`) が同じ属性を復元するか。読解であり実走ではない。

## 実測 3 — 対象 2 file に凍結 bytes の pin は無い

親の測り方: `git grep -q <blob sha>` を 2 file の HEAD blob について実行し、両方 rc=1 (不在)。

**攻撃せよ:** path 以外を key にする pin (role 名、xdist group 名、file 全体の sha256 を
別の場所へ焼いた golden など) を親は探していない。`tools/acceptance_shards.py` や
`orchestrator/tests/conftest.py` の内容に束縛された検査が他にあれば挙げよ。

## 実測 4 — 並行 wave の編集面

全 worktree で `git status --porcelain` を走らせた結果、`tools/acceptance_shards.py` を
未 commit で触っているのは `.codex/worktrees/accwall-unit-b` の 1 件だけ。
`orchestrator/tests/conftest.py` を触っている worktree は無い。
