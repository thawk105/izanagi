---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2176-dense-cycle4-fixture
seq: 1
---

## 新規

### {{F:producer-waiter-returns-while-alive}}. 待ち手が producer 生存中に rc=0 で戻る [手順漏れ]

- 事象: `tools/dev_wave_wait.py producer` を背景で起動したところ、producer (変異 harness の
  runner script) がまだ走っている最中に **rc=0 で戻った**。本 wave で 3 回観測した
  (mut-probe、mut-after、mut-before2)。いずれも標準出力の最終行は
  `producer: /proc/<pid>/stat を読めないため pid-only へ縮退します` で、`--receipt-file` へ
  receipt が書かれないこともあった。`--max-wait-seconds` を明示した前景実行では 60 秒指定で
  正しく `stage=producer-timeout rc=70` を返したので、待ち手そのものは機能している。
- 根本原因: 未特定。縮退経路 (`/proc/<pid>/stat` が読めないときの pid-only 判定) が、
  対象 pid を生存と判定できずに完了扱いで抜けている疑いがあるが、本 wave では切り分けていない。
  共有ファイルシステム上で `/proc` 読み取りが一過性に失敗する F810 と同時期に観測している。
- 恒久対応: 未実施。運用側の対応は `docs/dev-wave/core.md` の `DW-C00` が既に定める
  「完了は `.done` 非空で決める」をそのまま守ることで、**待ち手の rc を完了判定に使わない**。
  本 wave では 3 回とも `.done` の不在で気づき、待ち手を張り直して正しく待てた。
  待ち手側で縮退時に生存判定をやり直すか、戻り値に縮退の事実を載せるかは、原因を切り分けてから
  裁定する。
- 再発検知: 待ち手が rc=0 で戻ったのに `.done` が存在しない、または `.done` の中身が空である
  ことを確かめる。producer の生存は `pgrep -f <worktree path>` で照合する。
  生存していれば本エントリの型であり、同じ引数で待ち手を張り直せばよい。

## 再発

### F810

- **再発: 2026-09-02** — [T-2176] wave でも `tools/dev_wave_submodule_init.py` の 1 回目が
  `runtime-io-failure: detail={'label': 'submodule', 'kind': 'update-no-fetch'}` で rc=1 になり、
  同じ command の 2 回目が rc=0 で通った。wave 用 worktree で 1 回。加えて、DW-M08 の
  「変更前 HEAD の木」を自分で作った際には**初期化そのものを落とし**、その木の baseline が
  84 件赤になって変異 harness の fail-closed (`baseline が緑でないため production write を
  開始しない`) で 1 走を捨てた。手で作った比較用の木にも `DW-O08` が適用される。
