# [T-098] selector rationale の LP 族拒否 — codex 子の逐語 (2026-07-26)

本ファイルは `/dev-wave` 1 wave で起動した codex 子 **9 本**の最終メッセージを逐語で凍結したものである。
統合 commit = `ef9ef76`、基準 = `c129e73`、branch = `worktree-dev-wave-t091-093-hardening`。
材料レポートは同ディレクトリの `2026-07-26_t098-selector-lp-reject.md`、
変異台帳は同 `-mutation-ledger.json`。

## 表記規約と defang (D88 (6))

検出対象の 3 バイト列そのものは本ファイルへ再掲しない。`tools/check_docs.py` の
`LITERAL_PLACEHOLDERS` を正本とし、宣言順に **LP-1 / LP-2 / LP-3** と呼ぶ。

子の出力に含まれていた LP の literal 出現は、**全角山括弧への 1:1 可逆置換**
(`<` → `＜`、`>` → `＞`、内側の文字列は不変) で defang した。置換後に対象 3 族の gate 語で
**0 hit** であることを機械検査済みである。原文はこの置換を逆に適用すれば復元できる。

各節の見出しに **原文 (defang 前) の SHA-256 と byte 数、LP の出現回数**を併記する。

| 節 | 原文 SHA-256 | 原文 bytes | LP 出現 |
|---|---|---|---|
| plan.md | `d15060481f7bc4c5ff153a19df5cd7226b4b1312568a32bb2a6c13a15d721329` | 16150 | 0 |
| adv-A.md | `623983547dd5f420e3c2a4e80a83967fcb3a7ebaf01ea4e3705872b75df3d46b` | 6662 | 0 |
| adv-B.md | `80878fe7c958a852cf14f6e0259519fcffbe726bca2b9d71d4adc1ff5a9bfa61` | 13748 | 0 |
| impl.md | `09ea7e98c0d0f2b6a4a8ba68ce785ae8ca058418a358c23a8dc7915ce63e8c88` | 5752 | 0 |
| rev-A.md | `7eb22cff8c38da38448906fca55c12e6212edece2c881545f6be4194754b6b22` | 462 | 0 |
| rev-B.md | `2622846906d1c8706c1216b82a04b9b44445180b804f007213eb75f3b0a2f3b9` | 9772 | 6 |
| fix.md | `f0aa1cb8859e52fb176d23118becf24196123e216d49b878d3e62be76e665c1d` | 4294 | 0 |
| refocus.md | `524cb1e67a99be79731fc06ae7443182cc649d90350f70df8898ac01bc6aacb3` | 10084 | 0 |
| fix2.md | `6279846c24ff9f429b022fc32b9f1384c5a7d3aa9e922ae7f0a45c59bcf80b81` | 2238 | 0 |

---

## 段 2 プラン起草 (codex gpt-5.6-sol / reasoning=max / read-only)

- 原文 SHA-256: `d15060481f7bc4c5ff153a19df5cd7226b4b1312568a32bb2a6c13a15d721329`
- 原文 bytes: 16150
- LP の literal 出現 (defang 済み): 0

## 1. `s8b_selector_output.py` の差分案

対象は現行 [`s8b_selector_output.py:11–14`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:11) と [`:110–118`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:110)。

### 定数

現行 13 行目 `_MAX_RATIONALE_LENGTH` の直後へ、次を追加する。

```python
_RATIONALE_LITERAL_PLACEHOLDERS = (
    # tools/check_docs.py:94-96 の LP-1、LP-2、LP-3 を同じ順序で複製
)
```

実際の右辺は [`tools/check_docs.py:93–97`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:93) の三つの文字列 literal をそのまま列挙する。

`LITERAL_PLACEHOLDERS` と同名にはしない。`tools.check_docs` 側は文書 lint の正本、parser 側は rationale 用の runtime mirror であり、同名識別子にするとレビュー・検索時に二義化するためである。先頭 `_` と `RATIONALE` を付けて用途も限定する。

### 検査

現行 115–116 行目の `rationale_too_long` 検査の後、118 行目の `return SelectorDecision` の前へ追加する。

```python
if any(
    placeholder in rationale
    for placeholder in _RATIONALE_LITERAL_PLACEHOLDERS
):
    raise SelectorOutputError(
        "rationale_placeholder",
        "rationale に literal placeholder を含めてはならない",
    )
```

確定値は以下。

- 定数名: `_RATIONALE_LITERAL_PLACEHOLDERS`
- error code: `rationale_placeholder`
- 例外メッセージ: `rationale に literal placeholder を含めてはならない`
- 対象: JSON decode 済みの `rationale` のみ
- 照合: case-sensitive な `substring in`。strip、正規化、casefold、正規表現は使わない
- 位置: `rationale_blank` と `rationale_too_long` の両方の後

### 診断順序

| 入力 | 採用位置での code | blank と too-long の間に置いた場合 |
|---|---|---|
| LP-1 単独 | `rationale_placeholder` | 同じ |
| 空白だけ | `rationale_blank` | 同じ。LP は非空白なので競合しない |
| LP-1 を含む長さ 2001 の文字列 | `rationale_too_long` | `rationale_placeholder` に変わる |

最後の入力は変更前から `rationale_too_long` だったため、両検査の後へ置くことで既存 error code を維持する。受理集合は「長さ 1～2000 の既存受理文字列のうち LP-1/2/3 を含むもの」だけ縮小され、それ以前に拒否されていた入力の code は変わらない。

### P1〜P6

| 裁定 | 採否 | 理由 |
|---|---|---|
| P1 | 採用 | parser 内に literal tuple を持ち、テストで `check_docs` と等号束縛する。runtime import はしない |
| P2 | 採用 | decode 済み `rationale` の substring 検査により JSON escape も同じ文字列として検出できる |
| P3 | 採用 | 新規 code `rationale_placeholder` に原因を分離する |
| P4 | 採用 | blank／too-long の既存診断を保存する |
| P5 | 採用 | `choice_id` は既存 enum 検査に任せ、rationale だけを対象にする |
| P6 | 採用 | LP 三語以外、他 producer、他 JSON 族へ拡張しない |

schema、role、freeze 成果物には差分を作らない。

## 2. `test_s8b_selector_output.py` の追加テスト案

[`test_s8b_selector_output.py:5`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:5) に `import ast`、現行 19 行目の後に `CHECK_DOCS_PATH`、現行 35 行目の後に AST helper と語彙定数を追加する。rationale の負例は現行 blank テストの後、優先順位テストは現行 126–127 行目の too-long テストの近傍へ置く。

`lp-1` 等の parametrization ID は AST 抽出した宣言順から作る。

| 提案 nodeid | 入力 | 期待 |
|---|---|---|
| `test_literal_placeholder_rationale_is_rejected[lp-1/2/3]` | rationale が各 LP 単独 | code=`rationale_placeholder`、上記の例外メッセージ |
| `test_embedded_literal_placeholder_rationale_is_rejected[lp-1/2/3]` | `"x"*1000 + LP-n + "y"*(1000-len(LP-n))`。全長 2000 | code=`rationale_placeholder` |
| `test_json_escaped_literal_placeholder_rationale_is_rejected[lp-1/2/3]` | `_raw()` の `<`/`>` をそれぞれ `\\u003c`/`\\u003e` に置換 | code=`rationale_placeholder` |
| `test_rationale_too_long_takes_precedence_over_placeholder` | LP-1 を含む全長 2001 | code=`rationale_too_long` |
| `test_placeholder_body_without_delimiters_is_accepted[lp-1/2/3]` | 各 LP から外側 delimiter を除いた文字列 | 正常受理。検出の一般化を防ぐ |
| `test_placeholder_vocabulary_matches_check_docs` | AST 抽出 tuple と parser tuple | 宣言順を含む完全一致 |
| 既存 `test_all_choice_ids_are_accepted_with_rationale_and_raw_hash[c01…c06]` | rationale=`"理由"` | 従来どおり `SelectorDecision` と raw hash が一致 |

JSON escape テストには、テスト自体の有効性を示す次の二つの assert も置く。

```python
assert placeholder not in raw
assert json.loads(raw)["rationale"] == placeholder
```

現行 `_assert_code` は `caught.value` を返す形へ拡張し、単独ケースで `str(error)` も固定メッセージと照合する。既存呼び出しは返り値を無視できるため影響しない。

## 3. `check_docs` 語彙との import なし束縛

