## 総括

**plan はそのまま承認できない。追加受理経路で、責任者未指名の説明文と NUL 1 文字の責任者が受理されることを、メモリ上の probe で確認した。** 一方、expectation／projection の検査を飛ばす変更は見当たらない。

指定の射影 9 ファイルはすべて読了。ファイル変更・commit・Git 状態変更は行っていない。**pytest・変異テストは実走していない。** 実施したのは静的調査と、`python3 -B` によるメモリ内の受理 probe・bytes 比較である。

以下の略記を用いる。`略記:行番号` は対応ファイルの行を指す。

|略記|ファイル|
|---|---|
|A|[p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/orchestrator/campaign/p3_b4_admission_record.py)|
|T|[test_p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/orchestrator/tests/test_p3_b4_admission_record.py)|
|D|[事前登録本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/docs/phase3-b4-reflux-ablation-preregistration.md)|
|P|[s2-plan.md](/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/artifacts/t2464-b4-start-time/s2-plan.md)|
|B|[s1-brief.md](/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/s1-brief.md)|
|C|[p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py)|

## 1. 追加受理集合に責任者未指名・制御文字が入る

**所見：追加分岐の責任者検査は、不変の識別子による指名を保証しない。**

現行関数の値走査だけを `P:40–62` のコードへメモリ上で置換し、他の 9 行と expectation を有効にした合成文書で確認した。次はすべて **ACCEPT** だった。

```text
実行責任者 = 担当者が決まり次第指名する、開始時刻 = 未記入
実行責任者 = thawk105（計測完了後に確定）、開始時刻 = 未記入
実行責任者 = \x00、開始時刻 = 未記入
実行責任者 = \x07、開始時刻 = 未記入
実行責任者 = ---\x00、開始時刻 = 未記入
```

`\x00`／`\x07` は説明用のエスケープ表記で、probe には実際のコードポイントを入れた。

**根拠：**

- `P:44` の capture は `、`・`=`・CR・LF 以外を許す。
- `A:658` はセル外周を `strip()`、`A:538–544` は NFKC と ignorable／format 検査だけを行う。
- `A:527–534` は `Cf` と列挙範囲を拒否するが、NUL／BEL の `Cc` 全般を拒否しない。
- `P:48–52` の `strip()`・非空・閉じた sentinel 検査では上記を除外しない。`---\x00` は whole-value 集合の `---` と一致しない。
- `D:40` は説明文・条件を禁じ、`D:339–340,349–350` は責任者を不変の識別子で指名する義務を維持している。

正規化についての probe 結果は次のとおり。

|責任者部分|結果と理由|
|---|---|
|`ＴＢＤ`|拒否。NFKC 後の `TBD` が sentinel|
|`ｔｈａｗｋ１０５`|受理。NFKC 後は `thawk105`|
|タブだけ／全角空白だけ|拒否。owner の `strip()` 後が空|
|U+200B／U+034F|拒否。追加分岐に到達する前の ignorable 検査|
|NUL／BEL だけ|受理。NFKC・`strip()` 後も非空|

**放置した場合：** 旧関数が開始時刻の `未記入` で拒否していた、責任者未指名の文書まで追加受理される。D1871 の「開始時刻だけを外す」ことと、責任者の指名義務を保持することの間に穴が残る。

ただし、**旧関数に責任者の意味検証があったわけではない**。`A:27–30` は意味・表示上の非空を非保証としている。問題は「既存の指名検査を削除した」ことではなく、**今回新たに受理する集合にも未指名が入り、案 B の根拠を満たさない**ことである。

**重大度：高。追加経路の境界として must-fix。** 修正範囲は今回の追加述語に限定すべきで、全セルの意味検証への拡張は別問題。

## 2. 負例の拒否原因と、証明にならないケース

**所見：全負例は旧関数でも拒否される。ただし、それだけで負例全体が恒真・無効とは言えない。追加分岐を広げる変異を捕捉するものと、捕捉しないケースを区別する必要がある。**

根拠は `P:112–120`、追加分岐 `P:42–54`、既存拒否条件 `A:669–673`。

