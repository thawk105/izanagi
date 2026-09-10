# B-4 権威 floor 成果物の発行と配線 — D1530 が求めた「実 producer の接続と同じ変更単位」

2026-09-07〜08。dev-wave `b4-floor-issue-wire`。branch `worktree-dev-wave-b4-floor-issue-wire`。

## 何が壊れていたか

B-4 の production 分析経路は、材料レポートの生成器が凍結評価器へ無条件に `floor=None` を渡し、
評価器が必ず `FLOOR_DOMAIN_ERROR` を立てていた。**block 数や入力の正当性によらず、どんな測定を
入れても分析 verdict は `protocol_violation` の 1 種類しか出ない。**

これは事故ではなく既知の設計で、D1592 が事実として記録し、修正を先送りしていた。同 D の却下欄は
本 wave を名指ししている。

> **本 wave で production の floor を配線する** — 権威ある floor 成果物の発行が前提であり、
> 本 wave の scope 外である。D1530 に従い、実 producer の接続と同じ変更単位で閉じる。

本 wave がその変更単位である。

## 段 1 で実測して分かった、依頼が書いていなかったこと

**値の producer は既に存在した。** `orchestrator/campaign/floor_pair_driver.py` が create-only の
summary へ `candidate_floor` を出す。欠けていたのは (a) それを権威成果物として発行する経路と、
(b) 材料レポート側の配線の 2 つだった。事前登録 §11 も「§5 の floor 行を埋めるだけでは正規経路は
変わらない」「材料レポート側の接続は別の裁定と実装である」と明記している。

**そして型が断絶していた。** driver の `candidate_floor` は **float** だが、凍結契約の
`as_b4_exact_fraction` は float を明示的に拒否し、`int` / `Fraction` / `(int, int)` だけを受ける。
**発行段で exact ratio へ変換しない限り、配線しても恒真に `floor_domain_error` のままで機構が
空回りする。** これを段 3 の攻撃対象 (P1-a) に据えた。

## 丸めをめぐる対立と、その解き方

段 3 の 2 レンズが正面から対立した。

- レンズ A: 段 2 案の `nextafter(+inf)` による 1 ULP 切上げでは **exact D を覆わない**。
- レンズ B: `nextafter` は型変換ではなく **未裁定の値改変**であり、`as_integer_ratio()` で足りる。

親が数値で追試したところ、**両方とも正しかった**。

```
candidate_1=0.10000000000000003, candidate_2=reference=0.1 のとき
driver の D (binary64)      = 2.220446049250313e-16
その直上 1 ULP              = 2.2204460492503136e-16
同じ入力を exact 有理数で   = 2.7755575615628914e-16   ← なお大きい
```

切上げても足りず、かつ切上げ自体が未裁定の値改変である。**そこで丸めをやめた。**
`Fraction(*candidate_floor.as_integer_ratio())` で値を 1 bit も変えず型だけを合わせる。

exact 再導出への差し替えは採らなかった。それは producer の統計量を consumer が別に計算し直すこと
であり、D1383 (AI が値を既成事実にしない) と D1699 (D の式は実走前に凍結する) の両方に触れる。
**残る限界は非保証欄へ逐語で書き、裁定パッケージへ返した。**

## 段 6 の敵対レビューが見つけた実欠陥 8 件

すべて real、refuted ゼロ。7 件を直し、1 件 (一般 hardening) は scope 内と裁定して残した。
最も重かったのは次の 3 つである。

1. **`-0.0` が値域検査と bit 一致比較の両方をすり抜ける。**
   `-0.0 < 0.0` は偽、`-0.0 == 0.0` は真。producer は `abs()` を通すので必ず `+0.0` を出し、
   **`-0.0` は producer が生成し得ない入力**である。`math.copysign` で判別して拒否した。
2. **summary が束縛した spec を producer の閉 schema で検証していなかった。**
   `.get()` の拾い読みだったため、producer が絶対に受理しない spec からでも発行できた。
   新しい validator を書かず、**producer 自身の `load_frozen_spec()` を呼ぶ**形へ直した。
3. **不在時 bytes の非退行 test の oracle が、変更後のコード自身だった。**
   両辺に同じ変異を入れると通ってしまい変異帰属が立たない。変更前のコードから採取した
   **固定 digest** を test へ焼き込む形へ直した。

## 変異走行が暴いた、レビュー 2 本が見逃した欠陥

probe 段 (16 件) で 1 件が SURVIVED した。

**非保証の逐語を「source summary の参照先を実在照合していない」から「照合済みである」という
偽の主張へ反転しても、どの test も落ちなかった。** 段 6 の must-fix が要求した「検査していない
ことを検査済みと読める表現を残さない」が、実際には test で守られていなかった。

逐語を pin する test を足して閉じた。**逐語は module 定数を参照せず test 側へ literal で書いた。**
定数を参照すると、定数を書き換えたときに両辺が同時に変わって検査が空回りする。

**敵対レビュー 2 本が見つけられず、変異走行だけが見つけた欠陥である。**

## 走行中に producer の版が変わった

wave の走行中に別の作業 ([T-2369] / D1699) が main へ着地し、producer が v2 から v3 へ上がった。
親が local ref と現物で裏取りした非互換は 3 点。

