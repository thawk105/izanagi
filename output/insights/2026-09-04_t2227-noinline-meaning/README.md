# [T-2227] BACKOFF_NOINLINE の意味の節を枝選択 witness で確立した (D1569)

日付: 2026-09-04 / wave: `dev-wave-t2227-noinline-meaning` / branch `worktree-dev-wave-t2227-noinline-meaning`

## 要点

`BACKOFF_NOINLINE` の runtime-meaning arm は宣言が無いため常に `unestablished` で、`paper` を含む
全 use class の admission を通っていた。D1569 に従い、D1490 の compile-time 枝選択 witness を
registry factory から発行する形で厳格化した。受理集合は狭まるだけで、従来 unestablished (admit) だった
record は green (admit) か red (reject) になる。

## 実装前に確定した事実 (段 1 実測)

- **既受理成果物への影響は repo `output/` 内で空集合。** `output/` 全体 (untracked 含む) を走査し、
  `BACKOFF_NOINLINE` を runtime-meaning `unestablished` で含む実 admission record は 0 件。
  `unestablished_meaning_macros` field を持つ JSON も 0 件 (hit は変異 report 内の pytest 出力と設計文書のみ)。
  A-2 の実走は `a2gate-20260902a` / `b` の 2 回のみで driver_rc=2 (4 cell 緑未達)。t1683 cost probe の
  出力 2 件 (`output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr5_rmw0.json` ほか 1 件、
  2026-08-25) は関門導入 (0218acc61) より前で `condition_gates` を持たない。**repo 外の保存先
  (A-2 attempt root、s1 の output_root、t1683 の `--out`) は未走査であり、空集合の主張は repo 内に限る。**
  migration 不要も同じ範囲。
- **指令は所有 TU でなく header にある。** `#if BACKOFF_NOINLINE` は patch `patches/silo-backoff-fixed.patch`
  の `include/backoff.hh` hunk に 1 回だけ。所有 TU `cc/silo/transaction.cc` → `include/transaction.hh` →
  `../../../include/backoff.hh` の quote include 連鎖。
- **従来の shadow tree では header 計装が見えない。** 祖先 directory を symlink で鏡像化する形では
  `..` が実体側へ解決され marker 0 個 (toy tree、g++ 11.4.0)。全 directory 実体・file symlink の
  深い鏡像なら値 1 → (1,1)、値 0 → (0,1)。
- **A-2 の要求値は既定と同じ 0** (`paper_story_a2_certification.v2.json` の `controlled_define_base`)。
  現行 factory (要求 1・既定 0) では登録しても未確立一覧が縮まない → 対照値方式 (decisions 参照)。

## 段 3 / 段 6 の所見と裁定

段 3 (sol 8 件 / luna 9 件)、段 6 (review A / B、再レビュー 1 本) の所見で裁定に効いたもの
(逐語は `verbatim/`):

| 所見 | 裁定 |
|---|---|
| 登録簿へ足すと供給の節 `shared_branch_build` が cache route の同 macro で `compile-command-unavailable` を出す (sol-2) | real、採用。共有 build root を CMAKE_CXX_FLAGS route に限定。要求 1 の供給正例を登録 |
| D1492 は promotion 限定でない。t1683 probe は要求し admission を JSON へ保存する。backoff_sweep / silo_ladder は `BACKOFF_FIXED` 系しか要求しない (sol-3 / luna-4) | real、採用。配線先 = A-2、s1、t1683。brief の raw/promotion 境界は撤回 |
| 依存 file (`-MD`) で計装 header の実読を要求する検査 (plan の P1) は本題外 (luna-5) | real、削除。読まれなければ両観測 (0,0) で既存の非識別判定が red にする |
| 対照値方式は D1490 の値契約の拡張であり裁定が要る (luna-1) | real。D1490 は AI 決定であり、D1569 (ユーザー裁定) を満たす実装が他に無いため AI 決定として記録。ユーザーが覆す revert 点は factory の 1 条件 |
| `ConditionalBranchMeaningDeclaration` は registry と同値なら factory 外から構築できる (sol-1 / luna-3) | real (観測)、scope 外。受理条件は factory の再導出と等値比較で factory 条件に一致し受理集合は広がらない。発行元 capability は新防壁 |
| 深い鏡像は dir symlink を追うと hang しうる (sol-7) | real、実装条件 (`followlinks=False`、dir symlink と `.git` は symlink のまま、走査失敗は structured red) |
| toy は実 TU を含意しない (sol-8 / luna-7) | real、段 6 で実 patch 木 dogfood を計算ノードで実走 (下記) |

## 配線した driver と配線しない driver (D1492)

| driver | 判定 | 理由 |
|---|---|---|
| `paper_story_a2_certification.py` (`paper`) | 配線 | 要求し、receipt へ admission を載せる |
| `s1_direct_comparison.py` (`floor` / `certified-selection` / `raw`) | 配線 | 要求し、試行 WAL へ admission を載せる (全 role 共通経路) |
| `tools/pegasus/probes/t1683_rr5_cost_probe.py` (`raw-measurement`) | 配線 | 要求し、出力 JSON `condition_gates` へ admission を載せる |
| `backoff_sweep.py` / `backoff_repro.py` | 配線しない | 実呼び出しは `BACKOFF_FIXED` だけを要求する (`_require_backoff_condition_gate` の macro_values) |
| `silo_ladder_rung1.py` | 配線しない | `BACKOFF_FIXED` と rung / report macro だけを要求する |
| `paper_story_a1_paired.py` | 配線しない | `BACKOFF_FIXED` だけを要求する |
| `screening_driver.py` | 配線しない | 要求しうるが関門の返値を捨て admission を成果物へ載せない |
| `backoff_profile.py` | 配線しない | 関門を呼ばない (`admission=None`) |

