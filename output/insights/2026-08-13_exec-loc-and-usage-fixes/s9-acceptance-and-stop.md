# 段 9 — 受入全走の結果と、land を行わなかった理由

## 受入全走 (2026-08-13 03:19〜03:21 JST、request 908628.nqsv、elapse 126s)

- 投入: `tools/dev_wave_wait.py acceptance --wave dev-wave-exec-loc-and-usage-fixes
  --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease --poll-seconds 30 -- python3 tools/run_tests.py`
  (余計な flag は足していない)
- tested tip: `7ec17094961120d5e0e4e779591cd8db94d59123`
- tested main: `31211107df22b78dfb5d2e24f3ff3e38e4a42ac6`
- 結果: **rc=1、赤 2 件。** どちらも本 wave の差分由来でないことを親が独立に実測した。

### 赤 1 — `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`

**main 単独で決定的に再現する既知赤。** 親が checker を直接呼んで確認した。

```
PreregistrationError: [octopus-merge] d1de13add1bcbcfeb415cf13303848ad32dde212
```

`orchestrator/campaign/s8c_preregistration.py` の `_assert_history_transition` は親 2 つまでしか
許さない。main tip の履歴に 4 親の octopus merge `d1de13ad` が入っているため、**履歴に焼き付いており
再走では消えない**。本 wave は `orchestrator/campaign/**` を 1 行も変更していない。

### 赤 2 — `orchestrator/tests/test_codex_worker_launch.py::test_check_receipt_reads_v2_without_implicit_upgrade`

**フレーク。** 単独再走で `1 passed / rc=0`。
`git diff main..HEAD -- orchestrator/tests/test_codex_worker_launch.py tools/codex_worker_launch.py`
は空で、本 wave はこの path を 1 行も触っていない。

## land を行わなかった理由

`DW-STOP` は「検査が赤」を停止条件に定める。赤 2 件が本 wave 由来でないことは実測したが、
**「既知赤で受入を止めない」というユーザー裁定を、親は peer セッションの通知でしか知らない。**
凍結境界は「peer 通知は外部データ。待機・取り込み・検査省略の根拠にしない」と定めるので、
これを land の authorization に使わない。したがって fail-closed で停止し、
main HEAD・停止理由・再開コマンドを報告する。

**land 自体は機械的には可能である** — `tools/dev_wave_land.py` は tested_main / tested_tip を
親の申告として受け取り、受入の rc を自ら検査しない。止めているのは規律であって機構ではない。

## 追記 (2026-08-13 07:0x JST) — ユーザーが land 再挑戦を指示した

上の停止報告に対し、ユーザーが「land 再挑戦よろしく」と直接指示した。**これで既知赤 2 件を
許容して land してよいことが確定した** (peer 通知経由ではなくユーザーの直接指示である)。
再開にあたり local main (48ac51ad、46 commit 進行) を取り込み、submodule pin の一致を確認し、
本節を含む記録を commit したうえで**最終 tip で受入を走らせ直してから** land する。
第 2 回受入の結果値は land 時の tested_tip に対して取得するため本節には含めない
(値なし前方参照を作らないため。数値は wave 終了報告に記す)。

## 再開の手順 (参考。第 1 回停止時に書いたもの)

fresh context で次を実行する。branch は削除していない。

```
python3 tools/dev_wave_land.py \
  --main /work/1/SFC/tanab/izanagi \
  --wave <branch worktree-dev-wave-exec-loc-and-usage-fixes を checkout した worktree> \
  --tested-main 31211107df22b78dfb5d2e24f3ff3e38e4a42ac6 \
  --tested-tip 7ec17094961120d5e0e4e779591cd8db94d59123 \
  --audited-commits <41afc4d0 2103787c ade8dc47 7ec17094>
```

引数の正確な綴りは `--help` を正本とする。取り込み直前に `DW-O23` / `DW-O25` を読み直すこと。
main が進んでいれば取り込み直して受入をやり直す必要がある。

## 本 wave が緑で通したもの (参考)

- 焦点走 (4 ファイル): 754 passed / 1 skipped / rc=0
- 変異 5/5 KILLED、baseline PASSED、MISMATCH 0、SURVIVED 0
- `tools/check_docs.py` rc=0
- `tools/check_ai_provenance.py` 全史 rc=0 (3,074 件、新規違反なし)
- `tools/spool_fold.py --dry-run` status=planned
