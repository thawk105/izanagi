**判定: GO（計算ノードでの検証へ進める）。** 静的検査で probe の合否・kill 判定を壊す must-fix は見つかりませんでした。裁定文の不一致1件と、見積りの根拠に疑い1件があります。

指定資料を読み、前 wave との差分・anchor・論理行番号を確認しました。probe・build・自己試験は実行していません。197/197成功は親の記録として確認したものです。

## 所見表

以下の相対パスは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/` 基準です。

| 重要度 | 判定 | 箇所・所見 | 放置時の成果物への影響 | 最小の修正案 |
|---|---|---|---|---|
| should | real | [s4-ruling.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/s4-ruling.md:37) は C・C1'・C3 の3 checkoutを要求するが、[probe/run_probe.py:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/probe/run_probe.py:242) が抽出・全blob照合するのは C・C3 の2つ。`out/s5-author-B.md:407` の「逸脱なし」も文字どおりには成立しない。 | C0が緑でも「C1'を抽出してtreeと照合済み」とは言えない。後続の比較・kill判定には直接影響しない。 | 裁定を「C・C3を抽出し、C1'は祖先・raw diffで照合」に訂正し、報告にも明記する。利用しない第3 checkoutの追加は不要。 |
| should | 疑い | [s4-ruling.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/s4-ruling.md:68)、`s1-brief.md:15`。前例191秒から今回約0.1 node時間への移し替えに、差分の説明がない。M5は9→21 entryとなり、この段だけで前処理コマンドが36→84本になる。build対象もsilo→moccへ変わる。 | 合否・kill条件は変わらないが、実行時間と再投入余地を過小評価する可能性がある。0.1時間が誤りだとまでは静的に断定できない。 | 「前例に基づく暫定見積り」と明記し、増分を説明する。既存の実測Elapseによる再見積り・確認ラインを維持する。新しいgateは不要。 |

must-fix・nitはありません。

C1'については、祖先と差分の照合自体は存在します。前 waveから検査を削除した問題ではなく、今回の裁定文が実装より広い作業を宣言した問題です。

## 不成立の攻撃

| 攻撃 | 確認結果 |
|---|---|
| C0の祖先・raw diff・archive照合が弱化した | 不成立。`probe/run_probe.py:228` 以降で単一親、各区間の正確なfile集合、通常fileのmodeを確認。抽出したC・C3のfile集合・raw blob照合とexport属性対策も維持。 |
| C1の比較基点がC1'へすり替わった | 不成立。`:587` の比較は `epin`／`ecnd`、実体はC／C3。12 source・21 entry、完全展開・include活性、9件のinclude負例を維持。 |
| C3がsiloや片方のbinaryだけを比較する | 不成立。`:26`、`:420`、`:724` がmoccのTPC-C／YCSB両方を指す。nm・strings・正規化逆アセンブルの条件は不変。 |
| C5のprotocol／source contextが欠落した | 不成立。`:525` は `--protocol mocc --ccbench-root source`。B0ではC3のsourceを渡し、rc・certified・取引数を確認する。v2のX呼出しも残り、`model.py`の証拠面検出に対応する。 |
| 変異の理由集合・診断条件が緩んだ | 不成立。M1mは先頭理由、M3m／M4mは理由集合完全一致。D1／M2のmarker・1000件、M2のrc・E=C・C>commit条件、ERROR扱い・復元照合も維持。 |
| 仮想リスク向けの機構が追加された | 不成立。実差分は対象・OID・変異契約の置換、裁定どおりのM5m拡張、自己試験入口。`v3check.py`は前 waveとbytes一致。削除を推奨する新規機構はない。 |
| 「superproject実装面差分ゼロ」が検証免除に使われた | 不成立。作業木の`git status --short`・`git diff --stat`は空。ただしこれはtracked面の観測に限る。job dirのprobeとCCBenchは実装成果物であり、今回も変異検査・C8を免除していない。 |

## 変異の実効

全6 anchorについて、C3の実ファイル上で出現1回を確認しました。M2だけはD1適用後の内容で確認しています。

| ID | 静的な成立見込み |
|---|---|
| D1 | `tpcc.hh:118` の成功commit後・計数前に診断を挿入する。TRACE=1では旧quit returnが無効なので、診断を起こしたcommitも計数される。1000件到達は実走確認が必要。 |
| M1m | `transaction.cc:1161` のcontext取得だけを0Uへ変更。C/R/Wがv2となり、最初のCで`schema`。派生理由の併発は登録どおり許容される。 |
| M2 | D1上の旧quit returnだけを有効化。発火したcommitのC/Eは既に出ているが計数を飛ばすため、`witness`だけで落ちる見込み。 |
| M3m | `transaction.cc:1192` のv3 W表引数だけを変更。NewOrder署名は表5・7・8で残り、表6欠落・表5との対応崩れが`content-table`になる。構造上の表番号範囲は破らない。 |
| M4m | `transaction.cc:1165` のC種別引数だけを交換。操作署名に基づく表検査は変わらず、`content-txtype`だけになる。 |
| M5m | `transaction.cc:1283` の`#line 1187`を削除すると、直後の`ERR`の論理行番号が**1193→1207**へ変わる。`ERR → NNN → __LINE__`により完全展開へ現れ、次の`#line 1195`で復元される。 |

M5mはmoccの同一transaction sourceを使う4 targetすべてで展開差が出る見込みです。include指令は変えず、残る17 entryのsourceも変えません。したがって「4 entryだけ展開不一致・全21 entryのinclude活性一致・他17 entry一致」は静的に整合しています。実行時に`default`へ到達しなくても、前処理で検出できます。

## 総括

**GO。** 過剰な新規機構、前 waveからの検査弱化、登録変異が等価になる根拠は見つかりませんでした。C0の裁定文・報告を実装に合わせ、計算時間を暫定見積りとして扱う修正を推奨します。C0〜C6の実合格・変異kill・C8完了は、この静的レビューでは認定していません。