A-2 の admission は、供給の節が D1523 (別 wave) の `preprocess-root-dependent-builtin` で赤の間は
admitted=False のままである。本 wave の直接効果は「A-2 / s1 / t1683 の `BACKOFF_NOINLINE` meaning
record が `meaning-witness-undeclared` (unestablished) から green / red へ置換される」までで、
A-2 の受理済み成果物に現れるのは D1523 取り込み後の fresh run からである。

## 実装しなかった所見 (裁定パッケージ候補ではなく記録)

- 宣言 object の発行元を capability で識別する (D1491 の「factory 以外から発行できない」を object 同一性で
  実装する)。受理集合は変わらないため新防壁として scope 外。
- 依存 file で計装 header の実読を要求する検査。同上。

## 検査

| 検査 | 結果 |
|---|---|
| baseline (実装前) `test_condition_meaning_gate.py` | 88 passed / 5.07s (request 975694) |
| 単独走 (fix 前) `test_condition_meaning_gate.py` / `test_paper_story_a2_certification.py` / `test_s1_direct_comparison.py` / `test_pegasus_calibration_workload.py` | 100 / 113 / 107 / 8 passed、rc=0 (requests 975827 / 975851 / 975875 / 975876) |
| consumer 焦点走 39 file (fix 前) | 3411 passed / 3 failed / 13 skipped、268.6s (request 975878)。赤 3 件は s1 の file 全体 sha256 pin (`test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW`) と `run_role` の build sink 行番号 pin (`test_ccbench_spawn_sites.py` 1215→1219) で、s1 への 4 行追加に追随していない同一性 pin。先例 2e62753a7 と同じく literal 側で閉じた (fix 子 1 本、焦点再レビュー 1 本で closed) |
| fix 後の再走 2 file (`test_s8b_oracle_manifest.py`、`test_ccbench_spawn_sites.py`) | 151 passed、rc=0 (request 975915) |
| 実 patch 木 dogfood (計算ノード、`patchharness.checkout` + `applied` + `prepare_masstree_fetchcontent` + gflags/glog static build、probe は repo 外) | 要求 0/0: green、requested (0,1)・default (1,1)。要求 1/0: 意味 green・供給 green・admission true。実 `g++-11`、二段 include 経由。所要 17.8s (request 975894)、結果 `dogfood-result.json` |
| 変異 probe (全件 SURVIVED 期待で観測) | 10 変異すべてで赤 node を観測 (MISMATCH = 殺されている)、等価変異 E1 は SURVIVED (harness の正例)。baseline PASSED (`mutation-probe.json`) |
| 変異 本走 (M1〜M10 KILLED 期待・完全集合、E1 SURVIVED 期待) | **10 KILLED、期待 node 完全一致、E1 SURVIVED、baseline PASSED、rc=0** (`mutation-final.json`)。M1 (5 node)・M2 (3)・M6 (3)・M4 (2)・M8 (2) は複数 test が赤になる冗長 gate であり、単一理由の証拠は M3 / M5 / M7 / M9 / M10 (各 1 node) が担う |
| 全史 AI provenance 監査 (統合 commit + main 取り込み後) | 8073 件、新規違反なし、rc=0 (request 975954) |
| 受入全走 | 記録 commit 後に land 対象 tip へ投入する (DW-O12)。結果は land の受入受領証に残す。本 README には書かない |

## main 取り込み後の合成監査 (merge 36e6206d3)

受入前に main b5b5a583a を取り込んだ。main 側は T-2226 (D1523: inert 供給比較を差の分類へ変える) が同じ
`condition_meaning_gate.py` と同 test を変えていたため、競合なしでも Codex review 子に合成を監査させた
(`verbatim/s9-merge-audit.md`)。交差点 (route 限定 `shared_branch_build`、`stock_identity` 経路、両 validator、
test の helper / fixture、二重定義) はいずれも直交と確認された。取り込み後の焦点走 6 file は 486 passed、rc=0 (request 976186)。

監査は must-fix を 1 件挙げた: `_configured_define_compile_commands` の共有 seam を `BACKOFF_NOINLINE`
要求 0・既定 0 で使うと、供給側の control (stock root, 値なし) と意味側の対照 (source root, 値 1) が
食い違い `compile-command-drift` で red になる。親の裁定: **real だが現行成果物への影響なし、scope 外。**
共有 seam の production 呼び手は s3 / s5 / t152 (IZANAGI_BREAK 系、要求 1・既定 0) だけで、NOINLINE を
0/0 で seam に通す経路は存在しない。A-2 / s1 / t1683 は供給と意味を独立に評価する。段 2 plan の
「残る懸念」で fail-closed と決めた挙動そのものであり、merge 由来でもない。将来 NOINLINE 0/0 を seam へ
通す driver を書くときは、意味側を独立 configure にするか値 1 の第三 command を持たせる必要がある。

## 副産物

- 供給の節の `shared_branch_build` は「登録 macro は CMAKE_CXX_FLAGS route だけ」という暗黙の前提を
  持っていた。登録簿へ cache route の macro を足すと正当な要求 1 が `compile-command-unavailable` で落ちる。
  route 条件を明示して閉じた。
- 段 4 で配線先に s1 を足したとき、path での pin 閉包 (DW-O09) を s1 について引き直していなかった。
  s1 の file 全体 sha256 は reviewed spec の独立 golden に焼き込まれており、key 名でも値の字面でも
  見つからない型。配線先を追加した時点で閉包を引き直すべきだった (DW-C00「変更面の確定時にも再評価する」の未履行)。
