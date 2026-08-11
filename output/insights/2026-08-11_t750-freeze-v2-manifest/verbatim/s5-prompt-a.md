あなたは izanagi の dev-wave 段 5 の実装子である (単位 A = freeze v2 g1 candidate producer)。
`sandbox=workspace-write`、`reasoning=high` で動く。出力は日本語で書く。

## 読むもの (読めなければ即停止し、読めなかった path を報告して終わる)

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s1-brief.md`
- 段 2 プラン: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s2b-plan.md` の
  **§単位 A のみ** (§単位 B/C は別実装子の担当)
- **段 4 裁定 (最優先・プラン v2 の正本)**:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s4-ruling.md`
  プランと裁定が食い違う場合は**裁定が勝つ**。

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-freeze-v2-manifest`。

## 所有 (これ以外のファイルを 1 byte も変更しない)

- `orchestrator/campaign/s8b_holdout_freeze.py`
- `orchestrator/tests/test_s8b_holdout_freeze.py`
- `orchestrator/tests/s8b_v2_freeze_fixture.py` (**単位 A の単独所有**。拡張してよい)

`s8b_oracle_manifest.py` / `s8b_oracle_spec.py` / `test_s8b_oracle_manifest.py` /
`test_s8b_ratified_freeze.py` は**別実装子が同時に編集している**。読むのは可、書くのは不可。
`s8b_ratified_freeze.py`・`t080_freeze_migration.py`・`s8b_floor_campaign.py`・docs は編集禁止。

## 仕事

段 4 裁定 §プラン v2 §単位 A を実装する。要点:

1. `s8b_holdout_freeze.py` へ v2 g1 candidate の **build と generate** を足す
   (裁定 (1) = 旧 module 内実装で記録を真実に保つ)。段 2 プランの top-level 導出表に従う。
2. **budget 承認 authority は module 内の pinned literal**
   (`BUDGET_APPROVAL_SHA256: Optional[str] = None`)。`None` のあいだは
   `budget-approval-not-ratified` で必ず fail-closed する。
   **Git の commit message / trailer を承認根拠にしてはならない** (段 2 プランのこの部分は破棄済み)。
   非 `None` のときだけ固定 path の approval raw bytes の sha256 と exact 一致を要求し、
   さらに `approval["budget"]` と入力 budget の **canonical bytes 完全一致**を要求する
   (`100` と `100.0` は不一致として扱う)。
3. **出力 gate** は段 2 プラン `:153-165` の `SafeA` 署名を実装する。
   検査と open の間に symlink 差替え窓を残さない (root FD から `O_NOFOLLOW` で component を辿り、
   leaf は `O_CREAT|O_EXCL|O_NOFOLLOW`)。通る正例は
   `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` の 1 件だけ。
4. `measurement_closure` は producer が再導出し、captured HEAD の blob として存在しない path が
   あれば candidate を作らない (fail-closed)。
5. CLI subcommand `generate-v2-candidate` を純増する。値入力は
   `--floor-result` / `--budget` / 任意 `--output` のみ。`--approver` 等の承認面は作らない。
   既存 `search` / `generate` / `verify` の引数・戻り値・rc を変えない。

## 絶対に守る制約

- **v1 の受理集合を 1 件も変えない。** `build_document` / `generate` / `verify_document` / `verify` /
  `verify_cli_with_t080_receipt` / `TOP_LEVEL_KEYS` / `GENERATION_SCHEMA_FIELDS` の**本体を変更しない**。
  新しい関数・定数の追加だけで実装する。
- `output/s8b-freeze/` 配下へ 1 byte も書かない。実 repo に候補ファイルを作らない
  (テストは tmp root で行う)。
- T-080 受領証・`V1_FREEZE_SHA256`・`FROZEN_MANIFEST`・transition table を変えない。
- 実 floor result を作らない。実走・queue 投入をしない。正例は synthetic fixture 経由に限る。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。既存テストが赤なら
  実装側が誤りである。期待値の方が誤りだと判断したら、実装を変えずに報告して止める。
- 指示にない受理集合の拡大・縮小をしない。scope を書く前に現行の受理・拒否挙動を明記する。
- docs を編集しない。commit しない (親が行う)。

## 検査と報告 (すべて満たすこと)

- 緑を主張するなら**走らせた nodeid と範囲を併記する**。実走できなかった項目は
  「実装済み・未実走」と書き、`closed` と申告しない。
- テストを新設・改名したら、それを制約する meta-test も走らせる。
- fixture へ現行 hash を差し込んでテストを甘くしない。期待値に working tree の hash 等の
  揮発する診断 payload を焼き込まない。揮発源を実際に編集しても緑か確認する。
- 完了報告に、**所有外の caller・共有 fixture・consumer test への波及可能性**を静的に列挙する。
- 親 docs が未 land のため期待して赤くなる finding 集合を事前指定し、それ以外は回帰として報告する。
- 赤の内訳を完了報告に明記する。

最後に `## 総括` 節を置き、実装の骨子と残ったリスクを 5 行以内でまとめる。
