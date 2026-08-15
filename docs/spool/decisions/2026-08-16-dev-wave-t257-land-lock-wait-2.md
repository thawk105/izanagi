---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t257-land-lock-wait
seq: 2
---

## {{D:land-lock-bounded-wait}}. land の排他 lock を共有 deadline の有界待機にし、取得後に束縛を再検証する

**決定:** `tools/dev_wave_land.py` の `_acquire_land_lock` は、`LOCK_EX | LOCK_NB` を
equal jitter の backoff で反復する **有界待機**にする。上限は module 定数の 180 秒とし、
CLI flag も環境変数も作らない。deadline は `land()` で **1 本だけ**作り、初回取得と
provenance 監査後の再取得へ同じ絶対値を渡す。再取得へ新しい予算を給付しない。
上限到達時は `RC_LOCK_BUSY = 11` / status `lock-busy` / main 無変更を維持し、
`LandResult.reason` にだけ phase・待機実績・上限を載せる。結果 JSON の schema は変えない。

`flock` 成功直後・critical check より前に、main worktree / wave worktree / common git-dir を
**現在の path から** `O_NOFOLLOW` で開き直して保持 fd と inode 照合し、**再束縛した common dir から**
lock path を `follow_symlinks=False` で stat して保持 lock fd と照合する。metadata predicate
(regular / uid / nlink 1 / group-world writable でない) も両側へ適用する。不一致・path 消失・
symlink はすべて `RC_IDENTITY = 22` とし、`lock-busy` に畳まない。
lock fd の所有権は caller が取得前から持つ handle に置き、timeout・例外・割込み・identity 拒否の
すべてが単一の cleanup 経路を通る。

**待機中に main HEAD・control snapshot・audit 値を読まない。** 取得後に初めて `_locked_preflight`
を呼ぶ。`stale-main` の条件文と理由文は変更しない。

**本決定は D102 決定 (2) の「短時間 **nonblocking** lock」と、D254 理由文が既存契約として挙げた
「lock 保持中は 2 秒未満で `lock-busy` を返す」だけを supersede する。** D102 の他の決定
(lock を共有可変検査より前に取る順序、merge child だけへの fd 継承、長時間の review・テスト中は
保持しない、非接触例外の範囲) と、D254 の他の結論 (二相化、receipt 束縛、`already-landed` の
no-op と recovery を監査から除外、逃がし道禁止、timeout 480 秒) は**すべて維持する**。
待機は lock の**保持**時間を 1 秒も伸ばさない。変わるのは待ち手の応答時間だけである。

**理由:**
- ユーザー裁定が択 (a) + (d) を採り、検査を省かずに取り込み直しを減らすと定めた。
  段順入替と影響範囲による再走免除は同じ裁定で不採用になっている。
- 予算を 2 箇所で共有するのは、最悪待ち時間を予測可能にするためである。取得点ごとに別予算だと
  最悪が 2 倍 + 監査 480 秒になる。
- 上限 180 秒は**安全保証ではなく独立に裁定した availability cap** である。前景 600 秒にも
  受入 lease の残 TTL 保証 300 秒にも収まらない (監査 480 秒だけで既に超える)。
  実測した lock 保持時間の下界は median 6 / p99 18 / max 145 秒で、観測 max を覆う桁として選んだ。
  これは下界からの導出であって上限の証明ではない。
- **取得後の再束縛は待機が開けた穴の補償である。** 従来は open 直後に 1 回だけ試すので
  fd と path の乖離窓は実質ゼロだった。待機はこれを上限まで広げる。窓を作る変更が補償も持つ。
  実装は既存の provenance checker 束縛検証と同型で、新しい型を導入していない。
- knob を作らないのは、待ち上限が受理集合を広げないとしても、値を外から変えられる経路が
  lease や外側 deadline との整合を静かに壊すためである。

**却下した選択肢:**
- **`SIGALRM` + blocking flock** — process 全体の handler を奪い、main thread 制約と
  既存 subprocess 待機に干渉する。
- **blocking flock を thread / 子 process で包む** — 安全に cancel しにくく、子 process 案は
  D102 の「merge child だけへ fd を継承」に反する。
- **ticket file による FIFO** — stale ticket、owner crash、別の直列化 lock が必要になり、
  本 scope より大きい crash protocol になる。`flock` は FIFO を保証せず、本決定も
  **取得成功と公平性を保証しない**。保証するのは上限内に terminal outcome へ至ることだけである。
- **待機中に main が閉包外へ動いたら早期に諦める** — lock 外の読取りは racy であり、
  「拒否方向にしか効かない」ことの証明を要する。待機の遅延は fail-closed な拒否を増やすだけで
  受理集合を広げないため、複雑さに見合わない。
- **timeout を `lock-busy` 以外の rc にする** — repo 外の待ち手と上位手順の受理集合を変える。

**`docs/dev-wave/operations.md` は変更しない。** `DW-O25` は checker が節全文を exact pin して
いるため 1 byte も触らない。`DW-O23` へ「同一 invocation 内の有界待機は反復に含めず、上限到達時
だけ fresh context へ返し、取得成功と公平性は保証しない」の 1 文を足すことを検討し、実際に書いて
検査したが、**`DW-O23` は段 9 の無条件節で L1 に算入されるため、この 1 文 (158 bytes) がちょうど
L1 予算を超えた** (10783 > 10625)。予算の引き上げを提案しない方針に従って追記を取り下げ、
待機の契約は本決定だけに置く。`DW-O23` の既存文「stale / busy は fresh context で再試行」は
待機化後も真であり、意味の欠落は生じない。

**閉じない残余 (別 scope):** 待機化は provenance 監査の同時流入を増幅しうる。保持者が監査のため
lock を解放している間に待ち手が順に取得して各自監査を始め、最初の 1 本が land すると残りは
fingerprint 不一致で拒否される。上限は `13 x 480` 計算秒で、発生率は未計測である。
受入 lease が land 中も保持され残 TTL 保証が 300 秒しかない点も本決定では閉じない。
どちらもユーザー裁定へ返した。
