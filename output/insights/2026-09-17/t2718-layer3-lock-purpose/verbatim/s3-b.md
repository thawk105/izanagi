## 所見

以下、`L` は `orchestrator/campaign/layer3_report.py`、`T` は `orchestrator/tests/test_layer3_report.py`。brief／plan／probe は指定された job tmp 内の資料を指す。静的レビューのみで、pytest・変異テストは未実行。

**B-1 — 完了主張が実際の受理条件より広い。**

- **対象:** `brief.md:7,39,60`、`L:835–838`
- **主張:** 「中央 admission の HISTORICAL_RAW 受理集合と一致させる」は修正が必要。中央 admission が通っても、材料レポート固有の records/threads、WAL、calibration 等の条件が残る。
- **根拠:** 現行63対照も records/threads 検査で拒否されている。今回の変更後も、その検査は同じ。plan:145 の「admission と後段検査を満たす」という限定は正しい。
- **自己判定:** real
- **区分:** **must-fix（成果物の主張）**
- **修正要求:** 「歴史 grammar を理由とする再拒否を解消する。材料レポート固有の入力条件は維持する」へ限定する。

**B-2 — P4 は合理的な縮小案だが、実在3本での完全生成という要求は満たさない。**

- **対象:** `brief.md:8,20,39`、`parent-probe-results.md:6–35`、`L:835–838`
- **主張:** 合成 fixture で完全生成、実 corpus で同一到達点を示す分担は技術的に妥当。ただし、元の完了条件との差を裁定事項として明示すべき。
- **根拠:** records/threads が欠けた元 lock を保持し、対応変更も scope 外とする限り、**scope 内で実在3本すべてを完全生成させる経路は無い**。出力先・HEAD 引数ではこの検査を回避できない。lock の書換えや検査の monkeypatch は実 corpus の完全生成証拠にならない。
- **証拠の限界:** 提供された probe は exact-62 rr5、exact-24 rr5、63対照の結果を示す。exact-62 rr50／rr95 は所在一覧のみで、3本すべての停止点を実測済みとは確認できない。修正後、3本それぞれの例外全文・cause・lock/WAL bytes 不変を記録する必要がある。
- **自己判定:** real
- **区分:** **裁定パッケージ候補**

**B-3 — consumer の取り残しと歴史型の不適合は、plan の変更で解消できる。**

- **対象:** `L:755,815,853,866,937`、`T:2258,2279`
- **主張:** signature 追随漏れ、`preserved_v1_text()` 等への隠れた依存は見つからない。
- **根拠:** `_read_campaign_lock` の完全一致検索で、定義以外は本体2件・テスト2件のみ。歴史型の直接消費も下記一覧で尽きる。authority の使用 field は歴史型にも存在する。
- **自己判定:** refuted（取り残しの懸念）
- **区分:** nit（対応不要）

**B-4 — identity 渡しは、材料レポートの WAL 経路全体で等価。**

- **対象:** `L:815`、`orchestrator/campaign/wal.py:630,1099–1172,1733–1769`
- **主張:** P2 を採用できる。plan が留保した「authority を別途参照しないこと」も静的に確認できた。
- **根拠:** material-report helper が lock を消費するのは `_knowledge_lock_binding` と、その関数を呼ぶ `validate_knowledge_provenance_bindings`。いずれも identity の search_config だけを読む。以後は receipt と取得済み binding から projection を作り、authority を参照しない。`L:789–791` の exact key 検査により identity に `schema_version` は入らない。
- **帰結:** 同一入力・同一 HEAD 指定なら、63／v1 report に generator hash 以外の変更箇所は認められない。`wal.py` を変更する必要はない。
- **自己判定:** refuted（P2 による情報欠落の懸念）
- **区分:** nit（plan の留保を解消可能）

**B-5 — completeness の比較は generator hash を除外していない。**

- **対象:** `orchestrator/campaign/autonomous_trial_completeness.py:4653–4722`、`L:868`
- **主張:** I5 の「generator hash を除けば同一」と、旧 persisted report が fresh report と比較一致することは別。
- **根拠:** 指定された比較射影は `generated_from_head` を除くが、`meta.generator.sha256` は保持する。今回のソース変更でその hash は変わる。指定範囲外の処理による調整までは確認していない。
- **修正要求:** plan の影響説明にこの区別を追記する。今回の都合で比較を緩和したり、persisted artifact を再発行したりする必要はない。
- **自己判定:** real
- **区分:** nit

**B-6 — exact enum テストは主要変異を殺せるが、境界ケースを明記するとよい。**

- **対象:** `s2-plan-out.md:85–87`、`L:112`
- **主張:** 正常63 lock に文字列・別 Enum を渡す設計は有効。str subclass と enum constructor の扱いを追加明記する。
- **根拠:** 型検査を消すと、これら不正 purpose は通常 decoder 側へ流れて正常63 lock を読めるため、TypeError 期待が失敗する。存在しない path だけに依存していない点もよい。
- **追加ケース:** `class S(str)` の値は拒否。一方、`CampaignReadPurpose("HISTORICAL_RAW")` は正規 member 自身なので**成功する正例**であり、negative にしてはいけない。別 Enum は同名・同値 member を明示する。
- **自己判定:** real
- **区分:** nit

**B-7 — committed repo は rewrite helper 自体の依存ではない。**

