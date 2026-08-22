---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-lease-serialization-ban
seq: 1
---

## {{D:lease-wait-unreachable}}. 受入 lease の待ち機構を実装から除去し、lease 状態で受入投入を止めない

**決定:** D662 決定 1 (受入 lease の待ち行列は廃止する) を、散文の禁止ではなく
**到達不能性**として実装する。

1. `tools/dev_wave_wait.py` の acceptance は、投入前 claim を 1 回だけ行う。待ちループは
   関数ごと削除し、経路から到達できない。`--lease-optional` と `--poll-seconds` は後方互換で
   受理する no-op であり、flag・環境変数・引数のいずれでも旧挙動へ戻せない。
2. `tools/wave_land_window.py` の `claim()` は待ち札 (ticket) を作らず参照もせず、
   `queued` を返さない。lease が空いていれば旧札の有無に関係なく即取得し、
   他 wave が保持中なら即 `held` を返す。順番待ちと head-of-line blocking は存在しない。
3. **lease の状態を理由に受入投入を止める条件を新設してはならない。** claim 結果が壊れていても、
   lease directory が壊れていても、受入は進む。これは「一つの wave の失敗・競合・既知の不具合が
   全体を止めてはならない」という D662 の核心の原則の帰結である。

**維持するもの:** land の権威は 1 bit も変えない。`tools/dev_wave_land.py` の協調 lock、
ff-only、全史 provenance 監査、fold の lock 内直列化はいずれも非対象である。
**fold の lock は採番の正しさに必要な直列化であり、受入 lease の直列化とは別物である。**
受入 receipt の integrity 条件 (走行後 clean、index flag 検査、走行前後 fingerprint 一致、
main SHA 不変性) は未取得経路でも発火し、`receipt.lease_holder` は
wave slug の digest のままで land 側の照合を通る。
`stale-held`・`unavailable`・自己 holder の検証失敗は従来どおり fail-closed で拒否する。

**理由:**
- D662 は 2026-08-22 の裁定だが、対応するコード変更は opt-in flag に留まっていた。入口 command
  (常時読まれる層) は同じ日に「lease を取れたときだけ投入せよ」と命じたままで、
  散文だけの禁止が実際に破れることが実測された。
- 待ち行列は lease が空いていても新着 wave に `queued` を返す。混雑下ではこれが
  「空いているのに誰も進めない」状態を作る。待ち札の生存窓は 300 秒で、
  その間に到着した wave がすべて足止めされる。
- 恒真な pin では守れない。除去に伴い、待ちが復活したら落ちる pin
  (単発 claim・sleep 0 回、free lease が旧札を無視、未取得経路でも integrity 検査が発火、
  未取得で foreign lease を release しない) を同時に置いた。

**却下した選択肢:**
- **docs だけで「常にフラグを付けろ」と定める** — 同型の破れが既に起きている。
  フラグを付け忘れた呼出しが旧経路へ落ちる余地を残す限り、制限したことにならない。
- **既定値の反転に留め blocking 経路を残す** — 残った経路はいずれ再導入の足場になる。
  named flag を 1 つ足せば戻せる状態は「厳しい制限」ではない。
- **壊れた claim 結果を fail-closed で拒否する** (段 6 敵対レビューの提案) — lease directory の
  破損という一点で全 wave の受入が止まる。まさに D662 が否定した設計であり、実害も無い
  (未取得経路は claim payload の holder と main SHA を採らず、自分で計算した値を使う)。
- **公平性 (FIFO) を別の機構で維持する** — 待ち行列を消す目的が公平性の放棄そのものである。
  D662 は「止めないこと」を公平性より優先すると裁定している。
