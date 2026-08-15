---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t987-oracle-spec-design
seq: 2
---

## {{D:oracle-n-not-derivable-from-a12}}. 8b oracle の replicate 数を a12 stress-check から導出しない

**決定:** 8b oracle の事前登録値 `n` の根拠として a12 stress-check
(`output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json`) を
使わない。較正からの導出も、対象環境・対象 workload・対象 estimator での分布を
実測して誤選択率または検出力の目標を事前固定するまでは、承認材料として提示しない。
承認パッケージに書けるのは費用点の実測値と、導出に要る pilot の仕様だけである。

**理由:**
- a12 の `J` は t139/a11 study の cluster 数であり、その選択規則は当該 study の検出力基準
  (`J = min{ j in {4..13} : L_j^cert >= 0.80 }`) である。8b oracle の
  `build_schedule` における replicate 数と同一視する一次資料は無い。
- a12 が模擬する判定式は `mean - q*sqrt(s/J) > 0` という標本平均・標本分散・`q(J)` による
  下側信頼限界だが、配線されている `judge_oracle` の集約は各 trial の bench rep 中央値を
  さらに中央値へ畳む median of medians であり、configuration 間は float 完全一致による
  argmax である。同関数の docstring 自身が「この集約規則はまだ再凍結されておらず、
  実測開始前に明示的な再凍結が必要である」と宣言している。
- 下流の verdict が使う floor 条件も `median(on) - median(off) > floor` という
  **点推定値の閾値判定**であり、統計的不確実性の gate ではない。
  すなわち a12 相当の規則は下流にも配線されていない。
- a12 artifact 自身が `claim_scope.value = "a11_empirical_stress_model_only"` と
  `pilot_ready = false` を宣言している。
- 較正からの代替導出も同定されない。標本中央値の漸近式 `1.253*sigma/sqrt(n)` は
  iid な単一標本中央値のものだが、実 estimator は二段推定であり、certified 条件が使うのは
  2 推定量の**差**である。手元の較正は別 read ratio・別 extime の within-run CV しかない。
  同じ仮定の変奏で必要な `n` が 7 から 14 まで振れることを段 3 敵対子が算術で示した。

**却下した選択肢:**
- a12 の J 範囲 `[4,13]` を `n` の安全域として提示する — 別 study の別統計量の範囲であり、
  oracle の受理挙動を一切支配しない。proof chain の参照が誤る。
- 精度係数 `q(J)/sqrt(J)` の平坦化点を採る — 事前固定された elbow 規則が無く、
  評価判断であって導出ではない。値は J=13 まで単調に下がり続ける。
- floor protocol の session 数と同値を継承する — 別 estimator の数値先例にすぎない。
- 限界を注記したうえで推奨値として出す — 非同定な値に注記を付けても、
  ユーザーは承認の可否を判断できない。

## {{D:widening-split-from-narrowing}}. 受理集合を広げる改訂に、未裁定の縮小を混ぜない

**決定:** 正しさ防壁の受理集合を広げる改訂を設計するときは、同じ変更に含まれる
**縮小**を分離して別の裁定項にする。旧集合と新集合は、pin・authority・root の型・
全 entry の型を含む**同一の状態空間**で定義し、「拡大部分」と「安全側の縮小部分」を
別々に承認できる形で提示する。純拡大に留められる案がある場合は、それを先に置く。

**理由:**
- 規律 2 が求めるのは「広げる範囲と根拠の明示」である。同じ変更に未裁定の縮小を混ぜると、
  **承認された範囲が事後に判別できなくなる。**
- 8b oracle の lifecycle gate 改訂で実際に起きた。現行検査は `rglob("*")` + `is_file()` で
  走査するため、空の下位 directory・directory を指す symlink・broken symlink・FIFO・socket を
  受理している。これを no-follow の全 entry 比較へ置換すると、承認された 1 件を許す拡大と
  同時にこれらを拒否する縮小が入り、新旧は包含関係でなく**交差**になる。
  設計文書は当初これを「拡大だけ」と記述しており、段 3 敵対子が倒した。
- 縮小は必然ではなく選択である。走査規則を現行のまま据え置き pin 分岐だけを足せば、
  受理集合は純粋に拡大する。両案を並べて初めてユーザーは範囲を選べる。

**却下した選択肢:**
- 縮小を「安全側だから」として同じ承認に含める — 安全側かどうかは走査対象の実状態に依存し、
  root 自身が symlink や regular file である場合の扱いなど未設計の領域が残る。
  安全側だという判断自体が裁定対象である。
- 縮小を先に単独で行う — 現行から悪化しない拡大を待たせる理由が無く、
  かつ縮小だけでは lifecycle gate の目的 (承認済み 1 件を通す) を満たさない。
