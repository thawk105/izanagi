---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2417-policy-arm-perf
seq: 1
title: [T-2417] policy 腕の既存18 blockを回収し、登録式による条件付き結果と未認証の射程を記録した (コード + 既存測定・解析 + docs、branch worktree-dev-wave-t2417-policy-arm-perf)
---

## 本文

policy 腕 (p0 / p1 / p2) の trace 無効な性能を、腕と job 内時刻の交絡を断つ順序設計で測った。
一次資料は `output/insights/2026-09-08_t2417-policy-arm-performance/`。

**依頼が指した腕定義の所在が違った。** `orchestrator/campaign/site_policy.py` は Pegasus の
ノード判定だけで腕を 1 つも持たない。**「腕の測定順が固定」も既存の性能成果物には
当てはまらなかった** — 既存 7 腕 block は開始位置を巡回済みで、順が固定なのは trace 有効側の
反実仮想契約のほうだった。閉じるべき穴はそこだと段 1 で確定した。

**循環 3 通りの巡回では足りないことを数えて確かめた。** driver は腕を最内で回すので位置効果は
循環でも消えるが、一次持越しが消えない。6 通りの有向遷移のうち 3 通りしか現れず、逆向きは 0 回
だった。全 6 permutation × 3 = 18 block では 6 通りが各 213 回、各腕が各位置に各 6 回になる。
反復数は検出力から決めた ({{D:policy-arm-block-design}})。

**事前登録したread-heavyの等価予測に反した。** abortが少ないという想定で等価を予測したが、
記録値ではread-heavyでも42 threadsで+190%だった。実際のabortは非ゼロ (p0で1.91〜15.40%)なので、
無abort域の機序を反証したとはしない。
全24点の最大は balanced・30 threads の +249% である。回収時に表との不一致を訂正した。
結果を見てから予測を書いていれば、この誤りは記録に残らなかった。3 腕はいずれも未認証であり、
headlineと採用判断には使わない。compilerの記録は要求名が中心で、本体の完全identity一致は確定できない。
H1/H2/H3は記録値へ登録式を適用した条件付き結果として残し、登録条件への完全適合を主張しない。

**事前登録 v1 に、満たしえない identity 要求が 2 件あった**
({{F:preregistered-byte-identity-unsatisfiable}})。測定完走の直後、解析の 1 回目が構造検査で
拒否して判明した。throughput の値は 1 つも観測していない時点である。正誤表 1 で identity 述語
だけを訂正し、v1 の bytes は変えていない ({{D:identity-binding-is-meaning-not-bytes}})。

**敵対レビュー 2 本が、実走では見つからない欠陥を独立に同じ 2 件挙げた。** 最も重いのは
「producer が build 証拠を出さず、正常な成果物が 1 件も解析へ入らない」で、解析のテスト fixture が
手作りでその項目を足していたため隠れていた。18 block を投入する前に見つかった。
**同じ型の隠蔽が 2 度起きた** — 1 度目は build 証拠、2 度目は腕ごとの source hash。

**実投入でしか出ない欠陥が 2 件あった** ({{F:qsub-reply-is-a-sentence-not-a-job-id}})。
テストでも変異でも捕まらず、1 件目は実際に孤児 job を作った。

**棄却 finding はゼロ。** 検出した 19 件すべてを real と裁定した。scope 外へ送ったのは
既存 ITT の seed 穴 1 件だけで、本 wave の変更が作った欠陥ではない。

**親の手順違反 3 件。** fix 子の所有 path にテスト file を入れ忘れて赤が残った (2 回)。
また codex の sandbox 子が共有 Git 管理領域へ書けず `git merge` を実行できないことを、
子を 1 本無駄にしてから知った。以後は親が merge を開始して競合中の file を子へ渡す形にした。

**2026-09-10 の回収時点の裁定を反映する。** D1865/D1866とT-2265の別条件11 groupの部分認証・
費用打切りの後、最新裁定の項28は追加認証の残余を見送りとした。本18 blockの認証へ転用しない。
480 request案を新しい裁定待ちとして起票せず、未提供の自動撤回機構も今回の追加実装・新規タスクにしない。

**回収時の独立レビューを2本、採用修正後の焦点レビューを1本行った。** 集約JSONへ未認証2タグを保持し、
古いgroup fixtureをmainの前提へ追従させた。数値・入力拒否・認証範囲は不変。追加gate勧告は実18 blockで
不一致が無いため明示scopeに従い不採用とし、限界を明記した。焦点レビューはscope内GO。
変異本走は既存15/15 KILLED・期待node完全一致、表示感度2/2一致、baseline PASSED、wrapper rc0。
先行probeは共有木の状態変化でwrapper rc125となり、独立cloneで本走し直した。失敗証拠は保持した。
関連走はproducer/consumer 242 passed、周辺343 passed、hooks474 passed/1 skipped。
記録・検査の正本はinsightの`recovery-2026-09-10.md`。

**dev-wave改善候補:** merge競合をauthorへ渡す準備方法を既存leafで明確化する候補を専用handoffへ記録した。
merge状態のmidflight拒否と未commit権威文書のlauncher拒否を実測したためである。改善実装・次wave起動は行わない。

## 次の一手差分

### 完了

- [T-2417] 全6 permutation×3の既存18 blockを回収した。記録値へ登録式を適用した結果は
  H1 accepted、H2/H3 rejected。compiler完全identity未確認・未認証の条件付き結果として保持し、
  追加認証の残余は見送りとする。
  remaining: none
  base: 14ade7f74ca53c8e98474256da9378a1baf645ed19ee233013862404ff17e855

### 新規

- {{T:itt-trace-contract-seed-gap}} **P2・新規**: 既存 ITT の trace 契約が seed を検査せず、
  producer が受理して束縛を付けた成果物を offline consumer が拒否する状態を作れる。
  本 wave の変更が作った欠陥ではないので scope 外とした。
- {{T:dose-response-break-at-write-heavy-42}} **P3・新規**: 用量反応が 24 点中 1 点
  (write-heavy, 42 threads) だけ破れ、p2 が p1 を −10.7% 下回る。その機序。
