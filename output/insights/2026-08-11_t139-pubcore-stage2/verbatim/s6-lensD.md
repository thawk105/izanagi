# 敵対レビュー結果

**NO-GO。独立 blocker は 6 件です。**  
spool の機械文法は通りますが、裁定の実行状態、Q3、`p03`、roadmap 条件、予約正本、land の実効性に canonical 化前の修正が必要です。

## 段 3 所見の処理監査

段 3 の原文は A1〜A7 と B1〜B12 の **19 行**です。親の「real 15 / refuted 2」は A2+A3 と A4+B8 を同一根として数えたものと解釈すれば算術上は整合します。取りこぼし防止のため、以下では19行すべてを示します。

| 所見 | 段 4 の処理 | 独立判定 | 成果物影響 |
|---|---|---|---|
| A1 nit | real、SHA-256 を worklog に記録 | **must-fix・未反映。** worklog に現行 bytes の SHA-256 が一つもない。[worklog fragment:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/spool/worklog/2026-08-11-dev-wave-t139-pubcore-stage2-1.md:44) | 現行 canonical path の bytes が過去 pin と分岐しても、記録から検出できない。 |
| A2 blocker | N1(i)/Q1 | **処理は十分。** 攻撃系列と影響を明示した。[package:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:71) | 同じ根で ordinal 1 を再取得できる枝が裁定対象になった。 |
| A3 blocker | N1(ii)(iii)/Q1 | **blocker・部分反映。** Q1 は副作用を説明するが、新 core は依然「予約の正本は core+P だけ」と断言し、B `b01` の予約規範と矛盾する。[core v2:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:569)、[B v2:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:71) | exact bytes を承認すると、予約 authority が一意でない契約を凍結する。 |
| A4 blocker | 三段 commit 不採用、Q2 | **処理は十分。** P を未解決 marker 付き草案に限定した。[P draft:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:31) | 未承認 core の受理や永続的 resolver failure を避ける。 |
| A5 nit | package に記録 | **nit・十分。** parser との相違と現 bytes への非影響を明記した。[package:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:213) | 現候補の field 集合は変わらない。 |
| A6 must-fix | 高精度値へ差替え | **must-fix・ほぼ反映。** 数値はレンズ A と一致するが、`…` 付き近似値を「exact 値」と呼ぶのは不正確。[worklog fragment:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/spool/worklog/2026-08-11-dev-wave-t139-pubcore-stage2-1.md:44) | 後続実装が有限桁 decimal を論理境界そのものと読む余地が残る。 |
| A7 nit | 変更せず記録 | **nit・十分。** 保守側の `>` を維持し、差を記録した。[package:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:216) | 今回の `0.025` の棄却集合は変わらない。 |
| B1 blocker | refuted、Q3へ | **blocker・refuted は狭義に限り妥当。** brief には最新の直接指示として「凍結承認を返す」とあるが、ならば Q3 は既に決まった指示を再度問う違反である。[brief:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s1-brief.md:9)、[package:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:125) | Q3(a)/(b) により authority と追加承認手番が再び揺れる。 |
| B2 blocker | 部分 real、Q7 | **must-fix・部分反映。** Q7 は `p01` と `p02` を一括 yes/no にし、片方だけ変更できない。[package:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:182) | ordinal 受理集合と familywise 予算を独立に裁定できない。 |
| B3 blocker | p03 literal 除去、Q4 | **blocker・不十分。** core は「台帳実体が決まらないと確定しない」とする一方、Q4(a) は実体未定のまま `p03` 要件を凍結可能とする。[core v2:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:611)、[package:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:145) | `p03` の確定条件が二義化し、公表台帳の受理 authority が定まらない。 |
| B4 blocker | B v2 exact bytes を Q6へ | **must-fix・部分反映。** Q6 は新 blob を問う点は正しいが、「C-1〜C-5 実行済み」との記録と両立しない。 | source `main_admission` がどの B を受理するか、実行済みか未承認かが曖昧になる。 |
| B5 must-fix | D と B v2 に pin | **処理は十分。** primary 参照禁止を B v2 と decisions の双方へ置いた。[B v2:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:168) | primary/publication 台帳の受理条件の再結合を防ぐ。 |
| B6 blocker | 明示裁定として記録 | **blocker・部分反映。** 明示裁定の枠づけは正しいが、roadmap の全継承条件を列挙していない。 | 不完全な条件で downstream 例外が canonical に適用されうる。 |
| B7 blocker | refuted、実体確認済み | **must-fix・完全には refuted でない。** §S7 #7 が定義を持たない点は確認できたが、land 2 の必須要件として `b03` 公表台帳を所有している。[land1 package:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-manifest-land1/package.md:155) | 新しい T と既存 T-139/land 2 の所有関係を明記しないと二重実装または未所有になる。 |
| B8 blocker | A4 と同一 | **処理は十分。** P を同一 land の凍結対象から外した。 | 未承認 commit の resolver 受理を避ける。 |
| B9 blocker | 「手続き一本化」と記述 | **blocker・bytes へ未反映。** package は重複を認める一方、core v2 の置換文は「この二者だけ」と断言したまま。 | exact core の authority 宣言と B `b01` の規範が競合する。 |
| B10 must-fix | 落とした内容を逐語列挙 | **must-fix・部分反映。** 5 項目は列挙したが逐語ではなく要約であり、preamble や B5 終端文も追加されている。[B v2:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:212) | Q6 の「変更は1点だけ」という承認説明が exact diff と一致しない。 |
| B11 must-fix | C-2b を根拠とし別承認を要求 | **処理は十分。** [B v2:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md:3) | 初版承認を新 blob へ誤継承する経路を閉じる。 |
| B12 must-fix | N3/Q3 | **blocker・不十分。** runtime 成果物が不変な点は正しいが、canonical decisions・worklog・task・例外適用まで「何も動かない」に含めている。 | ユーザーが land の規範・台帳効果を知らずに承認する。 |

