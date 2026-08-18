---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1286-commit-receipt
seq: 3
---

## 新規

### {{F:receipt-gate-vacuous-under-green}}. receipt を要求する門を実装し全緑になった状態で、門は開いたままだった [恒真ゲート]

- 事象: 全 `STAGE_COMMIT` producer へ receipt を要求する実装を入れ、親が実走した焦点走 23 file が
  1388 passed / 0 failed になった。その状態で
  `VerifyResult(trace_dir="never-read", serializable=True, n_txns=1)` を手で構築して issuer へ
  渡すと live receipt が発行でき、trace parser も verifier entrypoint も一度も呼ばれなかった。
  同型が 3 面あった (primary issuer・replay issuer・capability の operation 非束縛による再利用)。
- 根本原因: 「receipt を要求する検査を足す」ことと「receipt が verifier 由来である」ことを
  同一視した。門の入力を呼び手が生成できる限り、門は入力の形式だけを検査する飾りになる。
  テストも同じ呼び手側の経路で receipt を作るため、検出力ゼロのまま全緑になる。
- 恒久対応: {{D:commit-receipt-issued-inside-verifier}}。capability は実 verifier 走行の
  内側でだけ生成し、operation・variant・workload・sink・lock を焼き込んで一回消費する。
- 再発検知: 呼び手が構築した検証結果オブジェクトから receipt に到達しないことの負の対照と、
  issuer / sink の call-site census を production 全走査で置く。
  **緑の焦点走を「塞がった証拠」と数えない。** 門を壊す変異が赤を出すことでのみ検出力を主張する。

### {{F:concurrent-wave-collision-by-plan}}. 並行 wave との編集面衝突を相手の plan で判定し、着地結果と食い違った [手順漏れ]

- 事象: 並行 wave の段 2 プランが closure 定数・exact-list pin・資格 identity を編集すると
  書いていたため、段 4 で「本 wave の単位 C と同一編集面で衝突する」と裁定し、
  実装順序を組み替えた。実際にはその wave が land した差分はこれらを 1 件も含まず、
  両側が触った file の積集合は空だった。裁定の前提が着地結果では成立しなかった。
- 根本原因: 衝突判定の一次資料を相手の**計画**に置いた。plan は wave 中に反証・縮小され、
  着地するとは限らない。branch の現差分がゼロなことも「触らない」の証拠にはならない
  (起動直後は必ずゼロである)。
- 恒久対応: 衝突判定は相手が land した後の `git diff --name-only <base>..main` と
  自分側の編集面の積集合で行う。未 land の相手については「衝突しうる」までしか言わず、
  受入直前に着地差分で再判定する。
- 再発検知: 段 4 で並行 wave との衝突を裁定に使うときは、根拠が plan か着地差分かを
  裁定文に明記する。plan 根拠のまま受入へ進まない。
