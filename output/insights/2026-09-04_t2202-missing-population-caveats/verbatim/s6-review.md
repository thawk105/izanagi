## 総括

must-fix 4 件、nit 1 件。削除・既存行変更は 0 件だった。  
最重要 1: `965996` の request 壁時計は 20,950 秒であり、「約 5 時間 5 分」とする帰属が一致しない。  
最重要 2: balanced の但し書きが、終了直前に本規模反復が始まった可能性を落としている。  
最重要 3: 誤値「24 反復」の直後に「値を無効にするものではない」とあり、誤値を再昇格し得る。

## 所見一覧

1. **real / must-fix** — 対象: `docs/b10-multinode-formal-run-design.md:20-25,153-156`、`output/insights/2026-08-31_t1905-b10-formal-run/README.md:161-165`、`output/insights/2026-09-02_paper-story-a6-certification/README.md:228-231`、`output/insights/2026-09-02_t1905-b10-multinode-design/README.md:35-40`、`output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:93-96`。  
   「5 時間」「5 時間 5 分」を request `965996` の壁時計としているが、一次資料の scheduler 実測は `Elapse=20950 秒`、すなわち約 5 時間 49 分である。5 時間 5 分がどの区間を指すかは射影資料から確定できない。根拠: `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:138-145`。  
   放置時: 材料レポートと設計文書で約 25 時間外挿の出所が誤り、真の request 壁時計から再計算した値と混同される。  
   直し方: 既存値は変更せず、但し書きから「request の壁時計」という断定を外す。正しい区間を確認できない場合は「5 時間 5 分の計測区間は現記録から判定不能。request 全体の Elapse は 20950 秒」と明記する。

2. **real / must-fix** — 対象: `docs/b10-multinode-formal-run-design.md:128-131`。  
   balanced の壁時計について「本規模反復は 0 件」とだけ書き、裁定された「終了直前に次の反復が始まっていたかは記録が無く不明」を落としている。0 件なのは完了記録であり、開始イベント自体は記録されない。根拠: 一次資料 `README.md:94-103,108-125`、裁定 `s4-adjudication.md:34-35`。  
   放置時: 設計文書が、WAL で証明できない「本規模反復は開始されていない」という強い読みを許す。  
   直し方: 「本規模の完了記録は 0 件。終了直前に 1 反復が始まっていたかは記録が無く不明」とする。

3. **real / must-fix** — 対象: `docs/b10-multinode-formal-run-design.md:145-147`。  
   「24 反復ぶん」を値の誤りと確定した直後に、無限定で「値を無効にするものではない」としている。旧誤値へこの定型を使わないという段 3 所見・段 4 裁定に反する。根拠: `s3-lensA-out.md:34-36`、`s4-adjudication.md:11,21,36`。  
   放置時: 材料設計で誤った 24 反復が、正しい 18 反復と並ぶ有効な見積り入力へ再昇格し得る。  
   直し方: 「24 反復を除く上記の測定値・派生値を無効にするものではない」と限定するか、24 反復について「誤りのまま」を明記する。

4. **real / must-fix** — 対象: `output/insights/2026-09-04_f241-perf-attribution/README.md:154-158`。  
   「13.7〜17.5 時間」の入力母集団を欠測 attempt の 3 反復だけで説明し、全体が高 commit 3 変種の本規模反復 5・5・3であることを記していない。また、この file の最初の但し書きなのに `commit` を「変種の認証確定」と定義しておらず、取引 commit と混同できる。根拠: 一次資料 `README.md:163-167,195-203`、`s3-lensA-out.md:30-32`、裁定 `s4-adjudication.md:34,47`。  
   放置時: F241 の材料レポートで、見積りが欠測 3 反復だけから作られたように読め、さらに transaction failure の話へ誤読される。  
   直し方: 「入力帯は高 commit 3 変種の本規模反復 5・5・3で、そのうち 3 反復が欠測 attempt」と書き、`commit` を「取引の確定ではなく campaign 記録上の変種認証の確定」と定義する。

5. **real / nit** — 対象: `output/insights/2026-09-02_b10-trace-truncation/README.md:217-221`。  
   「約 7 倍」の母集団を read-heavy の 5・5・3だけとしているが、比の実際の母集団には対応する write-heavy の各 5 反復もある。「write-heavy の範囲には掛からない」で欠測の非帰属は分かるものの、比の分母母集団は明示されない。根拠: 一次資料 `README.md:193-203`。  
   直し方: 「read-heavy は 5・5・3、対応する write-heavy は 5・5・5の三つの点別平均比」と補う。

削除行は diff metadata の `---` を除き 0 件。B11、B7、G1 への但し書き追加もなく、対象外裁定は維持されている。C・E・G の旧 `23 分・3.83 時間・3.1 倍` は「訂正を変えない」「旧値は誤りのまま」が入っている。a6 の EOF 追記は、既存本文を追記だけで訂正するという file 自身の宣言を守り、節名と値を個別列挙しているため、この file に限って妥当である。

## 閉包の実測

射影された段 3 の再帰検索結果を実 diff と再照合した。検索表記は `1690万 / 16.9M / 約17M / 17M`、`1346.9-1465.6 / 1350-1470 / 22.45-24.43`、`287 / 238 / 197 / 24 / 18 / 22 / n=3`、`49×6 / 15×6 / 15×5 / 5+5+5+3 / commits+aborts`、相関・係数、`79.6-86.0 / 13.7-17.5 / 1.7-2.1 / 3.1`、各 campaign・variant identity である。

意味上の全 hit は次のとおり。行番号は diff 適用前の検索結果である。

- `output/insights/2026-08-31_t1905-b10-formal-run/README.md:147-151`
- `output/insights/2026-09-02_b10-trace-truncation/README.md:12-26,45-65,80-82,101,148-158,179-202,220-221,235-236,253-276`
- `output/insights/2026-09-02_paper-story-a6-certification/README.md:100-103,164-168,179-210`
- `output/insights/2026-09-02_t1905-b10-multinode-design/README.md:32`
- `output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:1,14-20,24-45,55-56,69-83,102,108`
- `docs/b10-multinode-formal-run-design.md:16-26,115-131,227-230,243-248,304-312,420`
- `output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:29,35-44,55-58,68-86,128-131,148,274`
- `output/insights/2026-09-02_t2191-verifier-parallel/README.md:27-33,50-51,125-133,166-167,184-200`
- `output/insights/2026-09-04_f241-perf-attribution/README.md:151`
- 既開示 H: `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:94-104,159-168,178-203,249-260`
- 既開示 denominator-270: `output/insights/2026-09-02_b10-denominator-270/README.md:94-114,124-134`
- `docs/paper-story/` の再帰検索: 0 件

段 3 で閉包漏れだった G の `1.7-2.1 倍`、G の旧 `3.1 倍`、F241 の `13.7〜17.5 時間` にはすべて挿入がある。新たに但し書き自体が欠落した数値主張は見つからず、残る問題は上記 5 件の帰属・文面精度である。