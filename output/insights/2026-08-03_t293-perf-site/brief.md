# 段 1 brief — [T-293] 共有 policy `perf_candidates` の計算ノード実測

基準: commit `1a3604b` / branch `worktree-dev-wave-t293-perf-site` (clean)。
受入・実測環境: Pegasus (login = pegasus02、実測 = gen_S 計算ノード 1 node)。

## scope

- **やること:** T-293 の次の一手「計算ノード側の実測がまだ無いので、まずそれを取る」を実行する。
  計算ノードで、committed policy の `perf_candidates` 2 本が実在し機能するかを**実コード経由**で測る。
- **実装面は probe 1 式のみ** (`.pbs` + 測定本体)。既存コード・policy・test・gate は 1 byte も変えない。
- **やらないこと (すべて受理集合の変更 = D96 手続 → ユーザー裁定へ返す):** `perf_candidates` の値変更、
  `submission.py` の共有値読みの付け替え、`REQUIRED_CODE_IDENTITY_PATHS` の整理、gate の新設。

## 確定済みユーザー裁定 (前提)

- D115 決定 (2)/(5): 共有・サイト値は移さず、共有 file が凍結されている残余は D96 手続へ返す。
- D96: 受理集合を変える改修は、設計判断の記録と境界テストの同時更新を義務とする。
- runbook §7/§8: 重い処理は計算ノードで行う。§8 F49 (ii): 背景 job セッションからの `qsub` は可、
  投入直後に 3 点の有効性検査 (計算ノード側 marker の実在 / `qstat` 可視 / 会計痕跡) を行う。

## 承認済み裁定の前提を覆す新事実 (段 4 で再裁定する)

- **N1 — 「候補 2 本は存在しない」はサイト依存の主張である。** 計算ノードの旧実測
  (`output/env/pegasus/debug/perf-0_867873.nqsv.log`) では `/usr/lib/linux-tools/` が
  `5.15.0-100-generic` と `5.15.0-135-generic` の**2 つだけ**で、policy の候補 2 本は**実在し**、
  `perf --version` と `perf stat` も成功していた。login (pegasus02、本日実測) は
  `101/136/173` で候補は不在。**両サイトの版集合は互いに素**である。
- **N2 — login 側は perf へ到達する前に落ちる。** `prepare_toolchain` の解決順は
  python → cc(`gcc-13`) → cxx(`g++-13`) → cmake → perf であり、login に `gcc-13` は無い。
  T-293 の「`submission.py` はこの候補列から perf を解決し、機能しなければ fail-closed する」は、
  login ノードでは**より手前の cc で** fail する。
- **N3 — 本質は「stale な値」ではなく「サイト不一致」である。** `submit_t126_qualification.sh:363` は
  **login ノード**で `prepare_toolchain` を呼び、`t126_qualification.sh:577-597` は
  **計算ノード**で同じ候補列を解決する。値ではなく、前処理の実行サイトが問題でありうる。

## 不変条件

- **I1:** `tools/pegasus/policy.json` の sha256 = `b1c42e49…961ac` を wave 終端まで不変に保つ (段ごとに照合)。
- **I2:** `REQUIRED_CODE_IDENTITY_PATHS` / `FROZEN_MANIFEST` / `tools/pegasus/policies/registry_v1.json` を変更しない。
- **I3:** test・gate を新設・改変しない (条件 13 は不発火のまま維持する)。
- **I4:** probe は read-only 測定に限り、tracked file を変異させず、書き込みは新規 output 配下だけとする。
- **I5:** login ノードで perf を実行しない (`guard_bash.py` の拒否を迂回しない)。

## provisional 裁定 (攻撃対象)

- **(P1)** probe は**実コードを呼ぶ**。(a) `qualification.submission.prepare_toolchain(policy)` を
  そのまま呼んで失敗段を記録し、(b) 同 module の `_executable("perf", policy["perf_candidates"])` を
  直接呼んで path / sha256 / version を得る。(a) は cc で落ちうるので (b) を併走させる。
  smoke 相当の argv 再現だけは模擬であり、**模擬と明記して裁定根拠の主軸にしない** (F29)。
- **(P2)** 投入は gen_S・`-b 1`・`elapstim_req=00:10:00`。背景 job セッションの Bash から `qsub` し、
  F49 (ii) の 3 点検査を行う。計算ノード側が書いた marker の実在で (a) を確かめる。

## 成果物の形

- `output/env/pegasus/t293-perf-site/<JOB_TAG>/` に probe の JSON と raw ログ (計算ノードが書く)。
- `output/insights/2026-08-03_t293-perf-site/` に README + 逐語 + 裁定パッケージ。
- `docs/spool/` の fragment として worklog 1 件 (必要なら decisions / failures)。canonical 台帳は段 9 の land が書く。

## DW-G05 成果物影響

- **実測しない場合:** T-293 が「stale な値」という誤った前提のまま残り、恒久対応が値の書換え方向へ進む。
  policy bytes は identity (`REQUIRED_CODE_IDENTITY_PATHS`) に入るため、**不要な受理集合変更を
  ユーザーが承認しかねない** — certified 証拠の series identity が変わる。
- **probe を書かない場合:** 計算ノードの現況が不明のまま裁定できず、T-293 が無期限に開いたままになる。

## 段 6 レビューによる brief 自身の是正 (原文は上に残す)

敵対レビュー 2 本が親 brief の記述を攻撃し、親は次を **real** と裁定した。原文を書き換えず、
ここに是正を追記する (DW-O12: 裁定予定でなく実際に行った手順を残す)。

- **(P2) の「計算ノード側 marker の実在で有効性を確かめる」は誤りだった** (A 所見 3 / B2)。
  marker は「計算ノードで shell が開始した」証拠にすぎず、`prepare_toolchain` が呼ばれた証拠にならない。
  marker 直後に job が kill されても marker は残る。**測定の受理述語は
  `s4-adjudication.md` の 5 条件へ差し替えた**。marker は F49 (ii) (a) の
  「計算ノード側が書いたファイルの実在」という限定的な役割にのみ使う。
- **scope の「候補 2 本が実在し機能するか」を、実装は満たしていなかった** (A 所見 2)。
  `_executable` は最初に解決できた候補で `break` するため、第 2 候補の機能性は未測定だった。
  fix F-2 で候補ごとに独立測定する形へ変えた。
- **N3 の `real (仮説)` は裁定として不成立** (B5)。`gcc-13` / `g++-13` が両サイトに無いなら、
  perf の site を是正しても qualification は cc で停止する。N3 は**未裁定へ差し戻した**。
- **N1 の射程を 1 標本へ限定した** (B6)。旧証拠は 2026-07-19 と 2026-07-29 の観測であり、
  今日の probe も 1 node の 1 標本である。gen_S 全 bnode へ一般化しない。
- **I4 / I5 を強化した。** 出力は create-only とし symlink を追わない (B2)。
  ログインノードでの probe 実行は**行わない** — 候補が解決すれば perf が login で走るため (B1)。

## 分割方針と軽量版根拠

- 実装子 1 (Codex `role=author`): probe 一式。レビュー子 1 (read-only Codex): probe の妥当性。親: 投入・回収・記録・land。
- 正しさ防壁に触らず、受理集合を変えず、設計択一は wave 内で決めない (裁定へ返す) ため **DW-C00 の既定軽量版**とし、
  段 2・3 を省く。実装面があるため段 5 の Codex author は省略不可。計算ノード往復を無駄にしないため
  段 6 のレビューは 1 本だけ残す。
