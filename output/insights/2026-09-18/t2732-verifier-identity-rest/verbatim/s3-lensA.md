## 所見

以下、`s1-brief.md`・`s2-plan.md`・`verbatim-*.md` は指定 job directory 内、その他は parent worktree 内のファイルを指す。

**A1 — 3 path 追加と独立包含 test 1 本は裁定を満たす。**

- **主張:** plan の実装範囲に過剰・不足はない。P1 の「既存 4 file test を維持し、新 3 file を別 test で個別 assert」は妥当。
- **根拠:** `verbatim-d2120-item6.md:5–7` は「加える (40 → 43 path、択 (a))」「独立の包含 test を置く」。`s2-plan.md:23–26` の期待値は production 集合から生成せず、3 path の文字列を個別に assert する。既存 `orchestrator/tests/test_t126_pegasus_tools.py:1527–1531` と合わせて指定 7 file を検査できる。
- **重さ:** nit。
- **是正案:** 実装案を維持する。包含 test が証明するのは集合からの脱落検出であり、verifier の判定能力そのものではないと区別する。

**A2 — P3 は先例どおり成立する。旧形の拒否は blob 照合より前である。**

- **主張:** 互換層を作らない判断は既裁定に整合する。ただし、旧成果物が先行検査を通った場合の拒否経路として説明する必要がある。
- **根拠:** `orchestrator/qualification/contract.py:533–537` は `set(rows) != required` に対して `"series identity code_identity required set mismatch"` を送出する。driver は `t126_driver.py:1437`、collector は `collector.py:1487` で直接 `series_identity()` を呼ぶ。driver は `:1644–1646`、collector は `:1880–1883` で例外を invalid に変換し、driver CLI は `:1679` で rc=2 を返す。`verify_recorded_series_identity()` の直接呼出しでも `identity.py:124` が先に同じ検査を行い、`:140` の和集合検査には到達しない。
- **重さ:** nit。
- **是正案:** P3 を維持し、最終記録には上記経路を記す。`verbatim-d2091.md:13–18` のとおり、現行契約への不適合を過去の測定・当時の判定の無効化に使わない。

**A3 — P2 は今回の既裁定に照らして妥当。ただし「意味論不変」は identity まで含められない。**

- **主張:** 受理形の置換を DW-O13 の新設として扱わない判断は D2091 と整合する。一方、変更は required path の純増であり、qualification の受理集合は変わる。
- **根拠:** `verbatim-d2091.md:10–12` は「受理形は 1 形のまま」「受理形の増加ではない」。`docs/dev-wave/operations.md:102–104` は受理形増加と到達可能性を区別している。現物の集合は code 40、script 3。追加 3 file は regular file で、disk bytes と base `d2ebef7a4` の blob が一致した。`t126_driver.py:376–384` の `"identity code file missing"`／`"identity code file differs from HEAD"` が新たにこの 3 file にも適用される。
- **重さ:** should。
- **是正案:** 「trace に対する verifier の判定意味論と検証ロジックは不変。identity の受理形と照合対象は変更する」と限定する。新取得の実行 bytes と指定 commit の束縛強化は規律 2・3・7 に整合し、過去の承認済みコードへの固定ではない。

**A4 — 先例以降の committed JSON も再確認できた。ただし不存在の主張は調査範囲に限定する。**

- **主張:** 今回の静的探索では、変更に伴う修正が必要な旧 identity 成果物・golden・別名の集合定義・固定 hash pin は発見しなかった。
- **根拠:** base `d2ebef7a4` の committed `.json` 5,934 file を解析し、解析可能なものの exact `code_identity` key は 0 件。文字列としての出現は 10 file。解析不能 7 file にも同文字列はなく、壊れた fixture やログ等だった。`c09211d17..d2ebef7a4` の 397 commit に属する、JSON path を持つ 206 blob も確認し、解析可能なものの key は 0 件だった。履歴側の解析不能 3 file は上記 7 file に含まれる。

  contract/test の完全 SHA256・blob ID の作業木検索も 0 件。schema 文字列の production 出現は `contract.py:496` と `t126_driver.py:423`、test 側は `test_t126_pegasus_tools.py:1094` と `test_t126_qualification_contract.py:59,258`。fixture は同 `:76` の `"path: \"4\" * 64 for path in REQUIRED_CODE_IDENTITY_PATHS"` 等で追随する。`campaign_lock.py:107,204` と consumer test の path 列挙は、今回変わらない contract の path を指す。
- **重さ:** should。
- **是正案:** 「調査した committed JSON・関連 consumer に修正対象を発見しなかった。repo 外の旧成果物の存在・利用は未確認」と記す。schema 名の据え置きを旧形の互換性と説明しない。

## 親 brief への指摘

**A5 — 「verifier package 全 7 file」は誤り。plan の訂正を採用すべき。**

