# 段 1 brief — [T-248] Pegasus dispatch 経路に interpreter shim を配線する

対象 repo: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t248-dispatch-shim`
(branch `worktree-dev-wave-t248-dispatch-shim`、基準 `7b24f81`)

## 確定済みユーザー裁定 (worklog (94))

[T-248] 択 (a) 採用 — 「dispatch 側で 3.10 shim を配線し、孫プロセスの `python3` が計算ノード既定へ
戻る経路を塞ぐ。テスト側の個別対処は採らない」。理由は「同じ罠を今後どのテストでも踏むため一箇所で塞ぐ」。

## 段 1 前提実測 (親が実施、2026-08-01)

1. **裁定の症状は現ノード群で再現しない。** sanctioned 経路
   (`python3 tools/run_tests.py orchestrator/tests/test_t126_pegasus_tools.py -k
   test_m8b_post_qsub_prebinding_crash_never_uses_raw_stdout_authority`) で dispatch した結果は
   request `876518` / bnode002 / **1 passed / rc=0**。receipt の `result.interpreter` =
   `/usr/bin/python3.10`。**全走 baseline も緑**: request `876520` で
   **4709 passed / 19 skipped / rc=0** (3:39)。T-126 submitter 系の偽赤は再現しない。
2. **機序の再確認。** 計算ノードは `intelpython/2022.3.1` 既定ロードで PATH 先頭の `python3` が
   3.9.13 (docs/pegasus-runbook.md §4、F46)。しかし `_job_script` は
   `export PATH="$(dirname "$selected"):$PATH"` (`tools/pegasus/dispatch_compute.py:407`)、
   `_job_run` は `child_env["PATH"] = dirname(sys.executable) + PATH`
   (同 `:491-492`) で `/usr/bin` を前置するため、孫の `python3` は `/usr/bin/python3` に解決する。
   計算ノードの `/usr/bin/python3` は実測 3.10.12 (2026-07-19 insight、bnode097)。
3. **この PATH 前置は T-188 (`a34266d`) 由来で、closure wave の赤の観測時点より前から在る。**
   よって当時の赤を「3.9 fallback」で説明しきる根拠は無い (原因未確定として別 ID へ起票する)。
   さらに裁定の一次資料
   (`output/insights/2026-07-31_t126-f32-closure-wave/s6-ruling-package.md`) 自身の §2 は、
   同 wave の全走 `874775.nqsv` (bnode042) を **3710 passed / 19 skipped / overall rc=0** と
   記録しており、§6-3 の「この経路では偽赤になる」と整合しない。赤を観測した run の
   request ID・ノードは同文書に記録されていない (追跡不能)。
   本 wave の 2 回 (`876518` / `876520`) はいずれも **bnode002** であり、
   ノード群全体への一般化はしない。
4. **それでも構造的な穴は実在する。** 前置しているのは *dir* であって、孫が実際に起動する
   `python3` の版は probe でも `_job_run` でも**束縛されていない**。`dirname($selected)/python3` が
   古いノード画像では黙って fallback する。これは F46 の「記録するだけで発火しない値」family そのもの。

## scope

- **in:** `tools/pegasus/dispatch_compute.py` の子環境構築に interpreter shim dir を追加し、
  孫の `python3` を**検証済み interpreter そのもの**へ束縛する。作成不能・解決不一致は fail-closed。
  `orchestrator/tests/test_pegasus_dispatch_compute.py` に positive control と変異検出 node を追加。
- **out:** テスト側の個別 interpreter 明示 (裁定で不採用)、certification submitter
  (`submit_certify.sh` 等) の PATH 設計、closure wave の赤の原因究明 (別 ID)、
  `docs/pegasus-runbook.md` の環境事実の書き換え (事実は変わっていない)。

## 不変条件 (破ったら停止)

- 版数 gate の二層冗長 (probe と `_job_run` の `sys.version_info < (3, 10)`) を弱めない。
- 受理集合は「shim を張れなければ INFRA_RC(16) で fail-closed」方向にだけ変える。緩めない。
- `output/pegasus-dispatch/` は gitignored・FROZEN_MANIFEST 対象外 (実測確認済み) — 凍結 bytes は動かさない。
- 実装面は Codex `role=author` が書く。親は brief・裁定・統合・全走・記録・commit のみ。

## 成果物影響 (DW-G05)

実装しない場合、`/usr/bin/python3` が 3.10 未満のノードへ job が落ちた回で、孫プロセスだけが
未検証 interpreter で走る。台帳・worklog に記録する**受入全走の pass/fail 件数と rc** が
interpreter 差で変わり、certified 選択の根拠となる「緑で通した」という主張がノード依存になる。

## 分割方針

実装単位は 1 つ (`dispatch_compute.py` + 同名テストは所有が素集合にならない) → 段 5 は codex 1 子。
段 2 プラン 1 子、段 3 敵対 2 子、段 6 レビュー 2 子。

## provisional 裁定 (攻撃対象)

- **(P1)** 症状が再現しないのに実装を進めるのは正しい。裁定の対象は症状でなく「未束縛の
  interpreter 経路」であり、択 (a) の目的 (一箇所で塞ぐ) は構造的な穴に対して成立する。
- **(P2)** shim は `_job_run` 側 (Python) にだけ置き、bash `_job_script` には置かない。
  job script は `python3` を使わず選定 interpreter を直接 exec するため。
- **(P3)** shim は submission dir 配下の専用 dir に symlink `python3` → `Path(sys.executable).resolve()`
  として作る。wrapper script でなく symlink とし、`-I` / `-B` 等の起動 flag 意味論を変えない。
- **(P4)** 本 wave は軽量版にしない。受理集合が変わり正しさ防壁 (interpreter 版束縛) に触るため、
  `DW-C00` の carve-out に従い段 2・3 と段 6 review 子を省かない。
- **(P5)** positive control は環境非依存に構成する。同一 dir に新しい `python3.10` と古い `python3` を
  置いた fake PATH で子環境を組ませ、`python3` が選定 interpreter へ解決することを課す
  (現行コードでは赤、fix 後は緑)。実ノードの緑再現に依存しない。

## 受入・実測環境

Pegasus gen_S 計算ノード (sanctioned 経路 `tools/run_tests.py` → `dispatch_compute`)。
ログインノードでの pytest 直叩きは hook が機械拒否する (実測)。
