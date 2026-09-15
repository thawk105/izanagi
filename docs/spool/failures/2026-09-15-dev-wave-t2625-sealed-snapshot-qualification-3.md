---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-t2625-sealed-snapshot-qualification
seq: 3
---

## 新規

### {{F:non-detached-dispatcher-killed-leaves-orphan-hold}}. detached でない背景 job の dispatcher が殺され orphan hold が残った [手順漏れ]

- 事象: 焦点走の dispatcher を detached でない背景 job として起動したところ、計算ノードの job が
  走行中に投入側だけ殺された。job は生き残り、`pending-qsub` の orphan hold が 1 件残って
  以後の dispatch が全部止まる状態になった。job 自体は完走しており、出力から結果を回収できた。
- 根本原因: 同じ wave の中で、qualification の投入は `nohup setsid` の detached 経路を使ったのに、
  焦点走だけ背景 job の process 管理下で起動した。背景 job の終了判定は wrapper の終了で立つため、
  実体が走行中でも process group ごと片付けられうる。
- 恒久対応: 計算ノードへ投入する producer は例外なく detached 経路 (`nohup setsid`) から起動する。
  待ち手は `.done` の実在で判定し、wrapper の終了通知を完了と読まない。
- 再発検知: 投入直後に producer の pid を file へ書き、pid の生存と `.done` の両方で完了を判定する。
  hold の復旧は hold 自身が書く手順 (qstat で終端確認 → source の clean/HEAD 確認 → 手動削除) に従い、
  手動 `qdel` は使わない (別の防壁を武装させ、解除がユーザー手番になる)。

### {{F:preflight-green-via-user-package-registry-leftover}}. 事前検査が別 wave の残骸を拾って偽の緑を出した [恒真ゲート]

- 事象: 計算ノードで落ちる依存を login node で事前確認したところ、最小 cmake の
  `find_package(gflags REQUIRED)` が緑になった。実際には login にも計算ノードにも system の
  gflags/glog は無く、別 wave の残骸 prefix を CMake の user package registry 経由で拾っていた。
  この偽の緑を根拠に (P1) を立てたため、1 回目の計算ノード投入を空費した。
- 根本原因: 事前検査を**本番と違う finder**で行った。対象 project は自前の Find module を
  module path の先頭に置くため config mode で成立しても module mode の反証にならない。
  加えて user package registry は repo 外の他 wave の生成物を無警告で参照する。
- 恒久対応: 依存の事前検査は本番と同じ module path・同じ finder で行い、解決された実 path を
  出力して**どこから来たか**を確かめる。install を伴う事前構築では registry 登録を無効にする。
- 再発検知: 事前検査が緑のとき、解決先の絶対 path が期待した prefix の配下にあることを併せて表示し、
  期待外なら赤にする。
