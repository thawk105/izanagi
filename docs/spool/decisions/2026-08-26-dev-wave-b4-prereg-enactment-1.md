---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-b4-prereg-enactment
seq: 1
---

## {{D:b4-prereg-fields-stay-empty}}. B-4 事前登録 §5 は 1 欄も埋めず、代わりに §5.1 の解除条件を締める

**決定:** B-4 還流 ablation の事前登録 §5 の値欄は、本 wave で **1 セルも埋めない**。
全 10 欄が §5.1 の解除条件を満たさないためである。代わりに、解除条件そのものが欠けていた
3 欄へ規範を新設し、埋められない機械的理由を §10 へ書く。**文書は発効しない。**

**理由:**
- `floor` と `校正済み PerfConfig` は計測 campaign を要する。§5.1 は既存値の流用を禁じ、
  `default_perf()` は自ら「性能比較用の校正ではない」と宣言している。
- `対象 driver と軸` は §5.1 (ii) の probe を要するが、**その条件を満たす sanctioned CLI が
  存在しない**。build を伴う経路は次の synthesis と primary / secondary outcome を生成するため
  probe にならず、`--no-build` 経路は §3.1 の切替点を通らない。
  当初の親の裁定はこの点を取り違えており、段 3 の敵対レンズが refuted した。
- `env_tag` / `実行責任者` / `開始時刻` の 3 欄には **§5.1 の解除条件が存在しなかった**。
  任意値や後付け値を拒む規範が無いまま埋めると、異なる環境・時点・実行主体の試行を同じ発効版へ
  紐付けられる。埋めるのではなく規範を足すのが正しい。
- §6 は「1 つでも未充足なら実走しない」と定める。埋まらない欄を埋めたことにする書き換えは
  絶対規律 2 が禁じる方向である。

**却下した選択肢:**
- **埋められる欄だけ埋める** — `primary outcome の演算定義` は一見埋められるが、tie・欠測・
  非 certified の順位規則は各 block の比較値と確率優越を直接変える分析契約であり、
  既成事実化せず裁定へ返す。
- **解除条件が無い 3 欄をそのまま埋める** — 拒む規範が無い欄を埋めるのは、事前登録の
  拘束力を持たない値を書く行為であり、ancestry 条件を形式的に満たすだけの空洞化にあたる。

## {{D:b4-wiring-binds-invocation-not-proposal}}. B-4 の必須配線は「閉じた critic の併存」までを閉じ、決定と proposal 本文の因果は未了として残す

**決定:** 段 4 driver への必須配線は、**閉じた critic invocation が実在し、当該 campaign・arm・
iteration・digest・driver 種別に束縛され、一度だけ消費されたこと**までを機械強制する。
`prior_critic_reverse` は自己申告を禁じ receipt 由来にする。
**「その決定で次の合成を行った」ことは本 wave では閉じず、事前登録の未了項目として残す。**

**理由:**
- proposal が持つ receipt hash は proposal 作成者の**自己申告**である。valid な receipt を取得し、
  その hash を legacy critic 由来の proposal へ書き写せば通る。段 3 と段 6 の敵対レンズが
  独立にこの穴へ到達した。
- 閉じるには決定を入力とする sanctioned な proposal producer と、生成後の proposal bytes を含む
  handoff receipt が要る。閉じた critic module は設計上 proposal を書かない。規律 5 (段階導入) に従う。
- **狭めたうえでも到達点はある。** 以前は閉じた critic を一度も起動せずに off アームを名乗れた。
  以後は当該 campaign・arm・iteration・digest に対応する certified な起動が実在し一度だけ
  消費されることが要り、停止挙動を変える 1 bit も自己申告できない。偽装の costは実際に上がった。
- 到達点を実態より広く書けば、off 汚染された標本が受理集合へ入り、偽の negative が論文 §8 へ流れる。

**却下した選択肢:**
- **通行券のまま「前提条件 3 を充足した」と書く** — legacy 経路が実際には塞がらないため、
  差が出なくても「還流に価値なし」と読めない。絶対規律 2 が禁じる緑化にあたる。
- **proposal producer まで本 wave で実装する** — 合成ループ全体を閉じる別機構であり、規律 5 に反する。

## {{D:b4-marker-is-provenance-not-authority}}. B-4 の識別は campaign identity へ残す marker で行い、marker を分類の権限と見なさない

**決定:** B-4 として走ったかどうかは、`search_config` へ焼く exact な protocol marker で識別する。
marker 不在の通常走行には key 自体を足さず、既存 campaign の identity を 1 bit も変えない。
**marker は自己申告であり、分類の権限を証明しない**と事前登録へ明記する。

**理由:**
- 既存の `reflux` key は 3 driver の `default_cfg` が常に焼くため、存在判定では B-4 走行と
  通常走行を分けられない。
- `search_config` は campaign identity の正準原像に丸ごと入る。**新 key を無条件で足すと、
  B-4 でない通常走行の campaign 識別子まで変わり、既存 campaign dir・WAL・checkpoint が
  参照できなくなる。** opt-in にしてこれを避ける。
- marker は provenance にはなるが、marker を付けて任意の config を B-4 と名乗ること、および
  marker 不在の campaign を報告時だけ B-4 と名乗ることは機械では止まらない。
  必要条件であって十分条件ではない。

**却下した選択肢:**
- **receipt 引数の存在で B-4 を判定する** — receipt を省けば通常走行へ降格でき、閂にならない。
- **CLI flag だけで識別する** — 成果物に残らず、後から通常 campaign を B-4 と再分類できる。
- **marker の値に receipt の schema 文字列を流用する** — receipt schema を上げると campaign
  identity まで動き、同一実験の campaign が別 ID へ割れる。
