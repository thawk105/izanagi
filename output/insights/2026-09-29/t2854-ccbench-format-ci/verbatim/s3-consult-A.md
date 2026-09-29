## 所見 — 正しさ境界

- **must-fix｜整形だけであることの照合が不足。** 根拠: `s1-brief.md:14`。空白をすべて除いた bytes の一致は、文字列・raw string・コメント・マクロ本体・行継続での空白変更を見逃す。予測差分では 3 ファイルとも一致したが、`cc/silo/transaction.cc` では `//` コメントの物理行が動き、同ファイルと `cc/mocc/transaction.cc` には `#line` がある。放置すると、F を意味不変と記録しても TRACE=1 側の変化を見逃しうる。**修正:** F の実 commit と C2' の raw diff を全件読み、literal の内容、コメント境界、directive と行継続、`#line`、include の順序を照合する。予測差分では include の並べ替えや directive 値の変更は見えず、`.clang-format:56` も `SortIncludes: false` である。この確認は F の実差分に対して行う。

- **must-fix｜D297 の結果を F に結び付ける。** 根拠: `old-run_judge.sh:13-18,52-68,79-84`、`s1-brief.md:16`。旧 script は new OID と bundle head を C2' に固定している。固定値と表示文言を F に替えるだけでなく、F の親が C2'、bundle の head が F、bundle 内で C と F を解決できることを確かめ、**C→F** を GCC 11.4 と 12.3 で新規起動する必要がある。放置すると C→C2' の合格を F の判定として記録しうる。**修正:** 両方の新 report で `old_oid`、`new_oid`、`result`、実行した compiler を確認し、F の OID とともに記録する。検査器自体は変更しない。

- **should｜負例は F 上でも成立するが、実施は必須ではない。** 根拠: `old-run_judge.sh:106-138`、前回 `README.md §3`、`s1-brief.md:16`。`include/tpcc.hh` の `#line 56` は F の整形対象外なので、F に削除 commit を重ねて **C→負例 tip** を判定すれば、期待理由は TPC-C consumer の `header expanded 不一致` のままである。放置時の問題は、再実施する場合に旧 script の `errexit` 欠陥で末尾の理由確認が走らず、負例の記録が未確認になること。**修正:** 実施するなら欠陥を直し、rc と拒否理由を確認する。ただし D2277 項1 (2) が要求するのは F の正例再判定であり、検査器が不変なら前回の負例を再利用して再実施を削れる。

- **should｜予備 probe の結論を限定する。** 根拠: `pp_probe.py:8-20,23-29`、`pp_probe.log:1-12`。この probe は全 `#include` 行を除去し、`-nostdinc` で 2 文脈だけを比較する。TRACE=0 の一致も TRACE=1 の不一致も、実 include と全 production 文脈について「差は全部 `#if TRACE` 内」と証明しない。放置すると F の意味不変や D297 合格の根拠を過大に記録する。**修正:** probe は予測と明記し、F の実差分の確認と C→F の D297 本判定を根拠にする。規律1・2や D297 規則 v2 を緩める理由にはならない。

## 所見 — 実効性と過剰・削除

- **must-fix｜build の「CI と同じ」の範囲を明示する。** 根拠: `build.yml:33-40,55-83`、`ThirdParty.cmake:35-46,106-111,130-136`、`s1-brief.md:15`。`:ci` image 内で同じ configure/build argv を使っても、offline の `FETCHCONTENT_SOURCE_DIR_*` は CI の取得経路を迂回する。cache の HEAD 一致だけでは作業木 bytes の一致を示さず、CI には ccache restore と設定がある。image tag も取得時点で変わりうる。放置すると「GitHub CI と完全同一条件で緑」という記録になる。**修正:** 依存供給元の実 bytes/OID、image digest、compiler version、ccache 状態と追加 CMake 引数を実走記録に残し、「CI image と CI の build 手順による手元通過」と述べる。GitHub Actions 自体の緑は人間の push 後に別途確認する条件である。

