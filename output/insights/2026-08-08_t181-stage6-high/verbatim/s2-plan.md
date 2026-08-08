必読資料はすべて指定絶対パスから読取可能だった。以下の行番号は現行 HEAD `6cc3e59a7102c2f6fd93896ebb445a4f93805ea0` の編集前アンカーである。書き込み・pytest・checker 実走は行っていない。

## 実装方針

### 1. worker 契約

[docs/dev-wave/workers.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:48) を一行置換する。

変更前、87 bytes:

```text
実装 wave は異なるレンズの敵対レビューを必ず 2 本並列で行う。
```

変更後、115 bytes:

```text
段 6 の review 子は `reasoning=high`。異なるレンズの敵対レビューを必ず 2 本並列で行う。
```

これを段 6 review 子すべての唯一の effort 規定とする。`DW-S06-A` の敵対レビュー 2 本と、`DW-S06-C` の焦点再レビューを包含する。literal `` `reasoning=high` `` 自体は 16 UTF-8 bytes。

[docs/dev-wave/workers.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:67) は次の一行置換にする。

変更前、77 bytes:

```text
並列 fix の統合後、焦点再レビューは全体へ 1 本でよい。
```

変更後、51 bytes:

```text
統合後、全体を焦点再レビューする。
```

`DW-S02` の `reasoning=max`（7行目）、`DW-S03` の `reasoning=max`（12行目）、`DW-S05-A` の `reasoning=high`（24行目）は一文字も変更しない。`DW-S06-B` に新しい effort literal は置かない。

### 2. checker

[tools/check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:264) 付近で既存 S02/S03 定数を維持したまま追加する。

```python
DEV_WAVE_DW_S06_A_REASONING_HIGH_LITERAL = "`reasoning=high`"
DEV_WAVE_DW_S06_A_REASONING_HIGH_FINDING = (
    "docs/dev-wave/workers.md: DW-S06-A の `reasoning=high` は段 6 review 子の"
    "現行 adoption pin と不一致 — 変更には採用裁定と pin の同時更新が必要"
)
```

finding は「A/B 未完了」などの時系列状態を断定せず、[D223:10507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/decisions.md:10507) の time-invariant 方針に合わせる。

[tools/check_docs.py:3382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3382) の `_check_dev_wave_reasoning_effort_pins()` は、期待値を tuple に持たせる。

```python
for section_id, expected_value, finding in (
    ("DW-S02", "max", DEV_WAVE_DW_S02_REASONING_MAX_FINDING),
    ("DW-S03", "max", DEV_WAVE_DW_S03_REASONING_MAX_FINDING),
    ("DW-S06-A", "high", DEV_WAVE_DW_S06_A_REASONING_HIGH_FINDING),
):
    ...
    if values != [expected_value]:
        findings.append(finding)
```

- S02/S03 の既存定数、finding、`["max"]` という受理集合は不変。
- exact-list 判定を membership 判定へ弱めない。
- S05-A、S06-B、S06-C は pin 対象へ追加しない。
- [production 呼出し:3576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3576) は既に full checker path に接続済みなので変更しない。

## byte 会計

`Path.read_bytes()` 相当で実測した現行値は次のとおり。

| 文書 | 現行 bytes | 変更後 |
|---|---:|---:|
| `core.md` | 8,646 | 8,646 |
| `workers.md` | 4,575 | 4,577 |
| `operations.md` | 8,301 | 8,301 |
| `mutation.md` | 3,674 | 3,674 |
| 合計 | 25,196 | 25,198 |

置換会計は以下。

- 追加する新二行: `115 + 51 = 166 bytes`
- 削除する旧二行: `87 + 77 = 164 bytes`
- 差引: `166 - 164 = +2 bytes`
- aggregate: `25,196 + 2 = 25,198 ≤ 25,200`、残り `2 bytes`
- workers: `4,575 + 2 = 4,577 ≤ 5,000`、残り `423 bytes`

行数を変えないため LF の増減はない。Python・テストの変更はこの四文書 aggregate の対象外である。

[REFERENCE_LIMITS:176-180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:176) と [DEV_WAVE_AGGREGATE_BYTES:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:254) は不変とする。