現行 [`test_s8b_selector_output.py:13–19`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:13) 周辺へ次を追加する。

```python
CHECK_DOCS_PATH = _HERE.parents[1] / "tools/check_docs.py"


def _extract_literal_string_tuple(path: Path, name: str) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            values.append(ast.literal_eval(node.value))

    assert len(values) == 1
    value = values[0]
    assert isinstance(value, tuple)
    assert value
    assert all(isinstance(item, str) and item for item in value)
    return value


_DOCS_LITERAL_PLACEHOLDERS = _extract_literal_string_tuple(
    CHECK_DOCS_PATH,
    "LITERAL_PLACEHOLDERS",
)
_LP_IDS = tuple(
    f"lp-{index}"
    for index in range(1, len(_DOCS_LITERAL_PLACEHOLDERS) + 1)
)


def test_placeholder_vocabulary_matches_check_docs():
    assert (
        _DOCS_LITERAL_PLACEHOLDERS
        == s8b_selector_output._RATIONALE_LITERAL_PLACEHOLDERS
    )
```

一致方向は包含ではなく、順序付き tuple の等号とする。

- `check_docs` だけに LP が追加されれば左辺が長くなり必ず失敗する。
- parser だけに語彙が追加されても失敗する。
- 宣言順の変更も失敗する。LP-n が宣言順で定義されているため必要な束縛である。
- 負例 parametrization も `_DOCS_LITERAL_PLACEHOLDERS` を入力源にするため、parser から一語を落としてもその LP ケース自体は消えない。
- `tools.check_docs` の import・実行・副作用は発生しない。

## 4. 波及の静的棚卸し

### 実行経路

Python の symbol/path 横断検索で該当した production consumer は次の全件。

| 箇所 | 波及 |
|---|---|
| [`s8b_selector_freeze.py:370–395`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:370) `record_agent_attempt` | 今後の LP 応答を `status="invalid"`, `choice_id=None`, `parser_error_code="rationale_placeholder"` として返す。fallback はない |
| [`s8b_selector_freeze.py:175–209`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:175) `_reparse_agent_raw` | seal 済み valid row の raw が LP を含めば、新 parser は invalid を再導出し、記録済み valid と不一致として fail-closed になる |
| [`s8b_selector_freeze.py:879–905`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:879) `verify_prediction_freeze` | on/swapped の valid/invalid row を現行 parser で再 parse。off row は対象外 |
| [`s8b_prediction_runner.py:881–898`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:881) | 新規 agent 応答の invalid 結果と新 code を invocation record に透過記録する。code の enum 制約はなく、非空文字列として既存構造に収まる |
| [`s8b_prediction_runner.py:1429–1463`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:1429) | worktree の parser bytes を読み、新規 journal header の `parser_module_sha256` に使う |
| [`s8b_verdict.py:199–213`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_verdict.py:199) | `verify_prediction_freeze` 経由で現行 parser の再 parse 結果を受ける |
| [`s8b_floor_campaign.py:1355–1407`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1355) | prediction は現行 parser で再検証する一方、journal header の parser hash は `pre_oracle_head` blob から導出する |
| [`s8b_ratified_freeze.py:2523–2623`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_ratified_freeze.py:2523) | launch 射影は parser を実行せず、`pre_oracle_head` blob の hash を使用するため worktree parser 編集に不感 |

`_normalise_rows` は invalid row の `parser_error_code` を非空文字列として検証するだけで code 列挙を持たないため、consumer 側のコード変更は不要。

### 既存 seal と runner pin

現状の parser SHA と journal 1 行目の `parser_module_sha256` はともに `b8de4467…`。実装後は worktree parser SHA だけが変わるが、既存 journal は更新しない。

- 実際の `selector_predictions.json` が存在する状態で `seal()` を再実行すると、まず [`s8b_prediction_runner.py:1407–1409`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:1407) の既存 prediction 拒否で停止する。
- prediction 未生成の crash-resume 状態で旧 journal だけが残っている場合は、新しい worktree parser hash で binding を組み、[`ensure_run_header` → `_validate_header`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:367) が旧 header との不一致を `run_header.parser_module_sha256` で拒否する。
- floor/ratified launch 検証は旧 `pre_oracle_head` blob から旧 hash を再導出するため、既存 journal の歴史 pin は維持される。

### 実成果物

静的検索では、次の四つの agent raw、prediction の四つの agent rationale、journal の四つの invocation rationaleのいずれにも LP-1/2/3 はない。このため現行 parser での再 parse 結果は変わらない見込みだが、親が実走確認する必要がある。

bytes を変更しない対象は全て以下。

- `output/s8b-freeze/selector_predictions.json`
- `output/s8b-freeze/selector-runs/journal.jsonl`
- `raw_rr20_on.txt`
- `raw_rr20_swapped.txt`
- `raw_rr80_on.txt`
- `raw_rr80_swapped.txt`
- `payload_rr20_on.json`
- `payload_rr20_swapped.json`
- `payload_rr80_on.json`
- `payload_rr80_swapped.json`
- `envelope_rr20_on.json`
- `envelope_rr20_swapped.json`
- `envelope_rr80_on.json`
- `envelope_rr80_swapped.json`

payload/envelope は parser の意味検査対象ではない。prediction の `sources` 五件にも parser は含まれない。`holdout_freeze`、builder、role、input schema、output schema は全て no-touch とし、とくに output schema と role の SHA 照合を壊さない。

### 親が実行すべきテスト・検査

新規テストを含む必須ファイル:

- `orchestrator/tests/test_s8b_selector_output.py`

直接 consumer の重点 nodeid:

- `test_s8b_selector_freeze.py::test_record_agent_attempt_valid_and_invalid_never_falls_back`
- `test_s8b_selector_freeze.py::test_verify_binds_role_raw_and_exact_agent_provenance_to_files`
- `test_s8b_selector_freeze.py::test_verify_reparses_raw_and_rejects_forged_valid_agent_rows`
- `test_s8b_selector_freeze.py::test_verify_reparse_detects_choice_swap_and_off_row_agent_fields`
- `test_s8b_prediction_runner.py::test_invalid_raw_recorded_as_invalid_without_fallback`
- `test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected`
- `test_s8b_prediction_runner.py::test_materialize_seals_predictions_and_verifies`
- `test_s8b_prediction_runner.py::test_seal_claim_crash_resumes_and_seals_six_rows_with_missing`
- `test_s8b_prediction_runner.py::test_seal_success_runs_four_agents_two_static_and_reloads_destination`
- `test_s8b_verdict.py::test_verify_prediction_happy_path_returns_verified`
- `test_s8b_floor_campaign.py::test_floor_preflight_allowlist_hashes_verified_prediction_and_selector_run_files`
- `test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e`
- `test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence`
- `test_frozen_artifacts.py::test_frozen_artifacts_match_manifest`

波及検索で該当したテストファイルの全走対象は次の八本。

- `test_s8b_selector_output.py`
- `test_s8b_selector_freeze.py`
- `test_s8b_prediction_runner.py`
- `test_s8b_verdict.py`
- `test_s8b_floor_campaign.py`
- `test_s8b_ratified_freeze.py`
- `test_s8b_ratified_verify.py`
- `test_frozen_artifacts.py`

実成果物の受入には以下も必要。

