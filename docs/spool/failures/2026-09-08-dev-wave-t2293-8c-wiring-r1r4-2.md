---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2293-8c-wiring-r1r4
seq: 2
---

## 新規

### {{F:stage-8-ran-after-land}}. 段 8 を land の後に回し、是正の着地に受入全走をもう 1 回使った [手順漏れ]

- 事象: 本 wave は段 7 の記録 commit の後、段 8 を実行せずに段 9 の land を先に走らせた。
  land 自体は rc=0 で main を進めたが、段 8 の是正は tested tip より後に生まれるため、
  その受入証明では着地できない。復旧に受入全走 (13 分) と land をもう 1 度使った。
- 根本原因: 段 7 の後に受入投入と land が連続したため、段 8 を「land を待つ間にやること」と
  扱った。受入は tested tip を固定するので、段 8 の成果は tested tip の中に無ければならない。
- 恒久対応: `DW-S08` の「段 7 後に一度だけ」は既にあり規約の欠落ではないので、遵守の失敗として
  記録する。復旧手順は wave を main へ fast-forward し、段 8 の専用 commit を足してから
  受入全走と land を取り直すこと (本 wave で実施し着地を確認した)。
- 再発検知: 受入全走を投入する直前に handoff の「dev-wave 改善候補」節を見て、未裁定なら
  段 8 を先に閉じる。段 7 commit の message に段 8 の状態を書くと投入前に目に入る。

## 再発

### F26

- **再発: 2026-09-07** — 作成側の `git worktree add` が並行 wave の混雑下で 7 分かかり、
  Bash の 120 秒 timeout で背景化された。2026-09-02 の再発は kill された形だったが、
  本件は**背景化されても process は生きていた**。親がこれを失敗と誤読して `git reset --hard`
  を撃ったため、進行中の add と `index.lock` で衝突した。元の add の pid の終了を待つと
  checkout は正常に完了した。中途の dirty へ復旧操作を撃たず、pid の終了を待つ。

### F810

- **再発: 2026-09-07** — checkout 完了後に `tools/dev_wave_submodule_init.py --worktree <ABS>`
  を走らせた後、入れ子の googletest (ccbench 配下 shirakami の third_party) が
  staged deletion を大量に抱えた壊れた状態で残っていた。同じ tool をもう 1 度走らせて復旧した。
  **rc は観測していない** — 出力を `| tail -3` へ通したためである (F37 の再発)。
  「2 回目で通る」点は既載と同じだが、本件は入れ子側だけが壊れていた点が異なる。

### F37

- **再発: 2026-09-07** — 新規 worktree の submodule 初期化を `... | tail -3` で投げ、
  rc を `tail` のものにしてしまった。初期化の成否を判定できないまま次へ進み、入れ子
  submodule の破損 (F810 の再発) を後段の `git status` で見つけた。偽緑には至っていない
  (near miss)。恒久対応は F37 既存のとおり変わらない。

### F198

- **再発: 2026-09-07** — 変異 spec を書く前に契約を引かず、harness の起動前拒否から
  再導出したため、本走に入るまで **6 回**中止された (`--attempt-out` と `--wrapper-attempt`
  の対、spec の置き場所、exact key 名、runner argv の先頭実行体、`timeout_seconds` の下限、
  parametrize 済み期待 node)。**6 件すべて本エントリの恒久対応が指す到達面 (memory) に
  2026-08-16 以降すでに在った。** 実害は起動 6 回分の往復で、harness が全件を走行前に
  fail-closed で止めたため測定は汚れていない。**docs 予算を避けて到達面を memory へ置く対応は、
  引く規律が働いて初めて機能する**という点が本再発の内容であり、恒久対応そのものは変えない。
  L1.5 予算は今回も満杯で (追記 248 bytes が 246 bytes 超過)、D730/D782 の手順では
  独立 3 例に満たないため reference への収容は行わない。

### F686

- **再発: 2026-09-07** — 段 5 の実装子 3 本が 32 秒でそろって `f43_fragment` を返した。
  原因は逐語の欠落ではなく**射影そのものの欠落**で、prompt が指す `s4-adjudication.md` を
  job dir へ複製していなかった。子は fail-closed で正しく止まっており、`DW-O02` の射影義務も
  既にあるので、規約の欠落ではなく遵守の失敗である。job-id を変えて再投入し 3 本とも rc=0。
