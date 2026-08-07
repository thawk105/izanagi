---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t244-8c-wiring-design
seq: 2
---

## {{D:wiring-preconditions-8c}}. 8c 結線の前提 5 点を exact contract として設計し、発行 3 条件は 0/3 のままと確定する

**決定:** U-10 批准後に唯一起票できる設計 wave として、8c 自律 trial への origin ledger 結線の
前提 5 点 — source closure / result-evidence の exact 化 / 32 mask producer topology /
launch admission が発行する origin binding capability / 失敗・crash の event 対応 — を
`docs/phase3-8c-wiring-design.md` に設計する。実装は行わない。

設計の中核は次の 5 点である。

1. **cell 同一性の閉包は「同一 authority blob 内」までしか保証できない。** 現 loader が拒否できるのは
   その範囲の 4-tuple 重複だけで、series 横断の一意性は実装に存在せず、repo 内台帳で作ることは
   D211 が拒否済みである。したがって下流 consumer に
   `(authority_blob_sha256, origin_id, cell_key)` の 3 つ組 scope を義務づける。
   `cell_key` 単独での集約は同じ cell の二重計上を招く。
2. **物理実行と台帳を結ぶのは ledger ではない。** ledger は evidence digest を dereference しない。
   結ぶのは物理実行点で発行する create-only の result-evidence record と、それを読む formal
   consumer である。consumer は member→record の全域性だけでなく **record→物理 attempt の単射**
   (attempt id 相異・WAL 区間非重複・WAL の trigger binding 一致) を必須とする。
3. **validation 32 行は 1 batch に強制される。** P6 の一括 commit 条件と 1-open-batch FSM により
   分割できず、source 行を別 batch にすると行数下限 2 を満たせない。よって
   fresh origin・exact 1 batch・33 member (source 1 + mask 0..31) が唯一の成功 topology である。
4. **既存 6 event で意味は閉じるが、durable な recovery material が要る。** 足りないのは crash event
   ではなく、再送 payload を byte-for-byte 復元する run plan / recovery envelope である。
   state commitment は authority 全体の global CAS なので、次 event の base に直前 receipt の
   `resulting_state_commitment` を連鎖させてはならない (`current_state_commitment` を使う)。
5. **発行 3 条件はいずれも成立しない。** V-2 は artifact と consumer が未存在、topology は 33 物理
   attempt を生む producer が未存在、許可経路は **production runtime の初期化経路そのものが
   存在しない** (初期化は fixture 専用で、production は明示拒否されている)。
   本設計を land しても本番 authority の provisioning は行わない。

**理由:**

- U-10 批准パッケージ §7 が「次に起票できるのは実装 wave ではなく設計 wave」と定め、
  閉じるべき 5 点を名指ししている。本決定はその履行である。
- 敵対 2 レンズが独立に NO-GO を返し、blocker 8 件・must-fix 8 件を挙げた。親は主要 5 件を
  現物で裏取りし、すべて real と裁定した。特に「末尾の全 tombstone batch が certifiable seal を
  通る」「同一 mask の重複行は campaign ループが物理実行しない」「production runtime を初期化する
  経路が無い」の 3 件は、設計を書かなければ実装 wave の途中まで露見しなかった。
- 設計だけを先に確定させることで、実装 wave の受入条件 (前 wave の再起票要件 8 件のうち残り 5 件と、
  未着手の completeness / 材料レポート renderer の 2 層) を事前に固定できる。

**却下した選択肢:**

- **設計を書かずに実装 wave へ進む** — 発火経路が無いことは既に実測済みで、`DW-G04` に反する。
- **validation を複数 batch へ割る / 行数下限を 1 へ下げる / source の 2 行目を tombstone で埋める** —
  順に FSM 違反、正しさゲートの緩和、下限を実行せずに満たす恒真化である。
- **create-only を writer 認証とみなす** — `O_EXCL` は上書きを防ぐだけで最初の書き手を認証しない。
  保証限界として明記し、権限分離の是非は裁定へ返す。
- **ledger の terminal `certifiable` を certified 選択への昇格根拠にする** — launch admission の
  `certifying` は False のままであり、2 語は同義ではない。
- **repo 内で series 横断の重複を調べる** — D211 と矛盾する。
