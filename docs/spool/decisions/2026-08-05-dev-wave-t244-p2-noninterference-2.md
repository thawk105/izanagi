---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t244-p2-noninterference
seq: 2
---

## {{D:t244-p2-literal-tripwire-remand}}. D121 P2 の payload 非干渉検査は実装を差し戻す — 現行 critic payload が既に 5 bit を可逆に運ぶため、payload 不変の字面検査は恒真な保証になる

**背景:** D121 の P2 は「禁止集合・実効 mask・IR SHA・D51 逐次 provenance・driver 戻り値が
untrusted 面に現れない」であり、無条件義務のまま未着手だった。本 wave はそのうち **8c 自律試行が
untrusted role へ渡す入力 payload の面だけ**を閉じる検査を新規 leaf として実装するために起票され、
file:line 粒度の実装プランを起草した。段 3 の敵対 2 レンズが**独立に NO-GO** を返し、
所見 19 件 (BLOCKER 7、MAJOR 8、MINOR 4) を出した。逐語 =
`output/insights/2026-08-05_t244-p2-noninterference/`。

**決定 (1): 本 wave では実装せず、プランと裁定を設計メモとして凍結する。** 決め手は 3 件である。

第一に、**「payload の field も値も変更せずに payload 射影面を閉じられる」という中心前提が
実測で反証された。** critic payload の `harness_result.variant` は、diff 検疫 reject 経路では
`"diffq-" + sha256(genome の正準表現 + "|impl=" + 候補述語)` の先頭 12 hex、build 到達時は
`sha256(genome の正準表現 + "|src=" + source token)` の先頭 12 hex であり、どちらも preimage に
候補述語を含む。候補述語は 5-bit wire の正準関数で、universe は 32 点しかない。親と 2 レンズが
独立に 32 点を静的列挙した結果は一致した — **ID は 32/32 すべて一意、ID 中に自分自身の wire 字面が
現れるものは 0/32**。すなわち payload を不変に保ったまま書ける検査は字面部分一致の tripwire に
限られ、**現行 baseline の実漏洩に対して一度も発火しない**。これは D121 が「観測面の閉集合を先に
定義しないと恒真化する」と警告した状態そのものであり、規律 6 の「恒真な保証」に該当する。
land すれば「payload 面を閉じた」という誤った安心を作る。

第二に、**是正は親の裁量外の裁定 3 件に依存する。** critic の recipient policy は D121 が未解決の
択一としてユーザーへ返した項目である。auditor へ実効 diff と digest を渡してよいかは D121 の
recipient matrix と現行実装が食い違っており declassification の再定義が要る。「IR schema SHA」の
preimage (schema bytes / schema ID 文字列 / emitter source / 32 golden のどれか) も未定義である。
いずれも payload の field か値の変更を伴う。

第三に、**実装すると成果物を壊しうる。** role 呼出し seam の冒頭に fail-closed の raise を置くと、
現行の例外捕捉が provider 呼出し直前から始まるため generic な supervisor error に畳まれ、さらに
build mode では planner/coder 段の早期拒否時に campaign の報告ディレクトリが未生成のまま
Layer-3 finalization が無条件実行され、terminal report を作れない経路が残る。
no-build の fixture テストではこの欠落を検出できない。

**決定 (2): 名乗りの上限を固定する。** 本 wave は実装差分ゼロであるから「P2 を閉じた」
「P2 の部分実装」「非干渉検査を実装した」のいずれも名乗らない。P2 は引き続き FAIL であり、
D114 の承認上限 1 も不変である。将来 実装する場合も、字面一致に留まる限り名乗れるのは
**「8c supervisor の role 呼出し seam における candidate-literal tripwire」**までとし、
module 名に noninterference を使わない。既存の ability-probe 射影 tripwire が自らを
「字面 tripwire であり encoding・言い換え・semantic copy への保証ではない」と正直に名乗っている
前例に揃える。

**決定 (3): 確定後に実装すべき形を記録する。** secret を候補 wire、公開入力を固定した上で、
**provider へ渡る serialized sink bytes が secret を変えても同一であること** (indistinguishability)
を検査する。現行コードに対する予測は planner = PASS、coder = PASS、auditor = 明示 declassification が
必要、**critic = FAIL** である。critic が赤になるため緑では land できず、裁定が先になる。

**決定 (4): 親の provisional 裁定 3 件を反証として記録する。** (a) 「auditor に実効 diff と digest を
渡してよい」は recipient matrix に反し、かつ検査の期待値を被検査 producer と同じ値から取る
自己参照だった。(b) 「許可入力 = 現行 key 集合」は循環する — 秘密を許可 field の値へ符号化した
瞬間その値まで許可入力になる。(c) 「32 点 universe の digest は常に 5 bit 漏洩」は過大であり、
`I(W;ID | 公開 codebook) <= H(W) <= 5 bit` が正しい。diff 検疫経路は写像が単射なので一様な wire では
5 bit 全部を漏らすが、no-build で ID が空の場合や build 経路では条件付きになる。

**決定 (5): 段 2 が提示した変異 12 件を将来 wave がそのまま流用することを禁じる。** 実装差分が
ないため事前登録は行わない。加えて、そのうち 4 件は leaf 側の所有が driver を import しない契約の
下で帰属が成立せず、3 件は「新たな漏洩を作る」のではなく既存の可逆漏洩を字面へ展開するだけである。

**却下した選択肢:**
- 字面 tripwire だけを先に land し「payload 面の部分実装」と記録する — 現行 baseline に対して
  発火しない assert を防壁として記録することであり、D115 が却下した「索引だけ作り consumer を
  付け替えない」、D147 が却下した「未結線のまま leaf だけ land する」と同型である。
- critic payload の該当値を親の裁量で不透明 ID へ置き換える — 未裁定の recipient policy を
  既成事実にする行為で、D121 が却下した案と同型。受理集合にも波及する。
- auditor の例外 2 path を検査に組み込んで「全 untrusted role を閉じた」と名乗る —
  現状は raw mask と実効 mask が同一であるため、digest 単独の秘匿は恒真である。