```bash
python3 orchestrator/campaign/s8b_selector_freeze.py verify \
  --path output/s8b-freeze/selector_predictions.json \
  --freeze output/s8b-freeze/holdout_freeze.json \
  --root .
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

commit 後は `python3 tools/check_ai_provenance.py`。この worker は pytest・CLI 検査を実走していない。

## 5. 変異候補

「旧」は変更前 HEAD のテストだけを mutant 実装へ当てた場合、「新」は本計画の追加テストを含む場合。

| ID | 変異 | 新テスト | 変更前 HEAD テスト | 帰属 |
|---|---|---|---|---|
| M1 | placeholder guard 全体を削除、または条件を常に false にする | KILL: 単独ケース | SURVIVE | 成立 |
| M2 | `_RATIONALE_LITERAL_PLACEHOLDERS` から LP-2 を一つ削除 | KILL: AST 等号と LP-2 の挙動ケース | SURVIVE | 成立 |
| M3 | `placeholder in rationale` を `rationale == placeholder` にする | KILL: 長文埋め込み | SURVIVE | 成立 |
| M4 | decode 済み `rationale` ではなく raw JSON の `raw` を検索する | KILL: JSON escape ケース | SURVIVE | 成立 |
| M5 | error code を `rationale_too_long` 等へ置換する | KILL: code assert | SURVIVE | 成立 |
| M6 | placeholder guard を too-long 検査より前へ移動する | KILL: 2001 文字の優先順位ケース | SURVIVE: 既存 2001 文字ケースは LP を含まない | 成立 |
| M7 | `placeholder[1:-1] in rationale` など delimiter を除いて照合する | KILL: delimiter なし正例 | SURVIVE | 成立 |
| M8 | `_MAX_RATIONALE_LENGTH` を 3000 に変える負の対照 | KILL: 優先順位ケースと既存 too-long ケース | KILL: 既存 `test_rationale_over_maximum_length_is_rejected` | 帰属不成立。LP 実装の検出力証拠には数えない |

M1〜M7を本変更の mutation evidence とし、M8は「新旧双方 KILL」のため ledger 上も非帰属 control と明記する。

---

## 段 3 敵対相談 A — 受理集合と証拠鎖 (max / read-only)

- 原文 SHA-256: `623983547dd5f420e3c2a4e80a83967fcb3a7ebaf01ea4e3705872b75df3d46b`
- 原文 bytes: 6662
- LP の literal 出現 (defang 済み): 0

静的検査のみを行い、pytest は実走していない。

照合できた事実は次のとおり。

- 現行 artifact は 6 rows で、非 null rationale 4 件に LP はなく、残る 2 件は null：`output/s8b-freeze/selector_predictions.json:43-83`, `:85-133`, `:135-174`
- worktree 再読の `sources` は実際に 5 ファイルだけ：`orchestrator/campaign/s8b_selector_freeze.py:61-65`, `:888-893`
- parser はその集合に含まれず、別途 journal binding に入る：`orchestrator/campaign/s8b_prediction_runner.py:97-109`, `:1426-1455`
- 関連 fixture の rationale に LP は見つからない：`orchestrator/tests/test_s8b_selector_output.py:22-29`, `test_s8b_selector_freeze.py:62-71`, `test_s8b_prediction_runner.py:87-96`, `test_s8b_floor_campaign.py:2751-2771`
- 提案された guard は既存の blank/長さ検査後に拒否を追加するだけで、静的には受理集合を広げる例外・早期 return・順序変更はない：`orchestrator/campaign/s8b_selector_output.py:110-122`, `plan.md:19-51`
- invalid 時の既定 choice fallback はない。choice は null になり、verdict は indeterminate を明示する：`orchestrator/campaign/s8b_selector_freeze.py:379-387`, `orchestrator/campaign/s8b_verdict.py:356-367`, `:442-443`

## A-1 floor 検証は worktree parser に不感ではない

深刻度: must-fix

根拠:

- brief は floor 側も `pre_oracle_head` blob から再計算するため worktree 編集に不感と述べる：`brief.md:21-27`
- 実際には floor preflight が最初に `verify_prediction_freeze()` を呼ぶ：`orchestrator/campaign/s8b_floor_campaign.py:1355-1372`
- この verifier は raw を読み、現在 import されている parser で再 parse する：`orchestrator/campaign/s8b_selector_freeze.py:175-209`, `:879-902`
- `pre_oracle_head` の parser hash を使うのは、その後の journal binding 検査だけ：`orchestrator/campaign/s8b_floor_campaign.py:1374-1407`
- plan 自身も floor では現行 parser による再検証があると認識しており、brief と矛盾する：`plan.md:158-159`

成果物影響: LP を含む seal 済み valid row は floor launch では新たに拒否され、同じ prediction/journal の受理集合が ratified 検証と分裂する。現行 6 rows は LP 0 件なので、今回の既存 bytes が変わらない理由は「不感」ではなくデータ依存である。

## A-2 ratified proof chain は新しい gate を一度も実行しない

深刻度: blocker

根拠:

- ratified 側の prediction 検査は構造検査だけ：`orchestrator/campaign/s8b_ratified_freeze.py:2523-2542`
- parser hash は `pre_oracle_head` blob から算出されるが、その blob は実行されない：`orchestrator/campaign/s8b_ratified_freeze.py:2580-2601`
- journal 解決も shape・binding・行対応の検査であり、raw の再 parse はしない：`orchestrator/campaign/s8b_ratified_freeze.py:2603-2625`, `:2627-2700`
- 構造検査上、valid row に必要なのは enum choice と非空 rationale 等だけである：`orchestrator/campaign/s8b_selector_freeze.py:814-823`
- plan はこの非実行を記載しているが、proof-chain 上の保証欠落として裁定していない：`plan.md:159`, `:171-192`

静的推論: prediction と journal が互いに整合し、raw hash も一致していれば、LP を含む raw を `status="valid"` とした証拠も ratified selector exemption を通過し得る。

成果物影響: ratified レポート・台帳は、LP 排除を証明していない selector evidence を valid な proof-chain 参照として保持でき、「certified 選択の rationale は LP ではない」という結論を独立再検証できない。

## A-3 schema と producer role は新しい受理集合を表現していない

深刻度: must-fix

根拠:

- schema は rationale に文字列・長さしか課さず、3 LP をすべて受理する：`orchestrator/schemas/s8b_selector_output_schema.json:4-12`
- selector role も「非空 rationale」しか要求しない：`.claude/agents/selector-8b.md:66-78`
- 一方、提案 parser はそれらを `rationale_placeholder` として拒否する：`plan.md:19-41`
- schema と role は sealed prediction の pinned `sources` である：`output/s8b-freeze/selector_predictions.json:18-24`, `orchestrator/campaign/s8b_selector_freeze.py:888-893`

これは scope 外のファイルを今すぐ変更せよという指摘ではない。既存 seal を壊さず解決するには、parser-authoritative 契約の明文化、または versioned schema/role への移行を裁定パッケージにする必要がある。

成果物影響: producer が schema-valid・role-compliant な LP を返しても台帳では invalid/choice null となり、verdict は indeterminate になる一方、schema 準拠記録だけを見るレポートは入力不正を説明できない。

## A-4 「既存 journal の再 launch は header mismatch」は経路を限定していない

深刻度: nit

根拠:

- 既存 prediction がある seal 再実行は parser を読む前に拒否される：`orchestrator/campaign/s8b_prediction_runner.py:1407-1409`
- parser 読み込みと header 検証はその後：`orchestrator/campaign/s8b_prediction_runner.py:1426-1463`
- parser hash mismatch が成立するのは、prediction 未生成で journal だけが残る crash-resume 経路である。plan はこの限定を正しく書いている：`plan.md:163-169`
- brief は限定せず「既存 journal 再 launch」としている：`brief.md:26-27`

成果物影響: certified 値や artifact bytes は変わらないが、失敗参照が `prediction already exists` と `journal header mismatch` のどちらになるかという診断記録を誤る。

## A-5 plan の検証表は floor と ratified の受理差を証拠化しない

深刻度: must-fix

根拠:

- 新規テストは parser 単体の拒否・順序・delimiter 正例に限られる：`plan.md:66-142`
- consumer 側は既存 nodeid の再実行だけで、LP を含む同一 evidence が floor では拒否され、ratified では非検査となる境界テストがない：`plan.md:194-226`
- floor fixture は通常 rationale のみ：`orchestrator/tests/test_s8b_floor_campaign.py:2751-2771`
- ratified fixture も通常 rationale のみ：`orchestrator/tests/test_s8b_ratified_freeze.py:554-562`

成果物影響: テスト証拠だけでは、同じ prediction/journal が floor certificate と ratified report で異なる受理結果になることを説明できず、proof-chain の保証範囲が過大表示される。

**NO-GO**

---

## 段 3 敵対相談 B — 検出力・迂回経路・テスト帰属 (max / read-only)

- 原文 SHA-256: `80878fe7c958a852cf14f6e0259519fcffbe726bca2b9d71d4adc1ff5a9bfa61`
- 原文 bytes: 13748
- LP の literal 出現 (defang 済み): 0

静的検査のみ。pytest・CLI は実走していないため、以下の KILL / SURVIVE はコード上の予測である。

## B-1 gate は恒真ではないが、実到達経路のテストがない

深刻度: **must-fix**

根拠: [`selector-8b.md:68–78`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/.claude/agents/selector-8b.md:68)、[`s8b_selector_input.py:102–111`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_input.py:102)、[`s8b_prediction_runner.py:1125–1231`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:1125)、[`s8b_prediction_runner.py:847–895`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:847)、[`s8b_selector_freeze.py:370–395`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:370)

payload は固定 descriptor と固定 catalog だけで組み立てられ、role 本文にも LP は現れない。したがって入力からのコピー経路はない。到達源は、headless LLM が自由生成する envelope `result` だけである。しかし `result` は文字列型以外を制限されず、そのまま `record_agent_attempt` → `parse_selector_output` へ渡るため、LP 出力は実際に到達可能であり、gate は飾りではない。

問題は、提案テストが parser 直呼びだけであること。現行 consumer テストは `not json` または `markdown_fence` しか流していない（[`test_s8b_selector_freeze.py:232–244`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_freeze.py:232)、[`test_s8b_prediction_runner.py:405–428`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:405)）。collector が新 code だけを書き換える、または旧 parser 相当で再判定する誤実装は、提案テストと既存 consumer テストをともにすり抜ける。

fake provider から LP rationale を `drive_journal` へ流し、journal と materialized row の `status="invalid"`、`choice_id/rationale=None`、新 code を固定するテストが必要である。

放置したときの成果物影響: LP rationale が `valid` row として `selector_predictions.json` に入り、当該 `choice_id` が certified 選択へ影響するか、少なくとも journal の `parser_error_code` が別値になる。

## B-2 exact-only の回避経路は広く、拒否拡張ではなく境界テストが不足している

深刻度: **must-fix**

根拠: [`brief.md:35–56`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/brief.md:35>)、[`plan.md:72–87`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/plan.md:72>)、[`decisions.md:3863–3868`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3863)、[`test_check_docs.py:1506–1522`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:1506)

想定される表記と本 wave の扱いは次のとおり。

| 表記 | 現仕様での結果 | 扱い |
|---|---|---|
| JSON の `\u003c` / `\u003e` | decode 後 exact LP なので拒否 | 本 wave で負例必須 |
| LP 本文の一文字を `\uXXXX`、大文字 hex、混在 escape | decode 後 exact LP なので拒否 | 現案に欠落。本 wave で追加 |
| LP-1 と LP-2 を同一 rationale に含める | exact substring があるので拒否 | 現案に欠落。本 wave で追加 |
| 全角山括弧、別種括弧 | 受理 | 検出拡張は T-100。受理を固定する正例は本 wave 内 |
| HTML entity / numeric entity | 受理 | 検出拡張は T-100。受理を固定する正例は本 wave 内 |
| token 内への空白・改行・U+200B 挿入 | 受理 | 検出拡張は T-100。受理を固定する正例は本 wave 内 |
| delimiter 除去 | 受理 | 現案で正例あり |
| token 外側の空白・backtick | exact LP は残るので拒否 | substring 契約の負例候補 |

全角、entity、正規化差、空白挿入を新たに拒否する提案は、却下済み一般化に該当するため本 wave 外である。ただし、それらが受理され続けることを固定する正例は一般化ではなく、brief の「受理集合は exact LP の分だけ縮小」という契約の検査である。

放置したときの成果物影響: 意図的な別表記は valid rationale として certified 選択へ残る一方、誤って NFKC・HTML decode・空白除去を入れた実装は承認外に受理集合を縮小し、valid row を invalid に変える。

## B-3 提案テストは個別には恒真化でき、結合後も生き残る誤実装がある

深刻度: **must-fix**

根拠: [`plan.md:72–89`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/plan.md:72>)、[`test_s8b_selector_output.py:38–46`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:38)

各 assert だけを通す誤実装を構成できる。

| 提案テスト | 通してしまう誤実装 |
|---|---|
| LP 単独拒否 | `rationale == placeholder` のときだけ拒否。埋め込みを受理 |
| 2000 文字埋め込み | `"x"*1000` で始まる fixture 形だけ検索 |
| JSON escape | raw に対し小文字 `\\u003c` / `\\u003e` だけ置換して検索。本文 escape や大文字 hex は受理 |
| too-long 優先 | `len == 2001` かつ LP-1 の場合だけ先に too-long。2002 文字や LP-2/3 では code が逆転 |
| delimiter なし正例 | 完全一致する body だけ例外受理し、body を含む通常文は過剰拒否 |
| 語彙一致 | tuple は一致させるが、guard は空集合または hard-code を使用 |
| 既存全 choice 正例 | `rationale == "理由"` の場合だけ全 ID を受理し、他の正常 rationale を拒否 |

さらに、提案テスト一式をまとめても次は SURVIVE する。

- `unicodedata.normalize("NFKC", rationale)` 後に検索する実装
- `html.unescape(rationale)` や token 内空白除去後に検索する実装
- raw の小文字 angle escape だけを手動復号する実装
- `sum(placeholder in rationale for ...) == 1` とし、異なる LP を二つ含む rationale を受理する実装
- too-long 優先を LP-1 にだけ特別実装するもの
- collector が `rationale_placeholder` だけ別 code または valid に変換するもの

したがって、近似表記の正例、内部 Unicode escape、複数 LP、全 LP の priority、provider-to-row の統合負例が必要である。

放置したときの成果物影響: 同じ提案テスト結果でも、実装ごとに accepted rationale 集合、invalid row 数、`parser_error_code` が異なり、certified 選択と台帳が一意に定まらない。

## B-4 AST 語彙束縛は silent stale subset を許す

深刻度: **blocker**

根拠: [`plan.md:99–116`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/plan.md:99>)、[`plan.md:129–142`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/plan.md:129>)、[`check_docs.py:93–97`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:93)、[`test_check_docs.py:419–436`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:419)

直接 tuple に一語追加する通常変更については、等号の向きは正しい。`check_docs` のみ増えれば左辺が長くなり、parser の追随不足を検出する。

しかし helper はトップレベル `ast.Assign` だけを収集し、それ以外を黙って無視する。次の正当な Python 変更では恒真化する。

```python
LITERAL_PLACEHOLDERS = (
    # 現行三語
)
LITERAL_PLACEHOLDERS += ("追加語",)
```

AST helper は最初の三語だけを返し、parser tuple との等号も、負例 parametrization も三語のまま成立する。一方、実行時 `check_docs` は四語を検出する。これは静かな stale subset である。

宣言削除・`AnnAssign` 化・空 tuple は `assert len(values) == 1` / `assert value` により通常実行では fail-loud であり、静かな空集合経路ではない。ただし、それで `AugAssign` の穴は埋まらない。また、両側を同時に四語へ増やす変更も等号だけでは P6 の「三語固定」を検出しない。

既存流儀は production 定数から導出せず、三語を test-local に独立記述して positive control を作っている。修正条件は、少なくとも次の二つである。

1. 承認済み三語の独立 expected tuple と、docs/parser の双方を照合する。
2. 対象名への Store が一つのトップレベル `Assign` だけであることを検査し、`AugAssign`・再束縛を拒否する。

放置したときの成果物影響: `check_docs` が新 LP を拒否しても selector parser は同じ語を valid として受理し、docs gate と certified selector の受理集合が無警告で分岐する。

## B-5 M1〜M7 の帰属は成立するが、変異集合が弱い

深刻度: **must-fix**

根拠: [`plan.md:241–256`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/plan.md:241>)、[`test_s8b_selector_output.py:126–127`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:126)

静的帰属は次のとおり。

| 変異 | 判定 |
|---|---|
| M1 guard 削除 | 新単独負例が KILL、旧は LP を使わず SURVIVE |
| M2 LP-2 削除 | 新等号・LP-2 負例が KILL、旧 SURVIVE |
| M3 `in` → `==` | 新埋め込み負例が KILL、旧 SURVIVE |
| M4 decoded → raw 検索 | 新 escape 負例が KILL、旧 SURVIVE |
| M5 code 置換 | 新 code assert が KILL、旧 SURVIVE |
| M6 guard を length 前へ移動 | 新 2001 文字 priority が KILL、旧 2001 文字は LP なしで SURVIVE |
| M7 delimiter 除去検索 | 新 delimiter なし正例が KILL、旧 SURVIVE |
| M8 max=3000 | 新旧とも KILL。計画どおり帰属不成立 |

したがって、M1〜M7 に名指しすべき帰属誤りはない。M8 だけが非帰属である。

ただし、より鋭い事前登録候補は以下である。

- S1: AST `AugAssign` 追加 — 現提案新テストも SURVIVE
- S2: NFKC / HTML unescape / 空白除去してから検索 — 現提案新テストも SURVIVE
- S3: raw の angle escape だけ手動復号 — 現提案新テストも SURVIVE
- S4: 異なる LP がちょうど一語だけ含まれる場合のみ拒否 — 現提案新テストも SURVIVE
- S5: too-long priority を LP-1 だけ特別処理 — 現提案新テストも SURVIVE
- S6: collector で新 code だけ再分類 — parser 新テストも既存 consumer テストも SURVIVE

推奨した境界・統合テストを追加した後なら、これらは「新のみ KILL・旧 SURVIVE」の帰属変異になる。

放置したときの成果物影響: ledger が 7/7 KILL を示しても、承認外の受理集合拡大・縮小や journal code 改変を検出した証拠にはならない。

## B-6 P1 は NO-GO、P2〜P4 は主張範囲が過大である

深刻度: **must-fix**

根拠: [`brief.md:43–56`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/brief.md:43>)、[`plan.md:43–62`](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/plan.md:43>)、[`s8b_selector_freeze.py:381–395`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:381)、[`s8b_prediction_runner.py:950–960`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:950)

| 裁定 | 攻撃結果 |
|---|---|
| P1 | **誤り／NO-GO**。runtime mirror 自体ではなく、提示 AST 束縛が `AugAssign` を無視し、三語固定も pin しない |
| P2 | decode 済み substring 自体は exact-codepoint 契約には正しい。ただし「raw より強い」は JSON lexical escape に限る。HTML entity・NFKC・分割には無力で、現 escape テストも angle の小文字 escape しか固定しない |
| P3 | 一 code は family-level 診断としては成立するが、LP-n・複数 hit を機械可読に区別できない。invalid row では rationale が null になるため、識別には raw artifact の再読が必要。診断力の説明は過大 |
| P4 | 既存 code 保存としては整合するが、長さ超過 LP は常に `rationale_too_long` となり、新 code による LP 発生件数から消える。これは「受理集合 gate」であって「全 LP occurrence detector」ではない |
| P5 | 妥当。`choice_id` は enum 拒否済み |
| P6 | scope 境界として妥当。別表記を新たに拒否する変更は T-100 候補へ送るべき。ただし非一般化の正例は本 wave に必要 |

P3/P4を維持するなら、成果物・レポートでは「新 code 件数 = LP 出現件数」と扱わず、「長さ検査後まで到達した exact LP の主拒否理由」と限定しなければならない。

放置したときの成果物影響: report/台帳の `parser_error_code` 集計が LP-n と multiplicity を失い、さらに overlong LP を `rationale_too_long` に隠すため、LP 検出件数・参照 raw が不完全になる。

**総合判定: NO-GO**

---

## 段 5 実装 (codex gpt-5.6-sol / reasoning=high / workspace-write)

- 原文 SHA-256: `09ea7e98c0d0f2b6a4a8ba68ce785ae8ca058418a358c23a8dc7915ce63e8c88`
- 原文 bytes: 5752
- LP の literal 出現 (defang 済み): 0

変更前は、構造・型・長さなどの既存条件を満たせば LP-1〜LP-3 を含む rationale も受理していました。変更後は、その集合だけを fail-closed に縮小しています。

## 1. 変更ファイル

- [s8b_selector_output.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:14)
  - `_RATIONALE_LITERAL_PLACEHOLDERS` に承認済み3語を宣言。
  - [122行目](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:122)で blank・too-long 検査後に decode 済み rationale を case-sensitive substring 検査。
  - 新規 code は `rationale_placeholder` のみ。

- [test_s8b_selector_output.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:21)
  - テスト内に独立した expected tuple を宣言。
  - AST で `tools/check_docs.py` を import せず読み、対象 Store が唯一でトップレベル `ast.Assign` であることを検査。
  - LP単独・埋め込み・JSON escape・複数LP・wrapper負例、近似表記正例、2001文字の診断順序を追加。

- [test_s8b_selector_freeze.py:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_freeze.py:247)
  - `record_agent_attempt` が LP rationale を invalid とし、code・raw hash・rationale非掲載を保つ統合負例を追加。

- [test_s8b_prediction_runner.py:1027](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1027)
  - fake provider → journal invocation → materialized row → freeze verify の統合負例を追加。

変更は指定4ファイルのみです。stage・commit・docs編集なし。schema、role、`output/` の前後hash/digestも一致しています。

## 2. 実行結果

| nodeid範囲／コマンド | 結果 |
|---|---|
| `python3 -m pytest orchestrator/tests/test_s8b_selector_output.py -q`（同ファイル全nodeid） | **67 passed** |
| `python3 -m pytest orchestrator/tests/test_s8b_selector_freeze.py -q` | **0実行、1 collection error** |
| 失敗箇所 | `ERROR collecting orchestrator/tests/test_s8b_selector_freeze.py` |
| 失敗原因 | 既存の `s8b_ratified_freeze.py` が `campaign` を absolute importし、単独起動時の検索パスに `orchestrator/` がないため `ModuleNotFoundError` |
| `PYTHONPATH=orchestrator python3 -m pytest orchestrator/tests/test_s8b_selector_freeze.py -q`（補助全走） | **29 passed** |
| `python3 -m pytest orchestrator/tests/test_s8b_prediction_runner.py -q`（同ファイル全nodeid） | **56 passed** |
| 指定の実成果物 verify コマンド | **exit 1**。同じ既存 import errorで検証開始前に停止 |
| `PYTHONPATH=orchestrator python3 orchestrator/campaign/s8b_selector_freeze.py verify ...` | **verified** |
| `python3 tools/check_codex_agents.py` | **OK** |
| `python3 tools/check_docs.py` | **違反なし** |
| `git diff --check` | **OK** |

submodule index lock 由来の偽赤はありません。赤は上記2件とも既存 import-path 条件のみで、実装 assertion の失敗ではありません。

## 3. 受理・拒否挙動

変更前：

- 厳密な単一JSON object、必須3キー、version、6 choice、非空白かつ最大2000文字の rationale を受理。
- LP-1〜LP-3を単独または部分文字列として含む rationale も受理。
- 不正JSON、重複キー、余分・欠落キー、不正choice、blank、2001文字以上などは既存codeで拒否。fallbackなし。

変更後：

- 変更前の受理集合から「decode済み rationale が LP-1〜LP-3のいずれかを exact substring として含む入力」だけを除外。
- JSON lexical escapeを経て同一文字列になる場合も拒否。
- 2001文字以上なら従来どおり `rationale_too_long` が優先。
- 外側delimiter除去、全角山括弧、HTML entity、token内空白・U+200Bは引き続き受理。
- strip・Unicode正規化・casefold・HTML unescape・正規表現は不使用。
- LPの種類・個数は機械可読化せず、codeは常に `rationale_placeholder`。

## 4. 波及の静的棚卸し

- caller:
  - `s8b_selector_freeze.record_agent_attempt` は新規応答を invalid として記録。
  - `_reparse_agent_raw` / `verify_prediction_freeze` は、LPをvalid扱いした偽造行を不一致でfail-closedにする。
  - `s8b_prediction_runner` はcodeをjournal・materialized rowへ透過し、parser module hashも更新される。
  - `s8b_floor_campaign` と `s8b_verdict` は `verify_prediction_freeze` 経由で新gateの影響を受ける。
  - `s8b_ratified_freeze` は現行parserを再実行しないため、新gateの射程外。

- 共有fixture:
  - selector-freezeの `_rows`、runnerの `_valid_raw` / `_RecordingProvider` は通常rationaleのまま。
  - runnerの `_binding` はparser hashを動的取得しており、揮発hashの期待値への焼き込みなし。
  - schemaとroleは未変更。schema自体は新しい意味制約を表現せず、parser-authoritativeのまま。
  - 既存seal済み成果物は補助verifyで成功。旧journal bytesは未変更。

- consumer testへの波及候補:
  - `test_s8b_verdict.py`
  - `test_s8b_floor_campaign.py`
  - `test_s8b_ratified_freeze.py`
  - `test_s8b_ratified_verify.py`
  - `test_frozen_artifacts.py`

既存の未完了journalを新しいworktree parserで再開した場合、parser hash不一致によりfail-closedになります。

## 5. plan-v2.mdからの逸脱

なし。

---

## 段 6 敵対レビュー A — 正しさ境界・受理集合・凍結成果物 (max / read-only)

- 原文 SHA-256: `7eb22cff8c38da38448906fca55c12e6212edece2c881545f6be4194754b6b22`
- 原文 bytes: 462
- LP の literal 出現 (defang 済み): 0

所見なし。

静的確認では、exact substring 検査は `rationale_type` → `rationale_blank` → `rationale_too_long` の後にあり、拒否集合・既存 code 順序は裁定どおりです。差分は指定 4 ファイルのみで、凍結済み raw の decode 後 rationale に LP はありません。新規統合テストの書込先もすべて `tmp_path` 配下です。

pytest は指示どおり実行していません。

総合判定: GO

---

## 段 6 敵対レビュー B — テストの検出力・恒真化・変異耐性 (max / read-only)

- 原文 SHA-256: `2622846906d1c8706c1216b82a04b9b44445180b804f007213eb75f3b0a2f3b9`
- 原文 bytes: 9772
- LP の literal 出現 (defang 済み): 6

静的検査のみ実施し、pytest は実走していない。事前登録 14 変異はすべて KILL 予測だが、登録外の変異耐性に must-fix がある。

### RB-1 exact 3 語以外の過剰拒否を防ぐ正例が不足

- 深刻度: must-fix
- 根拠: `orchestrator/tests/test_s8b_selector_output.py:193`, `orchestrator/tests/test_s8b_selector_output.py:204`, `orchestrator/tests/test_s8b_selector_output.py:216`, `orchestrator/tests/test_s8b_selector_output.py:227`
- 放置したとき成果物: 本来 valid な rationale が `invalid`、`choice_id=null`、`parser_error_code="rationale_placeholder"` となり、journal・materialized row・certified 選択の受理集合が不当に縮む。

現テストをすべて通す却下済み一般化を構成できる。例えば「token 内に空白/U+200Bを含まない ASCII `<...反映>` をすべて拒否」する実装は、全負例を拒否し、全角・HTML entity・内部空白の正例も受理する。一方、承認語彙外の `<結果を反映>` まで拒否する。

また、照合を `placeholder[:-1] in rationale` とする変異も現テストを通る。delimiter を両方除いた本文は受理するが、閉じ括弧だけない `<反映` を誤って拒否する。

必要な追加 assert:

- `<結果を反映>`、`<反映済み>` のような非承認 ASCII-angle 語を受理する。
- 各 LP の `placeholder[:-1]` と `placeholder[1:]` を受理する。
- 受理後の `decision.rationale` が入力と完全一致することも固定する。

これは検出語彙の追加提案ではなく、裁定済み exact 3 語以外を拒否しないための境界固定である。

### RB-2 AST 語彙束縛は `globals()` 経由の実行時再束縛を見逃す

- 深刻度: must-fix
- 根拠: `orchestrator/tests/test_s8b_selector_output.py:33`, `orchestrator/tests/test_s8b_selector_output.py:35`, `orchestrator/tests/test_s8b_selector_output.py:44`, `orchestrator/tests/test_s8b_selector_output.py:309`, `tools/check_docs.py:875`
- 放置したとき成果物: docs lint と selector parser の受理集合が分岐し、同じ文字列をレポート側は拒否する一方、journal・certified 選択側は valid として受理し得る。

検出状況は以下。

- 直接の `AugAssign`: `ast.Name(Store)` が2個になるため検出。
- 直接の再束縛: Store/Assign が複数になり検出。
- `AnnAssign`: Store 数またはトップレベル `Assign` 数で検出。
- 条件分岐内の直接代入: 既存代入との Store 重複、またはトップレベル `Assign` 不在で検出。
- `globals()["LITERAL_PLACEHOLDERS"] += (...)`: target は `ast.Subscript` なので検出不能。
- `globals().update(...)`、`exec(...)`、同名への import alias も検出不能。

具体的に次は語彙テストを通る。

```python
LITERAL_PLACEHOLDERS = (
    "＜反映＞",
    "＜受入結果を反映＞",
    "＜受入全走結果を反映＞",
)
globals()["LITERAL_PLACEHOLDERS"] += ("<絶対に docs に無い語>",)
```

helper は最初の literal tuple だけを抽出する一方、docs checker の実行時語彙には4語目が加わる。既存 `test_check_docs` の独立3語テストにも4語目の入力はない。

必要な追加 assert は、制御された fixture loader で `check_docs.py` を実行し、実行時の `module.LITERAL_PLACEHOLDERS == _EXPECTED_LITERAL_PLACEHOLDERS` を照合すること。production parser から docs を import する必要はない。

### RB-3 collector 統合負例が canonical LP-1 だけに偏っている

- 深刻度: must-fix
- 根拠: `orchestrator/tests/test_s8b_selector_freeze.py:247`, `orchestrator/tests/test_s8b_selector_freeze.py:249`, `orchestrator/tests/test_s8b_prediction_runner.py:1038`, `orchestrator/tests/test_s8b_prediction_runner.py:1042`, `orchestrator/campaign/s8b_selector_freeze.py:379`
- 放置したとき成果物: LP-2/LP-3またはescape表記だけ journal・row の `parser_error_code` が別値となり、レポート台帳が誤るか freeze verify が不一致で停止する。

S6 の「新 code を無条件に別 code へ再分類」は、両テストの exact code assert で KILL する。しかし次の collector 誤実装は捕まらない。

```python
if exc.code == "rationale_placeholder":
    code = exc.code if "＜反映＞" in raw_output else "invalid_json"
