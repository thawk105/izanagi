# [T-1068] 段 4 裁定 — plan v2 と変異の事前登録

入力: s1-brief.md、out/s2-plan.md (受理、check rc=0)、out/s3-consult-A.md (受理、rc=0)、out/s3-consult-B.md (受理、rc=0)。
裁定 inbox の再走査 (2026-09-27): `rulings-inbox/2026-08-16-rulings-full3-28rulings.md` 項 22「凍結する (R4 / R5 / R7)」のまま。wave 開始後に T-1068 へ触れる新裁定なし。

## 所見の裁定

| 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|
| brief P1 (案 B) | plan・A・B とも支持 | 採用 | 案 B で確定。案 A は R5 の `return;`・R7 の shadowing・R4 の reason reset を prologue の直前へ移すと通る (B 所見 1、plan §1) |
| A-1 変異 M5 の帰属が位置と bytes で混ざる | real | 採用 | M5 は「tally slot が任意 bytes を受理」だけを登録し、負例は tally 位置 (開き括弧直後) への `return;` とする。位置だけの変異は gate 無効化に結び付かないので登録しない |
| A-2 保証の過大表示 | real | 採用 | docstring・insight・報告は「abort() 宣言から BEGIN 行頭直前までの領域内」の R4/R5/R7 の提示形と移設形を拒否、と限定して書く。file scope・他 file・前処理器は別経路として残す |
| A-3 原文照合テストは submodule 未初期化で skip | real | 採用 | 受入 log で原文照合 node が passed (skipped でない) ことを個別に確認し insight に書く |
| A-4 発火層は fresh admitted build | real | scope 外 (記録のみ) | 実装を広げず、insight で適用範囲を fresh admitted build (derive / require) に限る。S8b resume・非 admissible・ENOENT は既知の外側 |
| B-2 独立照合テスト必須 | real | 採用 | plan §3 の 3 出所 (骨格 patch・tally patch・pin 原文) の独立照合を置く。汎用 patch parser・実行時 file 読込は足さない |
| B-3 misattr 専用形は不要 | real | 採用 | 受理形は 2 つだけ。misattr 専用の正例・定数・分岐は置かない (関数宣言より前 / abort() 外を凍結しないことは M4 の正例で示す) |
| B-4 compile fixture の stub は最小限 | real | 採用 | `_synthetic_silo_checkout` の stub は canonical head の compile に要るものだけ。再利用 helper 化しない |
| B-5 凍結 JSON・duration ledger は触らない | real | 採用 | 再 pin・ledger 更新をしない。ただし新テスト nodeid を要求するメタテストがあれば author が自ら洗い出し、その結果を報告する |

## plan v2 (確定)

1. `orchestrator/campaign/axis_trigger_gating.py` の既存凍結定数の隣に 3 定数:
   `FROZEN_TEMPLATE_ABORT_HEAD_BYTES` (pin 6810666 の CCBench 原文、`void TxExecutor::abort() {\n` から BEGIN 前の最初の `#endif\n` + 空行 `\n` まで)、
   `FROZEN_TEMPLATE_ABORT_TALLY_BYTES` (`instr-silo-backoff-trigger-gating-tally.patch` の `+` 行)、
   `FROZEN_TEMPLATE_PROLOGUE_BYTES` (`silo-backoff-trigger-gating-variant.patch` の abort() hunk の `+` 行のうち BEGIN 直前の 7 行)。
   比較用 2 形 = `HEAD + PROLOGUE` と、`HEAD` の宣言行直後へ `TALLY` を挿入したもの `+ PROLOGUE`。実行時に patch / CCBench を読まない。
2. `orchestrator/campaign/build_admission.py` `_require_materialized_trigger_axis_predicate`: marker 件数・順序確認の直後に
   `raw[:begins[0].start()]` が 2 形のどちらかで `endswith` しなければ `_reject_trigger_axis()`。epilogue・block/hole 照合、三分岐 (ENOENT 受理 / stock 受理 / marker あり照合) と呼出し元は変えない。
   受理言語の条件 4 (T-1048 の 1〜3 に論理積): 「BEGIN 行頭直前の bytes が、abort() 宣言行から始まる 2 形のいずれかで終わる。宣言行より前は比較しない」。
