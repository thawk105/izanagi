# 段 4 裁定 — [T-244] D121 P3 origin ledger (2026-08-04)

## 裁定: 本 wave では**実装しない**。設計メモとして凍結し、裁定パッケージをユーザーへ返す

`DW-S04` の「実装しない」経路を採り、段 5・6 を飛ばして `4→7→8→9` とする。
実装差分が無いため**変異 matrix と受入全走は対象外**である。

ユーザーの依頼は「D121 P3 を新規 leaf として実装する」であった。親はこれを縮小する権限を持たないため、
**縮小ではなく差し戻しとして返す**。理由は、依頼が置いた前提 (「未確定は予算値だけ」) を覆す事実を
段 3 が実測したことにある。判断を覆す材料が出れば、ユーザーの再裁定で実装 wave を再起票できる。

## 走行中に land した新事実 — 択一 1 の裁定 (worklog (161))

段 3 の実行中に main へ **[T-244] 択一 1 (予算値) の裁定**が land した。
「候補値 2/2/1 を `Q >= 1 + 32R + E_min` の下限式から**導き直す**。R=1 でも Q は 33 以上で
候補値 2 とは 1 桁違う」であり、**これで P10 (予算値・origin authority・軸 (iii)) の 3 点が揃った**。

本裁定への影響を分けて書く。

- **裁定パッケージ U-F は実質的に決着した。** 予算値そのものが下限式から導かれる以上、
  `constraints=()` を許す policy は裁定に反する。floor 制約は必須である (B-5 の裁定を強化する)
- **親 brief の「未確定は予算値だけ」は、いま「予算値も確定した」へ更新される。**
  ただし**残る未確定が消えたわけではない** — 下記 1・2 は P10 ではなく設計本文 §⑤ の未解決欄と
  軸 (iii) 実装定義に属し、P10 の充足では閉じない
- **P3 の負荷は下がるどころか上がった。** origin あたり Q ≥ 33、32R 回の測定が要るため、
  単一 in-flight の強制と no-refund の計数は**より load-bearing** になる。
  漏洩面も origin あたり 2 bit から 33 bit 超へ広がることをユーザーが明示的に受け入れている
- **差し戻しの判断は変わらない。** 択一 1 は値の決め方を決めたのであって、
  origin をどう識別するか (下記 1) と batch をどう表すか (下記 2) は依然未定である

## 差し戻す理由 — 依頼の前提を覆した 2 件

### 1. 予算を origin に束縛する設計が、origin 識別の未裁定によって成立しない (A-1 / B-3)

D121 決定 (5) の主張は「campaign ID に予算を置くと ID を変えるだけで予算が新品になるので、
一段上の `reflux-origin` に束縛する」である。ところがプランの `origin_id` は **caller が渡す
不透明な 64hex** であり、`repository_root` / `ledger_root` も caller 注入である
(`s2-plan.md:134,168-170`)。すると

- 別の `origin_id` を名乗れば予算は新品になる、
- 同じ registry bytes を持つ別 root を 2 つ用意すれば flock は別 inode なので両方が同じ CAS 値から成功する

の 2 経路で、**D121 決定 (5) が塞いだはずの穴がそのまま再現する**。

これを塞ぐ規則 — origin preimage への束縛、**同一の科学的 cell へ複数 origin を発行しない機械規則**、
authority root の同一性 — は、**設計本文 §⑤ が「未解決」として明示的に残した項目**である
(`2026-08-01_t244-reflux-design/README.md:303-305`)。値ではなく構造であり、予算値の後差しでは埋まらない。

### 2. 軸 (iii) の必須化により、FSM の形が未確定になっている (A-2)

2026-08-03 (126) の裁定で軸 (iii) (候補 batch の事前凍結) は**必須**になり、
「batch cardinality・全候補の事前 commit・seal までの結果非公開をセットで定義する」ことが条件に付いた。
プランの FSM は 1 slot = 1 `query-bound` = 1 scalar `query-result` であり、**batch > 1 の member 数も
各結果も表現できない** (`s2-plan.md:302`)。`batch_commitment_sha256` は nullable な seam に留まり、
テスト V16 も「保存できる」ことしか撃たない (`s2-plan.md:444`)。

