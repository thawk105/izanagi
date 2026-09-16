## 総括

親 brief の P1 は、判断の委任を人間による個別の喪失受容へ読み替えており、採用できない。  
段2の全30件救出案はこの問題を避けるが、内容照合の結果を「未保全」「完全保全」と断定する記述は訂正が必要。  
30 OID と53組の照合集合は一致し、37組の gzip 展開後一致を確認した。ただし commit 全体の着地証明ではない。  
提示された field の生成方針に確定的な schema 違反は見つからない。完成した30 JSON は未提示なので、全件通過とは判定していない。  
静的検査のみ実施。契約本文の変更や新しい gate は不要である。

## 所見

- [A-1] blocker | D2044 項7は、16件を `accepted-loss` にする人間の明示的受容を与えていない。
  - 根拠: `ruling-d2044-item7.txt:7` は「救出または喪失受容を具体的に判断する」とし、`:11` は「人間の明示的な喪失受容」、`:13` は「個々の喪失受容」を要求する。`docs/unreachable-object-ledger.md:53` も同じ境界を置く。`s1-brief.md:64` の「受容授権」はこの逐語から導けない。
  - 成果物影響: 16件を `accepted-loss` にすると、その OID が再報告されても stale 通知されなくなる。単なる説明の差ではなく、通知対象集合が縮む。
  - 是正: 段2の全30件救出案を採り、実際の ref 作成・到達性再検査後に `rescued` とする。親 P1 に戻さない。これなら契約変更も追加裁定待ちも不要。

- [A-2] must-fix | 「一致なし」を「main のどこにも同一内容が無い」と一般化している。
  - 根拠: `match_content.py:50`、`:66`、`:71` は basename と basename＋`.gz` の候補だけを検索する。別 basename への改名、別形式への格納は検索外。`:39` は `-z` なしで、`:45` の path は Git の引用表記を復号していない。`s1-brief.md:34` の断定、`s2-plan.md:113` 等の「未保全」は検索能力を超える。
  - 成果物影響: 16組／14 commit の `resolution_note` に、未確認の不在・喪失を事実として記録する。
  - 是正: 「今回の basename／basename＋`.gz` 照合では一致を確認できなかった」に限定する。全件救出の判断は維持でき、全探索を追加する必要はない。

- [A-3] must-fix | gzip 展開後の blob 一致を、commit の意味・状態・着地の保全証明にしてはならない。
  - 根拠: `match_content.py:46` で取得した mode は捨て、`:47` で gitlink を除外する。symlink は blob として残るが通常ファイルと区別しない。対して `tools/check_branch_landed.py:705` は path・mode・object type・OID を一体の証明状態として比較する。保存 JSON の集計は **53組中37組が gzip 一致、直接一致は0組**。
  - 成果物影響: `assessment_verdict=indeterminate` のまま note で「完全に main に保全済み」と書けば、実質的に `landed` を迂回主張する。実行権限、リンクの意味、配置、他の変更を欠いた証拠で判断を甘くすることになる。
  - 是正: note は「監査報告 path のうち N 組で、記載候補の gzip 展開後 Git blob OID が一致。commit 全体の着地は未証明」とする。`rescued` の根拠は ref の到達性確認に置く。
  
  同一 blob が別用途で配置されていても hash は一致する。submodule 内部もこの探索には含まれない。一方、通常の無置換 Git object 読取りについて、gzip 展開や `hash-object --stdin` 自体が内容を正規化して偽一致を作る根拠はない。SHA-1 衝突を今回の実証済み問題として扱うべきでもない。

- [A-4] must-fix | 照合結果の「main」が不変な参照へ結び付いていない。
  - 根拠: `match_content.py:39` は可変名 `main` を読み、`:96` の出力には比較先 commit OID、候補 blob OID、観測時刻を保存しない。また `:27`、`:75` は replace を無効化していない。replace blob が存在すれば、列挙された候補 OID と実際に展開する bytes が異なる経路がある。
  - 成果物影響: `resolution_note` の「main に残る」がどの状態への主張なのか確定せず、保存 JSON だけでは元 object に対する一致を再現できない。
  - 是正: 現資料だけを使うなら「保存済み照合 JSON が一致を報告した」と限定する。保全の事実として引用する場合は、親の一回限りの照合で固定した main OID と候補 blob OIDを証拠に残し、置換を無効化する。台帳 field や gate の追加は不要。今回 replace が存在したとは断定しない。

