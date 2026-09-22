| 元所見 | 判定 | 重大度 | fix 後の根拠と、残存・解消した影響 |
|---|---|---|---|
| A1：M2 自身の診断発火未確認 | **closed** | must-fix | `probe/run_probe.py:423,703,713`：自走の marker、worker C≥1000、rc=0、一意 witness、E=C、C>commits、理由集合完全一致を要求。時間切れだけによる旧誤 kill 経路は閉じた。 |
| B1：M4 が二重理由で拒否される | **closed** | must-fix | `probe/v3check.py:103,107,112`：表検査は署名で分岐。正常な操作群の種別交換は `content-txtype` だけになる。 |
| A2：単独変異と単一理由の混同 | **closed** | should | `probe/selftest.py:127,139,170`、`probe/run_probe.py:724,738`：理由集合を照合・記録し、M1 は先頭理由一致と明示。検出理由の過大評価を解消。 |
| A3：C1/C2 分割未照合 | **closed** | should | `probe/run_probe.py:226,233,254`：pin→C1 の header 2件、C1→C2 の silo 1件を raw diff で限定・保存。分割違反は C0 で停止する。 |
| B2：不要な build・全ファイル復元 | **closed** | should | `probe/run_probe.py:571,606,614`：初回は configure のみ。復元は touched のうち bytes が異なるファイルだけ。不要な再 compile を抑制。 |
| B3：OrderLine の過剰な合否条件 | **partial** | should／付随回帰は must-fix | `probe/v3check.py:116,243,251`：密連番・最小値0の条件は除去済み。ただし同時に R>0 の独立条件も削除し、下記 N1 の誤合格を導入した。 |
| B4：spec の未知 key・version 未拒否 | **closed** | should | `probe/run_probe.py:746,755,793`：top-level／entry の key 完全一致と version を出力ディレクトリ作成前に検査。未知指定を無視した実行は閉じた。 |
| 親 P1：build 並列度16固定 | **closed** | should | `probe/run_probe.py:89,183`：`os.cpu_count() or 1` を build に使用。裁定どおり上限16を除去。 |

以下の相対パスは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/review/` 基準です。必読資料はすべて読めました。レビューは静的検査と読み取り専用の anchor 再計数であり、自己試験・build・計算ノード実走は行っていません。

## 新規所見

**N1 — must-fix：F4 の変更で R>0 の検査まで消え、R が全欠落した trace を受理する。**

根拠：[修正後 v3check.py:243](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/review/probe/v3check.py:243)、[修正前 v3check.py:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/probe-snapshot-pre-fix1/v3check.py:245)。

修正前には次の独立条件を含む検査がありました。

```python
if not totals['R'] or not totals['W'] or ol_min is None or ol_min != 0:
    fail('content-table', ...)