## 削減候補の安全性

`workers.md:48` の置換では「異なるレンズ」「敵対レビュー」「必ず」「2 本」「並列」を逐語で保持する。「実装 wave は」は、より明確な「段 6 の review 子は」と置き換わるため義務の縮小ではない。49–50行目の author 帰属・所見ゼロの変異確認も触らない。

`workers.md:67` の削減は次の根拠で安全である。

- 「統合後」と「全体を焦点再レビューする」は変更後にも残る。さらに節見出し [65行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:65) 自体が「統合後の再検証」である。
- 「1 本でよい」は現に stale。[F146:3391-3401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/failures.md:3391) は、一巡打切りが三回連続で新矛盾を残し、四巡必要だったと実測している。
- F146 の旧記述「DW-S06-C が対応表を要求」は、その後 [3414-3417行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/failures.md:3414) で明示的に stale と訂正されている。実際、現行 S06-C には対応表語も `regressed` 語もない。
- 現在の担い手 [DW-O16:83-87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:83) は `closed / partial / regressed` 対応表を必須化し、NO-GO 時は最大三巡後に変異付き裁定を要求する。
- [条件16:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/.claude/commands/dev-wave.md:98) が焦点再レビュー直前の O16 読了を強制する。

したがって削るのは誤った一巡上限と重複語だけであり、テスト弱体化禁止、期待赤、波及報告、復元規律、対応表などの安全義務は削らない。特に `workers.md:49-50,59-63,68-69` と O16 は無変更にする。

## pin の静的確認

[_reference_id_sections():1689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:1689) を現行本文へ当てた結果、`DW-S02`、`DW-S03`、`DW-S05-A`、`DW-S06-A/B/C` はそれぞれ一節だけ取得できる。

計画文面へメモリ上で二置換を適用し、現行 regex を当てた結果は次のとおり。

| 節 | 抽出節数 | effort 値列 |
|---|---:|---|
| DW-S02 | 1 | `["max"]` |
| DW-S03 | 1 | `["max"]` |
| DW-S05-A | 1 | `["high"]` |
| DW-S06-A | 1 | `["high"]` |
| DW-S06-B | 1 | `[]` |
| DW-S06-C | 1 | `[]` |

[DEV_WAVE_REASONING_EFFORT_RE:276-282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:276) は `reasoning=` 系だけを認識する。S06-B の [59行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:59) にある `reasoning/sandbox` は `=` がなく、`DW-S05-A` も単なる節 ID なので抽出されない。

したがって B の継承記述とは衝突しない。B は review 子ではなく fix 実装子であり、[commands:67-78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/.claude/commands/dev-wave.md:67) により S05-A の high を継承する。C へ literal を重複追加する必要もない。

## テスト設計

[fixture 生成:565-572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:565) に S06-A の high literal を追加し、[置換 helper:4796-4807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:4796) の mapping に S06-A を加える。

既存 helper の hard-coded `max/high` は `expected_value` と `wrong_value` を引数化し、既存 S02/S03 ケースの意味を変えない。

追加・拡張する nodeid:

- `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pins_accept_current_workers_contract`
  - 既存正例。実 repo の S02=max、S03=max、S06-A=high が通ることを確認。
- `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_max`
  - S06-A を max にした単純負例。
- `...::test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s06_a_value`
  - literal を削除した負例。
- `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates`
  - 可視 max＋comment/fence 内 high、可視 high＋max、high 二個を拒否。
- `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_real_keys_and_quotes`
  - `reasoning_effort=max`、`model_reasoning_effort="max"` 等を拒否。
- `...::test_dev_wave_reasoning_effort_pin_rejects_duplicate_dw_s06_a_section`
  - S06-A 節そのものが二個なら拒否。
- `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max`
  - `_build_min_repo()` の workers を high→max にし、`main()` 経由で非ゼロと S06 finding を確認。
- `...::test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples`
  - S06-A について可視 high＋comment/fence 内 max が通るケースを追加。
- `...::test_dev_wave_reasoning_effort_pin_findings_are_time_invariant`
  - 新しい S06 finding の逐語を追加し、S02/S03 の既存逐語 assertion は維持。
