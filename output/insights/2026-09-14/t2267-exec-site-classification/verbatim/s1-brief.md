# 段 1 brief — [T-2267] 実行場所分類の対象・入力・実行条件を確認し、実測して記録する

## 研究前進

`docs/pegasus-runbook.md` §7.0 は「未実測 = `unknown` = `dispatch-required` と同じに扱う」で運用する。
T-2267 の対象 `tools/t2216_backoff_walk_model.py` (適応 backoff の歩行 model、`REPETITIONS=8`・
`DURATION_US=3_000_000`、参考実績で約 733 秒) は未実測のままで、再走のたびに計算ノードへの
dispatch 往復が要る。この実行体は T-2562 (tail report v1→v2 移行) と論文 §4-bis の再計算が呼ぶ。
本 wave は分類の 3 条件を現物で確定し、**既存の認可された経路で測れる範囲を測って記録する**。
完了判定 = §7.0 の記録 7 項目 (commit / argv / 入力の総 bytes と件数 / `memory.max` / 観測ピーク /
繰り返し数 / 測定日) が埋まる、または埋まらない項目ごとに不足理由が実測で特定されること。

## 確定済みユーザー裁定 (逐語は `verbatim/`)

- **D1938** (`verbatim/d1938.md`): 人間専任を解除し AI 担当。既存の上限付き実行経路を優先。
  専用 cgroup の charged memory、記録条件、未実測は `unknown`、hook 拒否を迂回しない、
  共有 cgroup の差分と per-process RSS を正式分類の根拠へ昇格させない、新たな承認儀式を設けない。
- **D180** (`verbatim/d180.md`): 測定専用 bounded surface の**即時新設は却下済み** (族再設計へ同梱)。
- **D210** (`verbatim/d210.md`): 上限付き実行は entry point の内側に閉じ、**汎用 launcher を作らない**。
  段 3 の敵対 2 本が trampoline を示して `tools/pegasus/local_run.py` を設計ごと取り下げた。
- **§7.0** (`verbatim/runbook-7.0.md`): 実行可能な経路が無ければ、その不足を AI の実装課題として特定する。

## 親が実測した事実 (段 3 はこれ自体も攻撃対象にする)

1. `hooks/guard_bash.py:1191` が LOGIN/SUSPECT で raw `systemd-run` を無条件拒否する。
   本 session の Bash tool から `systemd-run --user --scope -q --unit=izmeas-probe-$$ -p
   MemoryAccounting=yes -- /bin/true` を投げて拒否文言を実測した。
2. `tools/run_tests.py:1895 _scope_command` と `tools/check_ai_provenance.py:2731 _scope_command` は
   どちらも `sys.executable` + **自分自身の script** を再 exec する形。前者の `script_path`
   キーワード引数は repo 内に呼び手がゼロ (`grep -rn "script_path" tools/run_tests.py` で 2 hit、
   いずれも定義側)。`tools/mutation_fanout.py:1360` も自己再 exec 型で、D433 が本走不能を確定済み。
3. 対象自身は hook を通る — `python3 tools/t2216_backoff_walk_model.py --help` が rc=0。
   registry 未登録かつ `tools/pegasus/` 外なので拒否射程の外。
4. 入力の同定: `backoff_copy` = `external/ccbench/include/backoff.hh`、実 sha256 は
   `3e9f548507200532c79b14b94389abbfd4f87c7c03addde0099740f2df3d8cd7` で pin と一致。
   `--tail-json` 3 本は `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/` に実在
   (write-heavy 8359 / balanced 8342 / read-heavy 8382 bytes)。
5. 凍結 `measured.json` (`MEASURED_INPUT_SHA256 = f46cebdd…`) は **両 repo に実在しない**。
   `izanagi-job-evidence` 配下の全 JSON 846 件と、`/work/1/SFC/tanab/izanagi` 配下の
   `.git` を除く 20 MB 未満の全 JSON を sha256 で走査し、一致 0 件 (走査完了 rc=0)。
   `build_document` は `_sha256(measured_path) != MEASURED_INPUT_SHA256` で fail-closed に落ちるため、
   **凍結入力・本走 argv の実行そのものが現時点で再現不能**である。これは経路不足とは独立の第 2 の障害。

## (P1) 親の provisional 裁定 — 段 3 の主攻撃対象

**AI が使える login 側 dedicated-scope 実行面は存在しない。** よって凍結入力・本走 argv での
login cgroup 観測ピークは現時点で測れない。取りうる案は
(a) 既存経路で測れる形を洗い直す、(b) 不足を実装課題として特定し裁定パッケージで返す、
(c) 対象限定の最小実行経路を本 wave で作る。**親の既定は (b)** — (c) は D180 の却下と D210 の
「汎用 launcher を作らない」に正面から当たり、受理集合に触るため親裁量で実施しない。

## scope

- in: 対象・入力・実行条件の現物確定。既存の認可された経路で取れる観測ピークの実測と記録。
  測れない項目の不足理由の特定と、実装課題としての仕様化。記録 (insight / worklog / decisions)。
- out: 汎用 measurement 基盤・新しい bounded launcher・承認儀式の新設。registry の class 昇格。
  admission registry の族再設計。仮想リスク向けの gate・検査・台帳・一般化の追加。

## 不変条件

- 規律 2 を緩めない。未実測は `unknown` のまま。担当変更だけで class を軽い側へ倒さない。
- hook 拒否を迂回しない (別綴り・Codex 子・subprocess 経由の抜け道を使わない)。
- 共有 cgroup の差分と per-process RSS を正式分類の根拠にしない。
- 凍結 pin (`BACKOFF_COPY_SHA256` / `MEASURED_INPUT_SHA256` / `SOURCE_PIN`) を書き換えない。
- `tools/pegasus/admission_registry.json` と runbook の投影表は (path, class, evidence) の
  集合完全一致を `tools/check_docs.py` が検査する。片側だけ編集しない。

## 成果物の形

1. `output/insights/2026-09-14_t2267-exec-site-classification/README.md` — 対象・入力・実行条件の
   確定表、実測した観測ピーク (取れた範囲)、取れなかった項目と不足理由、逐語 log。
2. `docs/spool/` fragment — worklog 1 件、decisions 1 件 (経路不足の確定と実装課題の仕様)、
   必要なら failures 1 件。
3. 実装面の差分は既定ゼロ (docs-only)。段 4 で (c) を採る裁定になった場合だけ実装子を立てる。

## 分割方針

段 2 は plan 子 1 本。段 3 は敵対 2 レンズ並列 —
レンズ A「経路の不在という親の断定を壊す」(見落とした認可経路・既存 CLI seam・compute 側の
per-job cgroup の実在)、レンズ B「記録と分類の意味を壊す」(測れた値の射程の誇張、
未実測の軽い側への滑り、投影表と正本の不整合、入力同定の誤り)。
