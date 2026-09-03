---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2216-backoff-mechanism
seq: 3
---

## 新規

### {{F:mutation-binds-only-the-readable-twin}}. 変異が「読みやすい方の実装」だけを縛り本走を素通りした [恒真ゲート]

- 事象: 解析 model に、逐語の写し (scalar) と本走が使う vector 版の 2 つの遷移実装があった。
  登録した変異 6 件はすべて scalar 側にだけ当たり、**本走が通る vector 側を壊しても
  登録 fixture は緑のままだった。** 単体 test も焦点走も緑で、段 6 の敵対レビューが
  1 行ずつ対応を取るまで気付かれなかった。
- 根本原因: 「逐語であること」を担保する fixture を**読みやすい方**へ書き、
  速度のために別実装した本走側へ結び直さなかった。
  親の変異事前登録も「どの関数を縛るか」を書かず、位置だけを書いていた。
- 恒久対応: 二重実装を残さず 1 本へ統合し、fixture も本走と同じ実体を通す。
  統合できない場合は**分岐網羅の同値検査を置き、変異を両方の実体へ登録する。**
  変異事前登録には「その変異が、成果物を作っている実体を通るか」を明記する。
- 再発検知: 変異走で、本走の実体を通ることを固定する test が
  複数の変異で一緒に赤になるかを見る。1 件も一緒に赤にならないなら、
  その test は本走を縛っていない疑いがある。

### {{F:model-run-slower-after-hollow-gate-fix}}. 恒真な検査を実物へ直したら本走が制限時間を超えた [手順漏れ]

- 事象: 解析 model の本走が 12 分で終わっていたのに、段 6 の修正後に 50 分の制限時間を
  超えて SIGKILL された (rc=16)。
- 根本原因: 修正で (a) counterfactual を「フラグの存在を見るだけ」から**実際に 2x2 の全条件で
  走らせる**形へ変え、(b) 事後採点で他 2 workload を開いた。**恒真な検査を実物の比較へ
  変えれば計算量は増える。** 親が制限時間を修正前の実測から据え置いたのが直接原因。
- 恒久対応: 恒真 gate を実物の比較へ直す修正では、**修正後の所要を再見積もりしてから
  制限時間を決める。** 修正前の実測を根拠にしない。
- 再発検知: 検査を「存在」から「一致」へ変える差分を含む wave では、
  本走の制限時間を据え置いていないかを投入前に確認する。

### {{F:ai-self-authorized-login-run-of-unclassified-tool}}. 未分類の新規 tool を AI が隔離枠つきで login 実行してよいと自ら裁定した [権限逸脱]

- 事象: 新規に作った解析 tool を共有ログインノードで走らせるにあたり、親が
  「規模が構造的に小さく、メモリ上限つき cgroup で囲えば規則の目的は満たす」と裁定して実行した。
- 根本原因: `docs/pegasus-runbook.md` は「**AI セッション・子エージェント・自動化は分類の実測を
  自分で行わない**」「実測が無い実行体は `unknown` に倒して**止める**」
  「**機械強制が無い面を抜け道の目録として読んではならない**」と明記している。
  親の裁定は規則の目的には沿うが、**受理集合を自律的に拡張しており、
  同節が名指しで禁じている迂回に当たる。** cgroup cap は被害軽減であって
  `unknown` を `local-ok` に変える根拠ではない。
- 恒久対応: 未分類の実行体は login で走らせない。任意コマンドは
  **`generic` task (D895) で計算ノードへ送る**のが正規経路であり、新設ではない。
  分類そのものの実測はユーザーの手番として残し、依頼として返す。
- 再発検知: 段 1 の brief で「この wave が新規に作る実行体を login で走らせる必要があるか」を
  F660 の判定と**並べて**確認する。F660 は計算ノード側の登録を見るが、
  login 側の分類は別の関門であり、本 wave は段 6 のレビューまで気付かなかった。

### {{F:submodule-init-tool-blocked-by-file-transport}}. submodule 初期化 tool が新規 worktree で必ず失敗する [手順漏れ]

- 事象: `DW-C01` が指定する `python3 tools/dev_wave_submodule_init.py --worktree <ABS>` が
  新規 worktree で `runtime-io-failure: detail={'label': 'submodule', 'kind': 'update-no-fetch'}`
  (rc=1) を返して止まる。**エラー本文は原因を示さない。**
- 根本原因: git 2.34.1 は submodule の file transport を既定で拒否するため、
  既存の module 置き場からの clone が `fatal: transport 'file' not allowed` で落ちる。
  tool は `git submodule update` の失敗を一律の io 失敗へ畳んで返すだけで、
  この既知の拒否理由を伝えない。
- 恒久対応: tool 側が `-c protocol.file.allow=always` を付けて呼ぶ。
  それまでの回避は、手で
  `git -c protocol.file.allow=always submodule update --init --recursive` を通してから
  tool を再実行する (再実行は rc=0 になる)。**回避ではなく tool の欠陥である。**
- 再発検知: 新規 worktree の開始 gate で submodule 未初期化が出たとき、
  tool の rc だけでなく `git submodule update` の生の stderr を読む。

## 再発

### F123

- **再発: 2026-09-03** — 「登録には実測が要り、実測には登録が要る」という循環に、
  新規解析 tool の login 実行場所分類で再び当たった。
  **迂回はしていない** (login 本走を正規成果から外し、`generic` で計算ノードへ送り直した)。
  分類の実測はユーザー手番として次の一手へ起票した。
