## 所見

**B1 — consumer の「6 file・24 行」はコード内の直接参照として正しいが、全参照の棚卸しとしては不足。**

- **主張:** production / test の追加修正漏れは見つからない。ただし plan は検索範囲を限定せず「定数名の直接出現」と記述しており、docs と歴史記録を数えていない。間接 consumer の collector / artifacts も補記すべき。
- **根拠:** `s2-plan.md:34` は「定数名の直接出現は **6 file・24 行**」。現物のコード内参照は以下と一致する。

| file | `REQUIRED_CODE_IDENTITY_PATHS` の出現行 |
|---|---|
| `orchestrator/qualification/contract.py` | 39、533 |
| `orchestrator/qualification/identity.py` | 27、140 |
| `orchestrator/qualification/t126_driver.py` | 64、372 |
| `orchestrator/tests/test_t126_pegasus_tools.py` | 704、980、1026、1085、1486、1487、1519、1522、1528〜1531、1541、1554 |
| `orchestrator/tests/test_t126_qualification_contract.py` | 21、76 |
| `orchestrator/tests/test_t419_probe_causality.py` | 38、42 |

docs 内にはさらに以下の直接出現がある。

| file | 行 |
|---|---|
| `docs/archive/worklog-phase3-0801-100.md` | 94 |
| `docs/archive/worklog-phase3-0810-377.md` | 41 |
| `docs/archive/worklog-phase3-0812-496.md` | 9 |
| `docs/archive/worklog-phase3-0816-587.md` | 21 |
| `docs/archive/worklog-phase3-0917-1617.md` | 708 |
| `docs/decisions.md` | 5478、64321、65979 |

`output/` にも定数名を含む tracked file が 45 個ある。これらを runtime consumer と扱う必要はないが、「全 repo の直接出現が 6 file」は成立しない。

間接 consumer は plan 記載の `submission.py:216–217` に加え、`collector.py:358,473,1168,1487` の `series_identity(...)`、`:1515` の `verify_recorded_series_identity(...)`、`artifacts.py:1291` の `series_identity(series_preimage)` がある。いずれも契約関数経由で追随する。

指定の `docs/orchestrator-design.md`、`docs/pegasus-runbook.md`、`docs/phase3.md` には、今回更新すべき「40 path」「40-key」の記述は見つからなかった。

- **重さ:** should。
- **是正案:** 「production / test の直接出現は 6 file・24 行」と限定し、docs / output は歴史記録、collector / artifacts は契約経由の間接 consumer と補記する。歴史記録の件数は書き換えない。

**B2 — loader の説明は妥当だが、「campaign_lock 系 test は drift 赤」という一括扱いは広すぎる。**

- **主張:** 未 commit の差分で赤になるのは、変更した実 repo の live binding を取得・検証する経路。loader を import するだけ、fixture repo を使う、記録 HEAD blob だけで binding を作る test は別である。
- **根拠:** `campaign_lock.py:107` は `"orchestrator/qualification/contract.py",` を含む。`contract_loader_binding.py:526–529` は `if disk != blob:` で `contract-loader-drift` を送出する。一方、`campaign_lock_test_support.py:11` は「HEAD の実 blob digest から、disk 非依存の test-only binding を作る」と明記している。

AST で確認した `contract_loader_binding` の直接 import 元は、すべて `orchestrator/tests/` 配下の次の 11 file。

| file | import 行 |
|---|---:|
| `campaign_lock_test_support.py` | 7 |
| `test_artifact_admission.py` | 17 |
| `test_bench_first_real_wal.py` | 23 |
| `test_layer3_report.py` | 27 |
| `test_p3_b4_raw_record_producer.py` | 23 |
| `test_p3_b4_wiring_probe.py` | 21 |
| `test_s1_report.py` | 15 |
| `test_s6_sort_sweep.py` | 40 |
| `test_s8a_trigger_sweep.py` | 40 |
| `test_t1998_stock_inline_pair.py` | 20 |
| `test_t671_source_binding.py` | 261 ほか関数内 |

実 repo 比較の具体例は `test_p3_b4_raw_record_producer.py:110–112` の `_writer_authority()`。`:158` の writer から呼ばれ、`:705` の evidence 複製経路を通る `certified_evidence` 消費 test、例えば `test_m01_assembly_rederives_precursor_from_the_sealed_registry`（:2065）が影響を受けうる。