- [A-5] must-fix | 親 brief の期限・storage・verdict の一括断定を最終記帳へ持ち込めない。
  - 根拠: `s1-brief.md:26` は4件の timeout を「必ず」へ一般化する。`:38` は9月9日の loose object も期限超過とするが、`evidence.json:696`、`:1047`、`:2032`、`:2278` の mtime＋14日は9月23日。`collect_evidence.py:31` は `REPO/.git/objects` を直結し、pack membership を調べない。
  - 成果物影響: `assessment_verdict`／`assessment_reason`、`storage_kind`、`loss_possible_not_before` が未観測値や誤った下界になる。worktree を同 script に渡すと loose 不在の誤認も起こりうる。
  - 是正: 段2の個別 assessment と既存 retention 関数による再収集を維持する。packed の評価時刻への下界は「期限超過」と説明しない。段2で既に訂正された点なので、親 brief を優先して差し戻さない。

## 親 brief への直接の異議

P1 は撤回が必要である。`accepted-loss` は人間の受容を記録する状態であり、AI の内容照合により通知を消すための状態ではない。全件救出であれば、`indeterminate` の記録と通知解消は両立する。着地未証明の object を実際に保持するので、判定を甘くする変更には当たらない。

「30 entry が本当に通るか」について、段2は完成 JSON ではなく生成仕様である。静的に確認できた範囲は次のとおり。

| 対象 | 確認結果 |
|---|---|
| `object_oid` | 段2の30件は全て小文字40桁。findings・evidence・content-match・audit の集合と一致 |
| `source_tips` | `{}` は validator を通る。非空にする場合は値に full OID が必要 |
| GC 算術 | `(6700 + 255) // 256 = 27` |
| 初期状態 | `pending` と解決3 field の null は整合 |
| 最終状態 | `rescued`、Z終端日時、`refs/rescue/t2640/<OID>`、非空 note の組合せは整合 |
| その他の解決状態 | `resolved_at` と非空 note が必要で、`rescue_ref` は null |
| 未確定部分 | 個別 stdout の hash、実測日時、retention 値、完成 note は生成後の確認が必要 |

根拠は `tools/check_branch_rescue.py:1649`、`:1676`、`:1705`、`:1714`、`:1730`。特に `loss_possible_not_before` が算出不能で null になれば、現 schema の string 条件を通らない。架空の日時で埋めてはならない。

`現在、記録済み entry はない。` は現況記述であり、契約規定ではない。段2どおり116行目だけを記帳へ置換し、1〜115行を保持することに異議はない。残せば記帳後に虚偽となる。

pin について、指定2テスト内では親の結論を反証できなかった。`test_branch_rescue_ledger.py:187`、`:199`、`:330`、`:337` は schema 順・節内の正規表現・固定文字列を検査するが entry 本文を固定しない。`test_check_branch_rescue.py:848` の台帳は一時 repo の fixture であり、本台帳の件数 pin ではない。行番号・全文 digest・派生 digest・role 名を経由した entry pin も指定2ファイル内には見つからない。ただし、射影外まで含めた不存在は保証しない。

## scope 外だが real な所見 (裁定パッケージ候補)

`tools/check_branch_landed.py:38`、`:210`、`:226` には、全体 timeout と別に各 Git command を既定5秒で制限する実装がある。親が報告した `git command timed out: log` と整合する。ただし4件の観測から全30件の必然的 timeout は導けない。必要なら個別 stdout・stderr・rc を添えて別裁定へ返す。本 wave で timeout・判定器・T-2688 の rc 契約を変更する根拠にはしない。