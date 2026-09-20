## 所見一覧

| id | 区分 | 対象 | 所見 | 放置時の成果物影響 1 行 |
|---|---|---|---|---|
| B1 | nit | plan | helper の末尾性判定と M09 は削除可能。既存 outcome 別 stage 判定と重複する。 | FC07 の受理集合・reason・receipt は変わらず、変異台帳に等価変異が1本増えるだけ。 |
| B2 | nit | plan | 両入力経路への適用説明が不足。frame 経路では外枠検査は冗長だが、terminal 件数検査は実効性を持つ。 | 提案実装の挙動は変わらないが、変異結果を frame 経路でも実測済みと読める余地が残る。 |
| B3 | nit | brief | 本文の11 file表記・P3・P4は追補に統合し、設計文書の「行17」は「893行・表の項目17」へ訂正する。 | 追補と plan に従えば成果物差分はない。原文だけを引いた受入記録との不整合が残る。 |

**must-fix は0件。** 以下は静的検査の結果であり、KILLED・受入成功の実測報告ではない。

## 各所見の根拠

### B1：削れるのは末尾性の再検査

[plan](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/codex/s2-plan.md:7) の helper は、最後に terminal の stage membership を再検査する。一方、`orchestrator/campaign/reflux_formal_consumer.py:1145` の accepted 分岐は COMMIT、`:1152` の rejected 分岐は ABORT を既に要求する。

最小削減は、helper の最後を `return True` にし、M09 を削ること。件数1の検査は残す。これで受理集合は同じで、変異は10本になる。維持する場合も、plan が明記する「等価・単独の gate 証拠に数えない」という扱いなら問題ない。

それ以外の scope 超過は見つからない。専用 helper は一般化されておらず、trigger との定数共有、`_wal_trigger` の変更、非 terminal の外枠検査、terminal payload key 集合の閉包は提案されていない。D1730 の4項はすべて含まれる。

- key 集合：exact 比較。
- 値の型：str／有限の非 bool 数／dict。stage は既存 outcome 別判定でも制限される。
- 重複：root stage が COMMIT／ABORT の record 数を1に制限。
- root shadow：root の `build_attempt_id` 等を余分 key として拒否。

### 変異の帰属と判定順

`test_reflux_formal_consumer.py:468` の `_rewrite_wal` は source・projection・参照 hash・record・ledger member を同期する。root attempt が存在すれば payload attempt を書き換えないため、root-shadow 負例も成立する。

| 変異 | 新 test による検出予測 | 既存 test との切り分け |
|---|---|---|
| M02：gate 無効化＋M5 | payload-only stage が P6Unavailable まで進み、FC07期待に反する | 新負例が直接検出する。旧 root-kind 負例とは異なる |
| M03：superset 許容 | extra root key／root attempt shadow | 新負例だけで検出可能 |
| M04：bool 許容 | ts-bool | 新負例だけで検出可能 |
| M05：件数検査除去 | duplicate abort／commit before abort | 末尾 abort は正常なので、既存 stage 判定には阻まれない |
| M06：gate 無効化 | shadow・extra・欠落3・型違い4・重複2 | 新負例だけで検出可能。payload-only stage と末尾非 terminal は既存 stage 判定で拒否され続ける |
| M10／M11 | variant-int／env-tag-none | 新負例だけで検出可能 |

したがって、主要3変異 M03・M05・M06 は「既存 test が殺しただけ」の証拠には依存していない。ただし、**完全 kill 集合は未確定**。plan:121 の probe→再登録は DW-M07／M08 に合う。

等価予測も判定順と整合する。

- **M01／逐語M5**：exact keys 通過後は root stage が存在する。`_wal_field` は root 優先なので直接参照と同値。
- **M07／payload 型除去**：root attempt 無しなら `reflux_result_evidence.py:1636` の attempt 検査で拒否。root attempt 有りなら新 exact keys で拒否。
- **M08／有限性除去**：projection は `reflux_origin_artifacts.py:87` の strict JSON 検査を先に通る。非有限値はここで拒否される。
- **M09**：後続の outcome 別 stage 判定が残るため等価。

