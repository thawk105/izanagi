---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t503-liveness
seq: 1
title: [T-503] 変異復元耐久化の生死確認を実機で通した — 部分 bytes は出ず GO、物理ノード死は UNKNOWN のまま (コード + docs、branch worktree-dev-wave-t503-liveness)
---

## 本文

- **裁定の条件どおりに測り、GO が出た。** ユーザー裁定 (2026-08-05 /rulings) の「着手は `DW-G01`
  生死確認実験から (部分 bytes が出たら NO-GO)」に対し、Lustre 上の使い捨て root で 3 leg を
  実走した。判定は親の申告ではなく `verdict` 副 command が実成果物から導出した。
  逐語と射程は `output/insights/2026-08-06_t503-restore-durability-liveness/`。
- **L-A で部分 bytes は 1 byte も出なかった。** 別の計算ノードから見て 2 file とも完全 1 MiB。
  L-C (正の control) は「変異後 bytes の正確に半分」を検出して**書込前に**隔離したので、
  L-A の緑は空洞ではない。**L-B (物理ノード死) は実施せず `UNKNOWN` のまま**残し、
  L-B2 (walltime) を代用にしない。
- **実機でしか出ない食い違いが 3 件出た。** (1) login ノードでは `tools/pegasus/` を実行できず
  (`hooks/guard_bash.py`)、段 1 の前提 (P2) が refuted。迂回せず修復側も計算ノードへ移した結果、
  writer と recovery が別々の計算ノードになり要求をより強く満たした。(2) NQSV accounting の
  見出しと job ID 書式が想定と違い、初回 L-B2 が fail-closed した (拒否は正しい)。
  (3) recovery job が writer より先に走ると root 解決で即死した。詳細は {{F:t503-probe-realmachine-mismatch}}。
- **敵対レビュー 2 本 + 焦点再レビュー 1 本が「probe が自分の証拠を自分で検証している」型の
  所見を返した。** 閉じられる 14 件を fix し、原理的に閉じない 5 件 (kill provenance の独立 anchor、
  journal の hash-chain、既存祖先 directory の耐久性、repair 途中 crash からの再開、
  PBS 実 kill 経路を通る正例) は実装 wave へ回す。判断は {{D:t503-liveness-probe-scope}}。
- **途中版で測った run2〜run4 は採用しない。** `verdict` が probe の sha256 一致を受理条件に
  するため、版が混ざった leg 群は証拠が正当でも FAIL になる。全 leg を `2e0f76bd` で測り直した。
- 変異は事前登録 7 件すべて kill。M2 だけ台帳上 `MISMATCH` だが、これは `classify` が共有
  primitive のための過剰決定であり (`DW-M03`)、期待 node の赤は成立している。初回結果は
  書き換えずに残した。
- **wave 運営の反省**: 段 4 で「使い捨て probe を tracked にする」と裁定した結果、dev-wave の
  全装備 (単体テスト・変異 matrix・受入全走・provenance 監査) が付いてきて、`DW-G01` が
  意図した「最安の確認」より重くなった。fix は 5 巡、実験は 5 run 要した。

## 次の一手差分

### 更新

- [T-503] **P1・裁定済み → 生死確認 GO (2026-08-06 実測) → 実装 wave 起票可**:
  `DW-G01` の生死確認は済み。3 leg を同一 commit `2e0f76bd` で実走し、
  `verdict` が `GO` を導出した (L-A / L-C / L-B2 = PASS、**L-B = UNKNOWN**)。
  部分 bytes は観測されず、裁定の NO-GO 条件は成立しない。
  実装 wave は U-1〜U-10 + §9.1 必須 6 点に従う。ただし本実験が触れたのは §9.1 の 2 と、
  3 / 6 の一部だけであり、**1 (quiescence)・4 (canonical root)・5 (legacy 移行) は未接触**。
  probe が原理的に閉じられなかった 5 件は {{D:t503-liveness-probe-scope}} に列挙した。
  正本 = `docs/mutation-restore-durability-design.md` §9 / §9.1 と
  `output/insights/2026-08-06_t503-restore-durability-liveness/`
  base: 3a082533234d5ea3c9f646d1b19e76ff82824763173aaa7d4b9cc5eb0fcbe454

### 新規

- {{T:dw-g01-untracked-default}} **P2・新規・ユーザー裁定待ち**: `DW-G01` へ
  「生死確認 driver は既定で untracked の使い捨て、tracked 化は再走要件を brief に書ける場合だけ」
  を明文化する。本 wave で実測した無駄 (probe を tracked にした結果、テスト・変異 matrix・
  受入全走・admission registry 登録が付いてきて fix 5 巡・実験 5 run を要した) が根拠。
  **`docs/dev-wave/**` の byte 予算が上限のため今回は編集を見送った** — 2 行の追記で
  hard ceiling 25200 を 230 bytes 超過する。予算を上げずに入れるには既存 L2 節の削除が要り、
  削除の実施はユーザー裁定に限られる (`docs/skill-self-improvement.md` routing 3)。
  裁定してほしいのは「どの L2 節を落として空けるか」または「この明文化を見送るか」。
- {{T:t503-probe-kill-provenance}} **P2・新規**: 生死確認 probe の crash receipt に、
  scheduler 側の独立 anchor を束縛する。現状は `record-crash` が caller の wait status を
  信じるため、「READY → inspect → 実 kill 完了 → repair」の因果鎖は receipt だけでは証明できず、
  PBS accounting と commit hash の人手照合が前提として残る。実装 wave で本番機構へ持ち込む前に閉じる。
