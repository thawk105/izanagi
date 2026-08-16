---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t419-seam-checknet
seq: 3
---

## 新規

### {{F:replayed-gate-against-mutable-constant}}. 過去の遷移を毎回再判定する chain に、可変な現行定数との比較を置いた [恒真ゲート] [誤前提]

- 事象: 環境契約の後継判定へ「取得方式名が現行 probe 定数と一致すること」を足した。
  実装直後は正しく見えたが、activation chain は**読み込みのたびに過去の全遷移へ後継判定を
  再適用する**。したがって probe を改良して定数が変わった時点で、既に有効な過去の遷移が落ち、
  authority 全体が読めなくなる。同じ形が発行経路にも残っており、記録が 2 本以上になった後は
  新しい記録を一切発行できなくなる。段 6 の敵対レビューが前者を、親が後者を land 前に検出した。
- 根本原因: **判定の入力に「その時点の現在値」を混ぜたまま、再生される場所に置いた。**
  再生される判定は、記録された bytes だけから決まらなければ冪等にならない。
  この誤りは D329 が 2026-08-12 に取り除いた「probe の改良で過去の登録が構造的に通らなくなる」
  型と同一であり、層を変えて再発した。
- 影響: 検出できなければ、次の世代交代の後に probe を改良した時点で計算ノードの実験が全停止し、
  復旧には凍結側の再発行が要る。
- 恒久対応: {{D:activation-admission-artifact-faces}} で判定を 2 層に分けた。
  再生される経路には artifact の bytes だけから決まる 3 面を置き、現在値との比較は
  発行経路かつ「後継がまだ ever-active でない」場合に限定した。
  過剰拒否の正例を変異事前登録に 2 本置き、再生側へ現在値比較を戻す変異と、
  ever-active へも効かせる変異の双方が検出されることを実測で固定した。
- 再発検知: 再生される判定へ比較を足す改修では、**その比較の入力が記録済み bytes だけで
  決まるか**を先に確かめる。決まらないなら、その比較は再生経路ではなく発行・受理の 1 回限りの
  経路に置く。変異事前登録に「再生経路へ戻す」正例を必ず 1 本入れる。

### {{F:uncommitted-edit-red-in-enforcement-closure}}. enforcement source closure を編集した wave は、commit 前の焦点走で必ず偽赤が出る [偽赤] [手順漏れ]

- 事象: 環境契約まわりの実装を編集した状態で焦点走を投入したところ、
  `test_campaign.py` が 26 件赤になった。理由はすべて
  `contract-loader-drift: disk bytes が記録 commit blob と不一致` である。
  統合 commit の後に同じ範囲を再走したところ 26 件はすべて消え、真の赤は 4 件だけだった。
- 根本原因: `capture_contract_loader_binding` は enforcement source closure の 12 path について
  **disk bytes が HEAD blob と一致すること**を要求する。未 commit の編集はこの前提を必ず破る。
  したがって当該 12 path のいずれかを編集する wave では、commit 前の焦点走で
  campaign lock を作る系のテストが機械的に赤くなる。
- 影響: 偽赤を実装差分へ帰属すると、存在しない欠陥の fix を子へ投げることになる。
  逆に「commit 前は緑にならない」と気付かず受入へ進むと、受入の窓を 1 本捨てる。
- 恒久対応: 本 wave では統合 commit の前後で同じ範囲を実走し、
  26 件が commit だけで消えることを実測して切り分けた。判定手順は
  「赤の理由行に `contract-loader-drift` があるなら、まず commit してから再走する」である。
- 再発検知: `orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` に
  載っている path を編集する wave では、焦点走の赤を実装へ帰属する前に
  統合 commit 後の再走で切り分ける。

## 再発

### F355

- **再発: 2026-08-16** — 別 wave で 2 例目。`tools/dev_wave_wait.py producer` が
  producer 生存・`.done` 不在・成果物不在のまま、**出力に自分の echo 行を 1 行も残さず** rc=0 で
  終了した。同一 wave 内で 2 回起きており、いずれも同じ手順で張った他の待ち手 8 本は正常だった。
  3 点照合で検出し、Monitor 方式 (完了印の実在 + producer 生存を条件にした until ループ) へ
  切り替えて回復した。本エントリの「2 例目が出た時点で機序を特定し、待ち手側の fails-closed
  検査として実装する」という再発検知条件は、これで成立している。

### F250

- **再発: 2026-08-16** — Monitor が `.done` 不在・producer 生存のまま
  「完了 rc=0」を 1 度出した。イベント文字列は成功時と区別できない形で、
  完了印の実在を独立に確認して初めて偽と判定できた。恒久対応どおり 3 点照合で検出し、
  完了印が**非空である**ことを条件に含めた until ループへ張り直した。
