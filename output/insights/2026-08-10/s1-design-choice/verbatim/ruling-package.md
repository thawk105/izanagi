# 裁定パッケージ — 段 7 前提 S1 の設計択一 (案 A: trace-hook 移植 / 案 B: stock 専用計測経路)

```text
authority: dev-wave (背景 job) がユーザー裁定 Q2 = (a) を受けて起票 (2026-08-10)
wave: dev-wave-s1-design-choice / branch worktree-dev-wave-s1-design-choice
根拠: スコープ B 部分再開裁定 Q2 = (a) (rulings-inbox/2026-08-10-scope-b-reopen.md)
性質: 設計択一。本 wave は docs のみで実装差分ゼロ (ユーザー明示)
一次資料: brief.md / s2-plan.md / s3-lens1.md / s3-lens2.md (同 directory)
ccbench pin: d706650cdb31e442bef45b9b4216951d4fb40969
並走ガード (Q3 = (a)): (i) 計算ノード未使用、(ii) T-139 job 走行中のためキュー投入なし
  (wave 開始時 qstat: 900495 RUN / 900512 PRR)、(iii) 裁定帯域は A 優先 —
  本パッケージは A 側が裁定待ちでない時に処理されたい
```

## 0. まず伝えるべき結論 — 2 案は同じ目標の代替ではない

依頼は「2 案を 3 軸で比較して択一を返す」だったが、**比較の結果、2 案は同じ目標に対する
代替案ではないことが判明した。**

- **案 A (移植) だけが、段 7 の「certified な cross-protocol 比較」を成立させる。**
- **案 B (stock 専用計測経路) は、どれだけ設計を厳しくしても段 7 の比較を作れない。**
  作れるのは「正しさ未検証の性能観測」であり、それを比較表・順位・headline の片側に
  置いた瞬間に規律 2 違反になる (敵対レンズ 1 が blocker 認定、`s3-lens1.md` L1-4)。
  隔離条件を全部満たした案 B は、段 7 の成果物ではなく**別の偵察成果物**である。

したがって択一の実体は「A か B か」ではなく、**「段 7 の cross-protocol を certified 比較
として成立させるために、判明した本当のコストを払うか」**である。以下はそのための材料。

## 1. 3 軸の比較 (依頼された軸)

| 軸 | 案 A: 別 protocol への trace-hook 移植 | 案 B: stock 専用計測経路 |
|---|---|---|
| **実装コスト** | **当初想定より大きい。** hook 移植そのものは si の先例で安い (mocc なら silo 型で 30〜60 行規模) が、certified 比較の成立には次が**束で**要る — (1) trace 形式 v2 化 (§2-A)、(2) observer 防壁の protocol 対応 (§2-B)、(3) 遺伝子空間登録 + protocol 別較正 + between-run floor の 3→9 セル再実測 (§2-C)、(4) 公式 report / schema / selection consumer への接続 (§2-D)。段 2 の見積り 5〜8 人日 (mocc) / 7〜11 人日 (ermia) は (1)(2) までで、(3) の実測時間と (4) を含まない | **見かけは安いが、規律 2 と整合させると安くない。** 別 namespace・別 ledger・別 runtime type・厳格 loader・公式 consumer 拒否・負例テストが要り 3〜5 人日。C++・verifier・遺伝子空間・submodule pin の変更はゼロ |
| **検証可能性** | **高い。** 既存の機械検査 (verifier fixture の三値判定、trace-empty / verify reject / COMMIT 不在、COMMIT の AST gate、nm 漏洩検査、diff-of-diffs、build target) がそのまま効く。新規に protocol 別 positive/negative control (誤写像 mutant が赤になること) を足せば、移植の正しさを機械で示せる。**証明できない部分も明確** — 「全 logical read が必ず trace された」ことは静的検査と有限 workload では証明できない (mocc は protocol 自身が検証する read_set を trace source にできるので比較的強い、ermia は補助 buffer が追加 TCB) | **低い。** 確認できるのは「exact pin・clean tree・stock flags・TRACE=0 build・同一 workload・同一時間窓」まで。**確認できないのが本質的** — 候補 run の serializability、trace integrity、anomaly の不存在。得られるのは性能観測であって正しさを伴う比較値ではない |
| **規律 1 との整合** | **条件付きで整合。** 計装を全て `#if TRACE` 内に置けば別ビルド・別 run は保てる。nm 検査は protocol 非依存でそのまま効く。**ただし現行の diff-of-diffs は silo 固定** (`source_digest.py:79`) で移植先を見ておらず、さらに汚染された新 pin を baseline にすると diff-of-diffs 自体が「汚染 pin と同じ」と判定してしまう。**旧 pin 対新 pin の TRACE=0 翻訳単位同一検査**が最後の防壁として必須 (`s3-lens1.md` L1-3、blocker) | **整合する。** 候補が無改変 stock、両 arm が trace-disabled の別 run、同一時間窓なら検証計装による非対称は生じない。nm と CMakeCache の検査で担保できる |
| **規律 2 との整合** | **整合する。** 候補も既存の build→verify→bench→COMMIT を通り、anomaly / integrity failure があれば `pipeline.py` が ABORT して fitness も COMMIT も出さない。**ただし現行 trace v1 のままでは整合しない** — §2-A の偽陰性が残る限り、移植先も silo も「部分履歴で certified」になりうる | **段 7 の比較として使うなら違反。** 対抗馬だけ正しさゲートを免除する非対称比較になる (D44 が予告していた通り)。**正しさバグで同期を省いて速くなった stock ほど選ばれやすい**という、規律 2 が名指しで警告している reward hacking の形そのもの。隔離 6 条件 (§3) を全部満たせば「正式比較ではない別成果物」として規律 2 に抵触しないところまでは行ける |