現行 source に提案 helper と呼出しを**メモリ上だけで挿入**し、全12置換の `old` がそれぞれ1回だけ出現することを確認した。M02a は M02b の anchor を変更しない。`tools/mutation_harness.py:1079` は同一 mutant の `replacements` を累積適用するため、M02 は2置換を持つ1 spec で表現できる。実装後の再確認と注入 diff 確認は、planどおり別途必要。

### pin 閉包と焦点走

**生成物 pin を更新する第三 file は不要**という結論を支持する。

- `reflux_origin_fixture_baseline.json` は builder 出力の hash／byte length を固定する。
- `test_reflux_result_evidence.py:39` の4 golden と `:517` の1848 bytesも builder 出力に依存する。
- 新 test は function-scope の `case`（consumer test:374）を取得し、deepcopy（:507）と一時 evidence の書換えを行う。`_rewrite_wal` 自体は builder を呼ばず、`:452` の `_set_record` も case と ledger member の更新だけ。builder の既定出力へ戻る変更経路はない。
- `test_reflux_origin_fixture_builder.py:83` が固定するのは export API、`:107` は builder 出力、`:309` は fixture の33 record。consumer の test 関数数・node 数を固定するメタ検査ではない。
- `acceptance_duration_ledger.json:14384` 以降は nodeid ごとの履歴所要時間。`conftest.py:1739` は未知 node に `None` を返し、`:1800` 以降が未知所要を扱う。新15 node の追加を理由に台帳を更新する必要はない。

`_validate_wal_outcomes` の実行 caller は consumer:1448。その戻り値を生成物として hash／件数固定する別経路は見つからない。`docs/phase3-8c-wiring-design.md:893` は受入要件の表であり、機械的な hash／件数 pin ではない。

`git grep` では fixture builder の直接参照は**11 test file**。間接利用の `test_reflux_originless_compatibility.py` を加えると、planの12 fileになる。原文11 fileには `test_reflux_campaign_issuer.py:56` が欠けていたが、追補で解消済み。

なお `test_autonomous_trial_completeness.py:50` も P3 test module を import するが、使用箇所 `:5773` は `_coder_authority()` のみ。同 helper（P3 test:95）は CLI 引数処理であり、builder／consumer 呼出しへ進まない。これを13本目に加える根拠はない。

### B2：全層 scope の説明を補う

`reflux_result_evidence.py:1580` の分岐は次のとおり。

- canonical-list：list を canonical 化して返し、`parse_line` を通らない。
- frame：`:1595` で `parse_line` を通し、5 key の record へ射影する。
- 両者とも `:1640` の source／projection 一致検査後、同じ `ResolvedOrderedWal.records` を consumer:1448 へ渡す。

したがって提案 gate は両経路に効く。frame の外枠は `wal.py:364` の parser で既に閉じるが、parser は1行単位であり、**projection 内の terminal 重複は検査しない**。frame 経路でも件数検査は冗長ではない。

planにこの説明を足せば十分。新 test は canonical-list 経路なので、frame 経路での新 gate の実測まで主張しないこと。D1665 の canonical-list に関する理由は terminal にもそのまま成立する。

### B3：brief の本文・研究前進の表現

[brief:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/s1-brief.md:8) の「行17」は実際には設計文書893行の表項目17。P3・P4と焦点走数は追補:23〜25が訂正しており、planも訂正版を採用しているため、未解消の実装欠陥ではない。

研究前進の記述は、certified 選択集合不変を明記しており過大ではない。ただし守る成果物を、次のように直接書くと明確になる。

> canonical-list 経路で不正な terminal 外枠が FC07 を通過し、receipt／evidence-root 参照の発行へ進む経路を閉じる。certified 選択集合は変えない。

DW-O13 の490件は実 WAL の外枠観測、attempt 単位の16件は全て commit。abort の attempt 一意性や実8c projectionまで実測した証拠にはならない。この限界は plan:169・175 が適切に保持している。

## 総括

must-fix 0件、should 0件、nit 3件。
最重要確認点は、M03・M05・M06を新 test 自身が検出できることで、静的には成立する。
pin更新は不要、焦点走は追補どおり12 file。
両経路に gate は効き、frameでもterminal件数検査は実効性を持つ。
ファイル変更・pytest実行は行っていない。完全kill集合と受入結果は親の実測待ち。
