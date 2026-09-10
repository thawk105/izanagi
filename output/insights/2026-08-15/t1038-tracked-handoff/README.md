# [T-1038] / [T-1039] — 起動検査が main landed handoff を通す

wave `dev-wave-t1038-tracked-handoff` (2026-08-15) の材料。裁定と経緯の正本は worklog、
設計判断は decisions、失敗は failures 台帳を参照する。ここには変異台帳と実測値だけを置く。

## 変異 matrix

- spec: `mutation-spec.json` (sha256 = `4f820ad6f3e611927f2f6a52e04c45e9f03716602f6b81b01937c1c237402a74`)
- 台帳: `mutation-ledger.json`
- 対象 HEAD: `2cca355fab819b8c9b3db76c2208f53ef64353ee`
- runner: `python3 tools/run_tests.py orchestrator/tests/test_check_wave_startup.py -q -rf --force-dispatch`
  (`--runner-mode dispatch`、計算ノード)
- 結果: **9 変異すべて KILLED。SURVIVED ゼロ。**

| ID | category | 壊した不変条件 | 期待 node 数 | 実測失敗 node 数 |
|---|---|---|---:|---:|
| M01 | positive | wave 前の実コード (`iterdir()` 全件残置 + README 名前例外) へ関数まるごと復元 | 26 | 26 |
| M02 | negative | `ls-files` の rc≠0 を fail-open (`return []`) にする | 1 | 1 |
| M03 | negative | index tag の白名 (`H`) を外す | 3 | 3 |
| M04 | negative | index stage の `0` 検査を外す | 3 | 3 |
| M05 | negative | index mode の白名 (`100644` / `100755`) を外す | 2 | 2 |
| M06 | negative | main provenance 照合 (`rev-parse refs/heads/main:<path>`) を丸ごと外す | 3 | 3 |
| M07 | negative | index OID と main OID の一致検査だけを外す | 1 | 1 |
| M08 | negative | worktree entry の `S_ISREG` 検査を外す | 2 | 2 |
| M09 | negative | 同一 path の重複 record の拒否を外す | 1 | 1 |

**M01 の位置づけ.** ユーザー指示により、事前登録変異には wave 前の実コードの形
(tracked/untracked を区別しない `iterdir()` 走査) を必ず含めた。これは受理集合を*狭める*
唯一の変異であり、`DW-M01` の「受理集合を縮小する wave では過剰拒否を検出する正例も登録する」に
対応する枠として登録した。**M01 が KILLED になったことが、新テストが本 wave の唯一の正方向
(main landed handoff の受理) を測っている証拠である。** 期待 node 26 件は親が静的に導出し、
実測と完全一致した (MISMATCH なし、probe 不要)。

**kill に算入しなかったもの.** submodule 初期化失敗時の提示文の変更は診断文字列だけの変更であり、
`DW-M03` に従い kill に数えない。`DW-M08` の diagnostic sensitivity pin として、
`orchestrator/tests/test_check_wave_startup.py::test_resume_rejects_invalid_submodule_marker` と
`::test_resume_requires_non_symlink_submodule_git_entry` が新 message の
marker 条件・`.git` 条件・コマンド文字列を assert している。

## 親の実測 (すべて 2026-08-15 JST)

| 時刻 | 測定 | 結果 |
|---|---|---|
| 07:22 | 起動 gate (`--external-handoff`、main=01af552f) | rc=1、NG は `worktree-local handoff remains (dev-wave-t971-swo-oracle-floor.md)` の 1 行のみ |
| 07:22 | `git ls-files docs/handoff/` | 2 件 (README.md と当該 file) = tracked |
| 07:22 | `git status --short docs/handoff/` | 0 行 (untracked 残置ゼロ) |
| 07:26 | `git ls-files --stage -z -- docs/handoff` の形式 | `<mode> <sha> <stage>\t<path>\0` (NUL 終端) |
| 08:36 | `git ls-files -v --stage -z` の形式 | 先頭に tag 1 文字 + 空白 (`H 100644 ... 0\t<path>\0`) |
| 08:38 | `git check-attr filter text eol -- docs/handoff/README.md` | 3 つとも `unspecified` (filter / EOL 変換なし) |
| 08:22 | 焦点走 (bounded local) | 85 passed / 2 failed |
| 08:48〜08:50 | 焦点走 (bounded local) 3 回 | すべて rc=16 = `bounded scope の memory.max / memory.oom.group を走行中に attest できない` (dispatcher infrastructure failure、テスト結果ではない) |
| 08:51 | 焦点走 (`--force-dispatch`、計算ノード) | **95 passed / 0 failed** (2.53 秒) |
| 08:56〜09:08 | 変異本走 (dispatch) | 9/9 KILLED |
| 09:11 | 完了条件 ([T-1028]) 実データ走 | `check_wave_startup.py --mode resume --external-handoff <repo 外>` = **rc=0** |
| 09:12 | 実データ probe (`update-index --skip-worktree docs/handoff/README.md`) | rc=1、`NG: worktree handoff index tag is not H (docs/handoff/README.md: S)` |
| 09:12 | 同 probe の復元 (`--no-skip-worktree`) | tag が `H` に戻り、`git status --short` 0 行、再走 rc=0 |

## 敵対レビューが倒した親の判断

| 段 | レンズ | 指摘 | 帰結 |
|---|---|---|---|
| 3 | A | `ls-files` は index 登録しか証明しない。自 branch へ commit した handoff も通る | 受理条件を main provenance へ狭めた |
| 3 | A | `assume-unchanged` / `skip-worktree` で内容だけ差し替えられる | `ls-files -v` の tag 白名で閉じた |
| 3 | B | `_git()` の `.strip()` が `-z` の NUL 終端を消し、プランの検査が本番で必ず失敗する | `_git_raw` を新設 |
| 6 | C | 不適格 record を握り潰しており、worktree に entry が無ければ rc=0 | 拒否を failure として保持する形へ |
| 6 | D | mode / stage / tag の変異は `rev-parse` 失敗に隠れて SURVIVED する | 上と同じ修正で単独発火するようになり、3 本とも KILLED |
| 6 | D | tracked descendant のテストは membership と `S_ISREG` の二重拒否 | 二重であることを docstring に明記し単独変異の証拠から外した |
