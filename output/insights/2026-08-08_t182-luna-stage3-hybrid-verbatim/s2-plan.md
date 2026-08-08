静的読解の結論は、`DW-O01` を既定値、各 worker 節を上位指定とする案が最小かつ明確です。変更後は **25,197 / 25,200 bytes** です。ファイル変更・pytest・`check_docs.py` 実走は行っていません。

## 1. precedence 候補

バイト数は現行の `core=8,646 / workers=4,575 / mutation=3,674 / operations=8,301`、合計 25,196 を基準にした UTF-8 実数です。

| 案 | file:line と変更 | 正確な差分 | 制約 A | fail-closed |
|---|---|---:|---|---|
| **A: O01 で worker 優先を宣言（推奨）** | [workers.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:12) の `gpt-5.6-sol`→`gpt-5.6-luna`。 [operations.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:6) を `## DW-O01 — model: worker 節優先` に置換 | slug 11→12 = **+1**。見出し 37→37 = **±0**。合計 **+1** | workers 4,576、operations 8,301、総計 **25,197**。残り 3 bytes | **Yes**。DW-S02/S03 の明記値が O01 より上位。model 無記載の S05/S06 は O01 行8の sol が唯一の指定になる |
| B: S03 だけ局所優先 | [workers.md:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:10) を `## DW-S03 — model: 本節>DW-O01`、同:12 を luna に変更 | 見出し 32→34 = **+2**、slug **+1**、計 **+3** | workers 4,578、総計 **25,199**。残り 1 byte | **Yes**。S03 に限って優先元が一意。S05/S06 は O01 のみ |
| C: fallback 内蔵 placeholder | [operations.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:6) を `## DW-O01 — 起動`、同:8 の slug を `<worker節;既定=gpt-5.6-sol>` にし、workers:12 を luna に変更 | 見出し 37→20 = **−17**、model token 11→30 = **+19**、workers **+1**、計 **+3** | operations 8,303、workers 4,576、総計 **25,199** | 契約上は一意だが、擬似 placeholder の置換漏れと shell 解釈を別途保証できず、運用上の fail-closed は弱い |

推奨は案 A です。precedence の正本を、既定値を持つ `DW-O01` 自身に置けます。`DW-S05-A` / `DW-S06-A` への model 追記は不要です。安全義務を持つ [operations.md:8-12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:8) と [workers.md:13-17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:13) は一字も削りません。

案 B は一意ですが、記号的な局所例外で発見性が落ち、残りも 1 byte です。案 C は bare `<model>` と異なり S05/S06 の既定を保てますが、起動雛形を非実行的な記法にするため選びません。

## 2. `tools/check_docs.py` の変更

### 定数・正規表現

[check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:264) の reasoning 定数群の直前に、次を追加します。

- `DEV_WAVE_DW_S02_MODEL_SLUG = "gpt-5.6-sol"`
- `DEV_WAVE_DW_S03_MODEL_SLUG = "gpt-5.6-luna"`
- 節別の `DEV_WAVE_DW_S02_MODEL_FINDING` / `DEV_WAVE_DW_S03_MODEL_FINDING`
- `DEV_WAVE_CODEX_MODEL_RE`

抽出は canonical prose の `codex \`<slug>\`` を対象にします。

```python
DEV_WAVE_CODEX_MODEL_RE = re.compile(
    r"(?<![A-Za-z0-9_-])codex[ \t]+"
    r"`(?P<value>[A-Za-z0-9][A-Za-z0-9._-]*)`"
)
```

単に `gpt-...` を探す方式より、比較例や rollback 記述を model 指定と誤認しにくい形です。書式を `-m` 等へ変えた場合は抽出ゼロになり、明示的な pin 更新なしには通りません。

finding は D207 を根拠にしません。D207 は reasoning effort の裁定であり、model 変更の根拠は今回のユーザー裁定です。例えば次の意味に固定します。

> `DW-S03 の model は現行段別 pin gpt-5.6-luna と不一致 — 変更にはユーザー裁定と pin の同時更新が必要`

### 関数

[check_docs.py:3382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3382) の `_check_dev_wave_reasoning_effort_pins` の直前に、同型の `_check_dev_wave_model_pins(workers_text, findings)` を追加します。

処理は次のとおりです。

1. `("DW-S02", "gpt-5.6-sol", S02 finding)` と `("DW-S03", "gpt-5.6-luna", S03 finding)` を別々に走査する。
2. `_reference_id_sections` で節がちょうど 1 件か確認する。
3. `_visible_markdown_text` に通し、HTML comment と fenced code を候補から外す。
4. regex の `value` を列挙する。
5. `values != [expected]` なら finding を 1 件追加する。

これにより、欠落、別 slug、複数指定、可視 decoy の追加をすべて拒否します。

### 呼び出し元

