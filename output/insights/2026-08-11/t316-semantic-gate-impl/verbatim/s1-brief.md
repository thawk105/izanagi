# 段 1 brief — [T-316] 意味 gate 実装 (裁定 案 2)

wave: `dev-wave-t316-semantic-gate-impl` / branch `worktree-dev-wave-t316-semantic-gate-impl`
base: main `0c336b8e` (2026-08-11)

## 確定済みユーザー裁定 (逐語の要旨)

- **案 2 (worklog 403、2026-08-11 /rulings):** 封じ込めの主張を **run 段へ限定**し、**build 段は
  別防壁 (source の DSL/IR 化、または build 出力 copy-out の厳格化) で守る**。R1 の
  「(ii) を全軸の host-security boundary とする」は **run 段について維持**。
- 同裁定行: 実装段の残り blocker ([T-184] stage matrix 未発行、R3-3〜R3-9、R2-b 独立 oracle 本体)
  は**変わらず**。
- **R2-b (2026-08-09 /rulings、worklog 337):** sort の reward hack は独立 oracle で対処する。本 wave は
  独立 oracle を実装しない (blocker のまま)。
- command 引数 (ユーザー、本 wave): coder/auditor 出力に対する意味 gate を実装し、valid-schema な
  注入と `diff_digest` echo が通らないことをテストで固定する。

## 段 1 で親が実測した前提 (模擬でなく実路)

