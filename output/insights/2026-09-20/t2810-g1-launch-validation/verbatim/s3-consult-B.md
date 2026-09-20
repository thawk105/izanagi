## 所見 (B-1, B-2, … の番号付き。各 = 根拠 / 何が問題か / 放置時の帰結 1 行 / 分類 must-fix|should|nit / 推奨対処)

以下、`s1-brief.md`、`s2-plan.md`、`evidence/` は指定された job directory 配下を指す。静的検査のみ実施し、ファイル変更・pytest・追加の実測は行っていない。

**B-1 — α 全体は恒真ではないが、上限は独立保証ではない。分類: must-fix**

- 根拠: `orchestrator/campaign/s8b_ratified_freeze.py:493` の導入定義、`:1081` の G tree 実在検査、`s2-plan.md:148` の保証記述。
- 問題: G に対象 bytes が存在し、H 内の導入が一意なら、その導入 i は G の祖先か G 自身である。したがって `i ≤ G` は既存条件から従う。一方、D2077 は cert と result の別々の導入順まで強制しておらず、`C ≤ i` は一般には含意されない。
- 放置時の帰結: 受理集合は変わらなくても、上限検査を独立した防壁と数え、成果物の保証を過大評価する。
- 推奨対処: docstring と裁定材料で「上限は既存条件から従う重複検査、下限・一意性・非 merge が追加の制約」と明記する。

**B-2 — 「現物形だけ」の受理拡張という説明は狭すぎる。分類: must-fix**

- 根拠: `s1-brief.md:19` と `s2-plan.md:264`。後者は中間 commit 導入も受理すると明記している。
- 問題: P1 は現物 `i=C=G^` の救済だけでなく、任意の一意な非 merge 導入 `C ≤ i ≤ G` を許す一般化である。`i=G` の維持も fixture 互換という理由だけでは設計上の必然にならない。
- 放置時の帰結: 現物救済として承認した範囲を超え、中間導入や G 同時導入を含む履歴が受理される。
- 推奨対処: α を採るなら区間全体の受理を明示して決める。第 4 案との受理集合の差も示す。

**B-3 — 本 wave の効能と、旧 checkout への一般化を修正すべき。分類: must-fix**

- 根拠: `s1-brief.md:17` の「同じ結論しか出ない」、`:23` の「旧 pin checkout でも新 main でも段階 4 (journal)」、D2184 の「新 main の code でそれらを live 消費することには成立しない」。
- 問題: 新 main の live 拒否は journal ではなく policy。固定した旧 checkout には本修正が入らない。また、修正を移植した旧 checkout の全経路が同じ結論になることは未実測である。
- 放置時の帰結: 修正済み main と未修正の歴史再開 checkout を同一視し、実際には開いていない W-4 / W-5 の入口を開いたと読ませる。
- 推奨対処: 完了を「validator の互換性修復と historical reverify の段階 8 到達」に限定する。旧 checkout の移植実測は「scope 外で未検証のため省略」とする。

**B-4 — N3 は scope 外でよいが、削除案の帰結まで裁定材料に必要。分類: should**

- 根拠: `s8b_holdout_freeze.py:2005` は候補を measurement closure から除き、`:2177` は `O_EXCL`、`s8b_ratified_freeze.py:3048` の active-chain exemption は候補を含まない。
- 問題: 候補削除は scan 除外拡大ではないが、単なる無影響の掃除でもない。現 checkout の hit 集合と候補出力先の存在状態を変える。
- 放置時の帰結: N3 は残り続ける。説明不足のまま削除すると、候補の現物参照が失われ、再生成の create-only 存在拒否もなくなる。
- 推奨対処: 本 wave では削除せず、履歴での保存方法、pin、consumer、再生成時の扱いを含めて別件化する。

**B-5 — fixture 成功を loader 込みの chain 成功と同一視しない。分類: should**

- 根拠: `test_s8b_ratified_verify.py:643` は元 freeze から文書を作り、`:676` は `RatifiedFreeze` を直接構築する。plan の新 option は `s2-plan.md:158`。
- 問題: 独立 fixture の public `launch_validate` 成功だけでは、V1a を含む `load_ratified_freeze` 成功を証明しない。
- 放置時の帰結: `i=C` を通す検査は得られても、D2077 / V1a に適合した候補生成・批准全体まで検証したとの誤読が残る。
- 推奨対処: fixture の証拠範囲を launch core に限定して記す。実 repo の loader 成功と修正後 reverify は別の証拠として保持する。

**B-6 — runbook の「現在形更新」は正本の重複を増やす。分類: should**

