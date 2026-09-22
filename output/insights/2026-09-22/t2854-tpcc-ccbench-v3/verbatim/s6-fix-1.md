F1〜F7 と段6 §3の判定条件を、指定の4ファイルに実装しました。自己試験は **192/192、rc=0**。tracked file の変更、build、投入、index・HEAD の書込みはありません。

以下の closed は実装修正の完了を指します。計算ノードでの検証は未実走です。

| 所見 | 対応 | 修正内容 |
|---|---|---|
| A1 | closed | D1・M2自身のmarkerと1000 C以上のfileを要求。M2は理由集合・rc・witness一意性・E=C・C>commit_countsも確認 |
| B1 | closed | 表検査を署名基準へ変更。M4は`content-txtype`だけ |
| A2 | closed | 理由集合・先頭理由・条件別真偽を記録。M1は派生理由を許す先頭理由一致として明示 |
| A3 | closed | pin→C1のheader 2ファイル、C1→C2のsilo 1ファイルをraw diffで照合 |
| B2 | closed | 変異木の初回通常buildを削除。復元は変更したファイルのうちbytesが異なるものだけ |
| B3 | closed | OrderLineの密連番・最小値0の合否条件を削除。最小値・注文別最小値0の割合・見本を記録 |
| B4 | closed | top-level・entryのkey集合とschema_versionを固定し、起動前に拒否 |
| 親P1 | closed | build並列度を`os.cpu_count() or 1`へ変更 |

**変更ファイルと主な位置**

| ファイル | 行数 | 変更箇所 |
|---|---:|---|
| [run_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/run_probe.py) | 809 | 89行：並列度。`sources()` 217行：分割照合。423行：marker計数。`c6()` 567行：build・復元・結果記録。`mutation_verdict()` 698行：裁定の条件表。`load_spec()` 744行：厳格検査 |
| [v3check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/v3check.py) | 277 | `check()`内の`finish()`：103行から署名判定、124行から注文別最小値、251行から観測値出力 |
| [selftest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/selftest.py) | 264 | 127行以降：理由集合・OrderLineの確認。`harness_tests()` 188行：kill条件・spec拒否試験 |
| [mutation-spec.template.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/mutation-spec.template.json) | 73 | D1 replacementにstderr markerを追加し、intentを更新 |

**自己確認の実走結果**

作業worktreeで以下を実行しました。

```text
python3 output/runs/t2854-ccbench-v3/probe/v3check.py --selftest
v3check selftest: 192/192 passed; failures=0
rc=0
```

- `python3 output/runs/t2854-ccbench-v3/probe/run_probe.py --help`：rc=0。
- Python 3ファイルの`ast.parse`による構文確認：rc=0。bytecode出力なし。
- review/filesの最終bytesに対するanchor照合：D1・M1〜M5すべて出現1回、置換は非no-op。M2はD1適用後に照合。rc=0。
- 作業前後の`git --no-optional-locks status --porcelain`は空。終了時の`git diff --stat`も空。

追加は **46件＝正例10件・負例36件**です。

正例10件：

```text
all-lines-start-one, line-gap-zero-two,
D1-valid, M2-valid, M1-valid, M1-derived-reason,
M3-valid, M4-valid, M5-valid, spec-valid
```

負例36件（波括弧は各suffixを持つ個別ケース）：

```text
swap-all-txtypes
D1-{no-marker, below-threshold, check-failed}
M2-{no-marker, below-threshold, extra-reason, nonzero-rc,
    missing-witness, missing-batch-witness, unequal-e-c,
    c-equals-commits, c-less-than-commits}
M1-wrong-first
M3-derived-reason
M4-derived-reason
M5-{one-expanded-equal, one-include-different,
    eight-consumers, duplicate-consumer}
spec-missing-{schema_version, anchor_status, note, entries}
spec-entry-missing-{id, base, file, anchor, replacement,
                   target, kind, expected, intent}
spec-unknown-key
spec-wrong-version
spec-entry-unknown-key
```

**変更した既存負例の全件**

| ケース | 変更 |
|---|---|
| `swap-txtype` | first_reasonは維持。理由集合が`['content-txtype']`のみである確認を追加 |
| `table6-to5` | first_reasonは維持。理由集合が`['content-table']`のみである確認を追加 |
| `delete-Payment-signature-with-correct-count` | F1に従い`content-table`→`content-txtype`。理由集合も完全一致で確認 |
| `line-start-one` | F4に従い負例から正例へ変更し、観測値を確認 |

上記以外の既存負例の期待値は変更していません。

**所有外への波及・依存**

- 所有外ファイルへの編集なし。裁定からの逸脱なし。
- 親の実投入用specには、更新したD1 replacementの取り込みが必要です。古いspecではmarker条件を満たしません。
- JSONへ`raw_diffs`、`diagnostic_marker_count`、`conditions`、`reason_match_policy`、OrderLine観測項目を追加しています。
- 既存のread-only importは`s3_mocc_lock_coverage._resolve_toolchain`と`_normalize_objdump`。戻り値・正規化仕様の変更はtoolchain束縛・binary比較へ影響します。
- `fetch_third_party.py hydrate`のCLI/JSON、policyのcompiler digest・依存HEAD、現行verifierのCLI/JSON、CCBenchのCMake・trace・stdout形式に依存します。
- witness parserは裁定どおり局所実装を維持。内容照合は指定されたWの特徴検査であり、任意のR表誤記の検出やTPC-Cの直列化可能性認定は主張しません。

## 総括

- 指定4ファイルのみ修正し、F1〜F7・新kill条件を実装しました。
- 自己試験192件、構文、help、6 anchorの照合は成功しました。
- build・実trace・実前処理比較・D1/M1〜M5の計算ノード検証は **実装済み・未実走**です。
- 親は更新specを回収し、commit後の最終C2 bytesでanchorを再照合してください。