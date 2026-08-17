---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t848-mutation-timeout
seq: 2
---

## {{D:mutation-timeout-local-stop}}. 変異台帳の status は増やさず、local 申告 × 実 dispatch の timeout を停止 sidecar で閉じる

**決定:** 変異 harness の `--runner-mode local` で走った試行が、実際には計算ノードへ
dispatch していて queue 待ちのまま harness 側 timeout に掛かった場合、
**terminal record を書かずに停止する**。停止は D454 が確立した停止 sidecar と同じ形とし、
理由コードで区別する。台帳 schema `izanagi-dev-wave-mutation/v4`、status 集合、summary 欄、
D289 の TIMEOUT 全面拒否はいずれも変更しない。

判定は次のとおり。

1. `output/pegasus-dispatch/` 直下の submission 一覧を、**runner mode に依らず**走行の前後で取る。
2. timeout 時に現れた新規 submission のうち、**この走行だけの nonce** が
   `request.json` の `environment` に載っているものだけを「自分の走行」と判定する。
   nonce は `secrets.token_hex(16)` で、`PYTHONDONTWRITEBYTECODE` を運び屋にする。
3. 一致する submission があれば停止する。nonce が一致しないものは他者の走行として無視する。
4. inventory が取れない・`request.json` が読めない等の判定不能は、必ず停止側へ倒す。
5. **local 側では D454 の create-only latch を張らない。**
6. 非 timeout の local 走行の挙動は変えない。dispatch 経路の挙動も 1 bit も変えない。

**理由:**

- 台帳項が名指しした dispatch 経路は D454 で既に閉じており、既存テストが固定している。
  残っていたのは local 申告と実体の乖離だけである。`tools/run_tests.py` は
  `--force-dispatch` が無くても login headroom が不足すれば dispatch し、
  harness は申告と runner argv の実体を突き合わせていなかった。
- **新しい status を台帳語彙へ入れても、書き込む経路が 1 本も残らない。**
  dispatch 側は D454 が先に止め、local 側は本決定が止めるためである。
  死んだ語彙のために schema を上げると、既存台帳の `--resume` と既存 shard の
  再併合が全て拒否される。互換性の代償が検出力の利得を上回る。
- **receipt を一次証拠にできない。** dispatcher は polling 中に receipt を永続化せず、
  終端でしか書かない。harness は SIGTERM の 5 秒後に SIGKILL するため、
  timeout 時に receipt が残る保証がない。一方 submission directory は
  runner mode に依らず必ず作られるので、こちらを一次証拠にする。
- **latch を張らないのは D454 の署名規則に従うためである。** D454 は latch の署名を
  receipt の `job_may_remain` **だけ**と定め免除条項を置かない。local 停止はその署名を持たない。
  さらに submission directory は qsub より**前**に作られるので、未投入でも latch が張られうる。
  latch は次回投入・変異 source 復元・worktree 廃棄・受入 probe 掃除の 4 経路を
  人手の解除まで止めるため、署名のない停止で張ってはならない。
- **束縛を nonce 単独にしたのは、それ以外が原理的に成立しないからである。**
  当初は repo / task / argv の一致も要求したが、dispatch へ渡るのは pytest の子 argv であって
  harness の runner argv ではないため、自分の走行でも argv 一致は成立せず、
  「自分のもの」と判定できる状態が実運用で到達不能だった。
  nonce は走行ごとの 128 bit 乱数であり、それを載せた submission は自分のものである。

**却下した選択肢:**

- **queue 側 timeout に専用 status を新設して台帳へ書く** — 台帳項が指示した形だが、
  上記のとおり producer が残らず、schema 更新の互換性代償だけが残る。
  この選択は実装せず、新事実を添えてユーザー裁定へ返す。
- **dispatch 側へ queue 待ち上限を渡して dispatcher 自身に分類させる** — option 自体は
  実在するが、runner argv を組み立てる層から dispatcher の option を透過させる seam がない。
- **local 停止でも D454 latch を張る** — 未投入の可能性がある停止で 4 経路を止め、
  解除に人手を要求する。D454 の署名規則にも反する。
- **判定不能を terminal 側へ倒す** — 規律 2/3 に反する。証拠が取れないことは
  「実行された」ことの証拠ではない。