- 根拠: `docs/phase3-8b-restart-runbook.md:151` は「本書は判定規則だけを持つ」。一方、`s2-plan.md:223` と `:225` は今回の実測原因を runbook にも反映する案。
- 問題: journal 拒否を policy 拒否へ置換するだけでは、次の移行で再び陳腐化する。
- 放置時の帰結: 同じ P3 の現在値が複数文書に残り、次段へ進む判断が古い観測を参照し得る。
- 推奨対処: runbook は live / historical の判定規則と観測正本への参照にする。現在値は worklog 末尾・phase doc、詳細は一次資料へ置く。

## 択一 α / β / γ の裁定材料 (恒真性・第 4 案・推奨)

**α の区間述語全体を恒真とは判定しない。**

G に対象 path が存在するなら、その parent を存在する限り遡ることで G の祖先に導入 commit が見つかる。一意導入を要求する以上、それが i であり、`i ≤ G` は自動的に成立する。これは D2077 に適合した候補に限らず、既存 endpoint 検査を通る対象について成立する。

対して、例えば closure path が C より前に導入され、そのまま result の commit と候補生成を迎える履歴は、D2077 の「戻した成果物を commit」「candidate を生成」だけでは排除されない。したがって `C ≤ i` はこの履歴を拒否する実質的制約である。現物で `C=i=G^` だから成立することと、候補集合全体に含意されることは別である。

| 案 | 裁定材料 |
|---|---|
| α | 現物を受理でき、G/A/X の作り直しを避ける。一意・非 merge・下限は制約として残る。上限は重複検査。 |
| β | 親の「本 wave では採らない」は妥当。D2120 項 2 (b) の G の親指定に加え、D2077 の result commit → candidate の順序との整合も再検討が必要。G や世代 bytes の変更は A/X の参照へ波及し得る。 |
| γ | **同じ残存条件の下で導入条件を外すなら**最も広い。ただし G 実在・hash・履歴不変検査まで消える案ではない。α から何を削除するかを明示する必要がある。 |
| 第 4 案 δ | `i = document["frozen_at_head"]` かつ `C ≤ i < G`、一意・非 merge。既存 field と V1a だけで書け、新 field は不要。現物を受理し、`i=G` や frozen より前の導入を拒否する。 |

δ は「候補が参照する snapshot の commit で全対象を初導入した」ことを要求するため、α より狭い。ただし D2077 が要求するのは候補生成前の commit であり、**全 closure の初導入が captured HEAD と一致することまでは要求していない**。snapshot への存在束縛と初導入 commit の一致も異なる保証である。

推奨は **B-1 / B-2 を反映した α**。δ は選択可能な裁定候補として残すが、既存裁定の必然とは扱わない。α の保証は Git DAG 上の記録順であり、測定の実時間順や独立した承認の証明ではない。

世代文書導入 `{G}` の追加は、既存の wrong_g 負例が確認していた拒否を維持する局所的な置換として妥当。D2180 の AI 委任・trailer・A/X topology を変更する必要はない。

## 本修正が効く経路と研究前進の限定 (N1、_ACTIVATED_G1_REFUSALS)

本修正は、**新 main 上の historical reverify には直ちに効く**。`s8b_ratified_freeze.py:3736` の正規 API を使い、段階 4〜7 の不整合を解消できる。ただし提示証拠 `evidence/reverify-probe-journal-stage6-mutated.json:12` は `ok: false` で、段階 8 の候補 hit を示している。正式修正後の再実測が必要である。

live 再開への効果は次のように限定される。

- pin 前進前に固定した checkout: 本修正が含まれない。利用するなら別途移植と検証が必要。
- 新 main: 現状は N1 の policy 拒否が先行する。T-2812 で source / admission / identity / protocol の整合を揃える経路に、本修正が引き継がれる。
- その後も N3 と W-4 spec 承認が残る。本修正や T-2812 単独で launch 成功を保証しない。

したがって完了判定 (b) は局所修復の受入として適切だが、表題の「full launch validation を通す」の達成証拠にはならない。`s2-plan.md:211` の限定は正しく、brief と最終完了記録にも揃えるべきである。

`_ACTIVATED_G1_REFUSALS` の更新は **held node の現 main に対する真値の追随**であり、成功条件への緩和ではない。D2180 も実 repo consumer の実測値追随を求めている。N1 は T-2304 の policy epoch 前進の帰結なので、「T-2304 統合時に追随すべき期待値を、本 wave で補完する」と書くのが正確。本修正が policy 拒否を新たに生んだようには書かない。

## N3 候補文書の扱い (削除 commit の可否・pin・consumer・scope)

**候補だけを削除する commit は、「走査除外は広げない」と両立し得る。** scanner の受理規則を変えず、現 tree の対象を変えるためである。ただし D2077 は「退避の成功は……痕跡を消してよかったことの証明でもない」とも定める。削除の可否は、不要な候補コピーを廃止してよいという別の根拠を要する。

