---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t459-resume-topology
seq: 1
title: crash 後 resume の二重 build_start を recovery-abort で閉じた — 自動回復は build 完了前の crash に限定し、設計択一 2 件と実装待ち 5 件を返す (コード + docs、受入 6512 passed、変異 14/14 KILLED、branch worktree-dev-wave-t459-resume-topology)
---

## 本文

- **[T-459] の欠陥は段 1 で実測再現した。** `build_start`(attempt A) だけを書いた WAL は
  `replay` が「未終端・再評価対象」と返す一方、再評価が書く 2 本目の `build_start` で
  `AttemptTopologyError` になる。`EvalState.resumable` の宣言 (「リカバリで破棄して再評価すべき」)
  と attempt topology 検査が正面から矛盾していた。波及は variant 単位でなく campaign 単位
  (artifact admission が同じ validator を直呼びするため)。
- **既存成果物は未被害と実測した。** repo `output/` の WAL 30 本に未終端 attempt 0 件、
  `build_attempt_id` を持つ record も 0 件 (全部 pre-policy 形式)。**この走査は repo `output/` に
  限る** — 外部 exploration root と明示 `output_root` は未走査であり、不在の証明ではない。
  段 3 レンズの独立走査でも repo exploration WAL 0 本、`IZANAGI_EXPLORATION_OUTPUT_ROOT` 未設定、
  job root WAL 0 本だった。
- **段 4 の親裁定を段 6 レビューが 1 点反証した (記録に値する手戻り)。** 親は「並行実行が起きても
  生存 peer の後続 record は topology が loud に拒否する」と書いたが、`verify_done` / `bench_done` は
  attempt に束縛されないため、回復後に peer の RED signal だけが静かに受理される列が構成できた。
  対応は lease の新設ではなく**自動回復の対象を狭めること**とし、`build_start` 以後にその attempt の
  record が 1 つでもあれば回復しない形へ変更した ({{D:incomplete-attempt-recovery}})。
- **本 wave が自動回復するのは「`build_start` 直後〜build 完了前に落ちた attempt」だけである。**
  それ以外 (build 完了後・trigger 系 campaign・回復回数上限・既存 topology 違反・
  単一 variant に複数 active・truncated tail 併存) は 1 byte も書かずに停止し、人手介入を要する。
  **trigger 系 campaign では自動回復が効かない**ことを射程として明記する。
- **運用前提:** resume は旧 evaluator の終了確認後に行う。campaign 全体を覆う実行所有権
  (lease) は本 wave では導入していないため、これは機械強制でない運用契約である。
- **変異 matrix は 14/14 KILLED、baseline PASSED** (`repo_head=d575021f`、spec sha
  `eeb4d99c…`)。**初回走行は 5 件が MISMATCH だった** — MU-1 / MU-2 / MU-4 / MU-5 / MU-7 の
  実赤 node が事前登録の上位集合で、登録が過少だった。事前登録 node はすべて実際に赤くなっており
  生存はゼロ。初回台帳は `mutation-ledger-run1-erratum.json` として保存し、実測 node へ
  再登録して確定走行した。MU-1 / MU-2 は生成側と suffix 検査の二層が同じ入力を拒否するため
  **冗長 gate**であり、単一 gate の証拠には数えない。
- **受入全走 3 回。** (1) 実装時点 6467 passed / 20 skipped (request `891865`)、
  (2) fix 1 巡目 2 failed (内訳は下記)、(3) main 取り込み後 **6512 passed / 20 skipped / 0 failed**
  (確定値)。(2) の 2 件は「新テストの fixture 不備による実赤 1 件」と「F57 の再発 1 件」で、
  後者は単独再走で緑 (request `891949`)。
- **敵対レビューの棄却なし・scope 外裁定 7 件。** 段 3 で 10 件、段 6 で 11 件の所見が出て、
  すべて real と裁定した。うち本 wave で塞いだのは 9 件 + fix 2 巡、残る 7 件は設計択一または
  独立欠陥として下の「新規」へ起票した。焦点再レビューは残 blocker なしと判定した。
- 逐語 (brief / plan / 敵対 2 本 / 裁定 / 実装報告 / レビュー 2 本 / fix 裁定 / 焦点再レビュー /
  変異 spec・台帳) は `output/insights/2026-08-06_t459-resume-topology/` に凍結した。
- **段 8 の改善候補 2 件は byte 予算に収まらず取り下げた (記録のみ)。** (a)「受入全走の隣で
  子 process を走らせない」を `DW-O18` へ、(b)「実赤が期待を包含する MISMATCH は生存ではなく、
  erratum を残して実測 node で取り直す」を `DW-M08` へ統合しようとしたが、追記後に
  `docs/dev-wave/` の byte 予算と hard ceiling を超えた。**安全義務を削って捻出せず、
  予算引き上げも提案しない** (自己改善契約)。(a) の実体は F57 の再発記録に、(b) の実体は
  本エントリと insights の erratum 節に残る。

## 次の一手差分

### 完了

- [T-459] crash 後 resume が未終端 attempt を二重 `build_start` にする欠陥を、identity 照合済み
  seam の recovery-abort で閉じた。自動回復は build 完了前の crash に限定し、それ以外は
  fail-closed。設計は {{D:incomplete-attempt-recovery}}。
  remaining: none
  base: 0d23c5d7c285835fa1d3aa668db9b16048739ff98c6c6d1907f255d9712c1425

### 新規

- {{T:campaign-execution-lease}} **P2・ユーザー裁定待ち**: campaign 全体を覆う実行所有権
  (lease) の要否と形。現状は同一 campaign への並行 run を機械的に排除できず、回復が生存
  evaluator の attempt を中断扱いにしうる。推奨は run 全体で専用 lock を
  `LOCK_EX|LOCK_NB` 保持する形 (process 死で OS が解放するため stale lease を作らない)。
  同一ホスト限定である点と、同一 process の二重取得を避ける配線が論点
- {{T:recovered-campaign-certifiability}} **P2・ユーザー裁定待ち**: recovery 済み campaign を
  certifying とみなすか。WAL は hash chain を持たないため、recovery を許すと「二重 start で
  恒久拒否だった WAL」を救済できる列が 1 つ増える。admission decision へ recovery の可視化を
  入れるか、recovery 済みを non-certifying に落とすかの択一
- {{T:attempt-local-signal-binding}} **P2・新規**: `verify_done` / `bench_done` を attempt へ
  束縛し、consumer 側も commit された attempt の record だけを射影する。現状は variant 単位の
  帰属のため、crash した attempt の測定値が別 attempt の commit と結び付きうる。本 wave は
  回復対象を狭めて回避しているだけで、恒久解ではない
- {{T:trigger-recovered-provenance}} **P3・新規**: trigger proposal provenance へ回復済み
  attempt の記録を足し、admission の全 start 一致検査を通せるようにする。無いと trigger 系は
  crash 後に自動回復できないまま
- {{T:guided-nobuild-pseudo-wal}} **P3・新規**: guided の no-build pseudo-WAL は attempt schema を
  持たず、未終端 trial が二つ目の start を書きうる。回復の対象外なので別 schema 問題として扱う
- {{T:plotter-admission-gate}} **P3・新規**: 作図系が admission を経由せず WAL を直接読むため、
  topology 違反の WAL からも図と provenance が出る
- {{T:replay-read-only}} **P3・新規**: `wal.replay` は現在 trigger orphan の tombstone を書く。
  read 経路を真正な read-only にし、書き込みを resume seam へ移す