## 2. 実装コストの内訳 — 案 A に束ねられている 4 つの負債

### 2-A. trace 形式 v2 化 (**プロジェクトが既に「S1 と同時にやる」と宣言済み**)

`orchestrator/tests/test_verifier.py:601`–`638` に、**現行の verifier が certified にしてしまう
ことを意図的に assert している characterization テストが 2 本ある**。

- 末尾の取引が丸ごと欠落しても検出されない (欠番検査が `max(txid)+1` のため)
- C 行だけ残って R/W 行が消えても検出されない (C 行に R/W 件数が無いため)

同テストのコメントが「恒久対応は trace 形式拡張 (C 行に R/W 件数・終端マーカー) =
izanagi-trace ブランチ変更が必要で **S1 移植と同時に行う**」と明記している
(worklog 2026-07-02 [MED] 台帳)。つまりこれは新発見ではなく**登録済みの負債**であり、
案 A のコストには元から含まれている。

**重要なのは、この偽陰性が移植先だけの問題ではないこと。** 現行 silo の certified 結果も
同じ verifier の上に乗っている。

### 2-B. observer 防壁の protocol 対応

`source_digest.py:79` の `EVOLVE_BLOCK_SOURCES` と `:82` の `ALLOWLIST` が silo に固定。
全 protocol の単純 union は「別 protocol の dirty source を digest 外で許す」ため不可で、
protocol 別 map + 全 consumer + buildcache 呼出し + hook 側の写し + drift テストの更新が要る。
加えて §1 に書いた旧/新 pin の TRACE=0 翻訳単位同一検査。

### 2-C. 遺伝子空間・較正・floor (**段 6 前提タスク台帳 (b) と同じもの**)

`genome.py:88` の `SPACES` は silo のみ。`between_run_floor.py:52` の baseline も silo 固定で
測定点は 3 つ。protocol を 3 つにすれば floor 測定セルは 3→9 に増える。**これは実測時間で
あって人日ではない** — 段 2 の見積りが「別」として外に出している部分。

### 2-D. 公式成果物への接続 (敵対レンズ 2 が最重要 blocker と判定)

- `layer3_report.py:345` の floor 照合は (records, threads, workload) だけを見て
  **protocol をキーにしない**。protocol 別 floor を同一 workload で足すと「複数一致」で停止する
- `layer3_schema.json:5` は `additionalProperties: false`
- `layer3_report.py:544` が「certified-selection consumer はこの checkout に存在しない」と自認

新しい report ファイルを別に置けば公式の材料レポート・受理集合には反映されず、公式 report へ
統合するなら floor 選択・schema・acceptance receipt・selection consumer・fixture が追加で要る。
**どちらにしても、段 2 の見積りには入っていない。**

## 3. 案 B が規律 2 に抵触しないための条件 (参考。採る場合のみ)

段 2 が具体化し敵対レンズ 1 が「実効的な機構」と認めた 6 条件。

