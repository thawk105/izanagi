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

### {{F:closure-member-drift-misattributes-reds}}. 認証閉包 member を未 commit のまま測り、無関係な赤 29 件を実装差分へ帰属しかけた [手順漏れ]

- 事象: 閉包 member (`pipeline.py` / `wal.py`) を編集した working tree で焦点走を回したところ
  66 failed になった。実装を commit して閉包を再 pin してから同じ走行を回すと 37 failed に落ちた。
  差の 29 件はすべて `contract-loader-drift: disk bytes が記録 commit blob と不一致` であり、
  実装の欠陥ではなく測定条件の産物だった。
- 根本原因: live binding 検査は disk bytes を HEAD blob と突き合わせる。閉包 member を
  編集した未 commit の木では必ず drift が出るが、これが semantic gate より**手前で**落ちるため、
  本来の失敗が隠れたまま件数だけが膨らむ。
- 恒久対応: 閉包 member を編集する wave は、焦点走の前に必ず統合 commit を作る。
  赤の件数を commit 前後で比較し、差分を drift として分離してから帰属を判定する。
  **この手順を `DW-O18` へ書き足せなかった** — 同節は 995 bytes で L2 単節予算 1000 bytes に対し
  余白 5 bytes しかない。手順の追記はユーザー裁定へ返す。
- 再発検知: 閉包 member を含む差分で焦点走が大量の赤を返したとき、
  最初に `contract-loader-drift` の件数を数える。

### {{F:codex-resubmit-blocked-by-identical-prompt}}. 一過性で死んだ codex 子を同一 prompt で再投入できず 1 巡を失った [手順漏れ]

- 事象: 段 3 の敵対 2 レンズが codex 認証の 401 で出力ゼロのまま即死した。同じ prompt で
  再投入したところ `NG: 既存の完全な receipt は上書きできない` の rc=2 で起動せず、
  prompt 本文を書き換えて job-id を変えるまで再投入できなかった。
- 根本原因: job-id が prompt の sha256 から導かれるため、**内容が同じ再投入は常に同一 job-id** に
  なる。既存 receipt の保護 (正しい設計) と、一過性失敗の再投入 (正当な運用) が同じ鍵を共有している。
- 恒久対応: 一過性失敗の再投入は、prompt へ再投入の事実と新しい実測を追記して job-id を変える。
  子の意味を変えない空白追加だけの回避はしない (何度目の投入かが receipt から読めなくなる)。
  **この手順を `DW-O01` へ書き足せなかった** — 同節は既に 1275 bytes ある。追記はユーザー裁定へ返す。
- 再発検知: rc=2 と「既存の完全な receipt は上書きできない」を見たら、
  子の失敗が一過性かを先に判定し、prompt の更新で job-id を変える。

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