## Q1〜Q7 の答えやすさ

| 問い | 判定 | 成果物影響 |
|---|---|---|
| Q1 | **must-fix。** 新事実なので再裁定は妥当。選択肢は主要案を覆うが、推奨理由の「producer wave 以降は core §8.2+p03 が効く」は、失われる source `submit_main` gate を復元しない。package 自身は本走が通る枝を認めている。[package:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:93) | source 本走を許す集合と、公表表を許す集合が分離する。 |
| Q2 | **nit。** 新事実に基づき、主要な順序案は網羅されている。各選択肢の時期への影響を成果物影響欄にもまとめるとよい。 | P の発効時期と公表表生成可否が変わる。 |
| Q3 | **blocker。** 最新の直接指示を優先するなら (a) は既に決定済みで、再質問してはならない。C-4 を supersede した事実として記録すべき。 | authority、段階、追加承認手番が再度択一になる。 |
| Q4 | **blocker。** (a) は core §9 の確定条件と矛盾する。`p03` の exact requirements を承認する問いと、実体決定時期の問いも分離されていない。 | 未同定台帳に対する予約規則だけが凍結され、resolver が何を確定済みと扱うか不明になる。 |
| Q5 | **must-fix。** 5 行差分という事実は正しい。ただし §8.1 の内部矛盾を伏せたまま推奨しており、明示的な成果物影響欄もない。C-4 との関係は「最新指示による supersede」と記録すべき。 | 承認後は公表系列の normative authority と将来 consumer の受理参照が変わる。 |
| Q6 | **must-fix。** 新 blob なので別承認は必要。ただし「`b03` 縮小1点のみ」は exact diff の説明として不正確で、成果物影響欄もない。 | source core が受理する B の commit/path/digest と `main_admission` が変わる。 |
| Q7 | **must-fix。** 未裁定値を問う点は正しいが、`p01` と `p02` を別問にし、別値を選ぶ場合の具体値を回答可能にすべき。 | `p01` は ordinal、`p02` は Holm・同時下限・公表表の数値を独立に変える。 |

## worklog fragment

- **blocker — 実行状態が誤っている。** 「C-1〜C-5 を実行した」とあるが、C-2 の B 発効、C-2b の副作用受容、C-4 の core 承認は未実行で、Q1/Q3/Q5/Q6へ戻されている。[worklog fragment:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/spool/worklog/2026-08-11-dev-wave-t139-pubcore-stage2-1.md:12)  
  **成果物影響:** canonical worklog が未実行の承認・発効を実績として固定する。

- **must-fix — DW-O12 の時制違反。** 「凍結承認はユーザーへ返した」は、段6レビュー中に既に commit された fragment の時点では予定である。[worklog fragment:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/spool/worklog/2026-08-11-dev-wave-t139-pubcore-stage2-1.md:14)  
  **成果物影響:** 実際のユーザー手番より先に返却済みという不可逆記録が残る。

- **nit — P6 の記述は正確。** レンズ A は根を変えず台帳実体だけを交換する具体的攻撃を構成しており、P6 を倒したという記録は一次資料と一致する。[lens A:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s3-lensA.md:11)  
  **成果物影響:** Q1(i) の根拠は保持される。

- **must-fix — 数値の呼称。** `3.449997401748…`、`0.576279948558…`、`1.220995636198…`、`1.562340730078…` はレンズ A と一致するが、「exact」ではなく高精度近似である。  
  **成果物影響:** 境界判定は暗黙方程式または保守側 bound に束縛しないと再び丸め誤りを起こす。

- **nit — 実装差分ゼロは正確。** commit `44abd2fc` は 7 個の `100644` Markdown 追加だけで、コード・テスト・script・機械設定の差分はない。  
  **成果物影響:** runtime gate や現在の機械的受理集合は変わらない。

- **nit — セッション事象は整合。** handoff と `run-s3.sh`/`run-s6.sh` の PID-file 化が、偽 producer death と是正内容を裏付ける。  
  **成果物影響:** scientific artifact には影響しないが、待ち手の完了判定履歴には残る。

## decisions fragment