- **対象:** `s2-plan-out.md:73–79,93–94`、`orchestrator/tests/test_artifact_admission.py:594,760–780,3194–3203`
- **主張:** 「最短の構成」という説明は強すぎる。ただし、採用案自体に問題はない。
- **根拠:** exact-62 rewrite helper は既存 authority map を独立 literal tuple で選別し、canonical JSON を書くだけ。decoder 段の検証には新しい committed repo は不要。canonical serializer は sort・compact separators を使い、末尾改行も付けないため outer canonical 検査を満たす。
- **区別:** plan は rewrite 後に実 admission を通し、固定 epoch も検証する。この統合証拠と固定 fixture bytes のために committed repo を使う意味はある。完全に admission を stub 化する場合は、更新後の lock/WAL digest を持つ view を用意すれば decoder 経路を検証できるが、実 admission の証拠にはならない。
- **恒真化:** 固定 epoch literal、固定 identity、実 decoder による成功、例外全文という期待値設計に恒真化は見当たらない。
- **自己判定:** real
- **区分:** nit

## consumer 一覧

### signature 変更で赤になるもの

| file:line | consumer | 必要な追随 |
|---|---|---|
| `L:755` | `build_report` | HISTORICAL_RAW を指定 |
| `L:937` | `build_accepted_report` | CERTIFIED_ACCEPTANCE を指定 |
| `T:2258` | `test_artifact_refs_accept_validated_knowledge_receipt_digest` | CERTIFIED_ACCEPTANCE を指定 |
| `T:2279` | `test_artifact_refs_reject_receipt_changed_after_provenance_read` | CERTIFIED_ACCEPTANCE を指定 |

他 test file・他 module に当該 helper の直接呼出しは見つからない。`s1_report`／`s8b_oracle_report` の `_read_campaign_lock_bytes` は別関数。plan の一覧に漏れはない。

### 歴史型の全消費地点

| file:line | 消費 | 適合性 |
|---|---|---|
| `L:756,784–791` | identity、lineage、exact keys | 歴史型の dict identity で動く |
| `L:815` | WAL provenance helper | `.identity` 渡しへの変更が必要 |
| `L:835–838,856,864,870–871` | records/threads、calibration 条件、commit、workload、policy_hint | identity の内容は保持される |
| `L:853 → 375–402` | authority の environment contract hash | 歴史 authority に同名 field がある |
| `L:866 → 191–205` | authority の commit による HEAD fallback | 歴史 authority に同名 field がある |

`preserved_v1_text()`、authority の `as_dict()`、通常型への exact type 検査を要求する追加 consumer はない。

### 挙動が変わる、または影響確認が必要な公開経路

| consumer | 影響 |
|---|---|
| `L:951` の accepted builder 内部呼出し | 内部 decoded 型は変わる。入口937とcertified admissionは維持 |
| `L:1028` の `render`、CLI | 歴史 grammar が後段へ進む。公開 signature・CLI は不変 |
| `autonomous_trial_completeness.py:4666` | fresh rebuild が歴史 grammar を読める。63／v1は generator hash 以外の差を認めない |
| `p3_autonomous_workload_trial.py:3116` | `render` 経由で同じ変化。既存63出力の意味は維持 |
| `test_t126_qualification_artifacts.py:371,377,391,403,424` | builder を呼ぶが signature 追随不要。qualification 拒否は残る |

## 変異候補 × test の殺傷表

「殺せる」は計画どおり実装した場合の静的判定であり、実測結果ではない。

| 変異 | 観測点／対応 test | 判定 |
|---|---|---|
| M1 常に通常 decoder | exact-62／24 `build_report` 正例が schema error になる | 殺せる |
| M2 purpose 分岐反転 | 歴史正例の失敗、63／v1 の exact 返却型不一致 | 殺せる |
| M3 常に歴史 decoder | accepted 負例の正確な schema error が消える。通常目的の返却型も不一致 | 殺せる |
| M4 937 を HISTORICAL_RAW 化 | 拒否が後段へ移り、例外全文・codec cause の期待を満たさない | 殺せる |
| M5 755 を CERTIFIED_ACCEPTANCE 化 | exact-62／24 正例が schema error になる | 殺せる |
| M6 exact 型検査除去 | 正常63 lock＋不正 purpose が TypeError なしで成功する | 殺せる |
| M7 815 を decoded object 渡しに戻す | 歴史型を WAL が拒否し、完全生成正例が失敗する | 殺せる |
| M8 purpose に既定値追加 | purpose 省略で TypeError が出なくなる | 殺せる |
| M9 型検査を I/O 後へ移動 | 不正 purpose＋存在しない path が読取エラーになる | 殺せる |
| 966 の certified admission 削除 | exact-62／24 は937で停止し、変異地点へ届かない | 新規歴史負例では殺せない |
| 980 の E1 gate 削除 | 同上 | 新規歴史負例では殺せない |

63 lock の「成功と identity 一致」だけでは decoder 選択を区別できない。plan は exact-62／24 の実 decoder 正例と、63／v1 の exact 返却型検査を併用しており、この弱点を補っている。

## 総括

- must-fix は1件：brief の受理集合・成果物影響の過大な主張を限定する。
- P4 の縮小は技術的に合理的だが、実在3本の完全生成という要求との差は裁定事項として残す。
- plan に consumer 漏れ・scope 外の実装変更は見つからず、P1〜P3 は妥当。
- plan には enum 境界ケース、fixture の目的、completeness の generator hash 比較を補足する。
- 実装・pytest・変異実測は未実施。親による3本個別の到達点確認が必要。