---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1348-c09-c10-consumer
seq: 1
title: 8c 前提条件 C09 / C10 の consumer を acceptance へ配線した — 登録済み build 正例は前提条件 1 が未実装である限り原理的に緑にできないと実測で確定した (コード + テスト + 記録、branch worktree-dev-wave-t1348-c09-c10-consumer、変異 matrix = baseline PASSED・11/11 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「C09 / C10 を SATISFIED まで持っていく」だったが、評価器 `_evaluate_c09` /
  `_evaluate_c10` に SATISFIED を返す枝は存在しない。両者の成功枝はいずれも
  `EVIDENCE_UNDEFINED` + `completion-proof-not-machine-checkable` である。
  親はこれを到達目標と読み替え、段 1 brief の `(P1)` として攻撃対象に登録した。
  段 2・段 3・段 6 の子 4 本がいずれも同意し、反証は出なかった。到達を実測で確認した。
- **登録済み build report の acceptance 正例は緑にできない。**
  `trial_registry.HOLDOUT_BINDINGS` の workload (`rr80` / `rr20`) と
  `p3_autonomous_workload_trial.WORKLOADS` (`ycsb-a` / `ycsb-b` / `ycsb-c`) は互いに素であり、
  登録 manifest の build report は `assert_campaign_layer3_chain` の
  「workload is not producer-supported」で必ず fail-closed する。これは前提条件 1
  (H1 / H2 workload 定義の未実装 = C01 が未充足である理由そのもの) の帰結であって
  本 wave の実装不良ではない。段 6 のレビュー 2 本ともこの親判断を反証できなかった。
  fixture の workload を偽装して緑にすることはせず、
  「acceptance が層3 gate へ到達し exact な理由で fail-closed する」ことを pin する形へ書き直した。
  C10 の 12 field 束縛の正例は unit 段で緑である。
- 段 3 の敵対レンズ 2 本と段 6 の敵対レビュー 2 本が、実装を 2 度覆した。
  - 受領証の cross-binding aggregate を 1 値だけ保存する設計は、任意の 64 桁値へ差し替えても
    検証が通るため「C10 束縛済み」という主張を独立検証できない。per-trial の leaf を保存し、
    top-level の aggregate を leaf から再計算して照合する形へ変えた ({{D:cross-binding-receipt-leaves}})。
  - 権威 verifier が WAL の bytes を digest 照合した後、`read_records_checked` が
    ディスクから WAL を読み直していた。照合済みの内容ではなく未検証の内容から
    projection と receipt hash を作れる経路であり、検証済み bytes から record を構成する形へ直した。
- 段 5 の Codex 実装子が `max_cli_reported_tokens` の既定 1,000,000 に当たって SIGTERM で中断した。
  model call は 181 / 700 で余裕があり、**上限は model call ではなく token 側で先に尽きた**。
  差分 9 file / +1435 行は作業木に残ったため、上限を 8,000,000 へ上げた継続子で回収した。
  段 5 実装子には `--max-model-calls` だけでなく `--max-cli-reported-tokens` も上げる必要がある。
- 事前登録した 11 変異の probe 走は KILLED 5 / MISMATCH 6 / **SURVIVED 0** だった。
  MISMATCH はすべて期待 node 集合が実際より狭かったためで、検出漏れではない。
  実測 node を権威として再登録した本走は 11/11 KILLED である。
  ただし probe は検出力の事実を 2 件示した — M09 (WAL 被覆検査の削除) と
  M10 (`artifact_refs` の全件再読を 1 件目へ縮小) では、**そのために書いた専用の負例が発火せず**、
  隣接ゲートと正例が代わりに捕えた ({{F:masked-dedicated-negative-control}})。
- scope 外として実装せず、ユーザー裁定へ返す設計択一を 4 件残した (下記「次の一手差分」の新規項)。

## 次の一手差分

### 新規

- {{T:do-build-external-binding}} **P2・新規**: `do_build` を manifest または launch admission へ
  束縛する。現状は report と run-start の一致しか検査されず、supervisor の自己申告のまま
  C09 / C10 の build 枝を回避できる。manifest schema の変更を伴うため本 wave の scope 外とした。
- {{T:campaign-root-prereg}} **P2・新規**: campaign root を実走前に manifest へ焼く。
  本 wave は「report の run root から導いた output root と一致すること」までを実装した。
  実走前の事前登録は未実装である。
- {{T:c10-authority-scope}} **P3・新規**: lifecycle 台帳を C10 の authority に含めるかを裁定する。
  本 wave は acceptance receipt と検証 CLI を authority とした。
- {{T:c01-blocks-c09-build-positive}} **P1・新規**: 前提条件 1 (H1 / H2 workload 定義) を
  8c supervisor へ実装し、登録済み build report の acceptance 正例を緑にする。
  現状は `HOLDOUT_BINDINGS` と `WORKLOADS` が互いに素で、C09 の build 枝は
  fail-closed 到達の証明までしか書けない。
