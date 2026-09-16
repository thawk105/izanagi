## 所見

**A1 — P2 は歴史記録の保存と、現行 verify の互換性を分けて記述すべき。**

- **主張:** 互換層を追加しない方針は妥当。ただし「歴史記録として据え置き」が「新 verify による invalid 判定まで承認した」とは逐語から断定できない。
- **根拠:** `docs/archive/worklog-phase3-0817-622.md:485` は「過去の qualification 成果物は歴史記録として据え置き」。他方、`contract.py:533–534` は旧集合に `ProtocolError("series identity code_identity required set mismatch")` を返す。先行検査を通った旧成果物は、driver の `verify()` では `t126_driver.py:1365`、collector の receipt 検証では `collector.py:1487` で拒否される。どちらも後段の `verify_recorded_series_identity()` より前。直接同関数を呼んでも `identity.py:124` で同じ例外になる。driver は `:1572–1574` で `invalid` に変換し、CLI は `:1607` で終了値 2 を返す。collector も `:1880–1883` で `invalid` を返す。
- **重さ:** must-fix（説明・影響評価）。
- **是正案:** 「旧成果物の bytes と当時の判定は保持するが、現行 verify は旧集合を受理しない」と明記する。この結果を過去の測定の無効化に使わないことを、規律 7 と対応づける。互換層の実装要求ではない。

**A2 — 「検証意味論に触れない」は対象を限定しないと誤り。**

- **主張:** trace に対する verifier の判定意味論は不変だが、qualification identity の受理集合は変わる。required path の純増は、受理集合の単純な純増ではない。
- **根拠:** `contract.py:533` の述語は `set(rows) != required`。37 key 形が拒否され、新しい 40 key 形が受理対象になる。`t126_driver.py:365–370` の `"identity code file missing"` と `"identity code file differs from HEAD"` も新 3 path に適用される。
- **重さ:** should。
- **是正案:** brief の I2 を「検証ロジックは変更しないが、その定数変更により identity の受理形と検査対象を変更する」に修正する。新取得で実行 bytes と指定 commit を照合する強化は、過去の承認済み commit への一致を要求するものではなく、規律 2・7 に沿う。

**A3 — P3 は包含 test 単体について成立するが、DW-O13 の検討をそれで終えてはいけない。**

- **主張:** 新しい包含 test 自体は成果物の runtime gate ではない。一方、production の exact 述語が新たな受理形を持つ点は別に評価する必要がある。
- **根拠:** `s2-plan.md:21–25` は定数への個別包含 assert のみ。しかし `docs/dev-wave/operations.md:102` は「既存 exact 述語の改訂で受理形を増やす場合も新設に当たる」と明記する。A2 の変更は従来拒否された 40 key 形を受理する。
- **重さ:** should。
- **是正案:** P3 の非適用説明を test 単体に限定する。production 側については既存 `code_identity` field、driver の集合走査、追跡済みの新 3 path という到達可能性の根拠を記す。新規 census や gate の追加は不要。

## 親 brief への指摘

**A4 — 「壊れる既存成果物なし」は実測範囲を超える。**

- **主張:** committed JSON の検索結果と、過去の scope 記述から、repo 外を含む成果物不存在は導けない。T-548 の編集競合情報も互換性の根拠にはならない。
- **根拠:** `s1-brief.md:9` は「live qualification は未実施」「壊れる既存成果物なし」とするが、引用先 `docs/phase3.md:1313` は「live qualification は本項の scope 外」としか述べていない。`s1-brief.md:12` の「生存 process 0」「contract.py には触れていない」は編集面の情報である。
- **重さ:** must-fix（事実の一般化）。
- **是正案:** 「調査した committed 成果物に旧 identity の実体を発見していない。repo 外の存在・利用は未確認」に限定する。T-548 の記述は親の観測時点における編集競合評価として保持する。

**A5 — pin・fixture の再確認では阻害要因を発見しなかったが、「path pin は閉包のみ」は限定が必要。**

- **主張:** 3 行追加で修正必須になる golden や独立した 37 key 定義は今回の静的探索では見つからない。path を固定列挙する test は存在する。
- **根拠:** HEAD の committed JSON では `code_identity` 文字列が 7 ファイルに出るが、JSON を解析した exact `code_identity` key は 0 件。現 contract の SHA256 `c50e2b05…` と blob `6c1451b1…` の完全値検索も 0 件だった。schema 文字列の出現は production 2 箇所と test 3 箇所で、旧集合を固定した golden は発見しなかった。`test_t126_pegasus_tools.py:980,1025,1085` は集合から fixture と blob hash を生成する。独立列挙は `test_campaign_lock_codec.py:77` 等にも `"orchestrator/qualification/contract.py"` があるが、今回その path は不変。`submit_t126_qualification.sh:142–144` は `orchestrator` 全体を archive し、`:124–134,149–164` の入口列挙は code identity 全集合の複製ではない。docs の「37 path」は archive の過去記録だった。
- **重さ:** nit。
- **是正案:** 「path pin は閉包のみ」を「production の関連閉包に加え、test の独立列挙もあるが変更不要」に限定する。schema 文字列を据え置くことが旧集合の互換性を意味しない点も残す。

**A6 — 「dsg/model/parse の変更に series identity が反応しない」は強すぎる。**

- **主張:** 個別 hash と実行 bytes の照合から漏れていることと、series identity 全体が変化しないことは異なる。
- **根拠:** `s1-brief.md:6` は「変更に series identity が反応しない」とする。しかし `t126_driver.py:412–413` は `"superproject_commit"` と `"superproject_tree"` を preimage に含め、`identity.py:128–134` はその Git chain を検査する。commit された変更なら、この経路でも identity は変わる。
- **重さ:** should。
- **是正案:** 「新 3 file は個別 code hash と `_identity_files()` の disk/blob 照合対象に入っていない」に修正する。本変更を verifier 全閉包の完全な束縛と説明しない。

## 裁定パッケージ候補

**A7 — 除外 3 file には具体的な実行依存が残るが、今回の 3 file 限定は裁定の範囲内。**

- **主張:** `__init__.py`・`report.py`・`commit_receipt.py` の追加は別裁定候補。今回の実装へ自動的に含める必要はない。
- **根拠:** 裁定 `docs/archive/worklog-phase3-0817-622.md:483` は `dsg/model/parse` を名指す。一方、`orchestrator/campaign/pipeline.py:39` は `from ..verifier import`、`verifier/core.py:256,264` は `result_to_dict(result)` と `_domain_digest(...)`、`qualification/artifacts.py:855` は `validate_live_receipt(...)` に依存する。
- **重さ:** 裁定パッケージ候補。
- **是正案:** 「dispatch・構造化結果・receipt 検証を担う除外 3 file は、T126 個別 code hash と disk/blob 照合の対象外に残る。commit/tree・兄弟閉包の既存束縛を踏まえ、T126 でも直接束縛するか」を別件として返す。

## 総括

**実装案の 3 行追加と独立包含 test は妥当。実装範囲を広げる必要は認めない。** P1・P4 は支持する。P3 は test 単体について支持する。

親は A1・A4 の説明を修正すべき。旧成果物の現行 verify による拒否は実際に起こるため、「歴史記録の保持」「現行契約への適合」「成果物不存在の確認範囲」を分ける必要がある。規律 2・3 の verifier 挙動を弱める変更は見当たらないが、identity の包含 test は正しさ判定そのものの有効性を証明しない。

読取りと静的検査のみ実施。ファイル変更、pytest、変異実行は行っていない。