つまり単一 in-flight は、batch を使わず逐次 query するか、複数候補を 1 つの不透明 digest と名乗るかの
どちらでも**恒真化する**。FSM の形は P4 の定義が決まるまで固定できない。

### 3. 上記に加え、D121 自身が却下した形と同型である

D121 の却下案 (b) は「cap-lift guard を本 wave で実装する — guard が要求すべき前提は未裁定の択一に
依存し、実装すると未裁定設計を既成事実にする」であった。1 と 2 は、origin ledger が**まさにその性質を
持つ**ことを示している。加えて `DW-G04` の発火 artifact / 計測 ID は書けず (B-2)、実効性に要る 8 層の
うち 7 層が scope 外である (A-10 / B-9)。未結線 leaf が D115・D122 決定 (4) と同型だという B-1 の
指摘も、この文脈では独立の補強になる。

## 所見の裁定表 (real 17 / 疑い 1 / mixed 1 / nit 1)

| # | 要旨 | 裁定 | 扱い |
|---|---|---|---|
| A-1 | authority と lock domain を caller が分裂できる | **real・blocker** | 裁定パッケージ U-A / U-C |
| A-2 | 必須 batch freeze と単一 slot FSM が両立しない | **real・blocker** | 裁定パッケージ U-D |
| A-3 | `head-prepared` が state commitment の外で、同一 CAS 値に異なる許可集合 | **real** | 設計メモ (再設計時の must-fix) |
| A-4 | 4 crash 窓が end-to-end 回復を一意に決めない (provider 副作用) | **real** | 設計メモ。producer 層は別裁定 |
| A-5 | repair receipt を WAL 同型にすると replay 副作用が非 idempotent | **real** | 設計メモ |
| A-6 | flock の適用範囲・再入が未契約 | **疑い** | 設計メモ (U-C と併せて解く) |
| A-7 | T-126 の create-only capability / atomic publication を再実装で捨てる | **real** | 裁定パッケージ U-E に併合 |
| A-8 | テスト vector が 4 性質を十分に撃っていない | **real** | 設計メモ (再設計時に V1/V2/V4/V7/V9/V12/V14 を是正) |
| A-9 | 親 brief の 4 主張の監査 | **mixed** | 下記「親の誤り」参照 |
| A-10 | 実効性に要る層の大半が scope 外 | **real** | 裁定パッケージ U-G |
| A-11 | 変異事前登録候補 6 件 | **real** | 実装 wave へ持ち越す (本 wave は実装差分ゼロ) |
| B-1 | 未結線 leaf は「発火しない保証」と同型 | **real・blocker** | 裁定パッケージ U-G |
| B-2 | `DW-G04` を満たさず、D121 (7) から例外も導けない | **real・blocker** | 本裁定の直接根拠 |
| B-3 | `DW-O13` 違反: `origin_id` が実在 field と結び付かない | **real・blocker** | 裁定パッケージ U-A / U-B |
| B-4 | tracked registry は anchor でなく未実装の運用仮定 | **real・blocker** | 裁定パッケージ U-E |
| B-5 | `constraints=()` が既定政策になる | **real** | 裁定パッケージ U-F |
| B-6 | P3 単独では保証にならず、記録が「充足」へ短縮される危険 | **real** | 段 7 の記録規律として採用 |
| B-7 | 親 brief の 4 実測値 | **nit** (4 件とも反証されず) | 記録に残す |
| B-8 | erratum の「T-126 とほぼ同型」も過大 | **real** | 下記「親の誤り」参照 |
| B-9 | 実効性に必要な層の大半が scope 外 | **real** | A-10 と同一。U-G へ併合 |

## 親の誤り (A-9 / B-8 / A-7 による訂正)