[check_docs.py:3576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3576) の既存 block を次の順序にします。

```python
workers_text = decoded.get(_WORKERS)
if workers_text is not None:
    _check_dev_wave_model_pins(workers_text, findings)
    _check_dev_wave_reasoning_effort_pins(workers_text, findings)
```

既存 reasoning の定数・regex・関数は変更しません。`REFERENCE_LIMITS` と `DEV_WAVE_AGGREGATE_BYTES` も不変です。

## 3. テスト追加案

置き場は既存どおり [orchestrator/tests/test_check_docs.py:4796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:4796) 付近です。

まず、最小 repo producer の [test_check_docs.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:565) で、DW-S02/S03 の body にそれぞれ `codex \`<期待 slug>\`` を加えます。これがないと新 checker の production-path baseline が常時赤になります。

既存 reasoning helper と並べて、model 用の置換 helper と `_model_pin_findings()` を追加し、次を設けます。

- `test_dev_wave_model_pins_accept_current_workers_contract`
- `test_dev_wave_model_pin_rejects_dw_s02_non_sol`
- `test_dev_wave_model_pin_rejects_dw_s03_non_luna`
- `test_dev_wave_model_pin_rejects_missing_dw_s02_value`
- `test_dev_wave_model_pin_rejects_missing_dw_s03_value`
- `test_dev_wave_model_pin_rejects_decoys_and_duplicates`
- `test_dev_wave_model_pins_ignore_comment_and_fence_examples`
- `test_dev_wave_model_pin_rejects_comment_only_value`
- `test_dev_wave_model_pin_production_path_rejects_dw_s03_sol`
- `test_dev_wave_model_pin_findings_are_time_invariant`

production-path negative は `_build_min_repo()` の S03 を luna→sol にし、既存 [test_check_docs.py:2401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:2401) の `_assert_findings(root, S03_FINDING)` で、**違反理由がその 1 件だけ**であることまで固定します。これは呼び出し元から pin を外した場合にも赤になります。

fixture が期待定数を参照する一方、time-invariant test は `"gpt-5.6-sol"` / `"gpt-5.6-luna"` を独立した literal で assert し、checker と fixture の同時 drift を防ぎます。

なお、[tools/codex_reasoning_ab.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/codex_reasoning_ab.py:99) の `TRACKED_HASHES` は固定された `BASE_COMMIT`→`INTEGRATED_COMMIT` snapshot の hash です。現在の `check_docs.py` / test を編集しても更新対象ではありません。

## 4. `gpt-5.6-sol` consumer 棚卸し

archive / output / insights を除く tracked tree の全一致です。

### 本変更で更新するもの

- [docs/dev-wave/workers.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:12) — `DW-S03` の唯一の変更対象。

### 現役設定だが更新しないもの

- [docs/dev-wave/workers.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:7) — DW-S02 の sol pin。
- [docs/dev-wave/operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:8) — model 無記載 worker の既定 sol。
- [tools/codex_worker_launch.py:2475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/codex_worker_launch.py:2475) — 汎用 default。段3で利用するなら `--model gpt-5.6-luna` を明示し、global default は変えない。
- [tools/codex_reasoning_ab.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/codex_reasoning_ab.py:48) — T-181 の凍結 A/B 装置。
- [orchestrator/codex_roles/launcher.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/codex_roles/launcher.py:62) — 行 62, 130。
- [orchestrator/codex_roles/manifest.json:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/codex_roles/manifest.json:25) — 行 25, 208, 597, 740, 883, 1032, 1104, 1223, 1332, 1425。
- [orchestrator/codex_roles/spec.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/codex_roles/spec.py:609) — 行 609, 613, 615。
- `.codex/role-adapters/`: `auditor.json:80`, `axis-proposer.json:113`, `coder-v4-autonomous-sort.json:102`, `coder-v4-autonomous-trigger-gating.json:102`, `coder-v4-autonomous.json:96`, `critic-experiment.json:87`, `critic.json:46`, `planner-v4.json:54`, `profiler.json:69`, `selector-8b.json:191`。

後二群は native role-adapter 系で、現行 dev-wave は raw `codex exec` subprocess を使い、adapter は runtime blocked です。ここへ luna を足すのは別 subsystem の policy 変更になります。

### テスト fixture なので更新しないもの

- [test_check_ai_provenance.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_ai_provenance.py:37) — 行 37, 46, 164, 452, 2015, 2042, 2061, 2097, 2136, 2387, 2541, 2615。
- [test_codex_agents.py:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_codex_agents.py:461) — 行 461, 497。
- [test_codex_reasoning_ab.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_codex_reasoning_ab.py:203) — 行 203, 316, 517, 550。
- [test_codex_role_runtime.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_codex_role_runtime.py:651)。
- [test_codex_worker_launch.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_codex_worker_launch.py:380)。