削除しても official run_dir の journal / manifest / result は残り、D2077 / D2120 項 2 (a) の「main から official 床値を再起動できない」という帰結は消えない。

影響は以下のとおり。

- **B-10 pin:** `tools/pegasus/b10_backoff_grid.sh:585` の対象は `output/s1-freeze` と `output/s8b-freeze`。候補 directory は対象外で、候補だけの削除ではこの digest は変わらない。
- **G/A/X と成果物 hash:** 候補は `_measurement_closure` で専用 path として除外され、active-chain の 4 path にも含まれない。候補だけの削除なら、世代・承認・pointer・floor_source の bytes を更新する必要はない。削除 commit によって HEAD と scan の列挙結果は変わるため、load / reverify はやり直す。
- **他の参照:** `_ACTIVATED_G1_REFUSALS` の候補を含む hit 列挙は変わる。固定 HEAD の記録と削除後の観測は区別が必要。「あらゆる pin に無影響」とまでは今回の静的確認から主張しない。
- **consumer:** `generate_v2_g1_candidate` は固定 path へ create-only で書く。削除後はその path の存在による拒否がなくなる。全入力検証は残るので、再生成成功まで保証されるわけではない。再生成されれば候補 hit が復活し得る。
- **保存:** X2 の履歴 blob と現在の世代文書を参照して、候補 bytes と来歴を保持できる。現在 path へのリンクは履歴参照へ整理する必要がある。

本 wave に削除を追加しない判断を支持する。依頼の「別の不整合が出たら記録して止める」に該当する。候補を exemption に追加する案は既存裁定に反するため、局所修正の代案にはしない。

## 過剰と削除 (test・型検査・docs)

fixture option、現物 topology の正例、未知 event・片側 binding・不正 lineage・G 偽装の負例は、本題の受理集合を変えるために必要であり、過剰ではない。

binding の非空 str、両 event 間の値一致、reservation の基本型検査も、新しく受理する文法の境界として妥当。producer は `s8b_floor_campaign.py:6560` と `:7636` で同じ external binding を転記する。ただし「floor_liveness と同じ」は型述語の一致に限定する。`floor_liveness.py:259` は claim 時に検査する一方、plan は binding 無しにも適用するため、適用範囲は同一ではない。

削減可能なのは次の部分である。

- 各 field と全不正値の直積を大量の独立 Git fixture にすること。異なる検査分岐と bool/int 境界を覆う parameterization に整理できる。
- `i ≤ G` のためだけの helper 抽出と変異を、独立した public 防壁の証明として扱うこと。残すなら重複検査の単体試験と明記する。
- runbook への今回の exact 拒否値の再掲。
- 共用定数を参照するだけの consumer file への不要な編集。

「負例 ≥ 8」という件数だけでは十分性を判断できない。正例が旧 allowlist / 旧 `{G}` 条件で落ち、負例が対応する検査の除去で通ることを確認する方が重要である。plan の入力負例と実装変異を分ける方針、手前落ちを reason / cause で区別する方針は適切。実測の成否は親の検証待ちである。

## 裁定パッケージ候補 (scope 外の層の列挙)

1. **N1 / T-2812: 新 main での live 消費への移行。**  
   D2184 に従い、新登録・identity、driver source、successor protocol、admission の整合をまとめて扱う。policy を外す案や旧 receipt の張り替えで代替しない。

2. **N3: 未発効候補コピーの廃止。**  
   候補だけの削除 commit を第一候補とし、履歴保存、consumer の create-only 状態、hit 期待値、削除後 reverify を提示する。承認済み G/A/X や測定 bytes の変更とは分ける。

3. **歴史再開で本修正を使う場合の移植。**  
   固定した旧 checkout をそのまま使うのか、修正を移植した別 checkout を検証するのかを明示する。今回未実測の経路であり、必要が生じた時点の実施判断候補とする。

4. **W-4: oracle spec 承認。**  
   validator 修復、g1 批准、D2180 の AI 委任のいずれも spec 承認を代行しない。

5. **W-5 / certified 選択。**  
   実走 admission と oracle 証拠が揃って初めて進める層。本 wave は測定値・認証結果・certified の受理集合を更新しない。

全層を同じ wave で実装する必要はない。**修復対象、実効経路、未解決の依存先を全層にわたって示すこと**が必要であり、上記を未完了として残すなら今回の局所 scope は成立する。

## 総括

**α と journal の 2 修復を条件付きで支持する。** 必須の修正は、α の上限の重複性と受理拡張範囲を明示し、本 wave の達成を historical reverify の段階 8 到達までに限定すること。

N3 の削除、policy 移行、W-4 承認は本 wave に混ぜず、具体的な別件として残す。これにより「validator の不整合を修復した」と「g1 で研究を再開できる」を区別して完了判定できる。