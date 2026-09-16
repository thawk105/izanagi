# 旧 A-2 attempt の条件記述を訂正した図 (fig7) — 凍結を壊さずに誤った命題を直す

`authority: none` / `default_effect: no-state-change`。可変状態の正本は worklog 末尾と現行 phase doc。

## 何が問題だったか

論文図 5 `fig5_a2_certification_reject` は attempt `t2022-20260828c` を描く。値・median・効果・
外側 protocol status はすべて正しい。**誤っているのは条件の記述だけである。**

この attempt は patch が当たっていない stock の CCBench 木で走り、adopted cell が要求した
`BACKOFF_FIXED` (fixed 10 µs / 5 µs) は cmake の argv に載ったが、pin `511c9538` の CCBench に
対応する option 定義が無いため compile definition にならなかった (F707 の再発)。
実際に効いた条件差は `BACK_OFF` の 0/1 — CCBench 内蔵の**適応** backoff の有効/無効 — だけである。

ところが図は次の 2 箇所で「採用静的 backoff を測った」と述べ続けていた。

1. caption: `Median effects copied from certification are rr5 fixed 10 us … and rr50 fixed 5 us …`
2. **絵そのもの** — x 軸の目盛が `no backoff` / `fixed 10 us`、軸名が `performance arm`。

erratum は `docs/paper-story/figures/README.md` の fig5 節が持っていたが、**PDF を論文へ貼った
時点で erratum は付いてこない。**

## 依頼の前提が現行裁定で更新されていた (段 1 の実測)

依頼は D1645 (2026-09-05) だけを引いていたが、その後に次が着地していた。

- **D1993 (2026-09-14) 決定 1** — D1645 の「正しい identity で取り直した attempt が出るまで
  A-2 の結論を論文素材から外す」の解除条件は attempt `t2364-20260907b` が満たす。
  A-2 の結論は既に論文素材として使ってよい。その図は
  `fig6_a2_certification_observed_positive` として 2026-09-07 に着地済み。
- **D1936 項21 + D1993 決定 5** — 旧 fig5 の用途制限は**期限なし**。採用静的 backoff の
  結論・図として旧図を使わない。ただし「旧判定を歴史記録として説明すること」は禁じられていない。
- `docs/paper-story/figures/README.md` の追補が「旧画像・PDF・provenance JSON・統計・凍結稿・
  キャプション正文と outer `reject` は保持する」と明記。append-only の results 2 稿
  (2026-09-04 / 2026-09-07) が provenance JSON の SHA-256 `30113d50…` を記録している。
- **D1753** は「新しい図の filename を `fig5` 系にする」を凍結図との衝突を理由に却下済み。

したがって「図 5 を in-place で作り直す」は 4 つの現行裁定と正面衝突する。段 3 の 2 レンズは
**どちらも in-place を refuted と判定**し、「凍結解除も用途制限の撤回も求めずに依頼の目的を
満たす経路がある」と結論した。ユーザー裁定へ返す択一は無かった。

## 決定的だった機械事実 — caption は凍結 bytes と分離できない

`orchestrator/tests/test_plot_a2_certification.py::test_landed_fig5_repo_closure_and_caption_when_present`
が `validate_repo_closure` 経由で
`provenance["caption"] == _caption(provenance, _caption_prefix(outputs[0]))` を要求する。
**生成器の legacy profile の caption 文言を一律に直すと、fig5 を再生成しない限りテストが赤になる。**

親は段 1 brief でこれを「caption 訂正と凍結保持は両立しない」と一般化したが、**これは広すぎた**。
段 2 プランと段 3 の 2 レンズが一致して訂正した — **出力 prefix で分岐すれば両立する。**

## 採った設計 — 既定を正しい側に置き、凍結を例外として列挙する

段 2 プランは「新 prefix なら訂正版を返す」allow-list を提案したが、裁定は**逆向き**に採った。

```
FROZEN_LEGACY_CAPTION_PREFIXES = ("fig5_a2_certification_reject",)
```

legacy profile の caption・目盛・provenance の既定を**訂正後**にし、この列挙に載る出力 prefix の
ときだけ凍結済みの旧文言・旧目盛・2 行 provenance を返す。