- **should｜全並列 build の資源差を見積りに反映する。** 根拠: `build.yml:79-83`、`s1-brief.md:15,18`。`$(nproc)` は計算ノードでは 48 になり得る。CI runner と同じ式でも並列数とメモリ負荷は同じとは限らず、失敗が F のコード由来か資源由来か分かりにくくなる。放置すると CI の主張と 10〜20 分の見積りが過大に確実なものになる。**修正:** まず指定どおり実行して資源と結果を記録し、資源要因で再試行するなら並列数を制限した別条件として報告する。

- **should｜image 実行可否を先に安く確かめる。** 根拠: `s1-brief.md:9,13,15`、`format.yml:25-35`。apptainer が login にあることと、計算ノードで両 image を起動できることは別の事実である。放置すると build job の投入後に起動不能で (a)(b) に届かない。**修正:** 取得後、計算ノードで短い `apptainer exec` により `clang-format --version`、`cmake --version`、compiler と ccache の存在、bind した F の checkout の可読性だけを確認する。動かなければ host build は診断結果として実施できるが、CI image 同等の (b) は達成扱いにせず、実行環境の修復か push 後の GitHub CI を待つ。

- **should｜費用見積りは条件付きにする。** 根拠: `s1-brief.md:18`、前回 `README.md §3, §5.3`。1,944 秒の判定実測と未実測 build 10〜20 分の合計は約 **0.71〜0.87 node 時間**で、記載の 0.6〜0.9 は概ね妥当。ただし build 再試行や C2' の追加 build は含まれない。放置すると追加投入で 2 node 時間の確認線を越えうる。**修正:** 初回と追加 job の実費を累計し、線に達する見込みが生じた時点で追加投入前に裁定条件を適用する。

- **nit｜scan の「84 件」は CI 通過判定ではない。** 根拠: `fmt_scan.py:25-35`、`fmt_scan.log:1-10`。scan は stderr の `warning:` を数え、各呼出しの rc と `--Werror` を確認していない。放置すると「違反が 3 file」という探索結果を F の format job 通過と取り違える。**修正:** F で `format.yml:50-55` の対象列挙と `--dry-run --Werror` を実行し、その終了コードを (a) の根拠にする。

## (P1)〜(P7) への意見

| 案 | 判定 |
|---|---|
| P1 | 3 file への限定は scan と一致する。F の実 diff が本当にその 3 file だけか確認し、`:latest` image で format 手順を通す。|
| P2 | 空白除去一致・D297・build の組合せだけでは TRACE=1 の意味不変を保証しない。実差分の字句・directive 確認を加える。|
| P3 | `:ci` image は build 同等性の主張に必要。offline 供給と ccache 等の差を明記する。F が赤のときの C2' build は原因調査の選択肢であり、標準の完了条件から外せる。|
| P4 | F 用の OID、bundle、report の結び付けは必須。負例の再実施は削れる。再実施するなら既知の `errexit` 欠陥を直す。|
| P5 | 別名 branch と bundle は既存 branch を動かさず人間へ push を渡す手段として妥当。|
| P6 | 初回見積りは妥当な範囲だが build 時間は未実測。追加 job を累計する。|
| P7 | izanagi の実装差分 0 という整理は妥当。repo の受入全走は本依頼の CI 2 本・D297 判定の代用にはならない。|

## 総括

F の実差分で意味不変を確認し、F の checkout に対する format・build 手順の終了コードと、新規の **C→F** D297 report 2 本を得れば、brief の (a)〜(c) に届く。成果物には CI との環境差を明記して人間へ別名 branch の push を依頼すれば (d) に届く。前回の負例再実施と C2' build は通常経路から削れるが、GCC 2 版と build/format 用の各 image は現在の完了条件と CI 同等性の主張を支える。