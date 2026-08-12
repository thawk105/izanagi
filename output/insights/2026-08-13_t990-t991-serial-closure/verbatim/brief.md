# 段 1 brief — [T-990] 直列正本の閉包漏れ / [T-991] optional index lock

wave slug: `t990-t991-serial-closure`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure`
base: main `01487bb4`
正本: `docs/worklog.md` 2026-08-13 entry 512 の [T-990] / [T-991]

## scope

1. **[T-990]** `orchestrator/tests/conftest.py:160-219` の `REAL_REPO_SERIAL_NODES` の閉包漏れを
   fail-closed 側の実バグとして直す。既知 1 件 + 未特定 2 件 (下記)。
2. **[T-990] 検査の新設** — 正本リストと「実際の資源接触」の対応を機械で確かめる検査を足す。
   漏れが再発したら赤になること。
3. **[T-991]** `git status` を `GIT_OPTIONAL_LOCKS=0` なしで実行する read-only 経路を、同 repo 内の
   抑止済み経路 (`orchestrator/campaign/patchharness.py:73-75`) へ揃える。

scope 外: 受入 wall の短縮 ([T-989] / [T-992] / [T-993])、排他機構そのものの置き換え
(entry 512 で不採用裁定済み)、`test_codex_reasoning_ab.py` / `tools/codex_reasoning_ab.py`
(並行 wave `dev-wave-t983-snapshot-fixture` の lane)。

## 確定済みユーザー裁定

- 規律 2 を緩めない。**排他や検査を弱めて速くする変更は不可。**
- 速度改善は本 wave の目的ではない。**閉包を正しくした結果 直列鎖が伸びても採用してよい。**
- 実装面は Codex author (D95)。親は実装面を直接編集しない。
- 受入全走で `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  **だけ**が赤なら main 由来の既知赤 (octopus merge `d1de13ad`、
  `dev-wave-jobs/rulings-inbox/2026-08-13-known-red-octopus-merge.md`) として自分の差分に帰属させず
  land してよい。受入結果にその旨を明記する。

## 親が実測済みの事実 (段 2 は再検証してよい)

- `test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control`
  (`:216-229`) は `freeze_env` を取る。`freeze_env` (`:63-86`) は module scope の
  `real_known_axes_doc` (`:43-60`) に依存し、そこで `K.build_document()` が
  実 `external/ccbench` source を読む。同じ fixture を取る兄弟 10 node は正本に列挙済み
  (`conftest.py:196-205`) だが、この 1 node だけ漏れている。
  `conftest.py:228-231` の「意図的な除外」註記は「fixture 非利用 3 node」だけを除外と書いており、
  fixture 利用側であるこの node の不在は註記とも矛盾する。**この 1 件は確定。**
- `GIT_OPTIONAL_LOCKS=0` を設定しない `git status` 経路の候補:
  `orchestrator/tests/repo_tree_util.py:20-27`、`orchestrator/campaign/source_digest.py:761-770`、
  `orchestrator/campaign/silo_ladder_rung1.py:963,2084`
  (`scrub_environment()` は `GIT_*` を除去するが `GIT_OPTIONAL_LOCKS=0` を設定しない)。
  対照 = `patchharness.py:73-75` は抑止し、理由をコメントで明記している。
- 未特定: 「実 git object を書く node」と「共有 submodule common-dir を変更する canary」。
  親の grep では `hash-object -w` の実 root 書込は見つからなかった
  (`test_s8b_oracle_driver.py:1239` の `root` は tmp repo)。段 2 で file:line を確定させる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 新設検査は「fixture 閉包 + 実資源 path 定数」から集合を導出し正本と突き合わせる形とする。
  既存 `test_real_repo_serialization.py` は正本 vs 独立 golden の **リスト対リスト**しか見ておらず
  (`:37,573-576`)、両方に無い node を検出できない。**純増検出力 = 「正本にも golden にも無いが
  実資源に触る node」を赤にすること。** 別形 (実行時 tracer 等) が優るなら段 3 で潰してよい。
- **(P2)** [T-991] の是正は「`GIT_OPTIONAL_LOCKS=0` を env に設定する」だけとし、
  `--no-optional-locks` flag の追加や status 呼出しの削除・置換はしない。
  **抑止は読取専用性の回復であって排他の緩和ではない** (mandatory lock には影響しない) ことを
  段 3 で敵対検証する。
- **(P3)** 正本へ node を足すとき `test_real_repo_serialization.py:37` の独立 golden も同時に更新する。
  独立 golden の意義 (conftest の写し間違い検出) は保つ。

## 不変条件

- `REAL_REPO_SERIAL_NODES` から node を**削らない**。追加のみ。
- 新設検査は履歴・commit 数に比例するコストをテスト経路へ入れない。
- 新設検査は positive control (漏れを人工的に作ると赤) を持つ。恒真な assert にしない。
- 受入全走の直列鎖が伸びること自体は失敗としない。

## 成果物の形

- `orchestrator/tests/conftest.py` の `REAL_REPO_SERIAL_NODES` 追記 + 除外註記の是正。
- `orchestrator/tests/test_real_repo_serialization.py` の独立 golden 追記 + 新設検査。
- `GIT_OPTIONAL_LOCKS=0` を設定する差分 (段 4 で確定した箇所のみ)。
- 変異 matrix、受入全走結果、worklog entry。

## 成果物影響 (DW-G05)

閉包漏れを放置すると、実 `external/ccbench` を読む node と patch を apply/revert する writer が
別 xdist worker へ散り、**source_digest / known-axes freeze が半書き換え状態の submodule を読んで
`ccbench_pin` や digest を誤った値で確定しうる。** これは certified 選択結果と proof chain の
参照値そのものを変える。`GIT_OPTIONAL_LOCKS` の穴は同じ競合面に index lock 書込を足す。

## 並列分割方針

段 2 = plan 1 本。段 3 = レンズ A (正しさ境界: 閉包の完全性と検査の恒真性) /
レンズ B (整合・実効性: 検査コスト、既存 golden との二重化、[T-991] の副作用) の 2 本。
段 5 = author 1 本 (編集面が conftest.py + test_real_repo_serialization.py + 少数の env 行で
分割の利得より競合の害が大きい)。
