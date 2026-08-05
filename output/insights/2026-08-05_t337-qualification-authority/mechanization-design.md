# 正例 artifact 適格性の機械化設計 — **未実装。将来の設計メモ**

**この文書が記述する機構は 1 行も実装されていない。** すべて将来形で読むこと。
本 wave (`dev-wave-t337-qualification-authority`) は `DW-G04` 不成立と裁定し、docs だけを land した。
現在の実装被覆は **0/9 層**である ([T-339] が数えた 9 層 = 計測 producer / attempt registry /
schedule validator / RF calculator / 適格性権威 / 層 3 の次版 / selector consumer /
材料レポート consumer / 双射・変異検査)。

権威境界そのものの条文は decisions 台帳の新 D が正本であり、本メモはその機械化案だけを持つ。

## なぜ今日実装しないか

条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を示せるときだけ実装する (`DW-G04`)。
本 wave は示せなかった。実測は次のとおり。

- 3 arm を持つ唯一の計測 (request `877859`、`output/env/pegasus/t139-positive-control-probe/`) は
  W2 で順序が逆転して**不成立**であり、かつ 1 allocation・J=1 で cluster 間分散を 1 点も推定できない。
  負例の存在が条件付き機能の発火を正当化しないことは既決である。
- T-126 qualification producer は `output/env/pegasus/qualification/t126` へ書くが、
  当該 directory は現 worktree に**存在しない** (実 receipt 0 件)。加えて T-126 は subject/reference の
  二者であって 3 arm ではなく、`statistical_claim="none"`・`evidence-only/no-promotion` である。
- RF を消費する consumer と caller は repo 内に 0 件である。

## 発火条件 (これが揃った時点で実装してよい)

1. 3 arm (stock / 劣化版 / 候補) を持ち、事前登録を実走前に commit した計測が 1 本以上存在する。
2. その計測が `env_tag`・測定 checkout・CCBench pin・attestation を持つ。
3. RF decision を読む consumer (selector または材料レポート) の実 hook が実在する。

## 経路 (一方向)

```
raw receipts → read-only validator → hash 束縛 decision → sealed admission type → selector / 材料レポート
```

## producer が書けるもの / 書けないもの

producer が書けるのは、利用意図を示す閉集合の種別 field と、raw な実行事実・証拠 pointer だけである。
**種別 field の literal な名前は本 wave では確定していない** (ユーザー再裁定へ返した。理由は
`s4-ruling.md` の U1)。

producer が書いてはならない field は closed schema で未知 field として拒否する。最低限
`eligibility_status` / `pairing_valid` / `rf_acceptance_status` /
`recovery_measurement_eligibility` / `research_goal_eligible` / `pipeline_eligible` と
validator identity / result が該当する。

## validator の独立性 (段 3 レンズ A の指摘を反映)

- **consumer は decision を入力として受け取らない。** trusted validator を同一呼出し内で raw path から
  再実行し、その戻り値だけを使う。validator の source SHA-256 が decision に載っていることは
  「その validator が実行された」証拠にならない — producer は予定 validator の hash を読んで
  decision を偽造できる。既存 `orchestrator/campaign/artifact_admission.py` の
  `require_admitted_campaign()` が raw path から同一呼出し内で検査する形が先例である。
- **単一 fd / snapshot で読み、hash と parse は同一 byte buffer に対して行う。** 検査前後で hash を
  取り直す方式は ABA (検査中だけ適格な bytes に差し替える) を防がない。symlink は拒否する。

## 状態の閉表

固定閉表とする (「少なくとも」と書かない)。Q9 が状態名として裁定した
`weak_denominator_not_certifiable` を必ず含める。分母 screening は行わない。
`RF > 1` は「回復」とも「新規改善」とも帰属させず、stock 超過とだけ述べる。

## 再計算の順序

1. exact schema・closure・hash・measurement-start と事前登録 ancestry を再検証する。
2. arm label を信用せず、事前登録した source / binary identity へ再束縛する。
3. correctness anomaly は終端 reject とする (削除・置換・再試行で消せない)。
4. 事前登録した arm 代表値から cluster ごとに `D = m_stock − m_degraded`、`N = m_candidate − m_degraded`、
   `G = m_stock − m_candidate` を raw TPS から計算する。
5. RF は `E[N]/E[D]`、primary endpoint は trace-disabled の throughput とする。
6. `D > δ_D` かつ `N > 0` かつ `G > 0` の多重性調整済み同時信頼領域だけを適格性に使う。Fieller を primary とする。
7. J は実走前に固定し、結果を見てからの追加を認めない。

## 未解決 (この設計では塞げていない。**塞いだと書いてはならない**)

- **arm identity の再束縛先が無い。** 3 arm の source path/hash、binary hash、候補 bytes、`env_tag`、
  CCBench pin、trace mode を載せる field が現在の実成果物に存在しない。これが無い限り、
  合成システムが作っていない手製の中間版を候補と名乗らせる経路を閉じられない。
  producer 設計と同時に決める必要がある。
- **双射と family binding が自己根付きである。** 先に結果を見てから、成功した試行だけを含む
  事前登録 commit を作れば、schedule と attempts の双射も ancestry も通ってしまう。
  prereg manifest の path/hash、期待する workload / contrast / candidate の集合、`family_members`、
  alpha / spending 台帳、canonical registry head が別途要る。**file-drawer を塞いだとは言えない。**
- **cluster の独立性が自己申告である。** 同一 allocation・同一 node・同一時間窓の 33 run に
  `cluster_id` を 11 個振れば J=11 に見える。cluster を node / 時間窓から独立に導出する規則が要る。
  allocation ID の一意性検査だけでは足りない (Q4 は allocation ID すら独立性の必要十分条件ではないと裁定済み)。

## 識別子

RF study 側の試行 ID は **`rf_trial_id`** と綴る。既存 8c の `trial_id`
(`orchestrator/campaign/trial_registry.py`、H1/H2 × on/off/swapped の 6 cell、
`arm` / `holdout` / `campaign_id` に束縛) とは別実体であり、両者の foreign-key 規則は無い。
同名にすると材料レポートが RF decision を別の 8c trial へ結合しうる。

RF record の composite key は `(rf_trial_id, candidate_id, workload_id, contrast)` とし、
層 3 の calibration floor 閉表は広げず別区画へ置く。

## 実装候補 (発火条件が揃ってから)

`orchestrator/qualification/` 配下に raw receipt schema / decision schema / contract / append-only
registry / validator を新設し、`orchestrator/campaign/` 側に validator だけが生成できる immutable な
consumer 境界を置く。既存 `trial_registry.py`・T-126 schema・層 3 閉表・凍結 artifact には混載しない。