1. **brief の「4 vector が既存テスト未被覆」は repo 全体への一般化として誤りだった。** T-126 の
   既存テストが duplicate initial submission、exact-idempotent な outcome crash / finalize、
   surviving artifact からの missing ledger 拒否を撃っている。erratum 1 で訂正の方向は正しかったが、
   訂正後も**未被覆と言えるのは state commitment CAS と全 root 削除 anchor だけ**である。
2. **erratum 1 の「T-126 の 2 相 commit は本 wave の crash replay とほぼ同型」も過大だった。**
   同型なのは `constraint-added` 後・`query-result` 前の窓だけで、verifier red 後の窓に対応する
   event は T-126 に無く、seal・複数 query・次 slot の概念も無い (`series.py:118,257` は
   disk replay を FSM に結線していない)。
3. **erratum 1 の「T-126 も台帳ごと消されたら新品になる」は一般化として誤りだった。**
   `SeriesAttemptLedger.load()` 単体はそうだが、surviving attempt artifact を持つ consumer は
   missing ledger を拒否する実テストを持つ。**「ledger 削除は常に reset」とは言えない。**
4. 反証されなかった親の主張: `FROZEN_MANIFEST` = `output/` 23 path のみ、P10 の狭い意味での裁定状況
   (択一 3・6 は裁定済み、択一 1 は再導出待ち)、consumer 未結線ゆえ現成果物 4 種は不変。
   ただし「全設計で未確定なのは予算値だけ」という一般化は**不可**である (cap-lift 束縛は別 wave、
   P6 は未解決、そして本裁定が示すとおり origin 識別と batch 表現も未確定)。

## 裁定パッケージ (ユーザー判断待ち) — P3 実装の前に要る 7 件

| # | 択一 | 親の推奨 |
|---|---|---|
| U-A | `origin_id` を authority manifest の canonical digest に束縛するか、caller handle のままにするか | **束縛する。** 束縛しない限り D121 決定 (5) は実現しない。manifest schema は設計本文 §3.5 の列挙を固定する (中身は不透明 digest でよく、P1 / P5 の実装面には触れない) |
| U-B | 同一の科学的 cell へ複数 origin を発行しない機械規則をどう書くか (§⑤ の未解決) | **descriptor SHA・axis semantics・verifier policy・environment contract の組を cell key とし、registry が同一 cell の 2 件目を拒否する。** これが無ければ origin 分割で予算は骨抜きになる |
| U-C | authority root を単一に固定するか、caller 注入のままにするか | **固定する。** registry は repo 内の固定 path 1 点、ledger root はそこから導出。注入は test fixture に限る。再入と cross-node flock の契約もここで決める |
| U-D | 軸 (iii) 必須化を受けて、batch を ledger の第一級にするか | **第一級にする。** `batch-committed` 相当で cardinality と全候補 digest を先に固定し、seal まで結果を返さない。決めないと FSM の形が決まらない |
| U-E | anchor の強度 — T-126 の `git cat-file blob` による committed bytes 照合を採るか | **採る。** ただし static な authority record (照合あり) と mutable な runtime head (照合なし) を分離し、後者を「削除検出」と名乗らない。runtime head の commit 主体と頻度も決める |
| U-F | 予算 policy に U4 の floor 制約を必須化するか (`constraints=()` を許すか) | **実質決着済み** — worklog (161) が「予算値は下限式から導き直す」と裁定したため、floor を適用しない policy は裁定に反する。**必須化する** (最低 1 件)。値 (R / E_min) は authority が入れる |
| U-G | P3 の充足を leaf 単体で数えるか、producer 結線と P7 (consumer が origin proof を要求) まで含めるか | **含める。** leaf 単体は prototype 止まりとし、「P3 充足」と記録しない |

U-A〜U-D が決まれば実装 wave を再起票できる。U-E〜U-G は同 wave 内で併せて裁定するのが安い。

## 本 wave が残す成果物

- 設計メモ = `s2-plan.md` (file:line 粒度、30KB)。**未裁定部分を含むため設計確定ではない**
- 敵対レビュー 2 本 = `s3-lensA.md` / `s3-lensB.md`
- 本裁定と裁定パッケージ
- 変異事前登録候補 6 件 (A-11) は実装 wave へ持ち越す