3. docstring: 閉じたもの = 上の領域内の R4 型差し替え・reason reset、R5 非到達化、R7 局所 shadowing (提示形と移設形)。残るもの = file scope 宣言、他 file (header / class member) による名前解決、前処理器置換、R1、R3、R6、ENOENT。
4. テスト (`orchestrator/tests/test_build_admission.py`):
   - 負例 (1 関数に parametrize、名前は plan の `test_trigger_axis_rejects_mutated_abort_prefix` 相当): R4 GatePass 差し替え、R4 reason reset、R5 `return;`、R7 `const uint64_t FLAGS_clocks_per_us = 0;`、R7 `Backoff` の局所 shadowing (例 `struct Backoff { static void backoff(uint64_t) {} };`)、
     それぞれ実証位置 (prologue 内 / 宣言と BEGIN の間) と、prologue 直前への移設版。加えて tally 位置 (開き括弧直後) への `return;` (M5 用)。
   - 正例: 骨格のみ (既存 pristine・32 mask・epilogue 後の既存正例がそのまま通る)、骨格 + tally、関数宣言より前の bytes が異なっても受理 (M4 用)。
   - 独立照合: prologue 定数 ↔ 骨格 patch、tally 定数 ↔ tally patch、head 定数 ↔ `git -C external/ccbench show <CURRENT_PIN>:cc/silo/transaction.cc` の抽出 (submodule `.git` 不在時だけ skip、pin object / file 欠落は fail)。
   - fixture の形だけ更新 (受理・拒否の期待は変えない): `_trigger_source_bytes`、`test_campaign.py` `_write_materialized_trigger_source`、`test_buildcache_v2.py` の fake checkout 置換、`test_reflux_campaign_issuer.py` `_synthetic_silo_checkout` (`TxExecutor::abort()` + 最小 stub、`main` から `abort()` を呼ぶ)。
5. 規模上限: 変更行 (追加 + 削除) 450 行。超えたら差し戻す。Codex author 1 本 (所有 = 実装 2 file + テスト 4 file、素集合の分割不可)。

gate の禁止の署名と通る正例: 「marker ありの source は、BEGIN 行頭直前が凍結 2 形のどちらかで終わらなければ拒否」。通る正例 = 骨格 patch だけを当てた pin 6810666 の transaction.cc (evidence/transaction.cc.skeleton-applied) を hole 置換した source。

## 変異の事前登録 (実装後に位置・単一理由を確認し、期待 node は probe で完全集合を再登録する)

| ID | 位置 | 変異 | kill 期待 (種類) |
|---|---|---|---|
| M1 | build_admission.py 新 prefix 検査 | 検査を削除 | R4/R5/R7 の負例 (実証位置・移設版・tally 位置 return) が受理される (拒否側) |
| M2 | 同 | 照合を PROLOGUE 7 行だけの `endswith` へ弱化 | 移設版と tally 位置 return の負例だけが受理される (拒否側、案 A の弱さ) |
| M3 | 同 | tally 形を受理形から削除 | 骨格 + tally の正例が拒否される (過剰拒否側) |
| M4 | 同 | 比較範囲を関数宣言より前 1 行まで広げる (例: `\n` + HEAD を要求するなど、宣言行より前の bytes を要求) | 宣言より前の bytes が異なる正例が拒否される (過剰拒否側) |
| M5 | 同 | tally slot に任意 bytes を受理 (宣言行直後〜`  // remove inserted records` の間を不問) | tally 位置への `return;` 負例が受理される (拒否側) |
| M6 | axis_trigger_gating.py PROLOGUE 定数 | コメント 1 語を変える | prologue ↔ 骨格 patch 独立照合テストだけ (定数から入力を作るテストは同時に動くので落ちない) |
| M7 | axis_trigger_gating.py HEAD 定数 | コメント 1 語 (`// remove inserted records`) を変える | head ↔ pin 原文独立照合テストだけ |

- 2 file とも contract-loader 閉包。未 commit 変異で落ちる `contract-loader-drift` node は probe で別集合として記録し、単独検出力に数えない (DW-M03)。
  runner の file 集合を test_build_admission.py 中心に絞るかは probe の実測で決め、登録 spec に書く。
- 期待 node は初回 dispatch probe で完全集合を集め、erratum 再登録後に final を走らせる (DW-M08)。