|plan の負例|提案実装での拒否経路|検査上の限界|
|---|---|---|
|セル全体 `未記入`|fullmatch 不成立 → 既存 sentinel 拒否|無条件免除を捕捉する|
|owner が `未記入`|owner sentinel 条件不成立 → 既存 sentinel 拒否|owner の RE 検査削除を捕捉する|
|owner が空文字|capture の `+` により不一致 → 既存 sentinel 拒否|**`bool(owner)` 削除に対して恒真**|
|owner が空白だけ|capture 成立、strip 後が空 → 既存 sentinel 拒否|`bool(owner)` 削除を捕捉する|
|owner が `TBD`／`ＴＢＤ`／`N/A`／`要記入`|owner RE 条件不成立 → 既存 sentinel 拒否|owner RE 削除を捕捉する|
|owner が `x`／`---`|owner whole-value 条件不成立 → 既存 sentinel 拒否|whole-value 条件削除を捕捉する|
|start が `TODO`／`要記入`|fullmatch 不成立 → 既存 sentinel 拒否|開始時刻の許容語拡張を捕捉する|
|start に後続説明|fullmatch 不成立 → 既存 sentinel 拒否|`fullmatch → match` を捕捉する|
|順序逆転|fullmatch 不成立 → 既存 sentinel 拒否|列挙変異では主に無条件免除を捕捉する|
|追加の `、代理 = other`|owner capture 不成立 → 既存 sentinel 拒否|capture の `.+` 化を捕捉する|
|他行が `未記入`|対象外なので既存 sentinel 拒否|**label 条件削除だけでは全ケースとも拒否のまま**|

最後の負例にはさらに二点ある。

- `P:239` の「他行へ正例と同じ複合値を入れる」補足が必要。これを省くと、label 条件削除はこの node に対して **SURVIVE** する。
- expectation 行を `未記入` にするケースは、仮に sentinel 拒否を外しても `A:674 → A:509–511` の構文検査で同じエラーになる。**このケース単独では、その行の sentinel 保持を証明できない。**

**放置した場合：** node の成功を、実際には通っていない owner 条件や label 制限の証明として誤帰属する。

**重大度：中。** 空文字・空白の区別、expectation 行の再拒否、補足 fixture の必須性を明記すべき。

## 3. 変異は殺せる見込みだが、失敗 node は一意ではない

**所見：補足 fixture を含む plan 全体では、列挙された 10 変異に静的に明白な SURVIVE は見つからなかった。ただし、指定 node だけが赤になるという帰属は成立しない。**

以下は **読解結果であり、変異実走の kill 報告ではない**。根拠は `P:228–239` と前節の拒否経路。

|変異|指定 node の検出見込み／帰属上の問題|
|---|---|
|追加分岐削除|正例が旧 sentinel 拒否で赤になる|
|対象 label を無条件 `continue`|全体未記入だけでなく、owner 不正・別 sentinel・suffix・順序逆転・追加 field の各 node も赤になる|
|label 条件削除|`P:239` の env_tag 補足で検出。補足なしでは列挙テストに対して SURVIVE|
|`bool(owner)` 削除|空白ケースで検出。空文字ケースは赤にならない|
|owner RE 条件削除|reserved-owner に加え、unrecorded-owner も赤になる|
|owner whole-value 条件削除|reserved-owner の `x`／`---` で検出|
|start に `TODO` を追加|other-start-sentinels の `TODO` で検出|
|`fullmatch → match`|suffix の負例で検出|
|owner capture を `.+` に変更|extra-owner-start-field で検出|
|既存 RE から `未記入` 削除|other-rows 以外にも、whole-unrecorded、empty-owner、suffix、reordered、extra-field などが赤になる|

特に最後の変異では、提案された掲載順なら `P:112` の whole-unrecorded node が `P:120` の指定 node より先に失敗する。owner RE 削除でも `P:113` が指定された `P:115` より先に失敗する。

**放置した場合：** 全走の failed-node 集合を指定の 1 node と完全一致させる登録では MISMATCH になる。単独 node 実行で kill を確認することと、一意の診断ができることは別である。

**重大度：中。変異表の期待失敗集合を修正すべき。**

## 4. expectation／projection の到達性は増えるが、比較は残る

**所見：plan の `continue` は値走査だけを進める。後段を飛ばす経路は、読解上ない。**

**根拠：**

- raw expectation の構文検査：`A:674`。
- 正規化後 expectation の再解析：`A:675–677`。
- model／prompt 一致：`A:678–687`。
- record と文書の driver 別 projection 一致：`A:798–801`。
- 文書全体の hash／HEAD bytes 束縛：`A:775–783`。
- live な三 driver の closure 比較：`orchestrator/campaign/p3_b4_closed_critic.py:687–705`。
- launcher からの比較：`orchestrator/campaign/p3_b4_launcher.py:381–387`。

追加受理される文書は、旧 sentinel 拒否地点を越えてこれらへ到達する。第1節の不正 owner 文書も同様だが、期待値が一致しなければ後段で拒否される。**owner の不正自体を後段が救済して拒否する処理はない。**

また、admission validator 自身が closure 入力である。

