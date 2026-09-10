## 段 3 レンズ B 所見

指定資料のみを読み、テスト・追加 probe は実行していない。

1. **BLOCKER / real — (A)〜(D) は択一ではない**

   R-5 自身が、(D) は (A)〜(C) のいずれとも組み合わせて独立に必要としている。さらに、(A)=証拠取得、(B)=運用上の認可、(C)=revision authority、(D)=proof chain であり、判断軸が異なる。[package.md:209-220](/work/1/SFC/tanab/izanagi/output/insights/2026-08-11_t8b-restart-integration/package.md:209)

   実測後は少なくとも次を分けるべきである。

   - (A′) `qcat` spool 証拠 + process lineage 束縛
   - (E) official を空集合のまま維持
   - (B′) 証拠は取得するが認可には使わない
   - (D) proof chain への永続化

2. **SHOULD / refuted — 「A の実現可能性は未調査」は消えた**

   `qcat` の計算ノード可用性、byte 比較、末尾改行の挙動は実測で確認済みである。[brief.md:25-36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/brief.md:25)

   ただし、これは「scheduler bytes を取得できる」という狭い feasibility が解けたという意味であり、D86 §4 の admission 全体を満たしたことではない。P1 は狭い意味では real、全体解禁まで一般化するなら refuted である。

3. **BLOCKER / real — P3 は裁定を先取りする表現になっている**

   「User Attribute は新しい Git launch receipt ではない」は字義上は支持できる。しかし、そこから「D86(3) に直接は当たらない」と先に読ませると、「新しい authority として使える」という判断を事実上先取りする。

   D86(8) は submission artifact を認可の証明として扱うことを禁止し、D87(5) も submission record は authorization ではないと明記する。[decisions.md:3797-3805](/work/1/SFC/tanab/izanagi/docs/decisions.md:3797) [decisions.md:3845-3848](/work/1/SFC/tanab/izanagi/docs/decisions.md:3845)

   問うべきなのは「Git receipt か」ではなく、「scheduler record を revision authority として採用してよいか」である。

4. **MUST / real — 「事後変更不能」「人間が置く」は未証明**

   `qalter -U` が無いことは、所有者がその一つの CLI option で変更できないことしか示さない。管理 API、別の属性変更経路、request 再生成まで含む不変性は証明していない。

   また probe 2 は User Attribute を表示しただけで、誰が qsub したかを証明していない。[probe2.log:57-59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out2/probe2.log:57) 「qsub 時に人間が置いた」は、実測事実ではなく裁定前提として分離すべきである。

5. **BLOCKER / real — 受理集合の記述が甘い**

   `r`=revision、`j`=scheduler request、`p`=core を呼ぶ process とすると、現状と候補は次の通りである。

   | 状態 | 機械的に束縛されるもの |
   |---|---|
   | 現状 | `∅`。D86/D87 の guard が生きている |
   | A のみ | `qcat(j) == blob(r)+改行` となる request。`p` が `j` の子孫であることは束縛されない |
   | A + User Attribute | request 内の属性・receipt・HEAD・spool が同じ `r` に整合するもの。ただし `r` 自体は submitter が選べる |
   | trusted authority + lineage | ユーザーが指した `r` と、認証済みの `p` まで束縛する将来形 |

   probe は同一 job から別の同一所有者 request の `qcat` を読めることを示している。[probe.log:48-56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:48)

   したがって「人間が qsub した job の中の任意の process」だけでなく、少なくとも同一 UID・同一権限で request ID を選択できる process が攻撃面に入る。User Attribute を加えても、属性と revision を同じ submitter が自己選択できる限り、revision 射影は「ユーザーが指した revision」ではなく、自己整合する clean revision 全体に残る。

6. **MUST / real — P2 の「実測」と「脅威モデル」を分ける必要がある**

   probe は別 request の `qcat` 可読性を測ったが、同一 job 内で sibling process を起動し、同じ qstat attribute まで取得する実験ではない。したがって「兄弟 process survivor」は静的に real だが、「全証拠を実測済み」とは記録できない。

7. **SHOULD / real — qstat の結果要約を訂正すべき**

   probe 1 の raw ID では `qstat -f` が失敗した一方、probe 2 の normalized ID では `qstat -f` が `rc=0` で User Attribute も返している。[probe2.log:46-59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out2/probe2.log:46)

   よって「qstat が使えない」のではなく、「ID 正規化が必要で、script/hash/環境変数は返さないが User Attribute は返す」と書くべきである。

