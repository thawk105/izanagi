## 所見

以下の行番号は変更前。静的レビューのみで、pytest・実 corpus の再実測は行っていない。

### A-1：decoder が読んだ bytes と admission の bytes が束縛されていない

- **対象:** `layer3_report.py:733,755,795–800,937,951–975`、`brief.md:28,38`、`s2-plan-out.md:65,147`
- **主張:** 固定入力では certified 受理集合を維持するが、読取り途中の差替えを含めると、変更後だけ旧 grammar を通せる経路がある。I1/P3 の無条件な「不変」は成立しない。
- **根拠:** 795 行が hash するのは、755 行で decode した入力ではなく、パスから再読したファイルである。次の順序を排除できない。
  1. certified 条件を満たす現行63 lock **A** を937行と733行で読む。
  2. 755行だけ、有効な exact-62／24 lock **B** を読む。
  3. 795行までに A に戻す。admission digest との比較は成功する。
  4. report は B の identity／authority を使用するが、`admission_decision` は A のものになる。
  5. 966行も A を読むため、975行の decision 一致と980行の E1 検査を通せる。

  B の identity・authority を後段条件に適合させれば、この経路を閉じる比較は提示コードにない。変更前は755行の通常 decoder が B を拒否する。変更後は歴史 decoder が通す。`render_accepted` は1051行で builder を呼び、1057行でその report を書くため、追加の防壁にならない。

  A→別の現行63→A という競合自体は既存問題だが、**途中入力として旧 grammar まで許す差分は本変更で増える**。I3 の「builder が書き換えない」や実行前後の bytes 比較では、この差替えを排除できない。
- **修正案:** layer3 内で、decode に使う raw bytes を一度取得し、その同じ bytes の digest を admission decision と比較する。再読 hash だけでは不十分。v1 も含めるなら、改行変換を行う `read_text()` の結果を再 encode して raw digest の代用にしない。公開 `build_report` への purpose 追加や WAL の変更は不要。
- **自己判定:** **real**。到達経路を静的に特定。実行再現は未実施。
- **区分:** **must-fix**

### A-2：P2 の正規化は等価だが、knowledge 検査全体の等価性は未証明

- **対象:** `wal.py:1102,1135–1140,1733–1769`、`layer3_report.py:789–815`、`brief.md:37`、`s2-plan-out.md:39–47`
- **主張:** 指定範囲から「dict 化により knowledge 検査が弱まる」とは判定できない。同時に「WAL 全体で意味が等価」とも確定できない。
- **根拠:** 次の局所的な等価性は成立する。
  - 通常 decoded object は1748–1749行を通り、1768行で `.identity` になる。
  - identity dict は1752–1753行を通り、1769行でそのまま返る。
  - layer3 の789–791行が要求する exact key 集合には `schema_version` がない。
  - `_decoded_campaign_lock_value` は、通常 decoded object に対して authority を再検証していない。したがって、この型分岐自体が行っていた追加の authority 検査を失うわけではない。
  - 現行63／v1 は歴史 decoder 内でも通常 decoder を通るため、先行する decode の保証は残る。

  ただし、`_knowledge_lock_binding` 本文と material-report helper の1140行より後は、今回明示された読取り範囲外である。そこで authority や decoded 型を別途消費しないことは確認できない。plan がこの制限を明記した点は妥当だが、P2 の採用を確定する証拠はまだ不足している。
- **要求:** 親が当該 helper の推移的な呼出し先を確認し、authority 消費の有無を記録する。正常系の結果一致だけでなく、binding 欠落・不一致・receipt 不一致の拒否も比較する。
- **代替案:** authority 消費が見つかった場合、現行63／v1 は通常 decoder の返却 object を WAL に渡す経路を維持し、旧 grammar の identity 渡しを別に評価する。単に歴史型を通常型へ詰め替えて authority を装う案は採らない。
- **自己判定:** **real（証明不足）**。弱体化そのものは未確認。
- **区分:** **must-fix（P2 確定前の検証）**

### A-3：必須 purpose による dispatch は D1653 の boolean 緩和に当たらない

- **対象:** `layer3_report.py:112–120` の計画、`campaign_lock.py:620–731`、`artifact_admission.py:1016–1025,1530–1595`
- **主張:** P1 の必須 keyword enum と union 注釈は、指定された裁定に違反しない。
- **根拠:** 通常 decoder の grammar・返却型を広げず、既存の別入口 `decode_historical_campaign_lock` と別返却型へ dispatch する。`allow_legacy=True` のように通常 decoder の検査を緩める API ではない。中央 admission にも同型の purpose dispatch が存在する。

  exact enum 検査は I/O／decode 前、既定値なし、分岐は `is`。certified admission の view 分離も変更されず、965行の `require_certified_commit_evidence` が維持される。union はローカル dispatcher の返却注釈であり、通常 decoder／certified admission の受理 grammar の union 化ではない。
- **自己判定:** **refuted（裁定違反の疑い）**
- **区分:** **nit（変更要求なし）**

### A-4：固定された旧 lock が historical report 経由で certified に昇格する迂回はない

