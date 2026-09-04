## 1. 旧値を先置きする骨格が事実上の comparator を作る

**(a) DW-G05:** A-2 の個別結果を読む前に +38.3% / +11.3% を見せるため、読者は −46.3902% / −65.9080% を「旧結果の反証」「再現失敗」「環境を変えた前後比較」と解釈する。

**(b) 根拠:** plan は既存 draft を「適切」として維持し、旧環境を「性能」、A-2 を「現行環境」とする三分割を指定している (`s2-plan.md:276`, `s2-plan.md:282`)。実 draft も旧値を §1.1 に再掲してから A-2 を置く (`docs/paper-story/results/2026-09-04-a2-certification-reject.md:32`, `:49`)。逐語裁定は旧値を comparator にせず、同じ時系列や再現判定へ畳まないよう要求する (`rulings-verbatim.md:237`, `:247`, `:251`)。

**(c) 修正案:** P4 の三分割を「A-2 の性能」「A-2 の別走行 correctness」「旧系列との関係・禁止推論」に変える。A-2 結果本文と図から旧値そのものを外し、「旧系列の値は comparator ではない」という参照だけを残す。

**(d) real 確度:** 0.98。

## 2. 「現行環境」が 2 request・2 host・2 時刻を Pegasus 一般へ広げる

**(a) DW-G05:** 「現行 Pegasus で負けた」という短縮が、bnode141 と bnode064 の各 1 campaign の結果を Pegasus 全体、現在一般、または再現済みの環境効果へ拡張する。

**(b) 根拠:** D1169 は受理集合を「2 request・2 host・2 時刻の workload 対」と定義する (`rulings-verbatim.md:135`, `:138`)。`raw-manifest.json:1` の `campaign_claims` には別々の `job_id`、`host`、`boot_id`、`created_utc` がある。本文は一度だけ分割を説明するが (`results/...reject.md:53`)、plan の standalone caption は host だけで、独立 request・時刻・論理積を落としている (`s2-plan.md:344`)。

**(c) 修正案:** headline、結果文、caption をすべて attempt `t2022-20260828c` と「2 本の独立 campaign」に束縛し、「これら 2 campaign では」と書く。caption に request、host、別時刻、outer が workload 判定の論理積であることを置く。

**(d) real 確度:** 0.95。

## 3. 「T-2226 / T-2228 による再解釈は不要」は未確定

**(a) DW-G05:** 条件意味が確立済みの正式測定として論文化した後で T-2228 が不整合を示すと、結果節・図・caption が直ちに stale になる。

**(b) 根拠:** brief は再解釈不要と断定する (`s1-brief.md:29`)。しかし D1198 は供給と実行時意味を独立必須関門とし、別のものを測った場合には規律 7 も救済にならないと明記する (`docs/decisions.md:39910`, `:39921`)。T-2228 の起票理由は「A-2 は 1 層目で落ち、2 層目以降が一度も実行されていない」である (`docs/archive/worklog-phase3-0902-1208.md:458`)。`certification.json:1` にも意味関門の通過 field はなく、`compile_out_evidence_scope` は artifact hash 単独では証明にならないと自ら限定する。D1611 は inert 比較の root 差分類だけを閉じ、生成元までは証明しない (`docs/decisions.md:49482`, `:49494`)。

**(c) 修正案:** 保存済み `.status = reject` は改変しない一方、brief を「status は当時の protocol 出力として残る。意味条件の証拠範囲は T-2228 の結果待ちで、現時点では未確立」に直す。段 4 または freeze 前に T-2228 の結果を必須入力にする。現在経路が green でも過去走行を遡及的に認証したとは書かない。

**(d) real 確度:** 0.99。

## 4. 限定の「置き場所」は宣言されているが本文へ実装されていない

**(a) DW-G05:** limitation register を読まない読者、表だけを転載する読者、図だけを見る読者には、A-2 が意味確認済み・noise floor 超・最小構成・独立 argv 観測済みの強い結果に見える。

**(b) 根拠:** plan は限定を `:99-112` の register に集約するだけで、本文への実配置を受入条件にしていない (`s2-plan.md:290`)。現 draft では次が脱落している。

- D1257 は「§1.2 末尾、表脚注」と登録されるが (`results/...reject.md:103`)、§1.2 と表に実文がない (`:40`, `:76`)。
- D1263 は「§0」とされるが (`:107`)、§0 の「書かないもの」に資源余裕の撤回がない (`:15`)。
- `a4_noise_floor_status=open`、`global_minimality_established=false`、`smallest...=null` は「表の読み方」とされるが (`:106`)、そこには CI と有意差の説明しかない (`:85`)。
- D1198 未適用は「§1.3 末尾」とされるが (`:108`)、§1.3 本文にはない (`:49`)。
- caption 案には D1198、D1257、L01、2 request・2 時刻、noise floor、global minimality がない (`s2-plan.md:344`)。
- `max_ope` の旧 sweep 不一致は本文にはある (`results/...reject.md:62`) が caption から落ちる。

