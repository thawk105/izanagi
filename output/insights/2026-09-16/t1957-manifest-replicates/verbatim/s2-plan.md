## 変更面の実アンカー表

以下の行番号は**現行ファイル**のもの。新設箇所は挿入アンカーと提案内行番号で示す。略号はすべて指定 worktree 内を指す。

- R = [orchestrator/campaign/trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1957-manifest-replicates/orchestrator/campaign/trial_registry.py)
- T = [orchestrator/tests/test_trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1957-manifest-replicates/orchestrator/tests/test_trial_registry.py)
- E = [orchestrator/campaign/s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1957-manifest-replicates/orchestrator/campaign/s8c_preregistration_evidence.py)

| 実アンカー | 変更内容 |
|---|---|
| R:55–56 | manifest と registration をともに `/v3` へ変更。 |
| R:117–119 | `_TRIAL_KEYS` に必須キー `"n"` を追加。 |
| R:276–281 | `TrialSpec` にデフォルトなしの `n: int` を追加。 |
| R:769 | 既存 exact-key 検査で `n` 欠落を拒否。 |
| R:784–785 の間 | `n` の取得・厳密整数・下限検査を追加。 |
| R:785 | 検証済み `n` を `TrialSpec` に渡す。 |
| R:793–794 の間 | holdout ごとの3 arm の `n` 一致検査を追加。 |
| R:812–817、887–917 | 既存の単一版検査・共用 parser を維持。v2 互換分岐は追加しない。 |
| R:827–834 | `_trial_dict` に `"n": trial.n` を追加。 |
| R:844、864–870、913 | 共用 serializer・登録生成・parser 経由で `n` を保持することを検証。 |
| R:1566–1574 | canonical tuple に `trial.n` を追加。 |
| R:1583–1585 | identity の説明に `n` を追記。比較ロジックは維持。 |
| T:170–185、221、5481–5487 | 直接コンストラクタと手書き fixture 辞書に `n` を追加。 |
| T:1566–1576 の近傍 | 6 cell 正例と `n` 負例、registration round-trip を追加。 |
| T:5060–5061 | 重複キー負例の置換対象を v3 に追随させる。 |
| T:6765–6783 | canonical tuple 変異のパラメータへ `n` を追加。 |
| E:1650–1656 | 読み取り確認のみ。属性の部分集合検査なので変更不要。 |

## 決めたこと

1. **キーは trial object の `n`。** JSON 整数、Python 側は `type(n) is int`、値は `n >= 2`。デフォルト・変換・欠落補完は設けない。同一 holdout の3 arm は一致必須とし、H1 と H2 の値は異なってよい。逐語資料 A の cell ごとの指定と、C の holdout 単位の指定を両立する。

2. **両 schema を v3 に上げる。** R:817 と R:913 が `_parse_trials` を共有し、R:844 が `_trial_dict` を使うため、同じ必須フィールド契約へ同時更新する。旧版受理・移行処理は追加しない。記録済み実体0件は親 brief の報告に依拠し、この段では再実測していない。

3. **canonical tuple に `n` を含める。** R:1589–1594 の既存比較が反復数の差も拒否する。E:1651–1656 は実際に `{既存5属性} <= {参照属性}` であり、既存属性を残して `trial.n` を加えても**この属性検査は赤にならない**。C03 全体のテスト成功を意味するものではない。

4. **負例を両入力経路で検証する。** 欠落、文字列、bool、1、0、負値、浮動小数、arm 間不一致を manifest と registration に同じ条件で与える。拒否箇所・期待 assertion は次節に固定する。

5. **6 trial 正例は H1=2、H2=3。** 各 holdout の3 arm が同値であること、holdout 間の差を許容すること、読み込み後に値が保持されることを1本で確認する。

6. **変異は今回の schema 契約と束縛に限定する。** 必須性、型、下限、holdout 内一致、serialization、canonical identity、版判定を対象とし、殺す test node を後掲する。

「受理集合を狭める」は、**旧フィールドへ射影した契約上の制約を追加する**という意味で扱う。schema 名と必須キーが変わるため、生 JSON 集合として v3 が v2 の部分集合になるわけではない。既存条件の撤去・緩和は行わない。

## 負例と正例の設計

実装の拒否は Python `assert` ではなく既存様式の `_fail` にする。テスト側は `pytest.raises` で例外型とメッセージを確認する。未実装の絶対行番号は捏造せず、次の提案内行番号で指定する。

**V：R:784–785 間への挿入案**

```text
V1  n = raw_trial["n"]
V2  if type(n) is not int:
V3      _fail("field", f"{label}[{index}].n must be an integer")
V4  if n < 2:
V5      _fail("field", f"{label}[{index}].n must be >= 2")
```

**H：R:793–794 間への挿入案**

```text
H1  for holdout in HOLDOUTS:
H2      if len({item.n for item in trials if item.holdout == holdout}) != 1:
H3          _fail("field", f"{label} n must agree across arms for holdout {holdout}")
```

新規テスト `test_t1957_n_rejects` は `source={manifest,registration}` と明示的な `case` ID をパラメータ化する。正常 fixture の trial index 0 だけを変更し、registration は canonical JSON と終端改行を保つ。

提案内の期待 assertion は次の2行とする。