### 現行ファイル内の歴史記録なので書き換えないもの

- [docs/decisions.md:2076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/decisions.md:2076) — 行 2076, 2350, 2353, 4095。
- [docs/failures.md:1296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/failures.md:1296) — 行 1296, 2522。
- [docs/phase3-main-experiment.md:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/phase3-main-experiment.md:238)。
- [docs/phase3.md:710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/phase3.md:710) — T-182 当時の shadow arm と「当時は policy 不変」という履歴。
- [docs/worklog.md:1807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/worklog.md:1807)。

特に T-182 の既存記述は採用根拠へ書き換えません。今回の後発ユーザー裁定は新しい decision/worklog fragment で追記します。

## 5. 記録物

- `docs/spool/worklog/2026-08-08-worktree-dev-wave-t182-luna-stage3-1.md:1` を新設。親が実測した受入結果だけを書き、`{{T:stage3-luna-partial-adoption}}` に「DW-S03 だけのユーザー裁定による部分採用」「T-184 は残る stage matrix/default policy を引き続き所有」「T-189 は妥当な比較実験と attestation 未解決を所有」を明記します。
- `docs/spool/decisions/2026-08-08-worktree-dev-wave-t182-luna-stage3-2.md:1` を新設。`{{D:stage3-luna-user-ruling}}` として採用根拠をユーザー裁定だけに限定します。
- rollback は「workers S03 を sol に戻す」「S03 model pin を同じ変更で sol に戻す」「focused test と `check_docs` を再実行」「S02/S05/S06/O01 は変更しない」と具体化します。
- T-182 の 91% / −31.6% は理由欄に使わず、非採用根拠であることだけを明記します。

## 6. DW-M01 変異事前登録候補

以下はいずれも、正常 fixture の reasoning、節構造、byte 予算を保ったまま、model pin だけを攻撃できます。

| ID | 変異位置 | 入力と唯一の期待赤 |
|---|---|---|
| M1 | [check_docs.py:3578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3578) 付近の `_check_dev_wave_model_pins(...)` 呼び出しを削除 | S03=luna→sol。production-path test の「S03 model finding が 1 件」が消えて赤 |
| M2 | [check_docs.py:3382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3382) 直前へ作る pin table から `DW-S03` tuple を削除 | 同じ S03=sol 入力。S02 と reasoning は正常で、S03 finding 欠落だけ |
| M3 | 新関数の `if values != [expected]` を `if values and values != [expected]` に弱化 | S03 の model 指定を削除。missing-model finding 欠落だけ |
| M4 | 同条件を `if expected not in values` に弱化 | S03 に luna と sol を可視に重複指定。duplicate-model finding 欠落だけ |
| M5 | `visible_section = _visible_markdown_text(...)` を raw section に変更 | 可視 model を削り、HTML comment 内だけに luna を置く。comment-only finding 欠落だけ |

前段の [check_docs.py:3525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3525) は読取・UTF-8・byte 上限しか見ず、後段の reasoning pin は [check_docs.py:3402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3402) で reasoning key だけを抽出します。dispatch/reference 検査も model slug を読みません。したがって上記入力を同じ理由で拒否する前後層はなく、`_assert_findings(..., S03_MODEL_FINDING)` の 1 件へ帰属できます。

## 7. 親 brief への反論

- **P1: 結論は正しい。** ただし S05/S06 は局所的に sol を pin しているのではなく、O01 の既定値を継承しています。記録ではこの差を明示すべきです。
- **P2: 正しい。** DW-S03 の単一契約が全並列レンズへ適用されるため、全て luna とするのが自然です。
- **P3: 誤り。** bare placeholder は指摘どおり S05/S06 追記を要求し不成立です。案 A の明示 precedence、または案 C の fallback 内蔵形なら追記なしで解けます。
- **P4: 誤り。** checker の中心ロジックは 1 関数で足りますが、regex/期待値/finding 定数、呼び出し元、最小 repo fixture、独立 negative、production-path negative が不可欠です。1 関数だけでは未接続または fixture 常時赤になります。
- さらに brief 70 行目の「docs 1 ファイル」は、推奨案 A では workers + operations の 2 ファイルになるため、段4の実装単位記述を修正する必要があります。

## 総括

- 推奨は `DW-O01` 見出しで `model: worker 節優先` を宣言し、DW-S03 だけ luna にする案です。
- reference 合計は 25,197 / 25,200、個別 cap も不変で、安全義務 prose は削りません。
- `check_docs` は DW-S02=sol / DW-S03=luna を節別・可視テキスト上で exact-one pin します。
- test は direct helper と production path の両方で、pin 欠落が単一 finding になることを固定します。
- 最大リスクは、この pin が文書契約しか保証せず、実際の起動引数や served model identity を attest しない点です。