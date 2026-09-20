## must-fix

1. **[S-03] 「BACK_OFF=0 のみ」は一次資料と矛盾する。**
   C §3.2 に witness off・`BACK_OFF=1` の **2/120**、D §2.2 に同条件の **1/60** がある。[S-34]・表 C とも矛盾し、上流には backoff 有効時の検出が無かったと読ませる。evidence-map の S-03 も修正が必要。差し替え案：
   > Signals were reported with the witness disabled under both `BACK_OFF=0` and `BACK_OFF=1`. No signals were reported in the witness-enabled samples listed below.

2. **[S-02]・[S-41]・[S-57] 「全件 commit tid 差 1」は誤り。**
   C §3.4 の **B2/069** は、両辺の `v_ver` が **(59,2577)** と **(59,2575)** で、差は **2**。F「副次解析 (a)」、A §5.1、C §3.4、D §2.4 の表を合わせると、同 epoch は全 21 件、tid 差 1 は **20 件**。放置すると、静的候補を支持する形の一致を過大に見せる。evidence-map の S-02・S-41 も訂正する。差し替え案：
   > All 21 pairs have commit versions in the same epoch. The tids differ by 1 in 20 pairs and by 2 in one pair (B2/069 in the second September 18 experiment).

   [S-57] の冒頭も次へ変更する：
   > The “same epoch, tid + 1” pattern seen in 20 of the 21 reported cycles …

3. **[S-02] 「これまでの全走で 21 件」は集計範囲が不正確。**
   F「一次結果」「副次解析 (a)」には、42 走の外に先行 pilot `949964.nqsv` の G2 **1 件**が明記されている。21 は今回選んだ四実験の件数であり、全履歴の総数ではない。放置すると報告の網羅性を誤認させる。旧結果へ加算せず、範囲を限定する：
   > The four experiments summarized here reported 21 signal runs in total; this count excludes the earlier pilot observation mentioned in the August 26 report.

4. **[S-15] 非有意を「率を変えなかった」と断定している。**
   `it did not change the signal rate` は効果なしの主張。A §5.1 が示すのは **3/40 対 2/40、片側 Fisher p=0.5** であり、A §6 の断定的な表現を踏襲しても、今回の禁止事項と [S-08] に反する。上流には計装の影響が排除済みと読ませる。差し替え案：
   > In the direct comparison, the checker reported 3/40 signal runs without the instrumentation patch and 2/40 with it (one-sided Fisher p = 0.500); this sample does not establish that the patch has no effect.

5. **[S-55] 前提四つの英訳が A §3 と一致せず、RLL 条件も脱落している。**
   A §3 第三項は「**相手の read key を自分の write set に含めない**」「**cold・RLL 空**」。本文は前者を自分の read key に関する条件へ変更し、後者の RLL 空を省いている。現物 **1024–1025 行**の拒否には `searchWriteSet(...) == nullptr` が関わるため、集合条件は省略できない。

   ただし、A の「相手の read key」という逐語自体が、直前の W writes x / R reads x、R writes y / W reads y という例と整合しない。原文の誤記かは**不確実**であり、英訳で黙って補正してはならない。放置すると前提を検証済みの反例として読ませる。原文の整合性を解決するまでは詳細例を撤去し、次へ差し替える：
   > The source discussion proposes ordering (ii) as a candidate under additional assumptions, including cold-record access and empty read-lock lists (RLLs). We have not demonstrated this ordering in any reported signal run.

   evidence-map の S-55 も「同義の英訳」とする扱いを撤回する。

6. **[S-05] TRACE 内追加だけという検算を、全 producer へ広げている。**
   指定 diff が証明するのは **e9e477ca の一ファイル**と local master mirror の比較。[S-12] の軽量版は **+26/−6**、C §1.2 の診断版は read/validation に拒否条件を加える別 source である。放置すると、診断 arm を含む全実走が上流と TRACE 追加以外同一だったと読ませる。差し替え案：
   > We have not run upstream `master`. Section S-14 describes the static comparison of `transaction.cc` at the base fork commit `e9e477ca` with our local master mirror; the instrumentation, diagnostic and light-witness variants are described separately below.

7. **[S-27] 軽量 witness の write-lock 保持中の処理を過小記述している。**
   `keeps only a decode and a push … inside the hold` に対し、D §3 項 9 は publish 後・unlock 前の **decode + abort + push** に加え、初回・capacity 増大時の **reserve も write lock 保持中**と明記する。上流には軽量化後の観測者効果が、その二処理だけに限定されたと読ませる。差し替え案：
   > The lighter version moves the post-store log output after unlock. Decoding, a possible abort and a vector push remain between publication and unlock; initial or capacity-growing reservations also occur while write locks are held. Their timing effects were not measured.

8. **[S-46] witness-off の率の範囲が表と一致しない。**
   `roughly 0.02–0.06` は、F「一次結果」の **5/42 ≈ 0.119**、A §5.1 の **3/40 = 0.075** を含まない。evidence-map の S-46 が指定する箇所にも、この全体範囲はない。`such zeros are unremarkable` も、標本数と率への依存を消している。放置すると陰性結果の解釈を過度に弱める。正しく転記された CP 上限だけを残す：
   > The two-sided 95% Clopper–Pearson upper bounds for 0/40, 0/56 and 0/60 are 0.088, 0.064 and 0.060, respectively. These samples do not establish a zero signal rate.

