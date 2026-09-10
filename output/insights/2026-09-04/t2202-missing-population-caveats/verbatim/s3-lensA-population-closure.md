## 総括

所見は 12 件です。内訳は real 5、refuted 4、判定不能 3 です。  
最重要は、B11 の `16.90M / 1425.4 秒` が欠測 attempt 由来ではないこと、G と F241 に閉包漏れがあること、旧誤値へ「無効ではない」と書くと既存訂正を打ち消し得ることです。  
したがって、プランの「8 file・35 組で閉包」は refuted です。  
反復数の正しい対応は performance 欠測観測 3、read-heavy performance 18、全 performance 238、全 verify 287です。24 は誤りで、performance なら18、legacy込みなら22です。

## 所見一覧

1. **refuted** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s2-plan-out.md:31,108`  
   B11 の `16.90M commits / 1425.4 秒` を欠測 `constant-mu2` の n=3 とする帰属は誤りです。出現は `output/insights/2026-09-02_b10-trace-truncation/README.md:235-236`。n=5 の完了変種は `16.83-16.91M / 1374.8-1436.2s`、欠測変種は `16.92-16.94M / 1346.9-1444.2s` です (`output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:37,40`)。一次資料でも欠測点の平均は `16.928M (n=3)` です (`output/insights/2026-09-02_b10-missing-iterations-scope/README.md:199`)。  
   **直し方:** B11 と hard-cap 比較を D1529 但し書きから外す。

2. **判定不能** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s2-plan-out.md:27,107`  
   B7 の `r=-0.0213`、`0.93%`、`6.99%` は、本文が「同一変種の5反復」としか説明していません (`output/insights/2026-09-02_b10-trace-truncation/README.md:189-192`)。欠測点は n=3 なので、完全な n=5 群だけで計算した可能性を排除できません。一次資料が証明するのは、全238反復の集計には欠測3反復が入ることまでです (`output/insights/2026-09-02_b10-missing-iterations-scope/README.md:163-167,258`)。  
   **直し方:** この三統計の入力行を確定できるまで但し書き対象と断定しない。

3. **判定不能** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s2-plan-out.md:66,159`  
   G1 の「adaptive は commit が1/3」は、表のどの行を比較母集団にしたか明記されていません (`output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:35-44`)。高 commit 範囲の両端は n=5 の完了変種だけでも作れ、欠測行は範囲の内側です。  
   **直し方:** 高 commit 3変種の合同値から出した比だと確認できた場合だけ対象にする。

4. **real** — `output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:57`  
   T-2191 の `end-to-end 1.7-2.1倍` の再掲がプランから漏れています。元の見積りは欠測点を含む read-heavy 観測帯を入力にしています (`output/insights/2026-09-02_t2191-verifier-parallel/README.md:125-133`; 一次資料 `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:163-167,258`)。  
   **直し方:** G の但し書きにこの再掲を独立した主張として加える。

5. **real** — `output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:148`  
   `3.1倍` の歴史的再掲も G の対象一覧にありません。この値は欠測母集団由来であるうえ、既に計算誤りとして `2.95倍` へ訂正されています (`output/insights/2026-09-02_paper-story-a6-certification/README.md:194-206`; 一覧正典 `output/insights/2026-09-02_b10-denominator-270/README.md:124-126`)。  
   **直し方:** 単なる「値は無効でない」ではなく、既存訂正済みの旧値であることを保持して母集団だけ補足する。

6. **real** — `output/insights/2026-09-04_f241-perf-attribution/README.md:151`  
   `13.7〜17.5時間の read-heavy 走行` が第9の編集対象として漏れています。値の生成元は T-2191 の `660-840秒 × 75回` です (`output/insights/2026-09-02_t2191-verifier-parallel/README.md:127-131`)。適用規模と検査器外時間には欠測点を含む read-heavy 観測が入ります。  
   **直し方:** F241 を対象に加え、この予定時間へ主張単位の但し書きを付ける。

7. **real** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s2-plan-out.md:116,134`  
   C・E の案は旧 `23分・3.83時間・3.1倍` と訂正後の値を一括し、「値を無効にするものではない」としています。しかし旧値は帰属と計算の両面で既に誤りです (`output/insights/2026-09-02_paper-story-a6-certification/README.md:186-206`; `output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:14-45`)。この文面は規律7上、旧値を再昇格させる余地があります。  
   **直し方:** 「D1529の但し書きは既存訂正を変更しない。旧値は引き続き誤りとして残る」と明記する。

8. **refuted** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s1-brief.md:17-18`  
   F・G の「24反復」は現物と一致しません (`docs/b10-multinode-formal-run-design.md:121`; `output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:29,42`)。表は performance `5+5+5+3=18`、legacy 4を足して全 verify は22です (`output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:35-42`; 一次資料 `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:83,94-103`)。  
   **直し方:** brief から24を正しい母集団として扱う記述を除く。段2が対象外へ戻した判断は正しい。

9. **refuted** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s1-brief.md:14`  
   C の「同じ母集団」は不正確です。`23分` と観測帯は高 commit 3点の performance n=5,5,3ですが、`5時間で15点中3点` は未 commit 第4 attempt の時間を含む request 壁時計です (`output/insights/2026-09-02_b10-denominator-270/README.md:95-96`; `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:163-167`)。  
   **直し方:** 段2の C1/C2 のように performance 帯と job 壁時計を分ける。