**理由:** allow-list 側だと、将来 legacy 権威から別の図を作った人が黙って誤った条件記述を得る。
既定を正しい側に置けば、誤りを持つのは明示的に凍結した 1 件だけになる。列挙の長さは同じで、
新しい gate も検査層も増えない。列挙は機能の台帳ではなく「この 1 成果物の caption は訂正前の
文言で凍結されている」という**凍結の記録**である。caller は「どの成果物か」だけを選び、
caption 文字列を注入できない (D1752 / D1753 の形を踏襲)。

## 段 6 のレビューが暴いた被覆穴 (real、fix 済み)

段 5 の実装子が `test_cli_writes_complete_provenance_with_repo_relative_argv` の出力 prefix を
`fig5_fixture` から凍結名へ変えた (仮 repo に改訂稿が無いと `build_provenance` が落ちるため)。
その結果、**既定 (非凍結) legacy 経路を CLI から通す検査が消えた。**

レンズ B が具体的な欠陥を名指しした — **`main` が prefix によらず常に
`frozen_legacy_caption=True` を渡す**欠陥を、どの assertion も捕まえられない。
その欠陥が入ると、**caption は訂正済み・provenance は 3 行なのに絵だけが旧 `fixed 10 us` 目盛**の
図を新規生成しても検査が通る。

fix は `test_default_legacy_cli_provenance_argv_and_axis_labels` を足して閉じた。
`_publish_outputs` へ委譲する観測 wrapper で `main` を通し、実際に描かれた x 目盛と軸 label を
検査する。実処理を差し替えていないので、機構を stub で迂回していない。

## 不採用にした所見 (レンズ A、real だが must-fix にしない)

「新 caption が改訂稿に無い精密日時 (`created_utc`) を持つ」。**不採用。**
当該日時の権威は `tracked_inputs` の `certification` / `raw_manifest` 2 行 (権威 bytes) であり、
改訂稿ではない。成果物自身が `caption_source` 行の `authority_scope` を
`condition description only; not measurement values or protocol status` と明示的に限定している。
削れば出所のある provenance 情報を caption から**減らす**ことになる。
**この所見は親の prompt が「改訂稿を唯一の照合先」と読める書き方をしたために生まれた。**
レンズの誤りではない。

## 親の変異事前登録は 3 件が誤っていた

段 4 で登録した M1 / M2 / M5 の期待 node と赤理由が誤りだと、**両レンズが独立に指摘**した。

- M1 — 共有列挙は `_caption` と `build_provenance` の**両方**が読む。空にすると caption 不一致と
  入力集合の 2 系統で落ち、単一理由にならない。`_caption` 内だけの変異へ再照準した。
- M2 — 期待 node は 2 件ではない (訂正 caption テストは 2 parameter、加えて旧図着地・
  凍結負例の正常確認・新図着地 closure も同じ caption 投影理由で落ちる)。
- M5 — README 逐語一致は変異で変わらないので赤理由にならない。`_assert_named_landed_bundle` は
  closure で先に止まる。

**推測で再登録せず、probe 走で観測 node を実測した。** その結果、訂正後の期待 node は
5 件すべて probe の観測と完全一致した。

## 残る限界 (主張しないこと)

- 着地 closure は `tracked_inputs` の**行の削除自体を拒否しない**。記載された行の hash は束縛するが、
  着地 JSON の入力集合を完全固定する保証ではない。
- `caption_source` に `.md` を束縛したので、**同稿を 1 byte でも直すと着地 fig7 が赤になる**。
  同稿は自身を凍結物と宣言しているので運用上は整合するが、結合は存在する。
- 訂正 caption テストの図番号導出は 1 桁前提で、複数桁の図番号は射程外。
- 図の値・判定・cell identity は fig5 と同一である。**新しい測定は 1 件も行っていない。**
- 本図は採用静的 backoff についての結果ではない (D1936 項21・D1993 決定 5、期限なし)。

## 還元判断

CCBench 側の問題ではない。**還元対象なし。**
