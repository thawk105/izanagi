# 段 6 変異 matrix 1 回目の裁定 (2026-09-29 19:1x JST)

## 走行の記録

- 1 回目 (mutation/final.*、35859.nqsv、Elapse 123 s): spec の等価変異の category を harness の語彙外 `equivalent` と書いた親の誤りで、harness が変異前に `category が未知` で rc=2 停止。変異 0 件。spec-probe.json は使わない。
- 2 回目 (mutation/final2.*、35877.nqsv、Elapse 615 s、commit 1ec90f6d3、spec-final2.json sha256 50e3c7a9…): baseline 28 passed。registered 19 = recorded 19、matching 16 (KILLED 15、EQ-1 SURVIVED)、不一致 3。台帳 mutation/ledger-final2.json。
- login の plan-only (mutation/plan-only.log) は harness 内の `git worktree add` が Lustre の EINTR で失敗 (rc=125、spec 検査に到達せず)。

## 不一致 3 件の判定

| ID | 結果 | 判定 | 扱い |
|---|---|---|---|
| MUT-2 三項の足し戻し検査を外す | SURVIVED | real (test の欠落、冗長 gate) | test の fixture (dc_ro_gap_sum_us=5 → 三項の和 11 > 公開間隔 10) は「D-C exceeds observed interval」の検査でも拒否されるので、足し戻し検査単独の効きを示せない。**和が間隔より小さい不一致 (例: 9 ≠ 10) を起こす fixture を足す** (fix6) |
| MUT-12 1M 固定の検査を外す | SURVIVED | real (test の欠落、過剰決定の fixture) | fixture が「selected 4M」と「1M の maxrss 1000 KB < 4 × L3」を同時に作っていて、maxrss 検査が先に拒否する。**1M が 4 × L3 を満たしたまま selected だけ 4M にする fixture を足す** (fix6) |
| MUT-16 世代更新を公開の後へ戻す | MISMATCH (KILLED、期待外 node あり) | refuted as defect / 登録の誤り (erratum) | 2 つ目の置換 (`if (!all_ready)` → `if (true)`) が MUT-18 の構造 test も赤にした。変異は登録の意図どおり殺されている。**期待 node を {test_mut16…, test_mut18…} に直す erratum** とし、最終 spec で再登録する |

## 変異の追加登録 (fix5・fix6 分)

- MUT-19 (fix5 裁定): 時間の量のパネルを線形軸に戻す → 作図 fixture の y 軸 scale 検査 test で殺す。
- MUT-2・MUT-12 は fix6 の fixture で単一理由に殺せる形に再照準する (置換は同じ)。

最終 spec は fix5・fix6 統合後の commit に対して作り直し、全件を計算ノードで 1 job に束ねて取り直す。