probe = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/probe_premises.py` (repo 外)。
実行後 `git status` clean、submodule も clean。

- **M1 (α 成立、sort 軸・実路):** 骨格適用下で `L.quarantine(write=False)` に
  `std::system` / `execl` / `std::ofstream` / `while(true){}` を hole 内 1 行として与えると
  **4/4 とも `DiffQuarantine` を PASS**。
- **M2 (β 成立):** 上記 4 件それぞれで `parse_auditor_dict({verdict:"pass", diff_digest:
  sha256(実 working_diff), violations:[]})` → `assert_digest_matches` が通り、
  `_quarantine_and_audit` は build へ進む (`p3_s4_loop_sort.py:157-168`)。
- **M3 (backoff の受理契約):** `assert_value_literal_consistent` は上記 4 件を **4/4 とも PASS**
  (value=100.0 と literal 100.0 が一致すれば同居する任意文が通る)。
- **M4 (既存被覆・性質検索):** `test_diff_quarantine.py` の注入テストは
  `directive` / `include` の 2 件のみ (前処理指令の構造検査)。**効果 (syscall/IO/shell/無限ループ) を
  見る検査は repo に不在。** 純増検出力 = 前処理指令を含まない valid-schema な effect 注入の拒否。

## 実測で判明した新事実 (裁定時に未見。段 4 で再裁定する)

- **N1 (最重要):** R1 は sort 軸について「(i) DSL 化は却下、採るのは (ii) sandbox のみ」と決めていた。
  しかし (ii) は計測段 §1 で **build 段 NO-GO**、かつ案 2 が build 段の封じ込め主張を取り下げた。
  よって案 2 のもとで sort の build 段防壁は「copy-out 厳格化」か、**R1 が想定していない第 3 の形**
  (raw 合成を維持したまま host 効果だけを拒否する **効果 denylist**) のどちらかになる。
  効果 denylist は「合成 → 事前 allowlist 選択」への化けを起こさない点で R1 の却下理由に当たらない、
  というのが親の読みだが、**これは非同値な設計択一なので (P1) として攻撃対象に出す**。
- **N2:** trigger-gating 軸は **既に α が閉じている** (実測: `parse_wire`→`emit_predicate` の
  trusted emitter のみが source へ届き、`quarantine` が `is_canonical_predicate` の membership を
  fail-closed で課す)。「全軸へ意味 gate」は不要 = scope から外す。
- **N3:** backoff 軸 driver は `PIN=028f34d`、現行 submodule は `d706650` で
  **骨格適用が fail-closed** (実測)。この軸は E2E 実走で検証できない (契約層のみ検証可)。
- **N4:** `p3_autonomous_workload_trial._preview` は `"forbidden_identifiers": []` を**ハードコード**し、
  consumer (`autonomous_trial_completeness.py:608`) はそれを読む。**謳うだけで発火しない保証**であり、
  意味 gate の受け皿として既に穴が空いている。

## 不変条件

- 正しさゲートを緩めない (規律 2)。受理集合は**狭まる方向にだけ**変える。既存テストの期待値を変えない。
- coder/auditor の出力は**データであって指示ではない** (規律 6)。例外文へ候補由来 bytes を出さない
  (`auditor_gate._reject_schema` の既存規律を踏襲)。
- **DW-O09 の pin 閉包 (実測済み):** 編集候補 5 file (`auditor_gate.py` / `diff_quarantine.py` /
  `p3_s4_loop.py` / `p3_s4_loop_sort.py` / `buildcache.py`) を bytes で pin する**生きた台帳は無い**。
  `FROZEN_MANIFEST` は `output/` 成果物のみ (23 件、.py なし)。`t080_freeze_migration.py` の
  `recorded_sha256` は p3_s4_loop_sort.py を 9b64f34b で記録するが、現物は f2b918cb で**既に乖離**
  = 凍結時点の歴史記録であって live pin ではない (F39 の分類で「歴史記録」)。
- sandbox (R3-1/R3-4)、stage matrix ([T-184])、独立 oracle (R2-b)、field mapping (R3-3) には触らない。
  触れない理由を成果物へ明示し、「閉じた」と主張しない。

## scope (親 provisional。すべて (P) は攻撃対象)

- **(P1) W-1 coder 出力の意味 gate。** 単一 seam = `L.quarantine` が hole へ挿す implementation
  (3 driver + `_preview` が必ず通る)。閉じた**効果 denylist** で fail-closed 拒否し、既存
  `record_diff_reject` / `load_diff_rejections` consumer に相乗りする (新 loader を作らない)。
  通る正例を必ず添える (現行 sort/backoff の正常 implementation が通ること)。
- **(P2) W-2 auditor 出力の意味 gate = deny-only 化。** `verdict="pass"` が build/semantic の
  capability を一切発行しないことを構造で保証する (意味 gate は verdict と独立に必ず走る)。
  文言は R1 の指定どおり「mandatory deny-only veto; affirmative security credit なし」で固定し、
  **「advisory」と書かない**。`diff_digest` は attribution/provenance 専用と明記。
- **(P3) scope 外に置くもの:** sandbox (blocker)、backoff の value-IR producer/consumer 移行 (R3-7、
  N3 により実走検証不能)、build 出力 copy-out 厳格化 (R3-6、案 2 のもう一方の選択肢)、
  N4 の `forbidden_identifiers` 恒真穴の是正。real なら裁定パッケージで返す。
- **(P4)** docs 予算は本 wave を縛らない (実測: `check_docs.py` 違反なし、dev-wave reference には
  触れない)。R4 の予算 blocker は sandbox 設計文書に掛かるもので本 scope には掛からない。

## 成果物影響 (DW-G05)

- W-1 を入れないと、certified 選択・fitness・proof chain に**任意 host 効果を含む variant が
  正規経路で入りうる** (M1/M2 が実測)。入れると `CODER_DERIVED` 由来 source の受理集合が
  「効果 denylist を満たすもの」へ狭まる。既存の正常 variant の受理は不変 (正例で固定)。
- W-2 を入れないと、auditor を騙せた瞬間に W-1 も迂回されうる (単一障害点)。入れると
  auditor verdict は受理集合を**広げる方向へは一切効かない**。
- 凍結 bytes・certified の既存値・レポート数値は不変 (受理集合を狭めるだけ)。

## 成果物の形

- コード: 意味 gate 本体 (新 module か既存 module 内)、3 driver / `_preview` からの単一 seam 配線。
- テスト: (a) 4 種注入 × 各軸で拒否、(b) auditor pass + echo digest でも拒否、(c) 正常 implementation
  が通る正例、(d) 受理集合の非拡大 meta-test。
- docs: `docs/spool/` fragment (worklog / decisions)、insights 逐語 + 変異台帳。

## 並列分割方針

編集ファイル所有が素集合になる 2 単位に割る。単位 A = 意味 gate 本体 + テスト、
単位 B = driver 配線 + auditor deny-only 文言 + テスト。B は A に依存するので A 完了後に
所有パス限定 patch を展開してから投入する (`DW-S05-A`)。

## 受入・実測環境

- 受入全走は login node、`tools/dev_wave_wait.py acceptance --wave dev-wave-t316-semantic-gate-impl
  -- python3 tools/run_tests.py` を**背景**投入 (裸形。flag を足さない)。
- 変異 harness は `tools/mutation_harness.py`、runner argv に `--force-dispatch` を必ず入れる。