## should

1. **[S-30] 「計装なしの二行」の対象と判定用語を明確にする。**
   表 A には計装なしが三行ある。A §5.1 の再分類は **09-18 の二 arm**を指し、F「全 42 本の分類」は当時の 37 走を certified と記録している。現状では 08-26 の行まで同じ再分類を受けたように読める。差し替え案：
   > For the two September 18 rows without the instrumentation patch, the current checker labels zero-cycle runs `indeterminate`, meaning that the evidence required for its `certified` status is incomplete. These labels concern individual trace checks, not certification of MOCC.

2. **[S-15]・[S-20]・[S-26]・[S-28] 内部用語の初出説明が不足する。**
   `arm`・`block` は明示的な定義より先に使われ、`supported` / `contradicted` の判定対象も曖昧。A §4、C §0.2、A §6 に沿って追加する：
   > An arm is one build/runtime configuration; a block is a group of runs executed on one node.
   > Here, `supported` and `contradicted` mean agreement and disagreement between the producer inferred from the recorded read version and the producer decoded from the payload stamp.

   `witness` は [S-26] で説明されている。`X/P` は英語本文では使っておらず、定義追加は不要。

3. **[S-33] `equally consistent` は支持の強さが等しいと読める。**
   A §1 項 4・§6、D §3 項 1 は、観測者効果と希少事象の未検出を区別できないという限定まで。さらに括弧内の lock 保持中の出力は first witness に限定すべき。差し替え案：
   > These zeros are compatible with an observer effect, but also with sampling variability; the data do not distinguish those explanations. For the first witness, post-store output occurs before unlock.

4. **[S-61] runner の所在が根拠表と食い違う。**
   `runner scripts … are in our project repository` に対し、A §2・§10 と C §1.4・§6.2 は実走 runner 原本を repo 外の job dir に置く。repo 内には逐語写しがあるため、上流が直接実行できる公開 script と誤認しうる。差し替え案：
   > The checker is in our project repository. The experiment runners are preserved in our experiment archives, with textual copies in the repository; they are available with the reproduction materials.

5. **[S-14] に関係する brief／段 4 の日付種別を訂正する。**
   P3 は `2026-06-28 fetch`、evidence-map K5 と本文は commit 日付として記述する。指定 diff に fetch 日付の証拠はなく、fetch 日は**不確実**。放置すると mirror の取得時点を確認済みと読ませる。brief／段 4 から `fetch` 日付を削除する。英文は：
   > The comparison uses our local mirror at `50c7946d`; the mirror's fetch date is not established by the supplied artifacts.

## nit

1. **[S-16] `common to all arms` は [S-17] の例外に依存する。**
   C §1.3、D §1.5 は BACK_OFF=0 を基底とし、bo1 で置換する。全 arm の実効 define が同じと一瞬読ませるため、冒頭を次へ変更する：
   > Baseline configure defines, with the `BACK_OFF=1` substitution described next: …

## 照合結果と scope

- **表 A〜C の件数・分母・CP 区間**は、A §5.1–5.2、C §3.2、D §2.2、E の判定 JSON、F「一次結果」、G「結果」と、表示の丸め精度で一致する。
- **[S-31] の commit 数・比率、[S-32]・[S-34]・[S-37] の p 値と検出力**は指定出所と一致する。[S-41] の thread 確認範囲、[S-42] の最大 key `0x55` と二理由辺を持つ二 cycle も一致する。commit tid の全件隣接という主張は上記 must-fix。
- **[S-52]〜[S-59] の引用行番号**は現物と一致する。ただし [S-54] の counter 検査説明は、現物 1025 行の write-set 条件を補う必要があり、[S-55] の前提問題と合わせて修正すべき。
- **[S-14] の diff**は静的に再集計し、**141 insertions / 0 deletions、非空追加行はすべて TRACE 内**を確認した。後続 master 未確認・master 実走なしは本文に明記されている。master 上の挙動は**未実測**。
- **D2148 項 13 の必須二点**は、hook/verifier 仮定の分岐未分離が **[S-04]・[S-25]・[S-44]**、witness による signal 走の読み値の出所照合未達が **[S-28]・[S-45]** に明記されている。
- **P1〜P4 の採録方針自体は妥当**。診断節 [S-36]〜[S-39] は修正提案と明確に区別され、[S-62]・[S-63] は対応を要求していない。ただし P2 の前提、P3 の適用範囲・日付、P1 の履歴範囲には上記修正が必要。
- 指定資料の静的読解のみを実施した。ファイル変更、pytest、追加測定、送信、PR 作成は行っていない。

## 総括

**must-fix 8 件。** BACK_OFF 条件、全件 tid 差 1、履歴総数、非有意の解釈、静的前提、master 比較の範囲、軽量 witness の処理、率の範囲を訂正する必要がある。

**NO-GO** — 現状は、人間が送信判断へ進める本文案として記録する条件を満たさない。