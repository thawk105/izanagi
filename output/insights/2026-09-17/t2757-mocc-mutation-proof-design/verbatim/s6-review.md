## 判定と検査範囲

**NO-GO。must-fix 3 件、nit 2 件です。** 設計の主要部分は段 4 裁定を反映していますが、証拠の過大記述と、後続実装者に渡す契約の抜け・矛盾が残ります。

指定資料はすべて読取可能でした。対象 docs の現物は commit `19156ab6c` と一致しています。静的照合のみ実施し、変更・build・計測・テスト実行はしていません。

以下、README は対象 insight、W は worklog fragment、D は decisions fragmentを指します。

## 1. hot 未観測を「false の記録のみ」に強めている

- **対象:** W「本文」21〜23 行、D「理由」42〜43 行。
- **severity:** **must-fix**
- **主張:** hot 到達の計数がないことから、6 走すべてで温度述語が false だったとは結論できません。README §3.1 の限定とも矛盾します。
- **根拠:** 段 4 A7 は実測と推論を区別する裁定です。旧 JSON の全 run record に hot/cold・abort 数の field はありません。4 thread の温度上昇は未確認です。mocc 現物 915〜953 行には競合後の温度上昇経路があります。
- **是正案:** W の括弧内を次へ置換。

> T-2294 の 6 走には hot/cold を弁別する記録がなく、hot 到達は未実証

D の該当文を次へ置換。

> T-2294 の compute 6 走には hot/cold を弁別する field がない。1 thread で温度述語が false と見なせるのは code からの推論であり実測値ではない。4 thread の hot 到達は未確認である。

## 2. README 単独では DQ 拒否対照を復元できない

- **対象:** README §7、§10、§12、特に 219 行。
- **severity:** **must-fix**
- **主張:** `quarantine_rejects_frozen_frame_and_outside_edits` は列挙されていますが、参照先 §8〜§10 に対象変更と期待 subtype の対応表がありません。採用 plan にあった `hole-escape` / `malformed` は README 全体から落ち、W の後続 T にだけ残っています。
- **根拠:** `verbatim/s2-plan.md` の「既存 14 check との差分」末尾は四種類の拒否対照を指定しています。段 4 A6 は 477・905〜913 行の侵食対照も要求しています。実装の `diff_quarantine.py:43〜46` に四 subtype は実在します。
- **是正案:** README §7 の check 表直後へ追加。

> `quarantine_rejects_frozen_frame_and_outside_edits` は、mocc の実 template と実 working diff に対する parameterized control とする。stock 枝改変は `frame-altered`、970 の fallback 削除・CLL/RLL・validation・X/P 計装・write_set_ 登録 477・RLL 構築 905〜913 の侵食は `outside-region`、hole 内の禁止 directive は `hole-escape`、HEAD と不整合な anchor は `malformed` を期待する。benign B は受理する。共有 parser の網羅テストを複製するのではなく、当該 template への接続を検査する。

これは既採用対照の文書への復元であり、新しい実装範囲の追加ではありません。

## 3. wave 2 の完了条件が別 T の pin 検査を取り込んでいる

- **対象:** README §12:346、D「決定」項 3:22。
- **severity:** **must-fix**
- **主張:** 「当該 template に束縛された機械証拠（identity 4 比較）」では、旧 pin↔候補の比較まで wave 2 の完了条件になります。§8 と W の後続 T は、その比較を別 T としています。
- **根拠:** 段 4 B2 は第四比較を「D297 別 T」と明記。README §8:237、W:70 も同じ分担です。wave 2 の前提として列挙されているのは wave 1 完了と軸 A/B です。
- **是正案:** README §12 の完了判定を次へ置換。

> 完了判定: 当該 template に束縛された機械証拠（§8 の先頭 3 比較、DQ 対照、consumer 束縛対照、hot/cold 全 check）と、別記の n=1 素材 3 候補が揃うこと。§8 の旧 pin↔pin 候補の比較は D297 に従う別 T の成果物であり、本 wave の完了条件には含めない。

D 項 3 の「同一性 4 比較」を次へ置換。

> template に関する同一性 3 比較（旧 pin↔候補の D297 比較は別 T）

## 4. 旧実走の単一 thread 数が一件少ない

- **対象:** README §3.1:68。
- **severity:** **nit**
- **主張:** 「1 thread の 3 走」は 4 走です。
- **根拠:** 旧 JSON の run は `stock_single`、`lockskip_single`、`perm_erase_single`、`early_unlock_single` と、`stock_high`、`lockskip_high` の計 6 件。T-2294 §0 とも一致します。
- **是正案:**