- `floor-pair-summary` v2→v3。**`floor-pair-spec` も v2→v3** (plan と window も上がっていた)。
- `session_medians` が平坦な 3 role から side ごとの `{candidate, reference}` の入れ子へ。
- `compute_gain_difference` が 4 引数へ。D は各 side が自分の probe 区間内で測った reference を
  分母にする形へ。

段 4 の裁定は「pin の前進は T-2369 着地後の follow-up」としていたが、**その T-2369 が本 wave の
走行中に着地したので前提が覆った。** v2 のまま着地させると、取り込み後の実 producer の出力を
すべて拒否し、D1530 が禁じた「使われない防壁」になる。再裁定して v3 対応を本 wave に含めた。

その結果、**非保証の 1 件が偽になった。** 「その版が D1699 適合をまだ満たしていない」は、
v3 producer が D1699 の求めた形を実装したことで成り立たなくなった。実際に証明していないこと —
「凍結が測定の結果を見る前に行われたことを証明しない」— へ差し替えた。
**偽の非保証を残すことは、検査していないことを検査済みと読ませるのと同じ向きの誤りである。**

## 変異 matrix

3 段で回した。

|段|件数|結果|
|---|---|---|
|probe|16|KILLED 11 / MISMATCH 2 / SURVIVED 3|
|本走|14|KILLED 13 / MISMATCH 1|
|M15 erratum|1|KILLED 1|

**最終: baseline PASSED、KILLED 14、SURVIVED 0、MISMATCH 0。**

- probe の MISMATCH 2 件 (M8 / M9) は書式ずれだった。実測には xdist group 接尾辞
  `@p3-b4-material-report` が付き、M9 は 4 状態のうち `[True-False]` だけが落ちる。
- probe の SURVIVED 3 件のうち **M12b / M12c は冗長 gate**。M12a の `-0.0` 拒否が先に効くため
  到達しない。DW-M03 に従い単独変異の証拠から外した。**M15 だけが実欠陥だった。**
- 本走の MISMATCH 1 件 (M15) は**期待より広く検出された**型。issuer 側 1 node を期待したが、
  材料レポート側の伝播 pin も落ちて 2 node になった。erratum を残して期待集合を実測へ直し再走した。
- 除外: M1 (issuer 単体へ帰属せず、契約側の `floor_domain_error` が先に出る)。

harness の collection 照合は、**期待 node の書き間違いを 2 回とも投入前に捕まえた。**
1 度目は fix によって test が parameterize されていたこと、2 度目は v3 適合で v2/v3 の負例が
入れ替わって param 名が変わったことによる。

## 証明していないこと

- **binary64 の中間丸めにより、記録された float D は同じ入力を exact 有理数で計算した D より
  小さいことがある** (上記の実例で差 5.55e-17)。値を変えない方針を採ったのでこの限界は残る。
  実効上の大きさは相対 1e-16 で、床値の典型値 (3% 級) の 14 桁下である。
- **凍結が測定の結果を見る前に行われたことを証明しない。** 成果物を読むだけでは時点は分からない。
- **source summary の参照先を実在照合していない。** 権威成果物が指す summary の path と hash は
  形だけ検査する。
- **D1696 が人手責任に残した 9 項目**は検査していない。exact 2 window・標本数・24 時間間隔・校正照合・
  セル集合の一致・authorization journal・raw が JSONL であること・finalize hash 束縛・
  成果物名の意味的一致。
- **本 wave は事前登録の発効も §7.1 の 4 分類の実効化も主張しない。** §5 は sentinel のままである。
- repo 内の挙動検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない
  (D387)。

## 権威 floor の発行を実際に通すには、独立した 2 つの障害が残る

どちらか一方を直しても発行は通らない。

1. **`protocol` が凍結 spec に存在しない。** D1641 は成果物名に env_tag・protocol・threads・
   workload・campaign 識別子の 5 要素を求めるが、v2 でも v3 でも spec の exact top-level key 集合に
   `protocol` は無く、build receipt からも導出できない。issuer は推測せず、
   欠けている要素名を付けて発行を拒否する。
2. **[T-2412] 凍結 spec loader の hash 不動点。** 別 wave の報告によれば、loader が
   「spec bytes == HEAD の blob」と「spec 内 source_commit == HEAD」を同時に要求するため、
   追跡 file である spec が作成不能である。したがって当面 `candidate_floor` 自体が生成されない。

## 収録物

- `verbatim/` — 段 2 plan、段 3 レンズ A / B、段 5 実装 A / B、段 6 レビュー A / B、fix 1〜4、
  段 1 brief、段 4 裁定、段 6 裁定
- `mutation-spec-probe.json` / `mutation-ledger-probe.json` — 変異 probe 段
- `mutation-spec-final.json` / `mutation-ledger-final.json` — 変異本走
- `mutation-spec-m15-erratum.json` / `mutation-ledger-m15-erratum.json` — M15 の期待集合の erratum 再走

逐語はいずれも子の出力そのままで、親は編集していない。子の主張がそのまま正しいことを意味しない —
親が real / refuted を裁定した結果は各 commit message と本書にある。
