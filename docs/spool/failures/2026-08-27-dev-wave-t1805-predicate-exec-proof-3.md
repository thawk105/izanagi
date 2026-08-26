---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1805-predicate-exec-proof
seq: 3
---

## 新規

### {{F:truncated-failure-digest-misdiagnosis}}. 切り詰められた failure digest を主因判定の根拠にした [手順漏れ]

- 事象: 焦点走が 118 件の赤を返し、親は描画された excerpt だけを見て
  `configuration-mismatch` を主因と判定した。修正後の赤は 117 件で、ほぼ減らなかった。
  同じ誤りを 2 度繰り返した。真因は 1 nodeid の単独走で全文を採って初めて判明した。
- 根本原因: 焦点走の failure digest は byte 予算 (49152) で切り詰められ、
  117 件中 10 件しか描画しない。母集合と描画数の差を確認せずに分布を読んだ。
  `-q -rf` は 1 件あたりの excerpt が大きく、描画率がとくに低い。
- 恒久対応: 主因判定は**切り詰められていない出力**で行う。
  `--tb=line` へ切り替えると 1 件あたりが小さくなり描画が 10 件 → 44 件へ増える。
  それでも足りなければ 1 nodeid の単独走で全文を採る。
  digest の `omitted_failures` を必ず読み、0 でなければ分布を主因の根拠にしない。
- 再発検知: 「n 件中 m 件しか描画されていない」を報告に書かせる。
  既存 memory「道具の絞り込み後の値を総量として引用しない」と同型。

### {{F:shared-component-mandatory-evidence}}. S8b 固有の証拠要求を共有部品の必須引数にした [権限逸脱]

- 事象: 実装子が 2 度、異なる部品で同じ誤りを犯した。単位 A は S8b の関門を共有
  `prepare_cell` へ無条件に入れ、S1 の 57 テストを落とした。単位 B は
  `source_snapshot_sha256` を共有 `build_v2` の既定値なし必須引数にし、
  `pipeline` 4 箇所と `b10_backoff_shape_sweep` 1 箇所を呼出し時点で TypeError にした。
- 根本原因: 実装子 prompt が「証拠の要求はその主張が立つ境界に置く」を書いていなかった。
  新しい証拠を「必須にする」方向が既定で正しいと見え、共有部品の受理集合を全利用者に対して
  狭めることの意味 (受理集合の縮小ではなく他 campaign の可用性喪失) が指示に無かった。
- 恒久対応: 実装子 prompt に定型として入れる —
  「証拠の要求は主張が立つ境界に置く。共有部品の受理集合を変えない。
  共有部品へ足す引数は既定値ありにし、既定時は変更前と厳密に同じ挙動 (cache identity の
  preimage に key を足さないことを含む) にする」。
- 再発検知: 共有部品へ引数を足す変更では、未指定時の digest が変更前と一致することを
  機械で固定するテストを要求する。本 wave では固定 digest の一致で確認した。

### {{F:gate-placement-vs-fake-driven-tests}}. 実 I/O を要する関門を fake で駆動される経路へ置いた [テスト代表性]

- 事象: 関門の設置場所を 4 度変えた。共有実体化器 (57 件が落ちる) →
  identity 合成器 (下流 117 件) → campaign の build 経路 (同) →
  build 実装の内側 (解消)。設置場所を変えるたびに焦点走を回し直し、
  118 → 117 → 161 → 222 → 3 と推移した。
- 根本原因: 単体テストは実 build を注入で差し替える。実 CCBench repo と実 pin を要求する処理を
  campaign コードへ置くと、それらのテストは必ず落ちる。
  段 1・段 4 の時点で「関門候補の経路を fake で駆動する既存テストが何件あるか」を数えていなかった。
- 恒久対応: 関門は**その主張が立つ最小の場所**へ置き、identity 合成器や共有 wrapper へ置かない。
  判定材料は「その経路は既に実 I/O を行っているか」「その経路を fake で駆動するテストが何件あるか」。
  テストが実 build を飛ばすとき関門も一緒に飛ぶのが正しい対応関係である。
- 再発検知: 関門を新設する wave では、段 4 の裁定に関門候補ごとの
  「fake 駆動テスト件数」を書かせる。

### {{F:overlap-scan-counts-main-advance}}. 編集面の重複測定が main 側の前進を編集中と誤認した [手順漏れ]

- 事象: 依頼が「稼働 wave が対象 file を編集中」と告げ、重複測定でも 14 の worktree が
  `s8b_floor_campaign.py` を触っていると出た。未 commit 差分だけで測り直すと、生きた編集は
  test 2 file だけで、production file には 1 件も無かった。誤った所有制約のまま進めば、
  編集できる面を編集できないと誤認して wave が着地不能になるところだった。
- 根本原因: 重複測定が `git diff --name-only main` を使っており、これは **worktree が main から
  遅れている分** (main 側が進めた file) も差分として返す。古い worktree ほど多くの file が
  「編集中」に見える。
- 恒久対応: 編集面の重複は**未 commit 差分** (`git diff` と `git diff --cached`) で確定する。
  branch tip との三点比較は所有の判定に使わない。
- 再発検知: 重複を根拠に所有を分ける裁定では、測り方を根拠と併記する。

### {{F:killed-dispatch-leaves-orphan-hold}}. 走行を kill しても計算ノード job が残り、以後の投入を全部止めた [手順漏れ]

- 事象: 焦点走を `pkill` したところ、投入ラッパーだけが死に計算ノード job が残った。
  その worktree に orphan hold が作られ、次の焦点走が rc=16 で弾かれた。
  hold の解除手順は「対象の不在または終端を `qstat` で確認してから手動削除」であり、
  手動 `qdel` は投入禁止フラグを立てるため使えない。
  さらに変異 harness でも、前走の container が残っている間は所有を拒否された。
- 根本原因: 「再投入は新しい path で」という規律は `--out` / `--attempt-out` について
  明文化されているが、**kill が queue を空にしないこと**と **scratch root も再走ごとに
  新しくすること**が書かれていなかった。
- 恒久対応: 走行を止めたら、次の投入前に対象 job の終端を `qstat` で確認する。
  再走は `.done` / 出力 / scratch root をすべて新 path にする。`qdel` は使わない。
- 再発検知: 投入が rc=16 で戻ったら、まず orphan hold の有無と `qstat` を見る。
