---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t316-semantic-gate-impl
seq: 1
title: [T-316] 意味 gate を実装した — 主張を「測定済み 4 種の受理集合縮小」に限定し、案 2 の build 防壁本体は裁定へ返した (コード + docs、branch worktree-dev-wave-t316-semantic-gate-impl)
---

## 本文

- **ユーザー指示 (2026-08-11、本 wave の command 引数):** [T-316] を裁定 案 2 で実装し、
  計測段 (`dev-wave-t316-sandbox-measure`) の判定材料を入力に coder/auditor 出力への意味 gate を
  実装して、valid-schema な注入と `diff_digest` echo が通らないことをテストで固定する。
- **段 3 の 2 レンズがいずれも NO-GO を出し、独立に同じ核心を突いた。** 有限 lexical な効果
  denylist は、裁定 案 2 が指定した二択 (source の DSL/IR 化 / build 出力 copy-out の厳格化) の
  **どちらでもない第 3 の選択肢**であり、build 防壁として採るならユーザー裁定へ返すべきである。
  親はこれを real と裁定し、**実装はするが主張を縮小する**方針を採った (詳細は
  {{D:coder-hole-effect-gate}} 決定 (3))。案 2 の build 防壁本体の択一は本エントリの
  「次の一手」で裁定へ返す。
- **親 brief の 2 主張が段 3 で refute され、撤回した。** (i)「W-2 がなければ auditor を騙すと
  W-1 も迂回できる」— 実コードは変更前から machine reject を auditor より先に返しており、
  W-2 は新規の安全性差分ではない (factoring と docstring 是正へ格下げ)。
  (ii)「閉じた効果 denylist」— 閉じていない。残余は決定 (6) に列挙した。
  親の実測記述も限定した: 段 1 probe は共有 seam の probe であって driver E2E ではなく、
  「repo に効果検査が不在」は正しくは「coder-hole admission / DiffQuarantine 層に不在」である。
- **段 6 の敵対レビュー 2 本も NO-GO** (blocker 1 + must-fix 8 + nit 1)。閉じた主なものは、
  非ゼロ浮動小数・char literal の無退出 loop (`while (1.0) {}` 等) で gate が発火しない blocker、
  入力長上限が無く括弧除去が二乗時間になる欠陥、critic の「計算のみ」という affirmative
  security claim、auditor 配線の変異が behavioral kill になっていない欠陥、V-8 未閉鎖層の
  docstring 未列挙、S6 provenance の非反射未検査、`python -O` で消える module assert。
  焦点再レビューが 10 所見すべてを独立に `closed` と判定した。
- **焦点再レビューが新しい blocker を 1 件出した。** 非整数 `coder.value` (例 20.5) は
  `assert_value_literal_consistent` を通る一方、genome は `int()` で 20 を記録する。
  実際に走る binary と台帳の genome が別値になる帰属の穴で、**本 wave の差分が作ったものではなく
  既存の欠陥**である。scope 外として実装せず、次の一手へ起票した。
- **変異は 3 走した。走 1 と走 2 は erratum として残す。** 走 1 (spec v1) は baseline 緑・
  SURVIVED 0・PARSE_ERROR 0 で 12 件すべてが赤を出したが、親の静的推定した期待 node が
  seam・critic・非反射投影への波及を取りこぼしており KILLED 2 / MISMATCH 10 になった。
  走 2 (spec v2、実測 node) は M8 の実測集合に `@real-repo` suffix 付きの非 collectable node が
  混ざり、collection 事前検査で停止した。M8 の変異 (旧 verdict 分岐へ戻す) は digest 検査の
  実行順まで変える**過剰決定**だったため、`DW-M03` の第一選択どおり単一理由へ差し替えた
  (呼び出しと sink 再検証は残し veto の効果だけを落とす)。
- **段 4 で登録した M5「無条件 loop 判定の無効化」も再照準した。** 殺す範囲が広すぎて単一理由に
  絞れないため、M5 (非ゼロ浮動小数枝) と M5b (char literal 枝) に分けた。これは段 6 で塞いだ
  blocker をそのまま pin する。M4 の category も誤登録だった (`read` は sleep-block ではなく
  file-stdio) — 焦点再レビューが独立に指摘し、spec で是正した。
- **`M7` / `M9` / `M11` は受理集合を変えない診断 pin である。** `DW-M08` に従い、kill ではなく
  diagnostic sensitivity pin として別枠で読む (M7 = scanner 入力の byte 束縛、M9 = 例外への
  bytes 反射、M11 = reject subtype 文字列の drift)。
- **背景 job の完了通知が 4 回、実体より先に届いた。** いずれも 3 点照合 (成果物実在 + `.done` +
  producer 死) で未完了と判定し、何もせず待ち手を張り直した。うち 2 回は codex 子
  (段 3 レンズ A、段 6 レビュー 1)、2 回は変異 harness である。harness 側は `.done` を作らない
  ため、pid を直接見るブロッキング待ちへ切り替えた。
