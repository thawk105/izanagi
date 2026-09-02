---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2176-dense-cycle4-fixture
seq: 2
---

## 再発

### F355

- **再発: 2026-09-02** — [T-2176] wave で 3 回観測した (変異 probe 走・変異本走 2 アームの
  待ち手)。producer 生存・`.done` 不在のまま rc=0 で戻る点は既知のとおりだが、**3 回とも
  標準出力の最終行が `producer: /proc/<pid>/stat を読めないため pid-only へ縮退します` だった**
  点が新しい。`--receipt-file` へ receipt が書かれない回もあった。同じ待ち手を
  `--max-wait-seconds 60` で前景実行すると `stage=producer-timeout rc=70` を正しく返したので、
  待ち手そのものは機能している。縮退経路 (`/proc/<pid>/stat` が読めないときの pid-only 判定) が
  対象 pid を生存と判定できずに完了扱いで抜けている疑いがあるが、本 wave では切り分けていない。
  3 回とも `.done` の不在で偽完了を捕まえ、張り直した待ち手が正しい完了を拾った。

## supersede 追記

- F817 **supersede: 2026-09-03** — 本エントリは F268 / F355 と同型であり、新規 F を採るべきでなかった。台帳の正本は F355 とし、2026-09-02 の観測は同エントリの再発として記録した。以後この型は F355 へ追記する。
