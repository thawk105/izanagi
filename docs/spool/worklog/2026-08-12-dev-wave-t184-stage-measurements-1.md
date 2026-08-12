---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t184-stage-measurements
seq: 1
title: dev-wave 段別の所要時間・非受理率を receipt 397 件から実測し、resource envelope の択一を 5 直交軸へ再構成して測定先行を推奨した (docs のみ、branch worktree-dev-wave-t184-stage-measurements)
---

## 本文

2026-08-12 のユーザー裁定 ([T-184]) 「段別の実測一覧を作ってから resource envelope の択一を
再提示する」を実行した。実装面差分ゼロ。集計器は repo 外
(`dev-wave-jobs/dev-wave-t184-stage-measurements/`) に置き、repo へ入れていない。

**一次資料の同定が本 wave の実質的な発見である。** `tools/codex_worker_launch.py` が job ごとに
書く `receipt.json` (schema v3) に、段名・所要時間・上限・失敗の全 field が揃っていた。
2026-08-10 の前回提示が「台帳に資源上限の証拠は無い」と書いたのは、証拠が無かったのではなく
**この所在を把握していなかったため**である。`.done` file や mtime からの推定は不要だった。

母集団の作成で 1 度誤った。`find dev-wave-jobs -name receipt.json` の 1,362 hit のうち
3 分の 2 以上は別種 artifact (dispatch submission receipt 493、計算ノード job 出力 325、
pytest 一時 directory 内の複製 291 ほか) で、path だけで母集団を決めると 3 倍以上に膨れる。
必須 field による内容判定を足して 397 件に確定した。

段 3 の敵対相談 2 本 (sol = 集計方法論、luna = 推論と所有境界) が 22 件を返し、
うち 20 件を real として採用した。**3 件の blocker はいずれも実際に数値が誤っていた。**

- 被覆率の分子が集計器の実装バグだった。内容判定前の path 一覧から数えており、
  検証済み行から数え直すと receipt を持つ job dir は 52 (58 ではない)。
  投入の registry が無く分母を定義できないため、**被覆「率」の主張自体を取り下げた。**
- 「91 件すべて親が引き上げ」は誤りで、実際は引き上げ 90 + **引き下げ 1**
  (`t798-t799-finalize` の author が wall 1800 s・calls 60)。
- 「wall-clock には余裕がある」は 3 軸同時上限下の competing risk であって成立しない。
  proxy 2 軸で 964〜1,384 秒に殺された job が、その上限なしで 3,600 秒までに完了したかは
  観測できない。

さらに次を実データで確認した。**同一 logical job の外側再投入が 1 件実在し**
(`dev-wave-t657-stage0-rulings` の plan が別 artifact root で not_accepted → accepted)、
plan の非受理率は物理 3/46 = 6.5%、論理 2/45 = 4.4% と単位で変わる。
**token 上限で殺された consult 3 件は全件 luna** であり、段だけで括った上限が
段内の一方の lane を選択的に殺していた。CLI 版でも層が違う (0.146.0 は 21/348、
0.147.0 は 1/49)。

これらを受けて **親推奨を変えた。** 当初は「今 hybrid で段別値を決める」だったが、
具体値表を裁定パッケージから落とし、**測定先行**を推奨とした。値を決めるには
censoring を解く測定 (打ち切り 5 件の上限なし追走、事前登録した cap sweep、CLI 版の固定) が要る。
前回の「[T-183] 完了後」も改めた — resource で救えるのは非受理 22 件中 5 件だけだが、
resource の測定自体は [T-183] と独立に実行できる。

本 wave は canonical stage matrix も起動前 policy も発行していない。reasoning 面 (D266) は
値を 1 つも変えていない。retry policy には触れていない。
**[T-316] / [T-665] / [T-662] の待ちは解除されない。**

エージェント工数: 段 3 の 2 本のみ (luna 12,850 bytes / rc=0、sol 17,544 bytes / rc=0)。
待ち手が 1 度 rc=70 の偽失敗を出した — producer の pid を /proc 走査で取ったため別 process を
掴んだもので、`DW-O01` の detach 定型に「producer 自身が pid file を書く」段取りが
含まれていないことによる。子は生存しており、job-id で pid を取り直して待ち直した。

dogfood として、段 3 の consult 子には `max_cli_reported_tokens = 2e6` を渡した
(既定 1e6 は実測で consult を 3 件殺している)。したがって本 wave 自身の 2 件は
非既定層に入る。

## 次の一手差分

### 更新

- [T-184] **P1・ユーザー裁定待ち (実測完了)**: 段別の実測一覧を
  `output/insights/2026-08-12_t184-stage-measurements/` に発行した。receipt 397 件で
  非受理率は consult 11.8% / focus 10.0% / plan 6.5% (論理 4.4%) / review 3.2% /
  fix 2.4% / author 1.2%。既定上限が効いていた 306 走で **`max_wall_clock_s` の発火は 0 件、
  proxy 2 軸 (`max_model_calls` / `max_cli_reported_tokens`) だけが 5 件を打ち切った**が、
  これは 3 軸同時上限下の competing risk であり wall の余裕の証拠ではない。
  非受理 22 件のうち資源上限は 5 件だけで、残り 17 件は上限値を変えても解消しない。
  択一を直交 5 軸へ再構成し、**具体値は censoring のため出さず、測定先行を推奨**して
  裁定へ返した。reasoning 面 (D266) は不変、retry policy は [T-183] 依存のまま。
  本項を他タスクの待ち解除根拠にしない規定も不変。
  base: 19be848ccb52d32486664814254f5f79cb19e93a592e32f298b2ec97b968040a