8. **MUST / real — 費用見積りが実際の未解決点を含んでいない**

   350〜550 production 行、A-3/A-4 込みで 900〜1400 行という見積りは、qcat・属性・既知の seam 対策の規模である。[stage2-plan.md:160-173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/stage2-plan.md:160)

   しかし、process lineage の真正な束縛、User Attribute の認可性、D86(8) と両立する authority、A-5 の proof chain は別問題であり、lineage の費用は見積りにない。runbook §0 が 8b の証拠価値を限定している以上、裁定には少なくとも次の数字が必要である。

   - この証拠を何回・何候補で再利用するか
   - survivor による誤 admission をどの確率・損失まで許すか
   - T-139/A 系列に対する queue・計算時間の機会費用
   - proof chain 拡張をしない場合の証拠価値
   - lineage と authority を閉じる追加工数

9. **MUST / real — W-2 への返却粒度が大きい**

   A の feasibility は事実として閉じ、ユーザーに返すべき判断は「official を空集合のままにするか」「authority を新設するか」「proof chain を開くか」に分割すべきである。A〜D を一括で選ばせるのは、T-139 の裁定帯域を不要に消費する。[phase3-8b-restart-runbook.md:19-23](/work/1/SFC/tanab/izanagi/docs/phase3-8b-restart-runbook.md:19)

10. **BLOCKER / real — 並走ガード (i) は証明されていない**

    probe log には `901498.nqsv` と `901499.nqsv` が同時に RUN と記録されているが、`901498` の execution host は示されていない。[probe.log:48-52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:48)

    「性能値を採らないから同居しても歪まない」は、「ノード同居なし」というガードの代替にならない。P8 も自分の UID の process しか見ていない。したがって (i) は未充足、少なくとも未立証である。

11. **BLOCKER / real — qsub の規律適用を親が狭く解釈している**

    D87(1) は「AI は qsub しない」としている。[decisions.md:3825-3827](/work/1/SFC/tanab/izanagi/docs/decisions.md:3825) runbook §8 の背景 job 例外を使うなら、永続 marker、qstat 可視性、終了後の会計痕跡の三点が必要である。[pegasus-runbook.md:958-971](/work/1/SFC/tanab/izanagi/docs/pegasus-runbook.md:958)

    「diagnostic probe だから例外」は brief の自己解釈に過ぎない。親が AI セッションから 2 本を投入したなら real な手続き違反であり、F49(ii) の sanctioned な実行環境だったことを証明できた場合だけ refuted になる。

12. **MUST / real — probe 2 は read-only ではない**

    probe 2 は spool directory に `touch` し、その後 `rm` している。[probe2.log:23-26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out2/probe2.log:23)

    自分で作ったファイルを消していても、計算ノード上の scheduler 管理領域への外部書込みである。「非破壊」と「read-only」は同義ではない。絶対規律 6 上も、scheduler 側の領域を変更した事実を明記すべきである。

## 裁定パッケージに載せる問い

### Q1 — qcat 経路の扱い

- **(a) E: official は空集合のまま** — qcat の feasibility だけを証拠として記録し、実装しない。
- **(b) A′: bounded 設計を続ける** — qcat に加え lineage・authority を設計するが、official は空集合のまま。
- **(c) A+User Attribute で解禁** — self-consistent な request/process まで受理集合を広げることを明示的に受諾する。

### Q2 — User Attribute の意味

- **(a) 観測 assertion に限定** — revision 整合の診断値とし、認可には使わない。
- **(b) scheduler-level revision authority として採用** — submitter が選んだ clean revision を束縛するが、ユーザーの明示指示は証明しない。
- **(c) 署名付き allowlist 等を新設** — ユーザーが指した revision を機械的に束縛する代わりに、新 authority の設計・裁定が必要。

### Q3 — proof chain

- **(a) 先送り** — certificate v1・journal・ratified verifier は不変、official は空集合。
- **(b) 拡張する** — spool/request/source の証拠を certificate v2・journal・verifier に残し、D86(5) を再裁定する。
- **(c) 非公式診断台帳だけ** — 証拠は研究記録に残すが、certified result の受理根拠にはしない。

### Q4 — W-2 との優先度

- **(a) T-139/A の後まで保留** — 本 wave は結果付き再提示で終了し、追加 qsub・実装をしない。
- **(b) A 後に read-only 設計 wave を 1 本だけ行う** — 不足数字と lineage の選択肢だけを埋める。
- **(c) 直ちに実装** — 350〜550 行以上を投入するが、authority・lineage・proof chain 未解決のため official 解禁は別途必要。

## 総括

NO-GO: qcat feasibility の記録は GO だが、official 非空化・実装着手は不可。  
最大の攻撃点は、scheduler artifact の型分類を revision authority の可否へ滑らせた P3。  
A/A+User Attribute の実受理集合は「ユーザー指定 revision」ではなく、自己整合する request と未束縛 process まで広がる。  
並走ガード、AI qsub 例外、probe 2 の read-only 主張も未閉鎖である。