焦点走 4 file に当該 import / live capture は見つからない。`test_t126_pegasus_tools.py:24` が要求する `ratified_enforcement_source` も、`conftest.py:154–155` では空の compatibility fixture である。

- **重さ:** should。
- **是正案:** brief を「実 repo の live loader binding を取得する経路は未 commit 差分で拒否」と限定する。commit 後にはこの差分による不一致は解消するが、受入全体の緑は実走で確認する。

**B3 — fixture の追加対応不要は確認できる。basename 重複は衝突しない。**

- **主張:** 新 3 path に専用分岐や directory 作成処理を足す必要はない。
- **根拠:** `test_t126_pegasus_tools.py:980–982` は集合を反復し、`path = repo / relative`、`path.parent.mkdir(parents=True, exist_ok=True)` を実行する。新 3 path は特殊分岐に一致せず、`:1025` の `path.write_text(f"fixture {relative}\n", ...)` に入る。`:1050–1051` で add / commit、`:1085–1088` でその commit の blob hash を読む。既存 `core.py` と directory が共通でも `exist_ok=True` なので問題ない。

`_dependency`（:957–967）は外部依存 fixture の `source.txt` だけを作る。`test_t126_qualification_driver.py:99–107` は prologue 用の部分 map。`certified_writer_fixtures.py:93` 以下にも固定の copied 列挙はあるが、required code 全集合を作る builder ではない。

- **重さ:** nit（確認事項）。
- **是正案:** plan の実装方針を維持する。「fixture が実 verifier Python を実行する」証拠とはせず、identity 用 bytes と Git blob の整合を検査する fixture と説明する。

## 親 brief への指摘

**B4 — 「verifier package 全 7 file」は事実と異なる。**

- **主張:** 今回の到達点は verifier の 7 file の個別束縛であり、package 全 file の包含ではない。
- **根拠:** `s1-brief.md:5` は「verifier package 全 7 file」。`git ls-files --stage orchestrator/verifier` は 9 file を返し、`__main__.py` と `cli.py` が残る。`__main__.py:5` は `from .cli import main`、`cli.py:23–25` は core / parse / report を import する。plan の `:111–112` の訂正は正しい。
- **重さ:** should。
- **是正案:** 「裁定対象 3 file を加え、verifier の個別束縛を 4 → 7 file に広げる」に訂正する。残る 2 file を本 wave に追加する必要はない。

**B5 — P4 の script 記述は訂正が必要。固定列挙はあるが、変更対象の集合の複製ではない。**

- **主張:** plan の訂正を親 brief に反映すべき。script 側の実装変更は不要。
- **根拠:** `s1-brief.md:33` の「path 名を列挙しない」に対し、`submit_t126_qualification.sh:124–129` は 5 path、`:149–156` は 7 path を列挙する。`:142–144` の `git ... archive ... orchestrator` は新 3 file も含む。

`t126_qualification.sh:790–802` も protocol / policy / reservation policy / driver / job script の path を列挙する。`collect_t126_qualification.py:31–38` は collector へ委譲し、独立した identity path 集合を持たない。これらに code 集合の件数 40 / 43 への依存は見つからず、script 内の `{40}` は Git object ID の形式検査である。

- **重さ:** should。
- **是正案:** 「script には実行入力等の固定列挙があるが、required code 集合の独立した全列挙はない」と訂正する。

**B6 — DW-O10 非適用と件数・anchor の主要実測は支持できるが、実測範囲を限定して残すべき。**

- **主張:** 凍結 producer の修正を追加する根拠は見つからない。過去の worktree / process 走査結果を現在の全環境の保証へ一般化しない。
- **根拠:** `contract.py:39–80` は AST 評価で code 40、script 3、和集合 43。brief の変更位置・既存 test 名・fixture 行番号は現物と一致した。

変更前の hash も brief と一致し、contract は `e36d7c67… / 47fe1b3a…`、test は `bf50ef67… / 501337e8…`。今回の `output/` を含む検索でも完全 hash の hit は 0 件だった。`docs/dev-wave/operations.md:74` 以下は DW-O10 を「非凍結 producer 一般へ拡張しない」としている。live loader 比較と歴史 exact62 の path 列挙は、現在の source bytes を固定する golden と同一ではない。

- **重さ:** nit。
- **是正案:** DW-O10 非適用を維持する。164 worktree・稼働 process 等は親の時点付き実測として扱う。本相談ではその全走査を再実施していない。