- **主張:** 今回の追加後は package 内 9 file 中 7 file の個別束縛になる。「全 package」「完全な verifier 閉包」への一般化はできない。
- **根拠:** `s1-brief.md:5` は「verifier package 全 7 file」。tracked file は 9 件で、`s2-plan.md:111–112` の指摘が正しい。また `t126_driver.py:423` 付近の preimage は superproject commit/tree を持ち、`identity.py:128–134` がその Git chain を検査するため、追加対象も従来から commit/tree 経由では束縛されている。
- **重さ:** should。
- **是正案:** 「verifier package 内の指定 7 file に個別 code hash と disk/blob 照合を広げる」に修正する。

**A6 — P4 の script に関する記述は事実と異なる。**

- **主張:** script に独立した path 列挙は存在する。ただし required code 集合の複製ではなく、追加修正は不要。
- **根拠:** `s1-brief.md:33` は「path 名を列挙しない」。実際には `tools/pegasus/submit_t126_qualification.sh:124–134` が 5 path の tracked 検査、`:149–164` が 7 path の disk/blob 照合を行う。`:142–144` の `"orchestrator"` 全体の archive には追加 3 file も含まれる。`t126_qualification.sh:799` にも driver path の固定記述がある。
- **重さ:** should。
- **是正案:** plan の訂正を採用し、「required code 集合を独立に全列挙していない」とする。script の変更は足さない。

**A7 — Codex 子木の dirt の観測は、編集競合評価を超える結論を支えない。**

- **主張:** 親の観測は当該時点の競合リスクを低く評価する材料になるが、「無害」「今後も競合なし」や成果物互換性の証明にはならない。
- **根拠:** `s1-brief.md:17–18` の証拠は「contract.py は現 main と同一 sha256」「contract.py に触れず」「稼働 process 0」。これは対象 path・観測時点を限定した状態情報であり、他の dirt の意味や観測後の変更を示さない。
- **重さ:** should。
- **是正案:** 「親の観測時点では、今回の編集面に未着地の競合を認めなかった」と限定する。互換性や test の成否の根拠とは分ける。

**A8 — 「焦点走 4 file に drift gate は無い」は過大な推論。**

- **主張:** 先例の未 commit 成功から言えるのは、その走で実作業木の contract 差分が拒否要因にならなかったことまで。fixture 内の Git/blob 検査は存在する。
- **根拠:** `s1-brief.md:19` の断定に対し、`test_t126_pegasus_tools.py:1085–1088` は fixture commit の blob hash を生成し、`:3143` は `test_identity_consumer_rejects_git_chain_tool_hash_and_snapshot_traversal` を持つ。実 repo の loader 比較は `contract_loader_binding.py:526–529` の `if disk != blob`。さらに先例 commit から本 base までに、焦点走の `test_t126_qualification_driver.py` 自体が変更されている。
- **重さ:** should。
- **是正案:** `s2-plan.md:117` の「当該実 repo loader 比較は見当たらない」という限定を採用する。今回の焦点走・変異結果は今回の checkout で確認し、先例成功を代用しない。

## 裁定パッケージ候補

**A9 — 残る CLI 2 file は、確認した T126 経路では到達されない。追加裁定候補は立てない。**

- **主張:** `__main__.py`／`cli.py` が集合外に残ることを、先例 A7 と同じ「実行依存の穴」と呼ぶ根拠はない。
- **根拠:** `t126_qualification.sh:835` は `t126_driver.py run` を起動し、driver `:623` は `pipeline.evaluate()` を呼ぶ。`campaign/pipeline.py:39,505–507,614` は package API の `verify_trace_dir_with_capability` を直接使用する。`verifier/__init__.py:20–42` は CLI を import しない。collector 側も `qualification/artifacts.py:24` の receipt API を使う。一方、`verifier/__main__.py:5` の `from .cli import main` は独立 CLI 入口で、`orchestrator/verify.py:16` も同 CLI を import する。確認した T126 driver・collector・submit 経路からこれらへの呼出しはない。
- **重さ:** should。
- **是正案:** plan の「残る穴」は「集合外の CLI 入口」に改める。今回の実装にも裁定パッケージにも追加しない。

## 総括

**実装 must-fix は 0 件。3 行追加と独立包含 test 1 本の plan を支持する。** brief は package 全体という表現、script の列挙不存在、dirt と drift gate の一般化を訂正すべき。

先例 A1 は既裁定・P3 で解決済み、A2 の意味論の限定は引き続き必要。A3 は今回の裁定と到達可能性確認で充足する。A4・A5 は今回の JSON・履歴・pin 探索で補強できたが、repo 外には一般化できない。A6 は個別束縛と commit/tree 束縛の区別を維持する。A7 は今回名指された 3 file の追加で対処され、残る CLI 2 file には同じ所見を転用できない。

静的検査のみ実施。ファイル変更、pytest、変異実行は行っていない。