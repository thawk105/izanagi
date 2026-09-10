# 裁定パッケージ — [T-495]「消す前に止める」防壁の要否と形

本 wave は調査だけを行い、防壁は実装していない。以下はユーザー裁定を要する項目である。

---

## 前提: 何が起きたのか (実測)

`codex/dev-wave-improve` (tip `77db32c`) は、**2026-08-03 23:12 JST に対話セッションが
`git branch -D` を実行して消えた**。その 70 秒前にユーザーが「やっていい」と明示承認しており、
セッションは削除前に tip SHA を記録していた。さらに**削除の 2 日前 (2026-08-01) に、
ユーザー裁定が「main を正本にする。この branch の実装 50 path は land せず廃棄する」と
既に決めていた** (`output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md`)。

つまりこれは事故ではなく、**裁定済みの廃棄の執行**だった。起票時の見立て
「ahead>0 のブランチを**検査なしに**消した」は誤りである。

一方、次の 2 つは実測で残った。

- 削除した瞬間、`77db32c` は現存する ref のどこからも到達できなくなった。
  保護用の `rescue-t213` が作られたのは **32 時間 37 分後**である。
  その間、`gc` が走れば失われていた (既定 `gc.pruneExpire` = 2 weeks、`--prune=now` なら即時)。
- `git branch -D` を機械的に止めるものは repo 内に無い。
  `hooks/guard_bash.decide('git branch -D <名>')` は `(True, '')` を返す。
  防護パス語を含まないコマンドは `decide()` の fast path で即許可されるためで、
  `_GIT_READ_SUBS` から `branch` を外しても直らない (`hooks/guard_bash.py:1532-1543`)。

---

## 裁定 1: 「消す前に止める」防壁を作るか

### 判定に必要な事実

- **独立 2 例は無い。** `DW-G03` は族一般化に独立 2 例を要求する。全 session transcript を
  洗った結果、ahead>0 かつ未承認の `git branch -D` は 0 件だった。
- **ただしその 0 件は根拠として弱い。** 母集団は「残っている transcript に記録された実行」だけで、
  手動 shell、別 clone、別ホスト、削除済み reflog、GC 後の object を覆わない。
  事故が古いほど証拠が消えるため、欠測はランダムでもない。
- **事後検知には大きな穴がある。** `tools/audit_dangling_commits.py` ([T-494]、main に land 済み)
  が検出できるのは「**新規 path** が main と全 branch tip の tree に無い」場合だけである。
  次はいずれも**検出できない**。
  - 既存ファイルへの**編集だけ**を持つ branch (path が main にあるので除外される)
  - 既存ファイルの削除、同名・別内容
  - `gc` が到達不能 object を刈った後
  - 呼び出し口は `/cleanup-branches` の 1 か所だけで、定期実行ではない

### 選択肢

- **(a) 何もしない。** 実害が出た事例は 0 件で、唯一の候補事例は裁定済みの廃棄だった。
  独立 2 例が無い以上、`DW-G03` に従えば制度化しないのが既定である。
  - 損: 上記の「0 件の弱さ」と事後検知の穴が残る。
- **(b) rescue-before-delete 型を repo 層に置く (親の推奨)。**
  拒否ではなく「消える commit が現存 ref から到達不能になるなら、先に rescue ref を作ってから消す」
  という形にする。人間が既に「価値なし」と裁定した case でも、可逆性だけは機械が保つ。
  - 得: 意味判断を機械にさせない (機械は到達性だけを見る)。常時警告にならない
    (rescue を作って続行するので override を訓練しない)。本件でも発火し、
    32 時間の無防備な窓を消せた。
  - 損: 設置面は `hooks/guard_bash.py` の fast path 前で、**被覆は Claude の Bash 経路だけ**。
    Codex、script、変数展開、ユーザー端末、`git -C`、複数 ref 同時削除、ref rename は覆わない。
    保護対象は canonical common-dir の `refs/heads/*` に絞る必要がある
    (絞らないと `tools/codex_reasoning_ab.py` の隔離 snapshot sealing が偽陽性になる)。
- **(c) 事後検知の穴だけ塞ぐ。** `audit_dangling_commits.py` を path 名比較から
  blob / patch 比較へ強める。
  - 得: 既存ファイルの編集だけを持つ branch も拾える。設置面が 1 か所で完結する。
  - 損: 事後のままなので `gc` 後は救えない。既存の負例テスト
    (`test_audit_dangling_commits.py:139-162` が「同名別内容は報告しない」を固定) の
    書き換えが要る。

**親の推奨は (b)。** ただし後述の scope 制約を認めたうえでの話であり、
(a) を選んでも `DW-G03` には忠実である。

---

## 裁定 2: scope の線引き (どれを「やった」と書けるか)

実効性のある防壁は 3 owner に跨る。**repo 層だけを実装して「branch 削除を保護した」と
書くことはできない。**

| 層 | 誰が持つか | 状態 |
|---|---|---|
| Claude の Bash 経路 | このリポジトリ | 実装可能 (裁定 1 の (b)) |
| ExitWorktree の警告 | harness (Claude Code 本体) | **変更権限なし。** 現在の count は ahead-of-base で、観測した 8 件の警告はすべて偽陽性 (tip が main と同一か ancestor)。未 land 作業を救った例はゼロ。実際に反射的 override を訓練しており、ある rulings session は初回警告の後、続く 17 worktree を最初から `discard_changes:true` で除去していた |
| すべての Git 操作 (手動 shell・別ホスト・Codex) | 環境 / ユーザー | `reference-transaction` hook が最も広いが、`.git/config` は tracked でなく、dev-wave の helper は `core.hooksPath=/dev/null` を明示するため repo 内から強制できない |

**裁定事項:** harness 層と環境層を、別 owner の課題として起票するか、しないか。

---

## 裁定 3: `rescue-t213` の処遇 (継続審議)

2026-08-05 の /rulings で未裁定のまま残っている項目である。本 wave で追加実測した。

- `rescue-t213` が持ち、**現 main (`18149bcf`) に無い path は 7 件**
  (`tools/pegasus_policy.py`、`tools/pegasus/{submit_tests.py,test_dispatch.py,run_tests_job.sh,test_dispatch_policy.json}`、
  `orchestrator/tests/{test_pegasus_policy.py,test_pegasus_test_dispatch.py}`)。
  内容が違うだけの path が 16、同一が 37。
- これら 7 件は 2026-08-01 のユーザー裁定で**廃棄対象**と決まっている (FR-1: `DispatchPolicy` が
  `policy_path` を含む frozen dataclass のため、同一 bytes でも path が違えば `!=` になり、
  本番で submit も resume もできない)。
- ただし **branch 由来で未移植の知見が 1 件残る** — accounting の `Group Name` 束縛。
  現 main の `_accounting_present` は Request ID / Started / Ended / Elapse しか検査していない
  (`tools/pegasus/dispatch_compute.py:842-847`)。これは [T-222] が所有する。

**したがって「拾う中身は完全にゼロ」ではなく「直接 land / cherry-pick すべき実装はない」が正確。**
`rescue-t213` を消してよいかは、[T-222] が `Group Name` 束縛を main へ入れ終えるまで保留するのが
安全である。親の推奨は**保留**。
