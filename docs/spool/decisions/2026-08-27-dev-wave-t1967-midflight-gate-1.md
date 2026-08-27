---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1967-midflight-gate
seq: 1
---

## {{D:midflight-guarantee-is-remeasurement-not-freshness}}. 段 5 の midflight が保証するのは再測と提示までとし、乖離量は関門にしない

**決定 (D1153 の実装裁定):** `tools/check_wave_startup.py --mode midflight` は、段 5 実装子
dispatch 直前専用の mode とする。検査するのは legacy graft 不在、main 乖離が raw commit graph 上で
canonical に測定できること、local main が direct ref であること、作業 branch が main でも detached
でもないこと、rebase / merge が進行中でないこと、submodule marker の実在の 6 つだけである。
`HEAD == local main`、`HEAD` が local main を包含すること、clean tree、worktree handoff、
external handoff は検査しない。**main 乖離の「量」も関門にしない。**

保証の範囲は狭い。midflight が保証するのは「段 5 直前に乖離が再測され、gate 自身が測った実測値が
提示されること」だけであり、「古い anchor のまま実装子を投入しないこと」は保証しない。後者は
`DW-S05-A` に書いた親の義務である。この限界は `--help` と `NOTE:` 行に明記する。

**理由:**

- 稼働中の wave worktree を実測すると、clean tree でなく (段 1 の成果物や実装中の変更を抱える)、
  main を 102 / 343 commit 遅れている。既存 `--mode resume` を当てると赤になるのはこの 2 つだけで、
  branch・direct ref・進行中操作なし・submodule marker はすべて緑だった。落とす 5 検査は
  「wave 途中では構造的に満たせない」ものに一致する。
- 乖離量を関門にすると、並行 wave が land するたびに全 wave が段 5 で止まる。実測でも本 wave 自身の
  準備段の間に local main が 40 commit 進んだ。
- 「自 wave commit を持つこと」を要求にすると到達不能になる。実測で段 5 相当の時点でも自 commit 0 の
  wave が存在した。
- gate は可視化 `describe_main_divergence` の戻り値・出力文字列を根拠にせず独立に git を実行する
  (D364)。ただし**方向は逆にする** — 表示側が gate の測定値を使う。別々に測ると、表示が 0 で
  gate が 343 という食い違いが起こり、D1153 が塞ごうとした「気づかない」を再生産する。
- 専用 exit code は新設せず rc は 0 / 1 の二値を維持する (D822)。
- 誤用の残余は塞げない。D822 が確定したとおり checker は呼び出された時点を観測できないため、
  起動時に `--mode midflight` を明示する誤用は機械的に識別できない。診断で誤用者を正しい経路へ
  送るところまでが本 mode の射程である。

**却下した選択肢:**

- **乖離量に threshold を置く** — 実測値域が到達不能になり、全 wave が段 5 で止まる。
- **`--acknowledge-behind N` のような確認引数を要求する** — shell 置換で機械的に充足でき、
  発火しない assert になる。
- **`HEAD == main` かつ clean tree なら拒否して起動状態と判別する** — 段 5 時点でも
  自 commit 0・clean tree の wave が実在するため到達不能な述語になる。
- **段 5 であることの attestation を新設して誤用を機械的に塞ぐ** — 入力の実在と到達可能性の
  確認 (`DW-O13`) と launcher 側の面への変更を伴う。本 wave の scope 外としてユーザー裁定へ返す。

## {{D:dev-wave-l1-5-budget-minimum-raise}}. dev-wave docs の L1.5 予算を実測値ちょうどの最小増分で上げる

**決定:** `tools/check_docs.py` の `DEV_WAVE_L1_5_BYTES_MAX` を 9,566 から 9,696 へ上げる。
`DEV_WAVE_L1_BYTES_MAX` (10,625) と `DEV_WAVE_L2_SECTION_BYTES_MAX` (1,000) は変えない。
増分 130 bytes は実測値ちょうどで、余裕枠を取らない。

収容するのは次の 3 義務で、いずれも `DW-S05-A` に置く。終端条件は 3 件とも同じで、
dispatch 前の midflight 自動実行が launcher に入り、手順を docs から落とせるようになったときである。

1. 段 5 の各実装子 dispatch 直前に midflight を発火させる。
2. 発火対象を各投入先 worktree root へ束縛する (cwd と `--repo .`)。
3. anchor 再読の根拠を fail-open の INFO でなく gate 実測値の `NOTE:` に固定する。

**理由:**

- D782 の第 1 段 (既存記述の削減) を実施した。捻出できたのは `DW-S05-A` の言い回しの圧縮と、
  `DW-S06-A` の所見ゼロ規則を `DW-M02` へのポインタへ置き換えた分だけで、独立レビュー 1 本が
  どちらも「義務は保たれた」と判定した。
- 同じ削減の一環で `workers.md` preamble の「入口が指定する leaf 節を worker 起動前に読む。」を
  一度削ったが、独立レビューは**義務の削除**と判定した。単独段 dispatch では worker が入口本文を
  読まないため、起動前の leaf 読了を命じる文が他にない。D874 が却下している型そのものだったので
  復元した。**削減の限界が実測で確定した。**
- 第 2 段 (例外収容) も採れない。発火点の収容先は `DW-S05-A` 以外にない。段 5 の無条件節で
  あることが発火点の要件であり、byte の空きを理由に別節へ移すことは D874 が却下している。
- L2 単節は削減だけで閉じた。`DW-O20` の再走禁止文を「gate 成功後の再走は `DW-S05-A` だけ」へ
  書き換え、例外の定義を 1 箇所へ寄せた結果 989 / 1,000 bytes に収まった。禁止の射程は変えていない。

**却下した選択肢:**

- **一括で余裕を持たせた増枠** — D961 が明示的に禁じている。
- **L1 と L2 単節も同時に上げる** — どちらも本件では超過していない。
- **発火点を諦める** — D1153 はユーザー裁定であり、親が不採用にできない。