- **blocker — roadmap 条件の列挙不足。** 明示的ユーザー裁定としての枠づけは正しい。しかし fragment が列挙するのは事前登録、cluster-level、fail-closed、独立 validator の4群だけである。[decisions fragment:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/spool/decisions/2026-08-11-dev-wave-t139-pubcore-stage2-1.md:18)

  roadmap 条文にある次の条件が対応付けられていない。

  - source core・追補 A・本走時の追補 B、commit/path/digest、測定 checkout 祖先性
  - 6順列と workload 順の均衡、結果後の cluster 選別禁止
  - trace-disabled 性能測定と trace-enabled correctness の分離
  - correctness anomaly の候補終端 reject、測定開始後の予備置換禁止
  - 生受領証からの validator 再計算
  - D19/floor/通常 campaign へ流用しない境界

  **成果物影響:** 条件の一部を満たすだけで downstream exception が canonical に適用されたと読める。

- **must-fix — 「B5」と「第5案」の混同を避ける必要がある。** D2 の決定内容自体は旧 package の B5(a) と整合する。一方、最新 worklog の「追補 B 第5案不採用」は別案であり、親裁定の「B5不採用終端」という呼称は混同を招く。[worklog:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/worklog.md:1177)  
  **成果物影響:** primary 参照禁止と、erratum による第5案の不採用が同じ裁定だと誤って継承されうる。

- **nit — decisions の構造文法は適合。** 2件とも決定・理由・却下案を持ち、有効な `[T-数字]` の例示はない。  
  **成果物影響:** fold の採番や decisions parser は阻害されない。

## spool 形式

**形式面は GO です。** `python3 tools/spool_fold.py --dry-run` は `status: planned` となり、現 snapshot では `D283`、`D284`、`[T-790]` の割当てを予定しています。

- frontmatter、ファイル名、ledger、seq、title の有無は適合。
- worklog の H2 は `本文`、`次の一手差分` の2つだけ。
- `[T-139]` は未完なので `更新`、公表実装は placeholder 付き `新規` で正しい。
- `base:` は更新 item の末尾にあり、dry-run で受理された。
- decision H2 と placeholder slug も適合。
- UTF-8/LF/末尾 newline も適合。

**成果物影響:** 文法上はこのまま fold 可能であり、意味上の誤記も機械的にそのまま canonical 化される。

## 取りこぼし・越権・実効性

- **must-fix — land 2 との所有関係。** 最新 `[T-139]` は land 2 の必須要件に `b03` を含める。[worklog:2330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/worklog.md:2330) 新規 T は「非重複」ではなく「§S7 #7 を具体化して同じ producer 系列へ結線する」と記録すべき。  
  **成果物影響:** T-139 と新規 T が同じ公表台帳を別 ownership で実装する危険を避ける。

- **must-fix — P の越権境界。** `p01`/`p02` は候補値かつ authority none なので起草自体は越権ではない。`p03` も requirements の提案までは可能だが、Q4(a) で「実体未定でも確定できる」と承認させるのは core の閉集合条件を変更する越権になる。  
  **成果物影響:** 台帳 identity 未定の contract を確定済みとして consumer が受理しうる。

- **must-fix — B v2 の変更説明。** `b01`/`b02` の逐語保存は確認できるが、文書全体には再発行 preamble、B5 の終端禁止、落とした項目の説明なども追加されている。「1点のみ」は意味分類であって exact bytes の説明ではない。  
  **成果物影響:** Q6 の承認者が新しい恒久禁止文まで含むことを見落とす。

- **blocker — land の効果を過小申告。** runtime/scientific outputs が不変なのは正しいが、「成果物・受理集合も一つも動かない」は誤りである。[package:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-11_t139-pubcore-stage2/package.md:15)

  land によって実際に変わるものは次のとおり。

  1. 7 文書が main に入り、承認候補・P 草案・B再発行候補が durable reference になる。
  2. D 2件が採番され、downstream exception と primary参照禁止が canonical な設計判断になる。
  3. `[T-139]` の active item が Q1〜Q7 待ちへ更新され、新規 T が採番される。
  4. canonical worklog と decisions、`FOLDED.md` が更新され、fragment は GC される。
  5. 現 dry-run では worklog rotation が発火し、`docs/archive/worklog-phase3-0811-403.md` の新設と archive index 更新も行われる。
  6. C-3 の decision により、少なくとも**文書上の downstream 受理範囲**は変わる。

  変わらないのは、certified primary 選択、試行台帳、材料レポート、公表表、runtime gate、本走/pilot の投入可否、コードの受理集合である。

  **成果物影響:** ユーザーが「no-state-change」の意味を runtime に限定せず承認すると、canonical 台帳と normative 受理範囲の変更を見落とす。

## 総括

**NO-GO。独立 blocker 6 件。**  
最大の穴は、未実行の C-2/C-4 を「C-1〜C-5 実行済み」と canonical worklog へ残そうとしていること。  
Q3 の再質問、`p03` の確定条件矛盾、core/B の予約正本矛盾、roadmap 条件欠落も承認前に修正が必要。  
spool 文法は通るため、意味上の誤記も現状のまま確実に canonical 化される。