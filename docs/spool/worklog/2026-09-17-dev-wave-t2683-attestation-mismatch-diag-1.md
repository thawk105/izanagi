---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2683-attestation-mismatch-diag
seq: 1
title: [T-2683] T126 attestation の不一致で比較行を失敗時の診断 sidecar へ残した (コード + テスト + docs、branch worktree-dev-wave-t2683-attestation-mismatch-diag、変異 matrix = baseline PASSED・境界 3/3 KILLED + 診断 pin 8/8 赤・等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「[T-2683] attestation 不一致の内訳を失敗時の診断へ載せる (第 20 回 /rulings 項 14、着手時に main の
  D 番号を確認): 既存 `env_attestation.compare_profiles` が返す比較行 (field / expected / observed / verdict) を、呼び手
  (`execution_guard.py:612`、`t126_driver.py:459`) が捨てずに失敗時の診断 sidecar へ載せる局所修正。新しい gate は作らず
  受理集合は変えない。正例 = 不一致 1 field の sidecar に当該行が載る、負例 = 一致時は sidecar を書かない (項 15)。
  Codex author (D95) + 変異事前登録。本題の局所修正だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2683-attestation-mismatch-diag/README.md`。設計判断は
  {{D:t126-attestation-mismatch-sidecar}}。実装 commit `1444d5030` (Codex author)。裁定の正本は着手時に main で
  確認した **D2104 項 14・15** (wave 開始時は branch 上の fragment、段 4 直前に main b4631a92e へ fold 済みを確認して
  ff で取り込んだ)。
- **依頼の前提のうち execution_guard 側は実測で覆り、変更なしと裁定した (段 4 P1、段 3・6 の 4 本が反証せず)。**
  `attest_and_build_receipt` は 2026-07-19 (commit 950757e20a) から非 pass 行を `json.dumps` で例外 message に載せ、
  production 呼び手 4 本 (`loop.py`、`s8b_oracle_driver.py` ×2、`screening_driver.py`、`s8b_floor_campaign.py`) は
  `str(exc)` を伝播する。floor campaign は失敗時に出力 root を作らないことを test で固定 (開始前・副作用ゼロ) しており、
  file の sidecar は既存契約と衝突する。捨てていたのは T126 driver だけ (fork した子が `os._exit(31)` で file を残さず、
  台帳には stage / type / message だけ)。
- 実装: `_attest` の typed 例外 `AttestationMismatchError` (message 不変)、子側処理の module-level 抽出
  `_run_attestation_child` (不一致時だけ `{stage}-{n}.mismatch.json` を `create_json` で 1 つ、成功 payload の bytes 不変、
  書込み失敗・probe 例外は sidecar なしで rc=31)、親の `_attestation_rejection_message` (sidecar 実在時だけ message に
  attempt 相対 path と failed field 名、読取り不能は `unavailable`)。`run_series` の reject evidence の key 集合・`verify()`・
  成功 series の manifest・`execution_guard.py` は非接触。
- **段 3 の real 所見は 5 件 (A2・A7・A8・B1・B2)、うち must-fix 3 件を裁定した。** A8 (親 brief の「live 比較なし」は
  一般化しすぎ — `_identity_files` の HEAD blob 比較は live 照合) は brief を訂正 (新規実走は commit を要する通常運用、
  過去 attempt は記録 commit の blob で verify されるので無効化されない)。B1 (helper 直呼び test は production 配線を
  証明しない) は AST 配線 pin (子分岐・非ゼロ分岐の所属と keyword まで) + 実 `os.fork` の helper test で採用し、配線変異
  M10・M11 を登録した。A2・B2 (`create_json` の fsync stall と SIGKILL 後の staging 残留) は accepted payload の
  `create_json` と同じ型の窓であり局所修正の scope 外、限界として D に記録し裁定パッケージ候補 2 件を新規に起票した。
- **段 6 レビュー 2 本は must-fix 0 / GO** (A: nit 3 = AST pin の射程、`Path.exists` の全体 patch、M1/M5 の赤地点。
  B: nit 1 = AST pin の引数・分岐)。fix 子 1 本 (test file のみ) で 3 件を反映した。
- 実走 (計算ノード): 変更 test file 単独 65 passed (2747.nqsv、fix 後 2764.nqsv)。consumer 7 file は commit 前に
  `test_campaign.py` 32 件が `contract-loader-drift` (未 commit の identity file と HEAD blob の差、既知の型) で赤、他は
  1155 passed / 3 skipped。commit 後の consumer 再走 (campaign / t671 / pegasus_tools / artifacts) は 1062 passed / 3 skipped (2783.nqsv)。provenance full は
  10,910 件・新規違反なし。受入全走は docs commit 後に `dev_wave_wait.py acceptance` で投入し、`child-green` の受領証だけを
  land が tested tip と照合する (結果は受領証が正本)。
- **変異 matrix (container worktree `dev-wave-jobs/.../mutation-tree` = 実装 commit 1444d5030、`run_tests.py` 1 file、
  probe と本走で各 13 request = baseline + 12 変異)。** probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走。本走は baseline PASSED、負例 11 件 (M1〜M11) すべて KILLED で
  期待 node と観測 node が完全一致 (matching 12/12)、等価変異 E1 (docstring) は SURVIVED、MISMATCH 0、TIMEOUT 0。DW-M08 の枠:
  受理集合 / fail-closed 境界 3/3 KILLED (M2 成功時にも sidecar → 2 node、M6 汎用失敗の rc 31→34 → 4 node、M9 reader 例外の
  再 raise → 4 node)、診断感度 pin 8/8 赤 (M1 sidecar 削除 11 node = 不在の単一理由、M3 failed_fields 空 4、M4 非 pass 行だけ 1、
  M5 空比較で sidecar なし 1、M7 汎用失敗でも sidecar 3、M8 message 固定文言 6、M10 production raise 固定文言 1 (AST)、
  M11 closure 子分岐インライン化 1 (AST))。走行後の container は clean・HEAD 1444d5030 を親が確認。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1、全段 `gpt-6-astra` / `medium`)。親の実測は焦点走 4 本
  (計算ノード)、変異 2 走、provenance full 1 本、受入 1 走。

## 次の一手差分

### 完了

- [T-2683] T126 driver の attestation 不一致で、fork した子が比較行の全行を持つ診断 sidecar を失敗時だけ残し、
  親の reject message が sidecar の相対 path と failed field 名を指すようにした。execution_guard 側は既存策で足りる
  と裁定 (変更なし)。
  remaining: none
  base: b90bce448fc5bf2210c2a7226c22e2cd5e35352e0413af199e7e084660b1808e

### 新規

- {{T:t126-diagnostic-writer-fsync-staging}} **P3・裁定待ち (段 3 A2 / B2、段 4 で scope 外)**: T126 の診断 sidecar と
  accepted payload は同じ `create_json` (fsync) で書く。fsync の stall は子の timeout に入り mismatch 文言が timeout
  文言に置き換わる。子が SIGKILL されると create-only の staging file が残り、collector の「abandoned staging bytes」
  拒否で failure receipt が発行できない (accepted 経路に元からある窓と同型)。択: (a) 現状維持 (推奨 — 実害未観測、
  D2104 の「gate の新設は実害の観測に限り」)、(b) capability を保つ非 fsync の診断 writer を `artifacts.py` に足す、
  (c) collector の staging 回収を診断 file に限って許す。(b)(c) は共通層の変更で局所修正を超える。
- {{T:execution-guard-prestart-rejection-rows}} **P3・裁定待ち (段 3 B 観点 2、段 4 P1)**: `execution_guard.
  attest_and_build_receipt` の不一致は非 pass 行を例外 message に載せるだけで、開始前・副作用ゼロで拒否する呼び手
  (loop / oracle / screening / floor) では stdout / stderr にしか残らず、生ログを失えば比較値も失われる。択: (a) 行動なし
  (推奨 — 副作用ゼロ契約を守り、stdout / stderr の保存は外側の実行環境の責務)、(b) 外側 wrapper が例外 message を
  job dir の診断 file へ保存する、(c) guard 自身に書込みを足す (副作用ゼロの test pin と衝突、不採用)。
