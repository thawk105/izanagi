---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: worktree-dev-wave-t1142-oracle-n-pilot
seq: 1
title: 8b oracle の n を導出可能にする pilot を作り、目標を実測前に凍結した (コード + テスト + docs、branch worktree-dev-wave-t1142-oracle-n-pilot)
---

## 本文

[T-987] が「n は導出不能」と確定させた直系の後続。**導出不能の原因は 3 層あった。**

1. **判定規則の誤認。** 8b の勝者決定は on/off の 2 者比較ではなく、holdout ごとに
   6 configuration を並べた median-of-medians + float 完全一致 argmax である。
   親は brief で「素の構成との paired 差」を主対比に置いたが、実 estimator と一致しない。
   既存凍結も stock_common を「併記用の文脈セル」として検定比較対から除いている。
2. **目標の未定義。** 真の順位が未知なので素朴な誤選択率は定義できず、連続ノイズ下の
   完全一致 argmax はほぼ常に false unique-best を返すため、定義の取り方だけで
   結論が 0 と 1 の間を反転する。
3. **標本の不足。** R=8 では分散の相対標準誤差が 53.5% になり、[T-987] の
   「必要 n が 7〜14 に振れる」幅をそのまま再生産する。

**解は indifference-zone。** 誤選択を「真の best より相対 δ を超えて劣る構成を選ぶこと」と
定義し、tie は誤りに数えない。目標は (δ, α) の格子として事前登録し、出力は単一の n ではなく
表 `n(δ, α)` とする。**これで答えが振れるのは宣言済みの (δ, α) の違いによってだけになる。**
単一の (δ, α) 確定は集約規則の再凍結に属するので本 wave では選ばない。詳細は
{{D:oracle-n-indifference-zone}}、下限宣言と条件付けは {{D:oracle-n-pilot-lower-bound}}。

**敵対レビューが親の裁定を 4 件倒した。** (P3) 誤選択率を仮定なしに測れるという主張は
反証され (真の best が未知、global tie の二義性)、(P2) R=8 は算術で不足を示され、
(P1) 母集団は「同一 allocation 条件付き」と限定され、(P6) pin 不変仮定は撤回された。
逆に親が疑った build provenance の GeneratorId 流用は refuted (専用 ID 新設は policy SHA を
変えるので有害)、新 module 追加による凍結 5 source の失効も refuted
(`APPROVED_SPEC_SHA256=None` で承認自体が不在)。

**変異が静的レビューの見逃しを 1 件検出した。** 12 変異は生存ゼロだったが、
`test_m3_cache_containment_rejects_before_prepare_or_build` の 3 node が
**containment guard を丸ごと外しても緑のまま通った**。`match="cache_root"` が緩く、
3 param の cache root がいずれも実在しない directory だったため、guard を外しても
後段の identity 検査が同じ語を含む例外を投げていた。締め直し後は guard を外すと
赤になる node が 1 件から 4 件へ増えた (実測)。敵対 2 本はこれを指摘していない。

**実機に投げて初めて出た欠陥が 4 件。**机上のレビュー 5 本 (プラン・敵対 2・レビュー 2) の
いずれも指摘していない。(i) job script が third-party 依存 (gflags/glog) を配線していない、
(ii) `sort_best` の SWO oracle 環境が未配線、(iii) **job script が repo HEAD との等値を
要求しており、記録を 1 つ commit するたびに走行が拒否される循環に入った**、
(iv) `use_perf=True` の決め打ちで、perf の無い計算ノードで測定が落ちる。

(iii) はユーザーが「並行セッションを立ち上げ続ける。HEAD が違うからと長時間作業を
繰り返すなら一生終わらない」と指摘して止めた。**計測の同一性を決めるのは driver /
job script / 凍結データ / submodule pin / 環境契約の 5 つの内容ハッシュだけであり、
repo 全体の HEAD はそこに何も足さない偽の結合である。** 等値要求を撤廃し HEAD は
観測値として記録するだけに変えた。実測では main が 93 commit 進んでも固定 5 入力は
1 つも変わっていなかった。
(iv) は既存契約に正解があった — `use_perf_from_receipt` が唯一の入口で、
`_assert_perf_mode` は pilot モードでのみ no-perf を許す。決め打ちをやめて preflight から
導出し、実際の値と perf 条件を成果物へ記録する形にした。

**待ち手の自作で 4 時間空転した。** `qstat` は存在しない request にも rc=0 を返すため、
`! qstat` で終了判定する自作待ち手が永久に回り続けた。計算ノードの job は 338 秒で
成功終了し成果物も出ていたのに、`.done` が書かれず通知が来なかった。
runbook §7.3 が「待ち手を自分で書き起こさない ([T-740])」と明記していた型である。
判定材料をスケジューラの会計サマリ (`Ended Request Time:`) へ変え、成功・失敗双方で
書かれることを実測してから張り直した。

pilot は非公式の探索計測であり、出力 schema の `eligibility` 4 flag
(certified / floor_input / oracle_input / n_decision) はすべて false に固定されている。
`n` の値・`holdout_freeze.json` の floor/budget・oracle spec の承認値には触れていない。

## 次の一手差分

### 更新

- [T-1142] **P2・pilot 実装完了、実測進行中**: n を統計的に導出可能にする pilot を実装し、
  目標を実測前に凍結した。誤選択は indifference-zone (真の best より相対 δ を超えて劣る
  構成を選ぶこと、tie は誤りに数えない) と定義し、(δ, α) の格子を事前登録して
  表 `n(δ, α)` を出す形にした。実測は Pegasus・rr20/rr80・extime=5・6 configuration の
  12 cell で、1 巡 = 320 秒 (12 cell 各 26.7 秒、min 26.6 / max 26.8) を実測済み。
  R=33 を 3 allocation へ分割して取得中。**n の値は本 wave では確定しない** —
  集約規則の再凍結 (D143 (b) + [T-987] (b) + 世代移行) に従属する。
  per-pair floor も埋めない。
  base: 1bab5574f1604aabddd5f62bb71af1e432c484ce6b759d71e41d191d4f6f6a46