- **対象:** `layer3_report.py:937–994`
- **主張:** A-1 の競合を除けば、P3 の防壁は機能する。
- **根拠:** exact-62／24 は937行で止まり、951行の `build_report` に到達しない。仮に937行を歴史目的に変異させても、966行は通常 grammar の certified admission を要求する。historical view をそのまま certified view として使う構造ではなく、975行では decision 全体を再比較する。

  v1 は937行の codec を通るが、authority 不在の E0 が中央 certified epoch gate に拒否される。現行63は引き続き receipt、trial、report、certified commit evidence、decision 一致、E1 の条件を満たす必要がある。
- **自己判定:** **refuted（固定入力での昇格迂回の疑い）**
- **区分:** **nit（A-1 と区別して記録）**

### A-5：P4 は実測結果ではなく、未検証の到達予測を含む

- **対象:** `brief.md:39`、`parent-probe-results.md:6–29`、`layer3_report.py:757–838`
- **主張:** 63対照1本の838行到達から、exact-62全3本の同一到達点は導けない。
- **根拠:** 提示された実測は exact-62 の rr5 が755行で止まること、exact-24 の1本も同様であること、63対照が838行まで到達することを示す。旧 grammar 側には、それ以降の loop_state／whiteboard、identity・lineage、WAL stage・重複、bytes 照合、knowledge provenance、env_tag 一意性の未観測区間がある。いずれかが異なれば838行より前で止まる。

  `records/threads` 不在は「838行まで到達した場合には拒否される」根拠であり、そこまで到達する根拠ではない。
- **要求:** P4 を「予測、修正後に3本それぞれで確認」に修正する。plan の個別 probe 条件は維持し、先行拒否が出た場合も実際の到達点を報告する。
- **自己判定:** **real**
- **区分:** **must-fix（brief の証拠表現）**

### A-6：中央 admission と report の受理集合は一致しない

- **対象:** `brief.md:60`、`layer3_report.py:752–900`
- **主張:** 「中央 admission の HISTORICAL_RAW 受理集合と一致させる」は範囲が広すぎる。
- **根拠:** report 固有の ancestry、workload、calibration、schema 等の検査が残る。今回一致させるのは **lock の読取り grammar** であり、report 全体の受理集合ではない。P4 自体がその反例である。
- **自己判定:** **real**
- **区分:** **nit**

## 受理集合の追跡表

固定 bytes、先行 receipt 条件を満たす場合。生成成功には各後段条件も必要。

| lock 種別 | 経路 | 変更前 | 計画適用後 |
|---|---|---|---|
| exact-62 | `build_report` | 733 historical admission 通過後、755通常 decoderで拒否 | 755歴史 decoder通過。795照合→815knowledge→後段条件を満たせば生成 |
| exact-24 | `build_report` | 同上 | 同上 |
| v1 | `build_report` | 755通常 decoder通過、後段条件次第 | 歴史 decoder が通常 decoder を経由。後段条件次第。P2全経路確認は残る |
| 現行63 | `build_report` | 755通常 decoder通過、後段条件次第 | 歴史 decoder が通常 decoder を経由。identity／共通authority field維持 |
| exact-62 | `build_accepted_report` → `render_accepted` | 937 schema拒否、書込みなし | 同じ |
| exact-24 | 同上 | 937 schema拒否、書込みなし | 同じ |
| v1 | 同上 | 937通過可能、966の certified E0 gateで拒否 | 同じ |
| 現行63 | 同上 | 937→951→966→975→980を満たせば生成・書込み | 固定入力では同じ。P2確認が必要 |
| 現行63 A→旧grammar B→A | 同上 | 755で B を拒否 | A-1の順序では B をdecodeし、Aのdecisionでcertified化し得る |

## 変異候補への意見

- **M1〜M9 に、計画の記述だけから恒真・到達不能と断定できる候補はない。** 実装後のテストでの kill は未確認。
- **M4 はエラー位置の検証である。** 正確な schema エラーと cause を要求すれば、後段で別理由により拒否されても殺せる。ただし、それだけで966行の防壁を検証したことにはならない。
- **M6 の説明を修正する。** 型検査を除去しても、文字列 `"HISTORICAL_RAW"` は `is` 分岐を通らず通常 decoder 側へ落ちる。正常63入力で TypeError が出なくなることを検出する変異であり、「文字列で歴史 decoder に入る」変異ではない。
- **966行／980行削除を旧 grammar 入力だけで検査する案は到達不能。** plan の除外は正しい。各防壁を測るなら、937行を通過する現行63を使い、当該防壁までの前提を満たす必要がある。
- **追加優先候補:** A-1修正後の「decode対象 bytes の digest 比較を削除／パス再読 hash に戻す」変異。実 decoder を維持し、ファイル差替えの同期によって A→B→A を作る拒否テストで殺す。通常の前後 bytes 一致テストでは殺せない。
- **P2 の比較テスト:** 非Noneの正常結果一致だけでは拒否集合を保証しない。knowledge binding と receipt の不正入力について、object／identity 両入力が同じ拒否を示すことを追加する。

## 総括

must-fix は3件：A-1のbytes束縛、A-2のP2全経路検証、A-5の実測範囲訂正。
親 brief は I1/P3 の競合条件、P2の未証明部分、P4の予測と観測を修正する。
plan は同一bytesのdecode・digest比較と差替え拒否テストを追加する。
必須 exact enum によるdispatch自体はD422/D1653に適合し、固定旧lockのcertified拒否は維持される。