1. 公式 WAL・COMMIT・fitness・受理集合と別 namespace・別 schema・別 runtime type である
2. 公式 report / selector / optimizer が機械的に拒否する
3. stock のみ。variant 生成や性能フィードバックに使わない
4. 数値は正しさ未評価と表示し、winner・採用・headline を出さない
5. 後から案 A を実装しても、案 B の値や成果物を certified へ昇格・再ラベルしない
6. 正式比較は案 A 経路で新しく build→verify→bench→COMMIT をやり直す

**加えて敵対レンズ 1 が指摘した第 7 の条件** — 案 B の値で案 A の移植先を絞る「段階案」は、
条件 3 と両立しない。正しさバグで最速になった protocol を移植先に選び、他を候補から落とす
経路が開くため。**案 B を「順序付け」にしか使わず、候補集合から protocol を除外しない**
ことを条件に加えない限り、段階案は採れない。

## 4. 裁定を求める 3 問

### Q1: 段 7 cross-protocol をどう成立させるか (主問)

- **(a) 推奨: 2 wave に分ける。** 先に **trace v2 化 (§2-A) だけを単独 wave で land** し、
  その後に protocol 移植 wave (§2-B/C/D) を起票する。
  - 理由 1: §2-A は移植の是非と独立に価値がある。**現行 silo の certified 結果自体が
    この偽陰性の上に乗っている**ので、移植を採らなくても返す価値がある負債
  - 理由 2: 移植 wave の scope が縮み、見積り精度が上がる (今の 5〜8 人日は §2-A 込みの数字)
  - 理由 3: 規律 5 (段階導入) と一致する
- (b) 案 A を 1 本の wave として起票する (§2-A〜D を一括)
- (c) 段 7 の cross-protocol certified 比較を放棄し、headline から降ろす
- (d) 段 7 ごと先送りし、現状の checkpoint を維持する

### Q2: 移植先の初手 (Q1 で (a) または (b) を採る場合)

- **(a) 推奨: mocc。** 版 ID が silo と同型の native `(epoch, tid)` で写像が要らず、
  protocol 自身が validation に使う read_set をそのまま trace source にできる。補助 buffer 不要
- (b) ermia。**注意: `docs/ccbench-anatomy.md:211` が警告する `cstamp<<1` は、現在動いていない
  経路の話だった** — `commit()` (`cc/ermia/transaction.cc:905`) は `ssn_parallel_commit()`
  だけを呼び、そこは raw の `cstamp_` を格納する (`:765`)。**ermia の真の難所は別**で、
  成功した read の一部が `read_set_` に入らない分岐 (`:160`–`:174`) があり、そのまま si 型の
  hook を移植すると write-skew の片側の依存辺が消えて **serializable に false-green する**
- (c) 移植先は §2-A の完了後に再判断する

### Q3: 案 B (stock 専用の偵察経路) を解禁するか

- **(a) 推奨: 解禁しない。** 3〜5 人日を払って得られるのは「どの protocol を先に移植するか」の
  材料だけだが、その判断は本 wave の静的読解で既に mocc と結論できている (Q2)。
  規律 5 (盛らない) と投資対効果が合わない
- (b) §3 の 6 条件 + 第 7 条件つきで偵察専用に解禁する

## 5. この裁定で変わらないこと

- 絶対規律 1〜6、T-139 の事前登録・凍結 (追補 A 段階 2、blob 束縛)
- 8b の証拠価値の限定
- roadmap 本体 (§2 主経路・§8 ポジショニング)
- 本 wave は実装差分ゼロ。上のどれを選んでも、実装は別 wave の起票を要する

## 6. 副産物 — 既存 docs の訂正 3 件 (裁定不要。次の一手へ起票する)

いずれも本 wave の scope 外なので直していない。

1. `docs/ccbench-anatomy.md:211` — ermia の `cstamp<<1` 警告は dormant な `ssn_commit()` の話。
   現行 active な `ssn_parallel_commit()` は raw cstamp。**S1 着手時の「必須知識」として
   書かれている記述なので、そのまま従うと誤った写像を実装する**
2. `docs/ccbench-anatomy.md:126` — 「mocc 2^4」は現行 CMake と不一致。
   `cc/mocc/CMakeLists.txt:5`–`9` で変数化されている軸は `TEMPERATURE_RESET_OPT` と
   `KEY_SORT` の 2 つで、`RWLOCK` は固定 define (BACK_OFF は universal)
3. `docs/phase3.md:269` の must 表 S1 行 — 「silo 内に閉じる」という現状記述が、
   **si に trace-hook が既に入っている事実** (`cc/si/transaction.cc:526`–`553`) を落としている
