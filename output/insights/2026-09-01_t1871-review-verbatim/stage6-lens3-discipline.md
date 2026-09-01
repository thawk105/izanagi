## 検算した主張

結論として、現シートは段階 B の凍結対象にはできない。中心設計が段 3 後に差し替わり、現設計を見た敵対レビューは本レビュー 1 本だけである。

| 検査対象 | 判定 |
|---|---|
| 新設した連続 abort 数 | 許可観測の意味を決める部分は B の仕事だが、`thread_local` の配置、`abort()` での更新、`writePhase()` での reset、stock identity は C の機構設計。さらに brief と D48 が対象にした「既存メンバ読取拡張」ではなく、新しい状態機構である。`sheet:110-120`、`brief.md:29-34`、D48 決定 2 |
| 3 レンズ要件 | 未充足。段 3 の 2 本は raw `max_* .obj_` 案を検査しており、現在の連続 abort 数を見ていない。本レビューは v2 に対する 1 本目としては数えられるが、以前の 2 本と合わせて 3 本にはできない。`sheet:43-66,110-134`、`axis-onboarding.md:115-125` |
| D47 必須条件 4 | 元のメンバ読取拡張なら D48 が B 差し戻しを明示予約しているため抵触しない。しかし現在案は骨格所有状態の新設であり、その支持を引き継げない。同一軸の改版か新しい複合軸かを段階 A の人間 gate で再判定する必要がある。D47 必須条件 4、D48 決定 2 |
| D52 と D1012 | 現在 inactive の設計メモとして phase 正本を改訂しない判断は整合する。ただし、シート単独で (c') の拘束範囲を変更したことにはならない。v2 activation 前に日付付き・ユーザー承認付きの正本更新が必要。D52、D1012、`phase3-main-experiment.md:159-168` |
| D1012 の三すくみ | 「未解消」が正しい。D1067 は必要性主張を条件付き優越へ狭めただけで、識別問題は消していない。D1012、D1067 |
| D44 追記 1 | v2 の契約全体を実際に探索するなら単一スカラー軸とは限らない。ただし正例 1 件だけでは、実 generator/support が単一閾値へ縮退しないことを証明できない。`sheet:131-134,177-179`、D44 決定 1 |
| docs-only | 支持する。`git status --short` で確認できた変更は対象 Markdown 1 ファイルのみであり、D95 決定 2 の実装面に該当する path はない。D95 決定 2 |

必須条件 14 項の rightsize は次のとおり。分類は、(a) B に残す不可欠な契約・権威条件、(b) 仮想リスク向けの過剰防壁、(c) C の実装・検証へ送る条件、とした。

| # | 分類 | 放置時の成果物影響 |
|---|---|---|
| 1 | (a) | D 番号による採用権威がなく、C 着手可能状態にならない |
| 2 | (a) | 禁止観測が受理集合へ入る |
| 3 | (a) | `kUnset` で stock fallback が保存されない |
| 4 | (c) | 任意 C++ が build 面へ届く。要求は B で凍結し、parser 実装は C |
| 5 | (c) | reject-all admission が完成扱いになる |
| 6 | (c) | coder の受理面が単一代入から拡大する |
| 7 | (c) | stock と variant の identity/provenance が混同される |
| 8 | (c) | 新しい更新点が abort/commit 制御を変えても検出できない |
| 9 | (c) | v1 座標の bytes・意味・過去結果との対応が失われる |
| 10 | (c) | v2 の実効値域と軸適格性が未確定のままになる。新 counter が未実装なので C 着手前には実走不能 |
| 11 | (a) | シート由来の具体戦略や risk 仮説が提案入力へ届く |
| 12 | (b) | 現在の値・受理集合・参照への一行影響を示せない。別途承認された E 段 backlog に落とすべき |
| 13 | (b) | 現在の成果物を変えず、将来計装と台帳だけを増やす。既知限界の記述に留めるべき |
| 14 | (a) | 同一 marker の v1/v2 が consumer と provenance 上で二義化する |

`DW-G05` の一行影響を書けない must-fix は #12 と #13 である。`sheet:198-205`、`brief.md:11-15`。また #4から#10は有効な C 作業を含むが、「C 段着手前に消化」という見出しでは実行順序が成立しない。D48 の用語に合わせ「C 段で消化し、C 出口までに確認」へ分けるべきである。

## must-fix

1. 現 v2 を改めて 3 レンズへ出すこと。段 3 の 2 レンズが検査したのは撤回済み raw-word 案であり、新しい連続 abort 数の所有、更新、reset、入力隔離、activation を検査していない。本レビューを 1 本目として、残り 2 本を独立コンテキストで行う必要がある。`sheet:43-66,110-134`、`consult-sol.md:20-46`、`consult-luna.md:27-45`、`axis-onboarding.md:115-125`。

2. scope と段階 A の権威を取り直すこと。brief は D48 が予約した「既存メンバ読取への拡張」を本題に固定しているが、v2 は commit/abort をまたぐ新しい骨格状態を導入する。これは単なるシート訂正ではない。少なくとも人間 gate で「同一軸の契約改版」か「新しい複合軸」かを裁定し、後者なら段階 A から戻す必要がある。`brief.md:29-34`、`sheet:110-120,140-145`、`axis-onboarding.md:80-82,127-160,223-232`、D47 必須条件 4、D48 決定 2。

3. `contract_version` と activation を機械 identity に入れること。現状は Markdown の `contract_version: 2` と `designed/inactive` だけである。active consumer は同一 `MARKER_ID`、固定 5-bit wire、v1 frozen bytes を保持し、proposal schema、campaign identity、provenance に contract version がない。`sheet:9-14`、`axis_trigger_gating.py:23-49,73-96`、`p3_s4_loop_trigger_gating.py:123-178,553-589,875-937`。

   特に provenance header は `axis/pin/module` だけを記録し、再開時に header を更新しながら既存 entries を保持する。現在は旧シート path により v1 と読めるが、同一 campaign identity の in-place 切替では旧 entry と新契約が混在し得る。`p3_s4_loop_trigger_gating.py:365-409,565-589`。新 marker を使うか、version を proposal schema、campaign identity、WAL/provenance、resume gate、template contract のすべてに束縛し、不一致を停止させる必要がある。

4. D52 の扱いを「提案」に限定すること。`sheet:235-238` は (c') を旧部分空間へ限定したように断定するが、拘束力ある正本 `phase3-main-experiment.md:166-168` は axis 名で記述している。D1012 により今は改訂しない判断が正しい一方、v2 を active にする前にはユーザー承認付き発火 commit が必要である。シートだけで既裁定の射程を変えてはならない。

5. v2 の意味契約を B で閉じること。`sheet:145` は「exact allowlist」と称するが、比較・boolean 結合というカテゴリしか示さず、literal の幅・suffix・範囲、counter の具体型、増加時の飽和または wrap、reset の意味が未定である。`sheet:115,124-126` の自然数としての説明と unsigned 実装案もそのままでは同一契約ではない。これらを C の実装裁量に残すと、受理集合と意味が実装者ごとに変わる。

6. contract-only projection を実際の遮断設計へ落とすこと。D45 は、Read 遮断後もメインセッションによる手動射影と自然文 justification が既知限界だと明記する。`sheet:195-197` は禁止方針だけで、`sheet:251-253` の「必須条件 11 が塞ぐ」は実装より強い保証である。D45 決定 3、`p3_s4_loop_trigger_gating.py:125-133,882-930`。versioned machine schema から固定射影を生成し、自由記述経路と親の文書転記をどう扱うかまで定める必要がある。

7. 必須条件 #12 と #13 を本 wave の must-fix から外すこと。auditor gallery 追加と新しい fairness/liveness 台帳は、ユーザーが明示的に scope 外とした仮想リスク向けの検査・台帳追加であり、現在の成果物影響も示せない。リスク自体はシートに残し、別途ユーザー承認された scope へ送るべきである。`sheet:198-202`、`brief.md:11-15`。

## should-fix

- brief を superseded と明記するか訂正すること。M2 は `clear()` 後の全観測を恒値と誤記し、M3 は生存メンバを非網羅に列挙し、M5 は参照数を過少計上している。対象シートは訂正済みだが、brief 自体も検査対象であり将来の入力になり得る。`brief.md:38-41,67-70`、`sheet:25-32,68-76`。

- brief の P1-4 は上位集合による生存を無条件に述べるが、v2 admission と materialized bytes の保存は未実証である。シートの条件 #9 が済むまで prospective な主張に限定すべきである。`brief.md:42-44`、`sheet:36-39,188-190`。

- D44 適格性の証拠を positive control 1 件に背負わせないこと。非スカラー候補の受理は admission が恒偽でないことを示すが、実際の generator が単一 retry 閾値しか生成しない縮退を排除しない。generator/support の凍結時、すなわち B-5 発火時の事前登録側で判定すべきである。`sheet:131-134,177-179`、D44 決定 1。

- `sheet:253` の「実測された勝ち点も存在しない」は範囲が広すぎる。保存済み v1 provenance は既存偵察に具体点が存在することを記録している。正しくは「v2 の新設 counter を使う拡張空間には実測点がない」である。`p3_s4_loop_trigger_gating.py:188-208`。具体値・順位はシートへ戻してはならない。

- `sheet:119-120` の stock identity は未実装の設計予測である。「同じ macro 囲みを実装し、C の identity 実証を通れば保存される」と条件付きで書くべきである。現 v1 の同型保証自体は `patches/README.md:295-303` に実証記録があるが、v2 の更新点にはまだ適用されていない。

- `DW-G05` 影響を現状態へ合わせること。brief は B-5 と後続実装が参照できる着手可能な軸を作るとするが、現在は untracked の inactive design で、D 番号・3 レンズ・activation が未成立である。「条件を満たせば着手可能になる設計候補」と限定すべきである。`brief.md:79-84`、`sheet:13-14,163-164`。

## nit

- `sheet:151` は「二層」と書きながら三つの control を列挙している。admission の正負 2 層と、既存 misattribution control を別枠に分けると読み違いがない。

## refuted (シート・brief の主張のうち、根拠を確認して支持したもの)

- D1012 の三すくみを「未解消」とした記述は支持する。D1067 も「実装を足しても消えない」と明記している。D1012、D1067、`sheet:232-234`。

- inactive の B 設計段階で `docs/phase3-main-experiment.md` を改訂しない判断は支持する。D1012 は発火条件成立とユーザー承認まで拘束力ある追記を禁じている。ただし、これは v2 の activation も認める判断ではない。D1012、`sheet:235-238`。

- 現在の consumer が v1 を指したままであること自体は確認した。固定 5-bit wire、旧 frozen block、旧シート path、D48 契約が一貫している。`axis_trigger_gating.py:23-49,73-96`、`p3_s4_loop_trigger_gating.py:16-18,188-208`、`patches/README.md:287-303`、D48。

- 元の「既存メンバ読取への拡張を B へ戻す」判断は D47 必須条件 4 と衝突しない。D48 自身がその再レビュー経路を予約している。ただし、新設 counter 案にはこの支持を自動継承できない。D48 決定 2、D47 必須条件 4。

- 偵察の勝ち候補、利得数値、順位が現シートへ転記された形跡はない。地形の生死は二値に留まり、本文中の数値は契約空間の組合せ計算であって偵察利得ではない。`sheet:31,34-39,152-154`。

- 本 wave の現変更は docs-only である。確認できた変更 path は `output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md` のみで、D95 決定 2 の実装面はない。

## verdict

reject

## 総括

現案の最大の問題は、撤回済み案を見た 2 レンズを、新しく発案した連続 abort 数のレビューとして数えていることである。本レビューは v2 の 1 レンズにはなるが、3 レンズ要件は満たさない。

加えて、新設 counter は brief と D48 が予約した既存メンバ読取拡張を越えており、同一軸か新軸かの人間裁定が必要である。同一 marker のまま version を Markdown だけで分ける設計にも機械的な activation、campaign identity、provenance、resume 防壁がない。

静的検査のみであり、テスト・ビルドは実走しておらず、緑は主張しない。