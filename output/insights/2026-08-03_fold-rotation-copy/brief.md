# 親 brief — fold 形検査から rename/copy 検出を外す

## 背景 (一次資料)

izanagi の dev-wave では、wave が `docs/spool/` へ書いた fragment を、land が lock 内で canonical
台帳 (`docs/worklog.md` / `docs/decisions.md` / `docs/failures.md`) へ畳む (fold)。
worklog が行数閾値を越えていると、fold の計画に「過去エントリを `docs/archive/worklog-phase3-*.md`
へ移す」ローテーションが入る。

`tools/dev_waves/git_state.py` の `verify_declared_fold_commit` は、fold commit の形を
`diff-tree --root -r -m --no-commit-id --name-status -z -M -C <sha>` で取り、
その結果が `R` / `C` で始まると `path-status` で拒否する。
worklog から archive へ大きな塊が移ると git が copy と判定するため、
**ローテーションを伴う fold は構造的に land できない**。

親が scratch repo で実測した (2026-08-03)。worklog 相当のファイルの 85% を新規 archive ファイルへ移す
commit を作ると:

- 現行フラグ (`-M -C`): `C084	docs/worklog.md	docs/archive/2026-01.md`
- `--no-renames`: `A	docs/archive/2026-01.md`

移動割合が 50% 程度だと C は出ない (類似度閾値依存)。実 land は同じ理由で 3 回失敗し、
main は動いていない。

## 確定済みユーザー裁定 (変更不可)

**択 (a) 採用 = 形検査の差分取得から移動検出を外す。**
理由: 追加・削除のパス制限 (削除は fragment path のみ、追加は rotation path のみ、archive 追加は
1 件まで) が既に効いており、検出を外しても制約は緩まない。移動は「削除 + 追加」として現れ、
同じ制限で捕まる。
択 (b) (worklog→archive の移動だけ例外的に許す) は例外面を増やすため不採用。

## scope

1. `GIT_COMMANDS["commit-diff"]` (git_state.py:90-93) から `-M -C` を外す
2. 形検査 `path-status` (git_state.py:763) の `R`/`C` 拒否分岐の扱いを決める
3. `_landed_fold_output_path` (git_state.py:557-562) の `R` 分岐の扱いを決める
4. テストを純増する (`orchestrator/tests/test_dev_waves_git_state.py`)

scope 外: fold が受理する path 集合そのものの変更、`tools/spool_fold.py` のローテーション生成、
land の他検査、`_diff_entries` の parse 仕様の作り直し。

## 不変条件

- (I1) fold が受理する path 集合は広がらない。`M` = `_FOLD_MODIFIED_EXACT` ∪ `docs/archive/README.md`、
  `D` = fragment path のみ、`A` = rotation path のみ・archive 追加 1 件まで。
- (I2) landed 区間の fold 署名検出 (`docs/spool/FOLDED.md` の `M`、fragment の `D`) は弱まらない。
- (I3) 他の git 呼び出しと他 caller (`tools/dev_wave_land.py:1513/1820`,
  `tools/dev_waves/checker.py:543`, `tools/dev_waves/daemon.py:1526`) の挙動は変えない。
- (I4) 実装面 (コードとテスト) は Codex `role=author` が書く。親は直接編集しない。

## 親の provisional 裁定 (= 攻撃対象。守る側に回らないこと)

- **(P1)** `-M -C` を消すだけでなく、明示 `--no-renames` を付ける。
  理由 = repo-local `diff.renames` / `diff.copies` が plumbing の `diff-tree` に効く経路を潰すため。
  `_git_env()` は `GIT_CONFIG_GLOBAL` / `GIT_CONFIG_SYSTEM` を `/dev/null` にするが repo-local
  `.git/config` は読む。**この前提が正しいか実測 (または git のドキュメント/ソース) で確かめ、
  支持か反証かを述べること。** 反証なら「消すだけ」で足りる。
- **(P2)** `_landed_fold_output_path` の `R` 分岐と `path-status` の `R`/`C` 拒否は残す
  (将来 `-M`/`-C` が再導入されたときの耐性)。ただし到達不能な恒真保証になるため、
  `GIT_COMMANDS["commit-diff"]` に移動検出フラグが無いことを機械固定するテストで裏を取る。
  **この判断も攻撃対象** — 到達不能な分岐を残すのは「謳うだけで発火しない assert」で、
  izanagi では過去に問題になった型である。消す設計のほうが良いなら根拠付きでそう言うこと。
- **(P3)** 純増検出力: 既存 fold 系テスト 12 本に、rotation (archive への `A`) を含む fold の
  **正例は 1 件も無い**。helper `_fold_commit` は archive を作らない。よって純増は
  「rotation を含む fold が accept される」正例と、「移動検出フラグ不在」の機械固定。
  **既存テストがどこまで被覆しているかを自分で確認し、親のこの主張を検証すること。**

## 成果物影響 (実装しない場合)

worklog が閾値を越えている間、全 wave の fold が `path-status` で拒否され、canonical 3 台帳への
追記が main に入らない。certified 選択やレポートの数値は変わらないが、試行台帳と「次の一手」の
正本が main から欠落し続ける。

## 関連ファイル (file:line)

- `tools/dev_waves/git_state.py:90-93` — `GIT_COMMANDS["commit-diff"]`
- `tools/dev_waves/git_state.py:159-170` — `_git_env()`
- `tools/dev_waves/git_state.py:553-562` — `_fold_fail`, `_landed_fold_output_path`
- `tools/dev_waves/git_state.py:565-610` — `_diff_entries`, `_commit_diff`
- `tools/dev_waves/git_state.py:699-787` — `verify_declared_fold_commit`
- `tools/dev_waves/git_state.py:23-50` — `_FRAGMENT_PATH_RE`, `_ROTATION_PATH_RE`, `_FOLD_MODIFIED_EXACT`
- `tools/spool_fold.py:1316-1370` — `_rotation_name` とローテーション適用
- `orchestrator/tests/test_dev_waves_git_state.py:160-440` — fold 系テストと helper
- 明示 `--no-renames` の先例: `tools/check_ai_provenance.py:625`, `tools/dev_wave_land.py:827,1454`
