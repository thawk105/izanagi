---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-p24-gain-unify
seq: 1
title: 論文 §8 A-3 (P2-4 利得値の一本化) を read-heavy まで含めて閉じ、論文図の baseline 誤記を見つけた (docs のみ、branch worktree-dev-wave-p24-gain-unify)
---

## 本文

- 依頼は「+38.5% 系と +38.3%/+11.3%/-6.6% 系の計測条件を一次資料まで遡って突き合わせ、
  同一条件の不一致か別条件の値かを確定し、論文値を 1 つに決める」。新規計測はしていない。
- **結論: 別条件の値である。** 論文採用値は同一 sweep 内の no-backoff control (`BACK_OFF=0`) を
  分母として write-heavy +38.3% / balanced +11.3% / read-heavy -6.6%。
  結論・条件表・再計算・source ledger は
  `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。
- **+38.5% を採らない理由を精密化した。** profile cell は CCBench revision・`BACKOFF_NOINLINE=1`・
  `perf record`・反復数の 4 点で sweep と出自が違うが、**この 4 点が効果量を変えたという実証は無い**。
  上流 commit `dff0f1ef` の message 自身が「default (ADD_ANALYSIS=0) ... builds are unaffected」と
  書いており、D20 は noinline 単体の観測者効果を +0.76% (floor 3.0% 内) と実測済みで、
  profile は sweep に対し baseline -0.764%・fix10 -0.669% と同方向に動く。
  採らないのは **D20 が「perf 下 tps は headline 非使用」と定めているから**であって、
  0.133 パーセントポイントの差を実質差と読んだからではない。逆にこの近さを
  「同じ測定の丸め違い」の根拠にもしない。
- **read-heavy の正典 campaign を一意に確定した。** 同名 workload の campaign は 3 つあるが、
  `610004b9` だけが sweep 曲線と材料レポートを持つ。`6f169f90` は
  `reason: screen-slower-than-floor` で終わる screening の positive control
  (`orchestrator/tests/test_bench_first_real_wal.py` の fixture 元)、
  `8ff95955` は `reason: build-error`。どちらも headline 候補ではない。
- **旧文書に無かった分母を 1 つ足した。** P2-2 全探索の stock 最良を分母にした read-heavy の
  **-7.1%** (8,487,844 → 7,889,420)。write-heavy +39.0% / balanced +12.9% と対になるのに
  counterpart が書かれていなかった。論文採用値は -6.6% のままで、分母の取り違えを防ぐため両方載せた。
- **論文図 `figures/fig2_backoff_mechanism.png` の baseline が図の中で誤って label されている。**
  横破線に `stock adaptive backoff (Cicada-type hill-climb)` と書かれているが、その値
  1,867,747 tps は無 backoff である。決定的な自己矛盾として、赤い曲線の x=0 の点 (= `BACK_OFF=0`) と
  この破線が図中で同じ高さにある。write-heavy の stock 適応は 1,052,528 tps で図の縦軸に入らず、
  適応比なら +147.4%。パネル見出し `Synthesized static backoff beats stock adaptive` と
  2026-07-10 / 2026-08-23 両版のキャプションも同じ誤り。図が描く系列は headline 非適格な
  profile 系列である。誤記は 2026-07-10 版の初回収録 `ff3268f8` から入り、
  同日の「数値・図を監査修正」commit `3940bbe4` を通過している。
- **「stock」という語そのものは誤記としない。** D18 が `BACK_OFF=0` を指して
  「stock の `BACK_OFF=0`」と書く用法が実在し、曖昧なだけである。誤りは `adaptive` / 「適応」と
  明記した箇所に限る。
- **A-3 は 2026-08-24 の entry 898 で一度閉じていた。** 本 wave は独立再導出でこれを裏取りし
  (重なるセルの値・条件・source ledger の SHA-256 5 件が byte 一致)、read-heavy と図の誤記を
  足した successor である。08-24 の scope 限定は意図的であり、欠落の修理ではない。
  08-24 insight・2026-08-23 スナップショット・図・campaign 成果物はいずれも編集していない。
- **新しい日付の paper-story スナップショットは作らなかった。** 依頼は「更新が要るなら新しい
  日付の版を足す」だったが、08-23 以降に A-1 は entry 945 で実測済み、A-2 は [T-1647] が
  人間手番待ちへ進んでおり、A-3 だけ直した文書を「2026-08-25 版」と名乗らせると A-1/A-2 について
  新しい stale 主張を増やす。`docs/paper-story/README.md` は自身を「日付なしの入口
  (ポインタは腐らない・スナップショットは腐る)」と定義しているので、そこへ stale 注記と
  writer-facing ポインタを置いた。全体を再合成する版が要るなら別 wave の所有とする。
- **A-3 そのものには T 番号を採番していない。** spool の文法上 `新規` は採番前の placeholder、
  `完了` は既存 `[T-NNN]` と `base` digest を要求するため、同じ fold で採番と完了はできない。
  A-3 の決着は本エントリ (番号なし表題) とし、実際に残る図の再作成へ新規 T を採った。
- **敵対相談の記録。** 段 3 は 2 レンズ並列。数値レンズ (sol) は所見 7 件・nit 3 件を返し、
  親の provisional 裁定のうち「stock 1,867,747 自体が誤記」「08-24 と全項目一致」
  「C5 を後から追記」の 3 つを壊し、read-heavy -7.1% の列挙漏れを指摘した。
  scope レンズ (luna) は初回が model 出力の劣化 (同じ語の繰り返しが 21,871 桁続いて JSON parse
  失敗) で停止し、1 時間の wall-clock 上限で SIGTERM/SIGKILL (model call 25 回、CLI 報告
  トークン 150,303、成果物ゼロ)。上限 2400 秒と出力量上限を明記して再投入し、所見 6 件を得た。
  親は 13 所見すべてを real と裁定し、provisional 裁定 5 件 (新規 T の採番、部分改訂スナップショット、
  read-heavy の「見落とし」表現、成果物影響の書き方、3 台帳一律の fragment) を取り下げた。
- **段 8 の自己改善 1 件を予算超過で取り下げ、裁定パッケージへ回す。** 「read-only の子 prompt に
  所見数と 1 件あたり行数の上限を書き、繰り返しが始まったら打ち切らせる」を `DW-O05` へ足そうと
  したが、`docs/dev-wave/**` の L1.5 unique footprint が 9,759 bytes となり予算 9,566 bytes を
  193 bytes 超えた。予算のために既存の安全義務を削らない契約に従い追記を撤回した。
  同型の既裁定 (2026-08-25、`DW-O01` の予算) は「予算値は上げず、同 L1.5 集合の別箇所を
  意味等価に縮約して空きを作る。意味等価にできなければ独立審査へ戻す」である。本 wave では
  縮約を試みていない — この候補は成果物の値・受理集合・参照を 1 つも変えず (節約するのは
  子の wall-clock だけ) nit であり、nit のために無関係な規範文を縮約するのは釣り合わないと
  判断した。裁定を仰ぐ選択肢は (a) 別 wave で L1.5 を意味等価に縮約、(b) launcher 側で
  出力劣化を検知して早期に落とす (実装面のため別 wave)、(c) 見送り。
- **段 8 のもう 1 件は `docs/paper-story/README.md` へ統合した。** 「新しい日付の版は
  その日付時点の正典全体からの導出でなければならず、一項目だけの差分改訂を新しい日付の版として
  置かない」「図も凍結物なので上書きせず、後継図は別 filename で生成器つきのときだけ作る」。
  どちらも本 wave の実測 (A-1/A-2 が 08-23 以降に進んでいた、fig2 に生成器が無い) から出た。
- 実装面の変更はゼロ (コード・テスト・probe・機械設定を一切触っていない)。よって Codex 実装子なし、
  変異 matrix 免除。受入全走は免除せず実施した。

## 次の一手差分

### 新規

- {{T:fig2-backoff-baseline-relabel}} **P2・新規**: 論文図 `fig2_backoff_mechanism.png` を
  再作成する。現図は横破線を `stock adaptive backoff` と label しているが値は無 backoff であり、
  描いている系列も headline 非適格な profile 系列である。tracked な生成器が存在しないため、
  再現可能な生成器を伴う後継図を別 filename で作る (既存 PNG は凍結スナップショットの共有物なので
  上書きしない)。sweep 系列で描き直すか、profile 系列のまま `no-backoff control` と正しく
  label するかの選択を含む。根拠は
  `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。
