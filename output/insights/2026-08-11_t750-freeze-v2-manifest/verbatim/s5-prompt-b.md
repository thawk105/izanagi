あなたは izanagi の dev-wave 段 5 の実装子である
(単位 B = choke point 封鎖 + reviewed spec + oracle manifest CLI)。
`sandbox=workspace-write`、`reasoning=high` で動く。出力は日本語で書く。

## 読むもの (読めなければ即停止し、読めなかった path を報告して終わる)

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s1-brief.md`
- 段 2 プラン: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md` の
  **§単位 B/C のみ** (§単位 A は別実装子の担当)
- **段 4 裁定 (最優先・プラン v2 の正本)**:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s4-ruling.md`
  プランと裁定が食い違う場合は**裁定が勝つ**。

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest`。

## 所有 (これ以外のファイルを 1 byte も変更しない)

- `orchestrator/campaign/s8b_oracle_spec.py` (新規作成)
- `orchestrator/campaign/s8b_oracle_manifest.py`
- `orchestrator/tests/test_s8b_oracle_manifest.py`
- `orchestrator/tests/test_s8b_ratified_freeze.py`

`s8b_holdout_freeze.py` / `test_s8b_holdout_freeze.py` / `s8b_v2_freeze_fixture.py` は
**別実装子が同時に編集している**。読むのも import も可、**書くのは不可**。
`s8b_ratified_freeze.py`・`s8b_oracle_driver.py`・`s8b_oracle_report.py`・
`s8b_oracle_judge.py`・`s8b_floor_campaign.py`・docs は編集禁止。

## 仕事 (優先順位の高い順)

1. **B-1 (最重要): `verify_manifest` へ cell-product 検査を足す。**
   schedule の cell 集合が
   `{(h, c) | h ∈ schedule の holdout 集合, c ∈ _holdout_configuration_ids(freeze, h)}`
   と **exact 一致**しなければ `ManifestError` で拒否する。
   - 置き場所は **`verify_manifest`** である (`build_manifest` ではない)。
     理由 = 実行経路の choke point は `s8b_oracle_driver.py:1119-1129` が呼ぶ `verify_manifest`
     であり、CLI を足すだけでは迂回されるため (親が実測)。
   - `_holdout_configuration_ids` (`:530-559`) を再利用する。
   - **方向は受理集合の縮小のみ**。fail-open 方向の変更を含めない。
   - 親の実測: 既存テストの `CONFIGURATION_IDS` (`test_s8b_oracle_manifest.py:26-29`) は
     実 freeze の `variant_binding.entries` と完全一致するため、正当な manifest は通るはずである。
     もし既存テストが赤くなったら、**期待値を変えずに報告して止める**。
2. **B-2: reviewed spec の schema と validator** を新 module `s8b_oracle_spec.py` に作る。
   段 2 プラン §reviewed spec schema の exact key 集合をそのまま使う。
   承認 authority は **module 内の pinned literal**
   (`APPROVED_SPEC_SHA256: Optional[str] = None`)。`None` のあいだは `no-approved-spec` で
   必ず fail-closed する。**approval 発行 API・`--approver`・既定補完を作らない。**
   **Git の commit message / trailer を承認根拠にしてはならない** (段 2 プランのこの部分は破棄済み)。
3. **B-3: manifest CLI `build-approved`** を `s8b_oracle_manifest.py` へ足す。
   argv の値入力は `--output` **だけ**。`--schedule` / `--schedule-path` / `--freeze` /
   `--campaign-id` / `--campaign-ids` / `--spec` / `--approval` / `--approver` / `--root` /
   `--n` / `--master-seed` / `--block-sizes` / `--holdout-id` / `--configuration-id` は
   parser に登録しない (指定時 argparse rc=2)。
   `load_ratified_freeze` を使い legacy fallback をしない。active が無い現状は
   `no-active-ratified-freeze` を stderr へ出して rc=2 で止まり、出力を作らない。
   `namespace-dirty` 等の別 reason を `no-active` へ丸めない。
   CLI 専用 writer は単位 A と同じ dirfd + `O_NOFOLLOW` + `O_EXCL` + 候補 root 限定とする。

## 絶対に守る制約

- 既存 `build_manifest` / `write_manifest` / `_atomic_create_json` の
  **programmatic 受理集合を変えない** (B-1 の縮小は `verify_manifest` にだけ入れる)。
- `output/s8b-freeze/` および `output/s8b-oracle-spec/` 配下へ 1 byte も書かない。
  実 repo に spec / approval / manifest の実ファイルを作らない (テストは tmp root)。
- transition table・`FROZEN_MANIFEST`・凍結 pin・`s8b_experiment_numbers` の承認値を変えない。
- 実走・queue 投入をしない。正例は synthetic fixture 経由に限る。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。既存テストが赤なら
  実装側が誤りである。期待値の方が誤りだと判断したら、実装を変えずに報告して止める。
- 指示にない受理集合の拡大・縮小をしない。scope を書く前に現行の受理・拒否挙動を明記する。
- docs を編集しない。commit しない (親が行う)。

## 検査と報告 (すべて満たすこと)

- 緑を主張するなら**走らせた nodeid と範囲を併記する**。実走できなかった項目は
  「実装済み・未実走」と書き、`closed` と申告しない。
- テストを新設・改名したら、それを制約する meta-test も走らせる。
- fixture へ現行 hash を差し込んでテストを甘くしない。schedule hash の期待値を
  実装と同じ `build_schedule` から自己再計算しない (独立 literal を置く)。
- 完了報告に、**所有外の caller (driver / report / judge)・共有 fixture・consumer test への
  波及可能性**を静的に列挙する。特に B-1 で赤くなりうる既存 node を全部挙げる。
- 親 docs が未 land のため期待して赤くなる finding 集合を事前指定し、それ以外は回帰として報告する。
- 赤の内訳を完了報告に明記する。

最後に `## 総括` 節を置き、実装の骨子と残ったリスクを 5 行以内でまとめる。