- `orchestrator/campaign/p3_b4_closed_critic.py:646–647`
- `orchestrator/campaign/p3_b4_raw_record_producer.py:987–995`

**放置した場合：** expectation／projection 保証の解除は起きないが、実装変更により closure hash は変わる。「開始時刻だけなので成果物参照も不変」とは言えない。古い closure 値を据え置いた文書は live 比較で拒否される。

**重大度：保証維持を確認。** 規律2に関する残る問題は第1節の追加受理範囲であり、hash 比較の緩和ではない。

## 5. 親 brief の現物照合

**所見：未記入数は誤り。その他の主張には確認済み範囲と限定がある。**

|項目|現物の結果・根拠|
|---|---|
|残り 5 欄／対象込み 6 行|**誤り。対象外 6 欄、対象込み 7 行。** `D:159,162,163,164,165,166,167`。`P:7` の訂正が正しい|
|現在の実文書は拒否|再 probe で同じエラー。最初の未記入 `D:159` が `A:670` に当たるので、対象行だけが拒否原因という一般化はできない|
|対象行の生値・span|`D:167` と一致。値部分への検索で `未記入`, `(24,27)` を再確認|
|whole-file hash|現物は `09109bf472980fcceaa99b9aeab95f088b6d122d027aa62cd70d7031c4a4f47a`。親の記録先 `output/insights/2026-09-16_t2545-b4-publication-root/README.md:54` と一致|
|whole-file の live pin 不在|調べた production の定数・参照では反証なし。ただし **動的な whole-file 束縛は存在**する（`A:775–783`）。「束縛がない」と言い換えてはいけない|
|`check_docs.py:146`|living 文書の登録であることを確認。SHA 定数ではない|
|§5.1.1 bytes 不変|`P:132–134` の追補を指定位置へメモリ内挿入して比較し、**同一を確認**。raw SHA は `C:47–48` と一致。抽出範囲は `D:407` から `D:692` 直前|
|発行済み record 0 件|`A:99–101` の必須 3 パスは現物不在。`git ls-files` でも該当必須 record なし。他名の JSON は検査台帳であり、発行 record ではない|
|基準 commit|`HEAD` は `B:5` の `d97c423bdd14e0b416cb4f585d350e6c2b251287` と一致|

全出力領域を含む SHA 検索は途中で打ち切ったため、**「値検索の hit は全 repository で厳密に 1 件」までは独立確認していない**。記録の存在と、`orchestrator`・`tools`・`.codex` に同 SHA の literal がないことは確認した。

anchor は概ね正しいが、境界にずれがある。

- `B:93` の検査関数 `602–676` は末尾まで含まない。返却までなら **`A:602–688`**。
- `B:96` の文書束縛は、宣言 commit の検査から含めるなら **`A:746–785`**。
- fixture 本体は **`T:81–112`**。`B:97` の `83–115` は途中開始で次関数まで含む。
- 他の主要 anchor、対象行 `D:167`、開始時刻節 `D:341–358` は一致。

**放置した場合：** 実文書の拒否という結論は変わらないが、残存条件数と検査範囲の説明が誤る。pin 不在を過大に一般化すると、将来の発行済み record を無効化する変更を見落とす。

**重大度：件数・anchor は低、pin の一般化は中。**

## 6. plan が列挙していない §5 セルの受理経路

**所見：admission 検査を通らず、§5 の floor セルを読む production 経路がある。**

参照は次のとおり。

```text
p3_b4_material_report.py:215
  → resolve_preregistered_authoritative_floor
      p3_b4_floor_artifact_issuer.py:1484
  → _floor_cell(document)
      同:1502 → 同:1470–1481
  → 未記入なら None／それ以外は独自 grammar と artifact hash 検査
      同:1503–1516
```

この `_floor_cell` は文書全体から exact な行 prefix を探す。§5 の見出し境界・他の 9 行・責任者・開始時刻を検査しない。今回の関数は呼ばれない。

**放置した場合：** 「§5 の値の利用はすべて A を通る」という参照閉包の主張は誤りになる。ただし、この経路は floor の取得用であり、今回の開始時刻緩和によって挙動は変わらない。材料レポートも `p3_b4_material_report.py:875–884` で evidence-only／非認証を明示している。正式実走の admission bypass と断定する根拠はない。

**重大度：中。参照一覧の補完が必要。経路自体の改修は本 wave の must-fix ではない。**

## scope 外

全セルの意味検証、人物の実在確認、floor reader と admission の統合、新しい gate・台帳の追加は提案対象から外す。今回必要なのは、**追加述語が受理する不正 owner の扱い、負例の証明範囲、変異の失敗 node 帰属を確定すること**である。