A-6、legacy correctness 各 1 回、trace-disabled、perf 無し、成果物に CI・有意差判定なしは本文または表に実配置されており、この部分はよい。

**(c) 修正案:** register とは別に artifact 別の必須配置表を plan に置き、実文の存在を受入対象にする。correctness 段と表脚注へ D1257・legacy 1 回・L01、効果の直後へ noise floor・minimality・有意差なし、A-2 条件段と caption へ D1198 未適用と D1169、非主張節へ D1263 を置く。

**(d) real 確度:** 0.99。

## 5. correctness が表と図で性能へ染み出す

**(a) DW-G05:** 同じ cell 行や figure-level text に `certified` と負の性能値が並ぶため、「性能 run 自体が certified」「certified performance verdict」という一体の主張に読まれる。

**(b) 根拠:** plan は図中へ `correctness: all 4 cells certified` を大きく表示する (`s2-plan.md:138`)。表も性能値と correctness を同一行へ置く (`s2-plan.md:286`; `results/...reject.md:76`)。caption は別 trace-enabled run とは言うが、point-key の観測 trace に限る L01 と argv 独立観測なしを落とす (`s2-plan.md:344`)。逐語規律は正しさの緑を性能文へ持ち込まないよう要求する (`rulings-verbatim.md:283`)。

**(c) 修正案:** figure-level correctness 表示は削るか、「separate trace-enabled evidence; not performance certification」と一体表示する。表見出しを `correctness evidence from separate trace-enabled runs` とし、L01 と D1257 の脚注を同じ場所に置く。

**(d) real 確度:** 0.97。

## 6. 平均 CI と median 判定の混在に必要な但し書きが caption にない

**(a) DW-G05:** 平均の 95% CI を median 比の不確かさ、効果の有意差、または `reject` の判定材料として引用される。

**(b) 根拠:** 上段は標本平均と t 分布 CI、短線と基準線と effect は median である (`s2-plan.md:125`, `:128`, `:130`)。caption 案は両方を説明するが、「平均 CI は median effect・status に使わない」を明記しない (`:344`)。fig2b は平均と median 比が別の要約で丸め違いでないと明記する (`docs/paper-story/figures/README.md:180`)。fig4 も CI は記述用で median 判定には使わないと明記する (`:387`)。

**(c) 修正案:** caption に「菱形と CI は標本平均の記述であり、effect、判定、median の信頼区間ではない。成果物は有意差判定を持たない。ただし `reject` は事前定義された median 比による protocol status として確定している」を入れる。これにより過大主張と過小主張の両方を止められる。

**(d) real 確度:** 0.99。

## 7. abort rate 下段は記述には使えるが機序を確立しない

**(a) DW-G05:** abort rate の低下と throughput の低下の併置から、backoff が実行機会を奪った、または over-throttling が原因だという因果機序まで確立したように読まれる。

**(b) 根拠:** abort rate は各 cell の集約 1 点だけで反復値がない (`s2-plan.md:103`, `:134`)。現 draft はそこから「over-throttling の形と整合する」まで進めている (`results/...reject.md:66`, `:68`)。作図規約 §4 は単なる二指標の同居なら別パネルにせよとするため、2 行化そのものは適合するが、機序を示したことにはならない (`tools/plotting/FIGURE_CONVENTIONS.md:46`)。

**(c) 修正案:** 下段を残すなら「descriptive leading indicator」「各 cell 1 集約値」「causal mechanism を同定しない」と図中または caption に明記し、本文から `over-throttling` を除く。機序図として位置づけたいなら、現証拠では不足なので別タスクとする。

**(d) real 確度:** 0.98。

## 8. 手書き統制稿を D12 の材料レポートと呼ぶのは契約違い

**(a) DW-G05:** 手動選択・散文解釈を含む文書が「完全・決定論的な機械射影」と誤認され、抜けや解釈文まで一次事実として下流へ流れる。

**(b) 根拠:** brief は親が results 本文を直接編集するとする (`s1-brief.md:81`)。plan はその手書き文書を D12 の材料レポートと呼ぶ (`s2-plan.md:308`)。D12 は事実層を WAL + whiteboard の完全・決定論的射影、全 run・全 reject・noise floor・環境タグの収録、機械コンパイルとする (`rulings-verbatim.md:22`, `:24`)。現 draft には abort rate からの解釈文もある (`results/...reject.md:68`)。