```

canonical LP-1 を使う現在の direct/runner テストは通るが、LP-2、LP-3、`\u003c反映\u003e` は誤分類される。parser 単体テストは collector を通らないので補完にならない。

必要な追加 assert:

- `record_agent_attempt` を独立3語すべてと、少なくとも1つのJSON escape入力で parameterize。
- runner は一度の4セル走で LP-1/LP-2/LP-3/escape を各セルへ割り当て、journal と materialized row の全 code を照合する。

### RB-4 複数出現と前置き decoy に対する substring 性が固定されていない

- 深刻度: must-fix
- 根拠: `orchestrator/tests/test_s8b_selector_output.py:136`, `orchestrator/tests/test_s8b_selector_output.py:171`, `orchestrator/campaign/s8b_selector_output.py:122`
- 放置したとき成果物: LPを含む rationale が valid のまま journal・materialized rowへ入り、誤った `choice_id` と rationale が certified 選択へ到達する。

次の誤実装が生存する。

- 最初の `<...>` token だけを検査する実装。現在の全負例では最初の angle token がLPなので通るが、`<説明> / ＜反映＞` を受理してしまう。
- `hits == 1 or LP-1 in rationale` とする実装。単独3語と現在の LP-1+LP-2 は拒否するが、LP-2+LP-3 は受理する。

必要な追加 assert:

- `<無関係> / ＜反映＞` が `rationale_placeholder`。
- 3語から選ぶ全2語組合せ、および3語同時入力が `rationale_placeholder`。

## 14 変異の KILL/SURVIVE 静的予測

| ID | 新テスト予測 | 変更前テスト予測 | 主な検出点 |
|---|---|---|---|
| M1 | KILL | SURVIVE | 単独・埋め込み負例 |
| M2 | KILL | SURVIVE | 独立 tuple 由来の LP-2 ケース |
| M3 | KILL | SURVIVE | 2000文字埋め込み、wrapper |
| M4 | KILL | SURVIVE | angle/body JSON escape |
| M5 | KILL | SURVIVE | `_assert_code` の exact code |
| M6 | KILL | SURVIVE | 3語すべての2001文字順序 |
| M7 | KILL | SURVIVE | delimiter 全除去本文の受理 |
| S1 | KILL | SURVIVE | `AugAssign` による2個目の `Name(Store)` |
| S2 | KILL | SURVIVE | 全角山括弧正例 |
| S3 | KILL | SURVIVE | 大文字hexを含む本文escape負例 |
| S4 | KILL | SURVIVE | LP-1+LP-2 同時入力 |
| S5 | KILL | SURVIVE | LP-2/LP-3 の2001文字順序 |
| S6 | KILL | SURVIVE | direct collector と journal/row の exact code |
| N1 | KILL | KILL | 新順序テストに加え、変更前からある2001文字負例 |

S1 の旧側 SURVIVE は静的予測であり、計画どおり実測時には既存 `test_check_docs` による mask の有無を先に確認する必要がある。

## 各新テストの検出力

| 新テスト | 固定できていること | 生存する誤実装 |
|---|---|---|
| 単独LP拒否 | 3語、code、message | exact全体一致だけの検査はこのテスト単独なら通る |
| 2000文字埋め込み | substring、長さ境界 | 最初のangle tokenだけを見る実装 |
| angle escape | decode済み照合 | 小文字angle escapeだけ手動復号するS3 |
| body escape | S3、raw照合 | 却下済みの広い `<...反映>` 判定 |
| 2語同時 | S4 | LP-1を特別扱いする複数hit判定 |
| wrapper | 全体一致化を排除 | 広いangle-token判定 |
| delimiter全除去正例 | M7 | 片側delimiterだけ除去して照合 |
| 全角正例 | S2 | 文脈依存でのみ正規化する実装 |
| HTML entity正例 | HTML unescapeの過剰拒否 | 他のASCII-angle類似語の過剰拒否 |
| 内部空白/U+200B正例 | 一律除去による過剰拒否 | 未検査位置だけ空白除去する実装 |
| 2001文字順序 | M6/S5/N1 | 3語については十分 |
| 語彙三者照合 | ケース消滅と直接AugAssign | 動的再束縛、実際のconsumerが別判定を使う形 |
| direct collector | generic S6、hash、キー形 | LP-2/3・escapeだけの再分類 |
| journal/materialized統合 | LP-1の4セル伝播 | LP-2/3・escapeだけのcollector/runner誤処理 |

placeholder 系 parametrize の入力源はすべてテスト内 `_EXPECTED_LITERAL_PLACEHOLDERS` であり、実装定数から語を落としてもケース自体は消えない。`_LP_IDS` は表示IDだけを独立 tuple の長さから生成しており、恒真化要因ではない。

全角・HTML entity・内部空白・delimiter除去の正例は、現裁定の受理集合を実際に固定している。将来 T-100 等で正式に拒否へ強化すれば失敗するが、それは受理集合の意図的変更を知らせる正しい失敗であり、誤検出ではない。ただし exact 3 語以外の境界は RB-1 のとおり不足している。

## 追加すべき鋭い変異

| 追加変異 | 必要なテスト |
|---|---|
| ASCII `<...反映>` を一般化して拒否 | `<結果を反映>` の受理 |
| `placeholder[:-1]` / `placeholder[1:]` 照合 | 片側delimiter欠落の受理 |
| 最初のangle tokenだけ検査 | decoy token後のLP拒否 |
| LP-1を含むmulti-hitだけ特別拒否 | 全2語組合せ＋3語同時 |
| `globals()` でdocs語彙へ4語目追加 | docs checker実行時 tuple 照合 |
| collectorがLP-2/3・escapeだけ再分類 | collector/runnerの入力多様化 |
| guardをchoice検査より前へ移動 | `choice_id=c99`＋LPの主診断が `unknown_choice_id` |

総合判定: **NO-GO**

---

## 段 6 fix 巡 1 (high / workspace-write)

- 原文 SHA-256: `f0aa1cb8859e52fb176d23118becf24196123e216d49b878d3e62be76e665c1d`
- 原文 bytes: 4294
- LP の literal 出現 (defang 済み): 0

全所見を closed にしました。期待値の緩和、本番コード・docs・no-touch 対象の変更はありません。

## 1. 所見ごとの対応表

| 所見 | 状態 | 対応箇所 |
|---|---|---|
| RB-1 | closed | 非承認 ASCII 語の受理：[test_s8b_selector_output.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:223)、片側括弧欠落：[同:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:233)。全正例で `decision.rationale` の完全一致を確認。 |
| RB-2 | closed | `tools` の import path と実行時 import：[同:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:15)、既存 AST 検査：[同:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:36)、実効値照合：[同:367](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:367)。 |
| RB-3 | closed | collector の独立3語＋escape parameterize：[test_s8b_selector_freeze.py:252](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_freeze.py:252)。4セル割当と全journal/row code・raw hash照合：[test_s8b_prediction_runner.py:1027](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1027)。 |
| RB-4 | closed | 全2語組合せ＋3語同時：[test_s8b_selector_output.py:174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:174)、先行decoy：[同:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:185)。 |
| 追加 | closed | `c99`＋LPで `unknown_choice_id` 優先：[同:360](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:360)。 |

## 2. 変更したファイル

- `orchestrator/tests/test_s8b_selector_output.py`
  - exact 3語以外の受理境界、複数出現、decoy、診断順序、実行時語彙束縛を追加。
- `orchestrator/tests/test_s8b_selector_freeze.py`
  - LP-1～LP-3とJSON angle escapeのcollector統合負例を追加。
- `orchestrator/tests/test_s8b_prediction_runner.py`
  - 4セルへ4入力を個別割当し、journal・materialized rowの全codeとraw hashを照合。

## 3. 実走結果

| コマンド／nodeid範囲 | 結果 |
|---|---|
| `python3 -m pytest orchestrator/tests/test_s8b_selector_output.py -q -rf` — 同ファイル全nodeid | 82 passed、0 failed |
| `python3 -m pytest orchestrator/tests/test_s8b_selector_freeze.py -q -rf` — 同ファイル全nodeid | 0 passed、0 failed、1 collection error |
| 失敗node | `ERROR collecting orchestrator/tests/test_s8b_selector_freeze.py` |
| `PYTHONPATH=orchestrator python3 -m pytest orchestrator/tests/test_s8b_selector_freeze.py -q -rf` — 補助全nodeid | 32 passed、0 failed |
| `python3 -m pytest orchestrator/tests/test_s8b_prediction_runner.py -q -rf` — 同ファイル全nodeid | 56 passed、0 failed |

collection error は既存の `s8b_ratified_freeze.py` が `from campaign ...` を使用するための `ModuleNotFoundError: No module named 'campaign'` です。submodule index lock由来の偽赤ではありません。

補助検査：

- `python3 tools/check_codex_agents.py`：OK
- `python3 tools/check_docs.py`：違反なし
- `git diff --check`：成功

## 4. 受理集合

今回のfix roundでは本番コードを変更していません。作業開始時から存在した `orchestrator/campaign/s8b_selector_output.py` の13行差分はそのままで、追加編集は指定された3テストファイルのみです。

docs、schema、role、`output/` の差分は空です。staged差分、commit、`git add`もありません。

## 5. 逸脱

なし。通常のhandoff/worklog更新も、今回の3ファイル限定・docs編集禁止に従い実施していません。

---

## 段 6 焦点再レビュー (max / read-only)

- 原文 SHA-256: `524cb1e67a99be79731fc06ae7443182cc649d90350f70df8898ac01bc6aacb3`
- 原文 bytes: 10084
- LP の literal 出現 (defang 済み): 0

静的再レビューの結論は **NO-GO**。RB-1〜RB-4の直接所見は閉じていますが、choice 診断順序の固定が LP-1 一例に限られ、fix 後テストを通過する誤実装を構成できます。pytest は実行していません。

## 1. 所見ごとの対応表

| 項目 | 判定 | 深刻度 | 根拠 | 放置時の成果物への影響 |
|---|---|---|---|---|
| RB-1 | **closed** | must-fix（解消済み） | 非承認 ASCII-angle の受理を [test_s8b_selector_output.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:223)、片側 delimiter 欠落と rationale 完全一致を [同:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:233) で固定。 | 本来 valid な rationale が `invalid`、`choice_id=null` となり、受理集合が不当に縮む。 |
| RB-2 | **closed** | must-fix（解消済み） | AST の Store/Assign 検査は [test_s8b_selector_output.py:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:36)、import 後の実効 tuple は [同:367](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:367) で独立3語と照合しており、`globals()` 再束縛も検出する。 | docs lint と parser の語彙が分岐し、同じ文字列の受理結果が成果物間で食い違う。 |
| RB-3 | **closed** | must-fix（解消済み） | direct collector は3語＋escapeを [test_s8b_selector_freeze.py:252](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_freeze.py:252) で検査。runner は4セルへ別入力を割り当て [test_s8b_prediction_runner.py:1038](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1038)、journal/row の全 code・hashを [同:1081](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1081) で照合。 | LP-2/3・escapeだけ `parser_error_code` が誤分類され、journal、row、freeze verify の参照が分岐する。 |
| RB-4 | **closed** | must-fix（解消済み） | 全2語組合せ＋3語同時は [test_s8b_selector_output.py:174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:174)、前置き decoy は [同:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:185) で固定。 | LPを含む rationale が valid のまま、誤った `choice_id`・rationale として成果物へ到達する。 |
| guard と choice 検査の順序 | **partial** | must-fix | 現実装の順序自体は `unknown_choice_id` が [s8b_selector_output.py:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:107)、guard が [同:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:115) で正しい。しかし回帰テストは [test_s8b_selector_output.py:360](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:360) の `_EXPECTED_LITERAL_PLACEHOLDERS[0]`、つまり LP-1 だけ。 | `c99`＋LP-2/3の主診断が `unknown_choice_id` から `rationale_placeholder` に変わり、journal/row の `parser_error_code` が誤る。 |

## 2. 回帰の検査

- **本番コード:** HEAD 比では13行の承認済み差分がありますが、fix 前レビューが既に現在の guard を [rev-B.md:74](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t098/rev-B.md:74) で参照しています。現在差分との不一致はなく、fix による追加変更は検出しませんでした。ただし未commit状態には時点スナップショットがないため、Gitだけで時間的非変更を証明したものではありません。
- **期待値の弱化:** 既存 assert の削除・弱化・`xfail`/skip 化はありません。唯一の削除行は `_assert_code` の戻り値注釈変更で、code の exact assert は [test_s8b_selector_output.py:77](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:77) に残っています。
- **揮発値:** hash は入力から都度算出しています（例: [test_s8b_prediction_runner.py:1088](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1088)）。fixture HEAD も変数で受け渡しており、working-tree hash の直書きはありません。`generated_at` の固定日時は [同:1098](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1098) の決定的fixture入力で、期待値への現在日時焼き込みではありません。
- **no-touch:** 差分は指定4ファイルだけです。`output/**`、schema、role、docs、staged、untracked の差分はありません。
- **書込先:** runner の `root` は [test_s8b_prediction_runner.py:1031](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1031) で `tmp_path`、成果物パスも [同:1093](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_prediction_runner.py:1093) でその配下です。repo内 `output/` は読み取りのみです。

新規の回帰所見はありません。

## 3. 残存する誤実装

**構成できます。**

### A. LP-1だけ choice 優先にする実装

深刻度: **must-fix**

概略として次の順序なら現行テストをすべて通過すると予測します。

```python
if choice_id not in ALLOWED_CHOICE_IDS and LP_1 in rationale:
    raise unknown_choice_id
if any(placeholder in rationale for placeholder in placeholders):
    raise rationale_placeholder
if choice_id not in ALLOWED_CHOICE_IDS:
    raise unknown_choice_id
```

現テストの複合入力はLP-1だけなので通りますが、`c99`＋LP-2/3では誤って `rationale_placeholder` になります。

必要な追加 assert: `test_unknown_choice_id_takes_precedence_over_placeholder` を独立3語で parameterizeする。

放置時の影響: 受理集合は同じでも、journal/materialized row の主拒否理由と集計参照がLP別に分岐する。

### B. rationale の先頭1500文字だけを走査する実装

深刻度: **must-fix**

```python
if any(placeholder in rationale[:1500] for placeholder in placeholders):
    raise rationale_placeholder
```

埋め込み負例のLP開始位置は [test_s8b_selector_output.py:139](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:139) の1000文字目で、他の負例は先頭付近です。この実装は全新テストを通しつつ、1500文字目以降の exact LP を受理します。

必要な追加 assert: 各LPについて、全長2000でLPが末尾に接する rationale を `rationale_placeholder` と確認する。

放置時の影響: 後半にLPを含む出力が `valid` となり、`choice_id` と未完成 rationale がjournal・rowへ到達する。

いずれも既存3語の exact 検査を固定するassertであり、検出語彙の追加や全角拒否の提案ではありません。

## 4. 変異21件のKILL/SURVIVE予測

以下は実走結果ではなく静的予測です。

| ID | fix後テスト | HEAD版テスト | 検出点／HEAD版をKILLするためのassert |
|---|---|---|---|
| M1 | KILL | SURVIVE | 3語の単独拒否・exact code（output test:126） |
| M2 | KILL | SURVIVE | 実装定数と独立したLP-2ケース（同:121–131） |
| M3 | KILL | SURVIVE | 全長2000への埋め込み（同:139–142） |
| M4 | KILL | SURVIVE | angle/body JSON escape（同:150–171） |
| M5 | KILL | SURVIVE | `rationale_placeholder` のexact assert（同:129、freeze test:268） |
| M6 | KILL | SURVIVE | LP入り2001文字で `rationale_too_long`（output test:349–357） |
| M7 | KILL | SURVIVE | delimiter除去本文の受理＋rationale一致（同:212–220） |
| S1 | KILL | SURVIVE | Store/Assign個数と実行時tupleの双方を照合（同:36–64、367–377） |
| S2 | KILL | SURVIVE | 全角山括弧版の受理（同:255–264） |
| S3 | KILL | SURVIVE | 本文を大文字hex含みでescapeした負例（同:162–171） |
| S4 | KILL | SURVIVE | 全2語組合せ＋3語同時（同:174–182） |
| S5 | KILL | SURVIVE | LP-2/3を含む2001文字順序（同:349–357） |
| S6 | KILL | SURVIVE | direct collectorとjournal/rowのexact code（freeze test:252–270、runner test:1082–1116） |
| S7 | KILL | SURVIVE | 非承認ASCII-angle語の受理（output test:223–230） |
| S8 | KILL | SURVIVE | 各LPの片側delimiter欠落を受理（同:233–252） |
| S9 | KILL | SURVIVE | decoy angle token後のLP拒否（同:185–192） |
| S10 | KILL | SURVIVE | LP-2＋LP-3を含む全組合せ（同:174–182） |
| S11 | KILL | SURVIVE | import後の `check_docs.LITERAL_PLACEHOLDERS` exact照合（同:367–377） |
| S12 | KILL | SURVIVE | collector/runnerへLP-2/3・escapeを個別投入（freeze test:252–270、runner test:1038–1116） |
| S13 | KILL | SURVIVE | `c99`＋LP-1で `unknown_choice_id`（output test:360–364） |
| N1 | KILL | KILL | HEADにも2001文字の既存負例あり（`HEAD:test_s8b_selector_output.py:126–127`）。非帰属control |

登録済みS13そのものはKILL予測ですが、節3-Aの「LP-1だけ特別扱い」は別の選択的変異で生存します。

総合判定: **NO-GO**

---

## 段 6 fix 巡 2 (high / workspace-write)

- 原文 SHA-256: `6279846c24ff9f429b022fc32b9f1384c5a7d3aa9e922ae7f0a45c59bcf80b81`
- 原文 bytes: 2238
- LP の literal 出現 (defang 済み): 0

## 1. 対応表

| 項目 | 状態 | 対応箇所 |
|---|---|---|
| guard と choice 検査の順序 | closed | [test_s8b_selector_output.py:371](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:371) — LP-1〜LP-3 を parameterize し、すべて `unknown_choice_id` 優先を固定 |
| refocus.md §3-A | closed | [test_s8b_selector_output.py:376](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:376) |
| refocus.md §3-B | closed | [test_s8b_selector_output.py:145](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:145) — 各 LP を全長 2000 の末尾へ配置し、長さと `rationale_placeholder` を検査 |

## 2. 変更ファイル

- [orchestrator/tests/test_s8b_selector_output.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py)
  - choice 診断順序テストを独立 3 語へ拡張。
  - rationale 末尾に接する LP の負例を独立 3 語分追加。
  - 既存 assert の削除・弱化なし。

## 3. 実走結果

追加・変更箇所の nodeid：

- `test_trailing_literal_placeholder_rationale_is_rejected[lp-1～lp-3]`
- `test_unknown_choice_id_takes_precedence_over_placeholder[lp-1～lp-3]`

結果：`6 passed / 0 failed`

指定された全範囲：

```text
python3 -m pytest orchestrator/tests/test_s8b_selector_output.py -q -rf
```

結果：同ファイルの全 nodeid、`87 passed / 0 failed`。失敗 node・赤の内訳はありません。

補助検査：

- `python3 tools/check_codex_agents.py`：OK
- `python3 tools/check_docs.py`：違反なし
- `git diff --check`：成功

## 4. 本番コード

本 fix round 2 では本番コードを変更していません。`orchestrator/campaign/s8b_selector_output.py` には作業開始前からの未コミット差分 13 行が残っていますが、今回編集したのは指定テストファイルだけです。

`git add`、commit、docs・schema・role・`output/` の編集も行っていません。

## 5. 逸脱

なし。

---
