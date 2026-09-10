# land rollback の resume state 条件付き削除と fold dry-run の --show-diff — 実測と変異台帳

wave: `dev-wave-t766-t768-resume-diff` / 実装 commit `d7f9ac64`、fix commit `a10b233f`。
裁定は [T-766] (a) と [T-768] (a) (worklog エントリ 405、起票原文は
`docs/archive/worklog-phase3-0811-393.md` の [T-766] / [T-768] 項)。

`authority: none` / `default_effect: no-state-change`。可変状態の正本は worklog 末尾と現行 phase doc。

## 何を変えたか

- **[T-766]** `tools/dev_wave_land.py` の `_rollback_fold` は、復元点の失敗を `failures` へ積んだ
  後も fold resume state を無条件で `unlink` していた。削除を `elif not failures:` へ条件化した。
  state が symlink / 非 regular のときの型検査は `failures` の外に残す (先行 failure があるとき
  型検査が黙って消える恒真 gate を避けるため)。rollback 失敗時は、state が regular なら
  `resume journal preserved at <path>`、非 regular なら
  `non-resumable transaction state remains at <path>` を reason へ足す。
- **[T-768]** `tools/spool_fold.py` の CLI へ `--show-diff` を足した。`--dry-run` 併用時のみ有効で、
  全 target と全 `gc_paths` の before 実在・型・SHA を照合してから、stderr へ byte-oriented な
  unified diff を出す。stdout の JSON は byte 単位で不変。
- 運用導線として `docs/spool/README.md` の wave 中手順を `--dry-run --show-diff` に変えた。

## 段 1 の前提実測 (裁定の前提が今も成立するかの確認)

repo 外 probe (`probe_t766.py`、wave 作業ディレクトリに保存) が実 `_rollback_fold` を temp git repo で
呼び、ref 復元点を失敗させた。結果は
`failures = ['main moved beyond the fold commit; ref rollback refused']` かつ
`state_path.exists() == False`。**裁定の前提 (rollback 失敗でも state が消える) は成立**していた。

既存被覆はゼロだった。実 `_rollback_fold` を走らせるテストは 1 本も無く、唯一の言及箇所
(`orchestrator/tests/test_dev_wave_land.py` の RC wiring テスト) は関数自体を lambda で置換していた。

`tools/spool_fold.py --dry-run` の stdout は `targets[]` に path と before/after hash だけを持ち、
after bytes も diff も持たないことを実行で確認した。

## 段 6 レビューが見つけた面 (fix で閉じた)

- **信頼境界 (規律 6)**: fragment は AI が書く外部入力であり、`validate_spool_tree` は C0 制御文字を
  拒否しない。diff payload を無加工で stderr へ流すと、ANSI erase / cursor move で
  **この機能の目的である land 前の目視確認そのものを消去・偽装できた**。C0 (LF/TAB 除く) と DEL を
  可逆な `\xNN` へ escape し、制御 byte を含むときだけ `# payload_control_bytes=escaped-c-v1` を
  前置する。制御文字を含まない通常 diff の bytes は不変。
- **byte 忠実性の実装バグ**: 行分割に `bytes.splitlines` を使っていた。これは CR・VT・FF・
  FS/GS/RS・NEL でも切るため、「byte 忠実」という契約と実装が食い違っていた。LF 限定の
  `_lf_lines` へ替えた。
- **誤診断**: 非 regular な state が残っているときにも `resume journal preserved` と報告していた。
- **fail-silent**: 照合失敗時に診断ゼロで rc=2 を返す実装になっていた (親の fix 指示の誤りに由来)。
  既存の transaction-error JSON 経路へ戻した。

## 焦点走と、赤 5 件の帰属判定

`tools/run_tests.py --force-dispatch orchestrator/tests/test_dev_wave_land.py
orchestrator/tests/test_spool_fold.py -q -rf`。

| 走 | 結果 |
|---|---|
| 実装統合後 | 5 failed / 207 passed |
| fix 統合後 | 5 failed / 214 passed |

赤 5 件は `test_exploration_external_root_keeps_wave_clean` (campaign の
`CertifiedWriterAuthorizationError`) と、実 canonical をコピーする `test_spool_fold.py` の 4 本
(コピー先の `tools/check_docs.py` が `dev_waves` を import できず `ModuleNotFoundError`) である。
いずれも本差分が到達しない箇所であり、**wave の変更を 1 つも含まない未変更ツリーで同 5 件を再走して
同じ赤を再現**した。よって実装差分へ帰属しない。焦点走の実行形に固有で、受入全走の形とは環境が違う。
変異 harness の runner ではこの 5 node を `--deselect` する (しないと全変異が MISMATCH になる)。

## 変異台帳

`mutation-spec.json` (事前登録) と `mutation-ledger.json` (harness 出力) が正本。期待 node は
runner scope (上記 2 test file から known-red 5 件を除いた集合) の完全集合として登録した。
本走の `repo_head` は `39f81174`。

| ID | 変異 | 実測 | 期待 |
|---|---|---|---|
| M1 | `elif not failures:` を wave 前の逐語 `else:` へ戻す | KILLED (3 node) | KILLED (3) |
| M2 | state ブロック全体を `if not failures:` の内側へ移す | KILLED (4 node) | KILLED (4) |
| M3 | 正常時の `state_path.unlink()` を `pass` にする | KILLED (1 node) | KILLED (1) |
| M4 | `--show-diff` の `--dry-run` 必須検査を外す | KILLED (1 node) | KILLED (1) |
| M5 | diff の対象から `gc_paths` を外す | **MISMATCH (3 node 実測 / 2 登録)** | KILLED (2) |
| M6 | diff を stderr でなく stdout へ書く | KILLED (4 node) | KILLED (4) |

summary = KILLED 5 / MISMATCH 1 / **SURVIVED 0** / TIMEOUT 0。

### M5 の erratum

M5 は登録した 2 node に加えて `test_cli_dry_run_show_diff_matches_target_after_bytes` も落とした。
**検出力が登録より弱いのではなく強い**方向のズレである。原因は親の事前予測の読み落としで、
段 6 fix が hash 行の値照合を `gc_paths` にも広げたため、gc 出力を止めると同テストも赤くなる。

初回 ledger は消さず (`DW-M02`)、`mutation-spec-erratum.json` で M5 だけを正しい期待 3 node で
再走した (`mutation-ledger-erratum.json`、同じ `repo_head` `39f81174`)。結果は
**KILLED / 期待 node 完全一致**。したがって実質 6/6 KILLED、SURVIVED ゼロである。

M1 は memory `mutation-must-include-pre-wave-form` に従い、**wave 前の実コードの逐語** (`else:`) を
復元する形で登録している。

`apply_fold` が land の後段検証・commit より前に state を消す窓 (段 3 レンズ A の所見 2) は
本 wave の scope 外に裁定したため、その変異は登録していない (SURVIVED を equivalent と
誤記録しないため)。