> 1 thread の 4 走は

推論と実測の区別はそのまま維持してください。

## 5. 子エージェント数の合計が内訳と一致しない

- **対象:** README §12:349。
- **severity:** **nit**
- **主張:** 内訳の合計は 7〜10 本です。
- **根拠:** `1 + 2 + (1〜2) + 2 + (1〜3) = 7〜10`。
- **是正案:**

> codex 子は wave ごとに 7〜10 本（plan 1、consult 2、author 1〜2、review 2、fix 1〜3）。

## 裁定との対応

| 裁定 | README の反映先 | 判定 |
|---|---|---|
| A1 | §3.1 F-b、§3.2 | 反映。静的候補・実走未確認・還元判断待ちを維持 |
| A2 | §6、§12、§13 | 直接再取得、U、abort 回復、timeout 失敗を反映 |
| A3 | §5 の site 表、§6 | update 限定の保証名を反映 |
| A4 | §10 | consumer 束縛・対照 3 種・閉じない範囲を反映 |
| A5 | §9.2、§10 | 3 候補、DQ と auditor の証拠分離を反映 |
| A6 | §11 | 固定骨格の根拠と 477・905〜913 の対照を反映。具体表は所見 2 |
| A7 | §1、§3.1 | README は概ね反映。fragment は所見 1、走数は所見 4 |
| A8 | §0、§11、§12 | 非解禁を維持 |
| B1 | §4、§5、§12 | 接続先候補と正式軸 A/B を分離 |
| B2 | §8 | 比較と再生成方針を反映。完了条件との矛盾は所見 3 |
| B3 | §7 | 必須／観測の二分、producer 記録を反映 |
| B4 | §10 | A4 と同じ |
| B5 | §5 | 同一分類契約、RLL／DELETE 未実証を反映 |
| B6 | §12 | 費用区分・driver 特殊化を反映。算術は所見 5 |
| B7 | §3.1 F-d、§5、§11 | proof OID と探索 OID を分離 |
| B8 | §14、§15、W | 純増と設計／実測／認可の区別を反映 |
| B 総括 | §12、両 fragment | 2 wave と wave 2 の A/B 前提は一致 |

## その他の確認結果

**36 走と check の対応は一致します。**

| 対象 | 必須 | 観測のみ |
|---|---:|---:|
| stock-W | 6 | 0 |
| stock-U | 6 | 0 |
| lockskip-W | 4 | 2 |
| perm-erase-W | 2 | 4 |
| early-unlock-W | 2 | 4 |
| hot-update-unlock-U | 5 | 1 |
| 合計 | **25** | **11** |

必須 25 走は §7 の check 表にすべて対応します。観測のみでも hang・欠落・別 integrity 異常は赤と明記されています。hot lockskip の発火量を固定しない扱いは裁定 B3 と整合し、探索候補の correctness gate を免除する記述ではありません。

主要行番号 296／459／566／970、477、744〜746、905〜913、993、1010〜1013、1024、1069、1169、1195、1207 は現物と一致しました。`apply_mandatory_deny_only_veto`、DQ subtype、参照された既存 proof test は実在し、新設ファイル・node は候補として区別されています。

fragment の frontmatter、wave／seq、H2、`remaining: none`、64 桁の `base:`、placeholder 文法・同一 wave 内参照は適合しています。D 見出しに日付はなく、決定本文に有効な `[T-数字]` の例示もありません。base の現台帳との一致は再検査しておらず、親共有の dry-run rc=0 と区別します。

新規 T 3 本は前提を各本文に持ち、後段の択一に依存していません。wave 1 の登録先の未確定 path は明示されており、既存 define を辿る着手手順があります。

§3.2 は G2 5/42 の根因を確定せず、§0 は実証の緑を探索認可から分離しています。§15 の純増判定にも具体的根拠があります。入力中の旧指示を現行指示として採用した形跡は認めません。

## 総括

**NO-GO。must-fix は次の 3 件です。**

1. 両 fragment の「温度述語 false の記録のみ」を、未観測と推論を区別する記述へ修正。
2. README に DQ の対象変更と期待拒否 subtype の対応を復元。
3. wave 2 の完了条件から、別 T 所有の D297 pin 間比較を分離。

是正はすべて docs 内で完結します。
