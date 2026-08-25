---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1574-t1529-t1495-swo-isolation
seq: 3
title: [T-1574][T-1529][T-1495] sort SWO oracle の候補を protocol fd 非所有の worker へ隔離し、corpus を read-only arena で守った (コード + docs、branch worktree-dev-wave-t1574-t1529-t1495-swo-isolation、変異 matrix = baseline PASSED・13/13 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

D766 が求めた 2 条件 (候補が protocol write fd を一度も所有しない / 実 `WriteElement<Tuple>` の
snapshot 対象 memory への write を強制拒否または trusted 側で観測) を実装し、実測で確かめた。
採用した機構と保証範囲は {{D:swo-isolation-boundary}}、依存 manifest の置き場所は
{{D:swo-dependency-manifest-location}}、assert 設定の択一は {{D:swo-oracle-assert-strictness}}。

**着手前に裁定の前提を実測し、2 つが覆った。**

- A1 は生きていた。corpus を壊すだけの候補は REJECT、そこへ
  `trusted_snapshot = snapshot_corpus();` を 1 行足した候補は PASS。候補は 1 行で防壁を消せた。
- A2 は現 HEAD で再現しなかったが、**直ったからではない**。ccbench は masstree を
  `./configure --disable-assertions` で建てるため、oracle の翻訳単位で NDEBUG 依存の上流 assert が
  消えていた。`-DFORCE_ENABLE_ASSERTIONS=1` を足すと A2 は確定的に再現した。
  つまり同じ候補の判定が依存をどう configure したかで変わる状態であり、proof chain が機体依存だった。
- T-1529 / T-1495 の「ファイルごと skip」「26 件が `config-h-missing` で一括失敗」も陳腐化していた。
  計算ノードでは 62 件全緑だった。実際の欠陥は赤ではなく、機体上の repo 外 cache がある間だけ
  緑になる暗黙依存と、cache が無いと静かに skip して防壁が消えることだった。

**保証の言い方を 1 つ狭めた。** 実装当初は `SIGSEGV` / `SIGBUS` を corpus write と断定していたが、
`waitid` は fault address も access type も返さない。null 参照や arena 外の不正 pointer も
同じ材料になるため、一般の execution fault として記録する形へ改めた。
8 つの allocation class がすべて拒否されることは変わらず、変わったのは台帳に載る主張だけである。

**ユーザーへ返す裁定事項が 1 件ある。** この境界を完成させても、候補が報告した関係行列が
その comparator の真の関係である保証はない。`relation[]` と走査 root は候補と同じ
address space の書込み可能領域に残る。閉じるには候補を検証済み IR へ制限して trusted interpreter で
評価するか `ptrace` 相当で戻り値を採取するかが要り、D766 が却下したのと同じ規模の scope 拡大になる。
本 wave では非主張を receipt の exact field として固定するに留めた。詳細は {{T:swo-relation-provenance}}。

**段 3 と段 6 でレンズの判定が割れ、実測が一方を支持した。** 段 6 で境界レンズは
「fd 非所有の負例が実経路を故障注入していない」と指摘し、整合レンズは「MUT-5 は kill される」と
判定した。変異 probe を実走すると MUT-5 は identity churn だけで kill され、機構固有の落ち先を
1 つも持たなかった。境界レンズが正しかった。実効 gate を新設して閉じた。
この読み違いの構造は {{F:identity-churn-over-determines-mutation-kill}}。

**棄却した所見。** 整合レンズの「D766 は同一 wave での実装を禁じており未裁定の scope 拡張である」は
誤読として退けた。D766 の「本 wave ではコードを変更しない」は D766 自身の wave を指し、
同じ決定文が「強い隔離と同じ閉包で再設計する」と将来の閉包を明示している。
同レンズの「memo を消すのが小さい」も D636 未読による誤りとして退けた。D636 は memo と
独立完全性検査を規律 2 の必須要件として裁定済みで、消すと real-repo 直列鎖の復活か
完全性検査の喪失になる。

**エージェント工数。** codex 子 12 本 (plan 1、consult 2 + 拒否による再投入 1、author 3、fix 7、
review 2)。うち 1 本は段 3 で provider の安全フィルタに拒否された。原因は親の prompt で、
「候補になったつもりで bypass を探せ / 攻撃手順を C++ で書け」という攻撃者視点の書き方が
sandbox 脱出の exploit 開発と判定された。同じ資料を渡した整合レンズは通っている。
防御側の設計レビューとして書き直して通した。

**セッション異常が 3 件あった。** (1) 変異本走を 2 件目で中止させたのは親のミスで、
走行中に repo へ spool fragment を書き未追跡 file を作ったため harness が fail-closed した。
repo 外へ退避して `--resume` で継続した。`--resume` は `--attempt-out` に既存の通常 file を要求する。
(2) 待ち手が producer 生存中に「完了」で複数回戻った。落ちた待ち手と完了は見分けが付かないので、
毎回 process と成果物で実状を確かめた。(3) F457 を踏んだ。詳細は failures 側に書いた。

**実測値。** 焦点走 610 passed / 1 skipped (skip は `GROWTH_TEST_HOLDS` の
`explicit-user-command-only`)。変異 matrix は baseline PASSED、13/13 KILLED、
SURVIVED 0、MISMATCH 0、TIMEOUT 0、全変異で期待 node 集合と観測 node 集合が完全一致。
fixture として masstree の pin 済み source 99 file (1152438 bytes) と生成 `config.h` を取り込んだ。

## 次の一手差分

### 完了

- [T-1574] 隔離境界を実装し、A1 を閉じ、A2 を assert を殺さない向きで閉じ、protocol を v3 へ、
  contract を v4 へ上げた。保証しない範囲は receipt の exact field として固定した。
  remaining: none
  base: b952b26d5ca09b7d442c95b43fa4b3b915ee5031cd969979abf84cbe213311f9
- [T-1529] masstree 依存を test 所有の fixture へ移し、build 残骸への暗黙依存と
  依存不在時の静かな skip を撤去した。`libjson.a` と `*.o` の要求も外した
  (oracle の compile は archive も object も link していないことを実測)。
  remaining: none
  base: 9ee1c894349013935aba189200b88238322cf4580fcbbcfd9e8c3a20dc13380b
- [T-1495] `outcome='config-h-missing'` の一括失敗は現 HEAD では再現しないことを実測し、
  真の欠陥である repo 外 cache への暗黙依存を fixture 化で閉じた。
  remaining: none
  base: c18595773adec0a59013c6d346b01dfa6425edf08db55ef93bebfe6e8557eade

### 新規

- {{T:swo-relation-provenance}} **P1・ユーザー裁定待ち**: sort SWO oracle が報告する関係行列の
  provenance を保証する境界を入れるか。現状は候補が `relation[]` と走査 root を書き換えられ、
  broker は「trusted wrapper が comparator を呼んで戻り値を報告した」のか
  「候補が同じ形の観測を直接作った」のかを区別できない。閉じるには候補を副作用のない検証済み IR へ
  制限して trusted interpreter で評価するか、broker が `ptrace` 相当で戻り値を採取するかが要る。
  どちらも非同値な大幅 scope 拡大であり、D766 が同じ理由で即実装を却下している。
  現状は非主張を receipt の exact field で固定するに留めてある。
- {{T:swo-oracle-allowlist-exact-gate}} **P2・新規**: seccomp allowlist の exact 集合を固定する
  検査を置く。現在の検査は hard-code した forbidden syscall が `allow_syscall` に現れないことだけを
  見ており、将来 未列挙の syscall が allowlist へ加わっても緑のままになる。
  段 6 の境界レンズが backlog として指摘した。