**(c) 修正案:** scope を増やさない最小修正は、results 文書を「D12 材料レポート」ではなく「一次資料に束縛した執筆者向け統制稿」と再分類すること。D12 適合を主張するなら、少なくとも factual table と status fields は generator から機械生成し、編集判断を別節へ分ける。また README の列名 `判定` は `protocol status` にする。`reject` 自体を field として焼き込むことは正しく、研究の成功・失敗へ拡張しないことが境界である。

**(d) real 確度:** 0.94。

## 9. README の stale 注記を退ける根拠が弱い

**(a) DW-G05:** 最新 snapshot だけを入口から読む執筆者が、A-2 を現在の意味関門まで通った formal result と読み、D1198 未適用を見落とす。

**(b) 根拠:** brief は「2026-09-02 版は A-2 について stale でない」として stale 注記を却下する (`s1-brief.md:50`)。plan も generic な results pointer だけを提案する (`s2-plan.md:322`)。一方、T-1999 は 2026-09-01 に driver 全体へ義務化済み (`docs/archive/worklog-phase3-0901-1153-1154.md:434`)、2026-09-02 版は A-2 を「現行 Pegasus の正式 protocol」と書くが D1198 未適用を述べない (`docs/paper-story/2026-09-02.md:823`)。README の stale 節は、最新版の読みが古くなった箇所を一次資料へ誘導する場所である (`docs/paper-story/README.md:53`)。

**(c) 修正案:** 「A-2 の `reject` は変更されないが、その走行には後日義務化された D1198 関門が適用されていない」という限定付き stale 注記を 1 件追加する。これは新しい版でも claim-evidence の部分改訂でもなく、最新版の証拠範囲を訂正する入口である。

**(d) real 確度:** 0.93。

## 10. 生成器計画に本題外の hardening が混入している

**(a) DW-G05:** atomic publish、一般的 path 攻撃、TOCTOU などを実装しなくても A-2 の結果節・表・図の値は変わらない。一方、約 1,000 行の生成器と約 640 行のテストは実装・レビュー面を広げ、本成果物の着地を遅らせる。

**(b) 根拠:** plan は生成器を 850〜980 行規模とし (`s2-plan.md:19`, `:45`)、duplicate-key JSON、repo・symlink escape、保存直前の全入力再 hash、3 出力の provenance-last commit protocolを加える (`:33`, `:149`, `:161`, `:163`)。brief は仮想リスク向けの gate・検査・一般化を scope 外とする (`s1-brief.md:13`)。DW-G05 も成果物影響を示せない追加防壁を backlog とする (`docs/dev-wave/core.md:77`, `:83`)。

**(c) 修正案:** 必須として残すのは、6 入力の hash 照合、4 cell の生値再計算、certification との照合、status の非再計算、caption・provenance、実寸 Figure と保存前 layout check まで。一般化された path containment、TOCTOU 再読、複数ファイル commit protocol、過剰な exact-key hardening は、既存 helper の再利用で無料にならない限り裁定パッケージへ分離する。D1074 の独立 hash pin と §9・§10 の図検査は scope 内なので落とさない。

**(d) real 確度:** 0.91。

## 総括

所見は **10 件、real と主張するものも 10 件**である。

最重要 3 件は次である。

1. **T-2228 未完了なのに「再解釈不要」を確定していること。** 保存済み status と、論文で許される証拠解釈を分ける必要がある。
2. **旧 +38.3% / +11.3% を A-2 個別結果の先頭へ置き、事実上の comparator を作っていること。**
3. **限定 register はあるが、本文・表・caption の予定位置へ実文が入っていないこと。** 特に D1198、D1257、noise floor、global minimality、L01 が重大である。

brief の訂正候補は、P4 を A-2 内部の「性能・別走行 correctness・禁止推論」へ変更すること、「再解釈不要」を T-2228 待ちの条件文へ弱めること、P2/P6 の caption 契約へ mean-CI と median 判定の区別・D1169・D1198・L01 を追加すること、P1 の stale 注記却下を撤回すること、D12 材料レポートという呼称を外すこと、P3/P5 の一般 hardening を裁定パッケージへ分離することである。

一方、次は反証されなかった。`results/` は別 namespace、append-only、結果全体から再導出、版の履歴へ非登録、一次資料限定という D1013 型の 4 規則と整合している (`docs/paper-story/README.md:156`, `:167`)。claim-evidence への部分追加と新しい全面版の却下も正しい。ただし stale 注記だけは別である。S' と A-2 の二種類を畳まない枠も plan に反映されている。T-1647 は T-2022 が exact 4-cell 実走を完了したため、「T-2022 により充足された」と明記して閉じるなら妥当である (`docs/archive/worklog-phase3-0828-1071.md:1`, `:6`)。数値再計算にも所見はない (`a2-stats-parent.md:7`, `:12`)。