```

F4 は OrderLine の密連番・最小値0の不合格条件を外す指定ですが、fix はこの検査全体を削除しています。W と OrderLine INSERT の存在は F1 の表構成検査で担保されますが、**R の存在を代替する検査はありません**。

成立する反例は、`probe/selftest.py:21` の正常4 frame に対して次の変更を施した入力です。

1. 両ファイルの全 R 行を削除する。
2. 各 C の nR を1から0へ変更する。
3. W、E、txid、tx_type、stdout の witness は維持する。

分岐を追うと、nR=0 は `v3check.py:184` で許容され、`:210` の件数照合は0対0で成立します。W の署名・表構成は正常、C=E=commits=4、両 tx_type も正数です。修正後は `reasons=[]`、`passed=True` に到達します。修正前は `content-table` で拒否されます。これは静的に成立する反例で、実行結果を主張するものではありません。

**放置時の影響：C4 が R 全欠落を誤合格にし、同じ欠落を含む D1 も marker・閾値を満たせば PASS になる。M2／M4 でも従来併発した `content-table` が消え、理由集合完全一致による KILLED を許し得る。**

R>0 の独立検査を復元し、「全 R 削除＋全 nR=0」を負例に追加してください。OrderLine の密連番・最小値0の拒否は復元不要です。

## kill 条件の照合

`c6()` は `probe/run_probe.py:609` で `mutation_verdict()` を呼び、次の条件を適用しています。

| ID | 実装との照合 | 攻撃結果 |
|---|---|---|
| D1 | `:703` の marker・worker C≥1000、`:709` の `result['passed']` の論理積 | 条件式自体は裁定どおり。ただし「全検査」の中身が N1 により弱くなった。 |
| M1 | `:712` の `first_reason == 'schema'` | 派生理由を許す仕様どおり。単一理由とは報告しない。攻撃不成立。 |
| M2 | `:703,714`：marker、閾値、理由集合、rc、witness 一意性、E=C、C>commits | 裁定 F2／§3 と一致。marker 不在、逆向き不一致、重複 stdout を kill にする攻撃は不成立。 |
| M3 | `:722` の `reasons == ['content-table']` | 裁定どおり。余分な理由があれば KILLED にならない。 |
| M4 | 同じ分岐の `reasons == ['content-txtype']` | 裁定どおり。余分な理由があれば KILLED にならない。 |
| M5 | `:728`：9件・組の一意性、全 expanded 不一致、全 include activity 一致 | 裁定どおり。1件だけの展開不一致や include 活性の不一致では kill しない。 |

M2 の `witness_unique` は値の非 `None` を確認しますが、上流の `v3check.py:19` が各ラベルの出現数1・非負整数を確認して値を返すため、実際の c6 経路では一意性を保証します。

M5 の consumer 集合は判定関数単独では名前の接頭辞と件数による確認ですが、実経路では `run_probe.py:257` の `entries()` が source 宣言と compile database を完全照合し、`preprocess()` がその集合から TPC-C を抽出します。任意の9件で代用する具体的経路は見つかりませんでした。展開オプションも `-E -P -dD` のままです。

N1 を除き、必要条件を欠いて PASS／KILLED になる経路、正常な結果が判定式の誤りで ERROR／WRONG_REASON になる経路は見つかりませんでした。build・前処理失敗は `:610`、復元失敗は `:621` で ERROR になります。これは必要な失敗扱いであり、誤拒否ではありません。D1 不合格時の停止、全6件完了の要求も `:627,629` に残っています。

## F1 の単一理由化と正常 frame

- **M3：** 表6の INSERT を表5へ写しても、表5・7・8の INSERT が残るので NewOrder 署名です。宣言種別1と一致し、`content-txtype` は付きません。表6欠落と表5／6の Counter 不一致により `v3check.py:109` で `content-table` だけが付きます。構造・witness は置換で変わりません。
- **M4：** 操作群を変えないため署名は保存され、宣言種別との不一致だけが `:104` で検出されます。表検査は署名側で行われるので正常な構成は通り、両種別の件数も交換されるだけです。理由集合は `['content-txtype']` になります。
- **正常 NewOrder：** 表5と6は別々の Counter に入ります。同じ8 byte key が各表に1本ある場合は `a == b` と各 multiplicity=1 が成立します。表をまたぐ同一 key を重複として拒否する攻撃は不成立です。
- **正常 Payment：** 表4 INSERT が1本、表0・1・2 UPDATE、表5〜8への W なしなら `:113` を通ります。署名不定になる経路もありません。
- **署名なし／両署名：** `:103` で署名不定となり `content-txtype`。表検査へ入らないのは F1 の指定どおりです。

自己試験の単一 frame・全 frame 種別交換、表6→5、Payment 署名削除は、`selftest.py:127,138,139,144` で理由集合の完全一致を要求しています。

## 回帰と自己試験記録

N1 以外では、構造・witness 検査の弱体化は見つかりませんでした。フィールド検査、frame 順序、nR/nW 照合、txid、worker ファイル、stdout 一意性、C/E/commits 照合は維持されています。

既存負例の期待変更も、報告された次の範囲と一致します。

| ケース | 差分の確認 |
|---|---|
| `swap-txtype` | 先頭理由は維持し、理由集合完全一致を追加 |
| `table6-to5` | 先頭理由は維持し、理由集合完全一致を追加 |
| `delete-Payment-signature-with-correct-count` | F1 に従い `content-table` → `content-txtype` |
| `line-start-one` | F4 に従い正例へ変更し、観測値を確認 |

それ以外の既存負例の期待値変更はありません。しかし、N1 の「全 R 削除＋件数修正」は既存・追加ケースに含まれておらず、192件成功ではこの回帰を検出できません。

親の [selftest-fix1.log:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/review/selftest-fix1.log:2) は **192/192、failures=0**。コード上も trace ケース149件＋harness/spec ケース43件＝192件で、fix 子の件数報告と一致します。追加46件の内訳も正例10・負例36と整合します。親ログには終了コード自体の記載はありません。

C0〜C5 の手順・記録の削除はありません。`run_probe.py:502,528,555,633` に build、前処理と負例、警告検査、binary 比較、TPC-C／YCSB 実走が残り、保存・逐次 flush・未実行段の不合格記録も維持されています。C4 の**判定内容**には N1 が残ります。

C++ の最終3ファイルでは、今回の焦点である成功後の計数境界、v3 の種別・表出力、E 後の context clear に新たな問題は見つかりませんでした。実 compiler での成立は未実証です。

## 親の派生値の検算

spec を読み、`review/files/` の bytes に対して書込みなしで再計数しました。M2 はメモリ上で D1 適用後に照合しました。

| ID | 再計数 | 非 no-op | 置換内容 |
|---|---:|---|---|
| D1 | 1 | True | 成功1000回目に marker を stderr 出力し quit 設定。旧 quit/count 境界の前 |
| M1 | 1 | True | tx_type setter のみ削除 |
| M2 | 1 | True | D1 適用後、`#if !TRACE` → `#if 1` で計数前 return を復活 |
| M3 | 1 | True | v3 W 出力の表6だけを5へ変更 |
| M4 | 1 | True | v3 C 出力の種別1と2だけを交換 |
| M5 | 1 | True | setter 後の `#line 56` を削除 |

すべて `check-anchors-fix1.log:1` からの6件と一致しました。実投入用 `spec/mutation-spec.json` の `entries` は修正後 template と完全一致し、D1 の marker 取り込み漏れもありません。ここで照合した対象は提供された最終3ファイルであり、後から作成される commit の bytes まで確認したという意味ではありません。

## 総括

- **NO-GO。must-fix は N1：F4 に伴って消えた R>0 の検査を復元し、「全 R 削除＋全 nR=0」の負例を追加すること。**
- 元の A1・B1・A2・A3・B2・B4・親 P1 は静的には closed。B3 は番号条件の修正自体は完了したが、付随回帰のため partial。
- kill 条件の述語、F1 の M3／M4 単一理由化、正常 frame の受理、anchor 6件への攻撃は、N1 を除いて不成立。
- 192件の自己試験記録は整合する。計算ノードでの build・前処理・実 trace・変異 kill 成立は未実証。