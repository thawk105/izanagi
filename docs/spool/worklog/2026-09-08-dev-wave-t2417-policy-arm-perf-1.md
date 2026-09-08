---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2417-policy-arm-perf
seq: 1
title: [T-2417] policy 腕の trace 無効な性能を 6 permutation の 18 block で測った — 事前登録した「効果なし」の予測が逆向きに反証された (コード + 計測 + docs、branch worktree-dev-wave-t2417-policy-arm-perf、変異 baseline PASSED・KILLED 15・SURVIVED 0・MISMATCH 0・期待 node 完全一致 15/15)
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

**事前登録した「効果なし」の予測が、逆向きに反証された。** read-heavy は abort がほぼ無いので
向きの選択は効かないと予測したが、実測では read-heavy こそ効果が最大で 42 threads で +190% だった。
結果を見てから予測を書いていれば、この誤りは記録に残らなかった。3 腕はいずれも未認証であり、
成果物は headline と採用判断から機械的に隔離されている。

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

## 次の一手差分

### 完了

- [T-2417] 全 6 permutation × 3 の 18 block で trace 無効の性能を測り、事前登録した 3 仮説に
  判定を出した。H1 accepted、H2 と H3 rejected。
  remaining: none
  base: 2e58725e71110985d7123da64e9670bd59cbdcdb8529ef4c35c9d5f4a8cd1f79

### 新規

- {{T:policy-arm-serializability-certification}} **P1・ユーザー裁定待ち**: policy 腕の直列性認証。
  現行の受理集合は 2 cell だけで 3 腕を受け付けず、seed は certify と併用が明示拒否される。
  現行の identity 束縛のまま全 identity を認証すると 20 identity × 24 request = 480 request。
  要否と受理集合の改訂を諮る。
- {{T:policy-arm-withdrawal-mechanism}} **P2・新規**: 未認証腕の性能を撤回する機構の 4 点
  (policy 腕を受ける verifier、anomaly の受領証、成果物への束縛、解析または公表 consumer が
  読む撤回 field)。揃うまで自動撤回は有効化しない。
- {{T:itt-trace-contract-seed-gap}} **P2・新規**: 既存 ITT の trace 契約が seed を検査せず、
  producer が受理して束縛を付けた成果物を offline consumer が拒否する状態を作れる。
  本 wave の変更が作った欠陥ではないので scope 外とした。
- {{T:dose-response-break-at-write-heavy-42}} **P3・新規**: 用量反応が 24 点中 1 点
  (write-heavy, 42 threads) だけ破れ、p2 が p1 を −10.7% 下回る。その機序。