```text
A1  with pytest.raises(R.TrialRegistryError, match=expected_pattern):
A2      load_subject()  # manifest は load_trial_manifest、registration は load_trial_registry
```

| case ID／入力 | 落ちる検証・行 | A1 で照合する内容 |
|---|---|---|
| `missing`：`n` 削除 | R:769 → R:659–662 | `[schema]`、trial index 0、`missing=['n']` |
| `string`：`"2"` | V2 → V3 | `[field]`、trial index 0 の `.n must be an integer` |
| `bool-true`：`True` | V2 → V3 | 同上 |
| `bool-false`：`False` | V2 → V3 | 同上 |
| `one`：`1` | V4 → V5 | `[field]`、trial index 0 の `.n must be >= 2` |
| `zero`：`0` | V4 → V5 | 同上 |
| `negative`：`-1` | V4 → V5 | 同上 |
| `float`：`2.0` | V2 → V3 | `.n must be an integer` |
| `arm-split`：H1 の1 arm だけ `3`、残り `2` | H2 → H3 | `[field]`、`n must agree across arms for holdout H1` |

`expected_pattern` は完全なラベルを含めてエスケープし、末尾を固定する。特に bool は下限違反でも拒否され得るため、**型エラーであることまで照合**して型検査の弱化を検出する。

正例 `test_t1957_six_cell_n_round_trip` は T:1566 近傍に追加する。

- 6 trial に H1=2／H2=3 を設定し、入力順を逆転して manifest を load。
- **P1**：`assert len(manifest.trials) == 6`
- **P2**：`assert [(t.holdout, t.arm, t.n) ...] == [(h, a, 2 if h == "H1" else 3) ...]`
- `_registration_for` → `_registration_dict` → canonical JSONL → registration load を通す。
- **P3**：出力した各 trial 辞書の `n` が期待列 `[2,2,2,3,3,3]` と一致。
- **P4**：`assert registration.trials == manifest.trials`

canonical 束縛負例は既存 T:6765 のパラメータへ `n` を追加し、T:6774 の置換値に `trial.n + 1` を指定する。**既存 assertion T:6782** が R:1591–1594 の `trial sets differ` を捕捉する。このテストは parser を経由しないため、holdout 内一致検査に隠されず tuple の `n` 欠落を検出できる。

さらに `test_t1957_schema_versions` で両定数がリテラル `/v3` と一致することを assert し、`test_t1957_v2_rejected[source]` で `n` を備えた旧版入力も R:812–813／887–888 により拒否されることを確認する。

## 変異事前登録の候補

以下の node はすべて `orchestrator/tests/test_trial_registry.py::` を接頭辞とする。新規 node は実装予定名。

| 変異 | 殺すべき test node |
|---|---|
| `n` 欠落を `2` で補完して受理 | `test_t1957_n_rejects[manifest-missing]`、`[registration-missing]` |
| 厳密整数検査を削除し、比較可能な float を許容 | `test_t1957_n_rejects[manifest-float]` |
| 型検査を `isinstance(n, int)` に弱化 | `test_t1957_n_rejects[manifest-bool-true]`（型エラーの期待を外す） |
| `int(n)` へ暗黙変換 | `test_t1957_n_rejects[manifest-string]` |
| 下限を `n >= 1` に弱化 | `test_t1957_n_rejects[manifest-one]` |
| 下限検査を削除 | `test_t1957_n_rejects[manifest-zero]`、`[registration-negative]` |
| holdout 内一致検査を削除 | `test_t1957_n_rejects[manifest-arm-split]`、`[registration-arm-split]` |
| 全 holdout に同一 `n` を要求 | `test_t1957_six_cell_n_round_trip` |
| parser が入力 `n` を捨てて常に `2` を格納 | `test_t1957_six_cell_n_round_trip` の P2 |
| `_trial_dict` が `n` を省略／固定値化 | `test_t1957_six_cell_n_round_trip` の P3／registration load |
| `_trial_canonical_tuple` から `n` を除去 | `test_acceptance_rejects_registry_canonical_tuple_mutation[n]` |
| 片方だけ v2 のままにする | `test_t1957_schema_versions` |
| v2 互換受理を追加 | `test_t1957_v2_rejected[manifest]`、`[registration]` |

親が通常テストと変異 matrix を実測する。正例は schema の load／round-trip を証明し、正式系列の発効や反復観測の受理成功とは扱わない。

## 親 brief への反証

なし。

補足として、版上げに伴い T:5060–5061 のハードコード更新が必要。ここを残すと重複キーを作る文字列置換が発火しない。また、T:5481 の直接 `TrialSpec` 構築にも必須 `n` の追加が必要である。

## scope 外の既知不整合

R:3607–3612 は期待 slot の `replicate_index` を `0` に固定している。
そのため、n≥2 に対応する初回 slot を含む genesis は構造的に受理されない。
本 wave では変更せず、観測反復集合と登録 `n` の exact 一致は未解決のまま残す。

## 総括

trial ごとの必須 `n` を両 schema の v3 に追加し、型・下限・holdout 内一致・登録束縛を検証する。
凍結対象2文書、artifact 発行、既存受入 gate は変更対象にしない。
この段は静的確認のみ。ファイル変更・commit・テスト実行は行っていない。