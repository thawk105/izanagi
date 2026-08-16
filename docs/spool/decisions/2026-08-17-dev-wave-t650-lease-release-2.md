---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t650-lease-release
seq: 2
---

## {{D:land-terminal-lease-release}}. land が到達点ごとに解放可否を宣言し、終端でだけ受入 lease を自分で解放する

**決定:** `tools/dev_wave_land.py` は結果へ 2 つの直交する述語を持たせ、両方が成立するときだけ
受入 lease を自分で解放する。

- `release_safe`: main・fold transaction・mutation が quiescent で、lease を手放しても
  別 wave が中間状態の上で受入を始めないか。
- `retryable_same_request`: 同じ request をそのまま再実行して成功しうるか。
- 解放条件は `release_safe and not retryable_same_request` のみ。

**両述語の既定は False とし、明示的に宣言した到達点だけが値を上げる。** rc からは導出しない。
未宣言の経路・予期しない例外・中断はすべて自動的に保持側へ落ちる。

**解放の権限は 3 段で束縛する。** 受入 receipt bytes の digest、wave slug、
lease payload の `main_sha`。`tools/wave_land_window.py` の `release()` へ optional な
`expected_main_sha` を足し、指定時だけ holder 一致に加えて `main_sha` 一致を unlink の条件にする。
未指定時の挙動は現行と完全に同一とする。

**core 結果 JSON は解放より前に stdout へ flush し、解放結果は stderr へ 1 行で出す。**
JSON へ入れるのは 2 つの述語だけで、解放結果は入れない。JSON は compact separators で出力する。

**land の受理条件・全史 provenance 監査・ff-only・fold・lock・lease TTL・待ち札 FIFO・
通知の意味論は変更しない。**

**理由:**

- 解放は入口の契約文が親 (LLM セッション) へ要求するだけで、機械が保証する箇所が 1 つも無かった。
  D239 は claim〜release を包む機械的 transaction が無いことを受容した限界として明記し、
  D253 は「release 忘れが連鎖すれば待ち時間が lease TTL に比例する」と明文で予見していた。
  その限界が実害として発火したため、受容をやめる。
- **rc は解放安全性を表現できない。** 同一 rc に決定的拒否と一時障害の両方が畳まれている経路がある。
  全史 provenance 監査の rc は、checker が違反を返した場合だけでなく、timeout・中断・
  binding 読取失敗・dispatch の infrastructure failure・signal 由来の負値も同じ値へ畳む。
  したがって checker が違反を報告したと言い切れる終了 code だけを決定的として扱う。
- **既定を保持側に倒すのが正しさ側である。** 終端を再試行可能と誤る最悪値は
  「TTL または誤った loop が続く間の停止」であり時間損失にとどまる。一方、再試行可能・未知・
  中断状態を終端と誤る最悪値は「元の lander が再開可能な間に排他を解き、別 wave の受入を重ねる」で、
  正しさに隣接する。安全側は可用性側ではない。
- **rollback 成功後は解放しない。** ref・index・worktree・journal・symbolic HEAD の 4 状態を
  安く証明できないため、証明できるまでは保持する。
- **fold の finalize 失敗と active recovery 失敗は再試行可能だが解放安全ではない。**
  同一 request の recovery が実装されている一方、journal が open のままだからである。
  再試行可能性と解放安全性を同じ 1 bit へ畳まない理由がここにある。
- 解放結果を JSON へ入れないのは、main と canonical 台帳が進んだのに結果 JSON が
  書かれないまま終わる窓を作らないため、および通知経路の JSON 上限へ近づけないためである。

**却下した選択肢:**

- **claim から release までを 1 つの process の finally へ束ねる** — 起票時の想定はこれだったが、
  束ねると land を駆動する呼び手の形を全部変えることになる。land の終端に置けば
  呼び手を変えずに同じ保証が得られる。
- **rc の allowlist で終端性を決める** — 同一 rc に決定的拒否と一時障害が畳まれている以上、
  rc では表現できない。到達点ごとの宣言に替えた。
- **未知の rc を解放側の既定にする** — 可用性側であって安全側ではない。上記理由のとおり。
- **lease TTL の短縮・heartbeat の追加・fencing token の発行** — TTL は生存判定と最大窓の
  両方を兼ねており、短縮すると遅い holder から lease を奪う側の危険が増す。fencing token は
  別途見送り済みである。本決定は TTL に触れない。
- **`release()` の holder 照合だけに頼る** — 同一 slug の別 invocation が取り直した lease を
  古い invocation が削除できることを、敵対レビューが I/O seam 実行で実測した
  (別 slug は unlink 0 回、同一 slug の新世代は unlink 1 回)。`main_sha` の
  compare-and-delete を足して塞ぐ。

**受容した限界:** 別 invocation が**同じ main_sha で**claim し直した場合は区別できない。
完全な世代束縛には claim 側の generation 発行が要り、それは別途見送り済みである。
また land へ到達しないまま終わる経路 (argparse 失敗・context 死亡・SIGKILL) は本決定では塞がらない。