- `...::test_synthetic_repo_baseline_clean`
  - fixture に S06 literal を入れ忘れた変更を検出。
- `...::test_real_repo_clean`
  - 完成した実 repo 全体の正例。

実 repo を直接変異する production 負例は、統合 commit 後に [DW-O19:105-111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:105) に従う。

1. clean と anchor commit を記録。
2. 実 `docs/dev-wave/workers.md` の S06-A だけを high→max。
3. `git diff --stat` が対象一ファイル・一変異だけと確認。
4. `python3 tools/check_docs.py` が非ゼロかつ S06 finding を出すことを確認。
5. `git checkout -- docs/dev-wave/workers.md` で復元し、anchor と bytes を照合して clean を確認。

pytest は直接起動せず、親が `tools/run_tests.py` 経由で上記 nodeid、`test_check_docs.py` 全体、関連検査を走らせる。

## 波及

- [.agents/skills/dev-wave/SKILL.md:21-33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/.agents/skills/dev-wave/SKILL.md:21): 変更不要。worker/operations を直前に読む参照契約で、新しい pin を自動的に消費する。
- [.claude/commands/dev-wave.md:67-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/.claude/commands/dev-wave.md:67): 変更不要。S05-A/B/C と S06-A/B/C をすでに dispatch している。
- `docs/failures.md`: 変更不要。F146 は履歴として残し、3414–3417行目が現在の担い手 O16 を正しく示している。新規失敗がなければ failure を増やさない。
- `docs/decisions.md`: 追随が必要。ただし [core:89-93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/core.md:89) により canonical を直接編集せず、`docs/spool/` に新 decision fragment を作る。
- D207 と D223 は歴史的裁定なので改稿しない。新裁定には「T181 の六正例は非劣性・同等性の証明ではない」「その証拠限界を承知して段6 review 子へ high を採用」「S02/S03 max と S05-A high は不変」「S06-A が唯一の literal」を記録する。

## 変異候補

| # | 「効いていない」変異 | 殺す nodeid |
|---:|---|---|
| 1 | checker の tuple に S06-A を追加しない | `test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_max` |
| 2 | S06-A の期待値を誤って `max` にする | `test_dev_wave_reasoning_effort_pins_accept_current_workers_contract` |
| 3 | exact list を `"high" in values` に弱める | `test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates` |
| 4 | 最初の値だけを調べ、複数値を無視する | `test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates` |
| 5 | 実キー・引用符を regex から外す | `test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_real_keys_and_quotes` |
| 6 | comment/code fence の不可視化を外す | `test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples` |
| 7 | 重複 S06-A 節の先頭だけを受理する | `test_dev_wave_reasoning_effort_pin_rejects_duplicate_dw_s06_a_section` |
| 8 | full checker path から pin 呼出しを外す | `test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max` |

汎用化時に S02/S03 を high 受理へ壊す変異は、既存の `test_dev_wave_reasoning_effort_pin_rejects_dw_s02_high` と `...dw_s03_high` が殺す。

## 停止条件

並行 wave `dev-wave-t182-luna-stage3` も `workers.md` に触れうる。実装開始時に HEAD、旧二行、四文書 byte 数のいずれかが今回の実測と異なれば、この `+2 bytes` 証明は無効として停止し、land 後の内容から再計算する。上限引上げ、S02/S03/S05 の変更、安全義務からの追加削減で帳尻を合わせてはならない。

## 総括

- S06-A 一か所を段6 review 子の `reasoning=high` 正本にし、S06-C には重複 literal を置かない。
- stale な「1 本でよい」を除き、統合後・全体・焦点再レビューの義務は保持する。
- 文書差分は実測 `+2 bytes`、合計 `25,198 / 25,200` で残り 2 bytes。
- checker は S02=max、S03=max、S06-A=high を節別 exact-list pin する。
- テストは正例、max、欠落、複数値、実キー、重複節、full production path を覆う。
- 現時点に実装阻害要因はないが、並行 wave による文面・byte drift があれば再計算まで停止する。