- **`tools/dev_wave_codex.py` の投入で artifact 名を 2 度捨てた。** `--artifact-root` には
  wave 名 dir の**親**を渡す必要があり、かつ tool は `<root>/<wave>/<job-id>` を自分で作らない。
  知らずに投入すると codex は起動せず rc=2 の `.done` だけが残り、`DW-O01` の「既存 `.done` は
  再利用せず再投入を止める」規律により名前を捨てることになる。段 8 の改善候補とした。
- **受入全走は 8562 passed / 20 skipped / 557.26 秒 / rc=0** (計算ノード、request `902242.nqsv`、
  受入 lease 取得後に main を取り込んだ tip `31ea06c8`)。**焦点走で赤だった
  `test_checkpoint_direction_and_magnitude_domains_match_role_policy` は全走では緑**であり、
  差分外・実行経路依存という帰属が裏付けられた。本記録を足した最終 tip でも同じ受入を再走した。
- **変異 runner の範囲は既知赤 1 node を deselect して baseline を緑にした。**
  `test_p3_s4_loop.py::test_checkpoint_direction_and_magnitude_domains_match_role_policy` は
  `from codex_roles import policy` を使い、`orchestrator/` が `sys.path` に入る実行でしか解決
  しない。本 wave の差分は同 test も `codex_roles` も触っていない。焦点再レビューの指摘どおり
  「subset 固有」ではなく **import-path / 実行順依存**であり、別途起票した。

## 次の一手差分

### 更新

- [T-316] **P1・実装済み範囲と、返す裁定 R-1**: coder hole の有限 lexical 効果 gate
  (`coder_effect_gate.py`) と auditor の deny-only factoring を land した。**測定済み 4 種
  (`std::system` / `execl` / `std::ofstream` / `while(true){}`) に対する受理集合の縮小である**。
  **R-1 (要裁定)**: 裁定 案 2 の build 段防壁として (a) source の DSL/IR 化、
  (b) build 出力 copy-out の厳格化 (R3-6 の must-fix そのもの)、
  (c) 本 wave の lexical 効果 gate をもって充当、のいずれを採るか。
  **親の推奨は (b) を次 wave で実装し (c) を defense-in-depth として併置する** — (a) は R1 が
  sort について明示的に却下しており、backoff/trigger だけに入れても sort の raw 経路が残る。
  (b) は sandbox blocker に依存せず今すぐ実装できる。
  実装段の残り blocker ([T-184] canonical stage matrix 未発行、R3-3〜R3-9、R2-b 独立 oracle 本体)
  は**変わらず**。正本 = `output/insights/2026-08-11_t316-semantic-gate-impl/package.md`
  base: 29751dc729c7ee334629cfaf62ca8a33f21453d44bf4260edb491126d937bd50

### 新規

- {{T:t316-coder-derived-bypass}} **P2・[T-316] 由来 (要裁定)**: `quarantine()` を通らない
  coder-derived build 経路 (`p3_s4_red.py`、手動 patch + `--allow-coder-derived-build`、
  直接 `buildcache` caller、`s5_permutation_coverage` の直接 CMake build、shell materializer と
  任意 binary path) を admission 外の「非認証成果物」として機械隔離するか、残余のまま台帳に
  明示するか。段 3 レンズ A が実コードで列挙した。
- {{T:t316-gate-receipt-binding}} **P2・[T-316] 由来 (要裁定)**: cache / WAL / COMMIT / freeze に
  semantic gate の receipt を束縛するか。現状は同じ source bytes と admission であれば
  scanner を経ずに build された binary が cache hit で certified 経路に入りうる。R3-3 / R3-9 依存。
- {{T:t316-forbidden-identifiers-vacuous}} **P3・[T-316] 由来 (要裁定)**:
  `p3_autonomous_workload_trial._preview` の `forbidden_identifiers` は常に `[]` を返し、
  consumer (`autonomous_trial_completeness`) はそれを security evidence として読む。**恒偽**である。
  段 6 レビューの推奨は producer / consumer / schema からの削除 (trigger 軸は canonical IR のため)。
- {{T:backoff-value-truncation}} **P2・[T-316] 由来**: 非整数 `coder.value` (例 20.5) は
  `assert_value_literal_consistent` を通るが genome は `int()` で 20 を記録する。実行 binary と
  台帳 genome が別値になる帰属の穴。既存欠陥で本 wave の差分外。role policy は 1..1000 の
  `int|float` を許可している。
- {{T:codex-roles-import-path}} **P3・[T-316] 由来**:
  `test_p3_s4_loop.py::test_checkpoint_direction_and_magnitude_domains_match_role_policy` は
  `from codex_roles import policy` を top-level で使い、`orchestrator/` が `sys.path` に入る
  実行でしか解決しない。受入全走では緑だが、file 単位・subset 実行では赤になる。
  受入結果の緑赤が ambient な `sys.path` に依存している。