10. **refuted** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s1-brief.md:7`  
    記載された grep は閉じていません。`287/238/197`、`24反復`、`1346.9-1465.6`、`79.6-86.0`、`13.7-17.5`、`1.7-2.1`、式表記を検索せず、`docs/paper-story/*.md` は下位ディレクトリも見ません。これらが中核値であることは一次資料 `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:94-103,163-203` が示します。  
    **直し方:** 「この grep による0件」という証明は撤回する。再帰的な拡張検索では paper-story の該当は実際に0件でした。

11. **real** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s1-brief.md:13`  
    B の節名「所要は commit 数に…」は現物の節名ではなく、本文 `output/insights/2026-09-02_b10-trace-truncation/README.md:140` の一文です。実際の見出しは同 `:115` の「頭打ちの正体 — 横軸の取り違え」と `:171` の「所要の内訳と、並列化への入力」です。  
    **直し方:** アンカー表を実在する二見出しへ直す。

12. **判定不能** — `/home/SFC/tanab/.claude/jobs/a027c45b/tmp/wave-t2202/artifacts/s2-plan-out.md:98,117,126,135,143-149`  
    壁時計の案は記録済み legacy/performance 反復を列挙していますが、終了直前に未記録の次反復が開始されたかは判定できません。開始イベントはなく、各 attempt で開始済みだった可能性は高々1件です (`output/insights/2026-09-02_b10-missing-iterations-scope/README.md:108-129`)。  
    **直し方:** 「記録済み legacy 1 + performance 3 の時間を少なくとも含み、終了前の空白で追加1反復が開始されたかは不明」とする。balanced も同じ区別が必要です。

## 閉包の実測

検索したのは、直接値、丸め、式、別表記、identity です。具体的には `1690万 / 16.9M / 約17M / 17M`、`1346.9-1465.6 / 1350-1470 / 22.45-24.43`、`287 / 238 / 197 / 24 / 18 / 22 / n=3`、`49×6 / 15×6 / 15×5 / 5+5+5+3 / commits+aborts`、各相関・係数、`965996 / ed8a676b / 292d58f1dad8 / T-2191` です。

無関係な同値文字列を除いた意味上の全出現は次のとおりです。隣接行はまとめています。

- `output/insights/2026-08-31_t1905-b10-formal-run/README.md:147-151`
- `output/insights/2026-09-02_b10-trace-truncation/README.md:12-26,45-65,80-82,101,148-158,179-202,220-221,235-236,253-276`
- `output/insights/2026-09-02_paper-story-a6-certification/README.md:100-103,164-168,179-210`
- `output/insights/2026-09-02_t1905-b10-multinode-design/README.md:32`
- `output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:1,14-20,24-45,55-56,69-83,102,108`
- `docs/b10-multinode-formal-run-design.md:16-26,115-131,227-230,243-248,304-312,420`
- `output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:29,35-44,55-58,68-86,128-131,148,274`
- `output/insights/2026-09-02_t2191-verifier-parallel/README.md:27-33,50-51,125-133,166-167,184-200`
- `output/insights/2026-09-04_f241-perf-attribution/README.md:151`
- 既に母集団を開示する正典: `output/insights/2026-09-02_b10-denominator-270/README.md:94-114,124-134`
- 既に但し書き済みの一次資料 H: `output/insights/2026-09-02_b10-missing-iterations-scope/README.md:94-104,159-168,178-203,249-260`

このうち新たな閉包漏れは G `:57`、G `:148`、F241 `:151` です。B `:235-236` は逆に対象外、B `:190-191` と G `:43-44` は入力母集団が判定不能です。

`docs/paper-story/` は下位ディレクトリを含む Markdown 全件へ同じ検索を行い、該当0件でした。したがって「変更0」という結論は維持できますが、brief 記載の grep だけではその結論を証明できません。

## 親 brief への異議

- P5 は refuted です。G の表内 `3 (打ち切り)` は元観測の開示にすぎず、離れた `1.7-2.1倍`、外挿、閾値、余裕、旧 `3.1倍` を閉じません。
- C は performance n=5,5,3 と request 壁時計を「同じ母集団」として一括できません。
- F・G の24反復は一次資料と不一致です。
- paper-story の0件自体は再実測で支持されましたが、brief の検索式は閉じていません。
- アンカー A、C、D、E、F、G、H の節は現物と整合します。Bだけは本文句を節名としており不一致です。
- P6 の「15認証単位は構造数なので対象外」と、3・18・238・287の対応は一次資料と一致します。
- P7 は通常の有効値には使えますが、既に誤りとされた `23分・3.83時間・3.1倍` へそのまま使ってはいけません。