## 変異 matrix への提案

**B7 — N1〜N5 は新 test 固有の検出力を測れる。E1 も適切な等価対照。**

- **主張:** plan の期待集合 `{V}` は静的に妥当。今回の N1〜N5 を既存 test だけで殺せるとは評価しない。
- **根拠:** 既存包含 test（`test_t126_pegasus_tools.py:1527–1531`）は core / dsg / model / parse のみ。`:1541` の等価比較と `:1554` の parameter は production 集合に追随する。新 test は plan `:20–23` の独立した literal assert であり、`:87` の期待 node 名と一致する。ただし新 node は現物にはまだ存在せず、実装後の collection が必要。

`V`:

```text
orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_init_report_commit_receipt
```

| ID | 変異 | code 件数 | 既存 test 単独 | 新 test | 期待 |
|---|---|---:|---|---|---|
| N1 | verifier `__init__.py` を削除 | 42 | 検出しない | init assert が失敗 | KILLED、`{V}` |
| N2 | `report.py` を削除 | 42 | 検出しない | report assert が失敗 | KILLED、`{V}` |
| N3 | `commit_receipt.py` を削除 | 42 | 検出しない | receipt assert が失敗 | KILLED、`{V}` |
| N4 | `report.py` → `cli.py` | 43 | 検出しない | report assert が失敗 | KILLED、`{V}` |
| N5 | `commit_receipt.py` → `core.py` | 42 | 検出しない | receipt assert が失敗 | KILLED、`{V}` |
| E1 | 新 test の def 直後へ comment だけ追加 | 43 | 変化なし | 変化なし | SURVIVED、空集合 |

N4 の `cli.py` は `git ls-files --stage` で mode `100644`、blob `3c600cb4…` を確認し、現 code 集合の member ではなかった。置換後の tracked node は成功するはずであり、期待失敗 node に登録する理由もない。

`tools/mutation_harness.py:1555–1565` は期待 node と baseline collection の差集合を検査する。plan `:103` は変異下だけの parameter を登録しないと明記しており、先例 erratum を守っている。

anchor は現在の未実装 `contract.py` では新 3 path とも **0 回**。plan の 3 行をメモリ上で挿入した source では、完全な `"orchestrator/verifier/<name>",` がそれぞれ **1 回**だった。`"orchestrator/verifier/__init__.py",` は qualification / campaign / calibrator の同名 basename と混同しない。

- **重さ:** nit（登録時の確認事項）。
- **是正案:** 表を維持し、実装後 baseline で `V` の collection と全 `old` の一意性を確認する。anchor は basename に短縮しない。上表は静的予測であり、実測の KILLED / SURVIVED として記録しない。

**B8 — 焦点走・変異には 4 file で足りるが、受入全走をその 4 file に縮めてはいけない。**

- **主張:** 今回の変異の帰属確認に loader 系 test を追加する必要はない。間接 consumer と live loader の整合は commit 後の受入全走で覆う。
- **根拠:** B1 の直接 consumer は指定 4 file に含まれ、B2 の実 repo live loader 比較は含まれない。先例 insight §5 も、artifacts / floor receipt / official closure / source binding / campaign lock / admission / campaign 等を受入全走で覆うとしている。

tracked test は `test_t126_pegasus_tools.py:26–27` で自身の checkout を `_ROOT` とし、`:1567–1568` で `git -C _ROOT ls-files --error-unmatch` を実行する。新 3 path は今回新規作成する file ではなく、baseline から tracked なので、同じ commit を基にした通常の隔離 Git worktree でも判定できる。

- **重さ:** should。
- **是正案:** 焦点走・matrix は指定 4 file、受入は commit 後の通常全走を維持する。計算ノード実行を確定条件にするなら、brief の「自動判定」だけに頼らず runner に `--force-dispatch` を明記する。

## 総括

実装上の **must-fix は 0 件**。3 path の純増と独立包含 test 1 本で、裁定対象の除去・tracked 兄弟への置換・frozenset 重複化を検出できる設計である。

修正すべきなのは主に説明の範囲である。「全 7 file」「全参照が 6 file・24 行」「script は path を列挙しない」「campaign_lock 系 test は一律 drift 赤」を限定・訂正する。consumer や fixture の追加実装、変異候補の増設は不要。

本回答は静的検査による。ファイル書込み・pytest・変異実走は行っていない。