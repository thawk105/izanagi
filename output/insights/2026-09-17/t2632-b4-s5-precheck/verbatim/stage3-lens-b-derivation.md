## 所見

以下、`C/` は `orchestrator/campaign/`、`V/` は `/home/SFC/tanab/.claude/jobs/421393cc/tmp/wave/verbatim/`、`R/` は `output/env/pegasus/calibration/registered/` を指す。

### B1. base の resolver 同定は正しいが、registry 属性経路との同値性は現世代に限る

- 判定候補: real
- 根拠: `C/p3_s4_loop.py:117` の literal 写像を `:138` の `_admit_env_contract()` が `env_contract.lookup()` へ渡す。launcher も `C/p3_b4_launcher.py:166` でこの経路を使う。Pegasus wrapper は `tools/pegasus/p3_s4_loop_pegasus.sh:581` から base CLI を起動し、`C/p3_s4_loop.py:2678` で同じ解決を行う。一方、`C/p2_2.py:215` と `C/floor_pair_driver.py:1633` は required 属性から選ぶ。
- 親 brief への影響: **P3 修正文:**「現 checkout では両経路が同じ g1 object／`pegasus` を返すことを独立再現した。ただし恒久的な同値性はない。required 契約の追加・属性変更では属性経路が拒否したり別契約を選んだりする一方、base は literal の tag を引き続ける。g1→g2 の同 tag 更新だけなら双方とも追随する。」

既存 base 関数の評価は機械導出と呼べる。ただし「registry 属性から導出した」とは書けない。D924 の `lookup()` 使用には沿うが、写像の二重定義が消えたわけではない。

### B2. 計算ノード判定に NQSV marker は必須ではない

- 判定候補: real
- 根拠: `C/site_policy.py:30` の分類関数は、`:40` で `bnode[0-9]+` なら `has_nqsv` に関係なく `PEGASUS_COMPUTE` を返す。`:66` の `require_evidence=True` でもこの条件は変わらない。marker が効くのは主に Pegasus login／suspect の分類。
- 親 brief への影響: **P4 修正文:**「現コードの compute 分類は `bnode*` hostname による。『hostname + NQSV marker が必要』とは記さない。login 上の実観測は `PEGASUS_LOGIN` であり、compute 引数による写像評価とは区別する。」

### B3. precheck に計算ノード dispatch が必須、という反論は成立しない

- 判定候補: refuted
- 根拠: `V/prereg-s5-s5.1.md:180` は確定した driver・site から同じ resolver による tag 確認を要求するが、記入前確認を計算ノード上で実施するとは定めていない。`C/p3_s4_loop.py:138` は解決済み site を入力する関数。既存較正の acquisition receipt には計算ノードの観測がある（各 JSON `:4`／`:6`）：rr95=`bnode027`、rr50=`bnode048`、rr5=`bnode013`。
- 親 brief への影響: **P4 修正文:**「site が確定していれば、login から対象 driver の写像を評価する静的 precheck は可能。ただし live site admission を通過した証拠ではない。」

receipt は hostname／allocation の証拠であり、**B-4 resolver が計算ノード上で実行され `pegasus` を返した記録ではない**。較正 argv の `--env-tag pegasus` も明示入力である。確認した成果物から、この強い主張はできない。D1641 の床値 site を B-4 本走の確定と読めるかは、別途授権範囲の問題として残る。

### B4. 契約の三種類の hash を混同してはならない

- 判定候補: real
- 根拠: `C/env_contract.py:168` の `contract_sha256` は契約 dataclass の canonical JSON hash。source file の bytes hash ではない。g1／g2 は `:253`／`:270`、発効選択は `C/env_contract_activations/00000001.json:1`。未発効 hash は `C/env_contract.py:901` で拒否される。
- 親 brief への影響: **P3(b) 修正文:**「発効版の契約記録は、source path＋source bytes SHA、activation artifact path＋artifact bytes SHA、選択された env_tag・generation・contract_sha256 を区別して併記する候補とする。」

独立再計算は親と一致した。

| 対象 | SHA-256 |
|---|---|
| `C/env_contract.py` の bytes | `292bbed314a6824e0618da83d1d94253f0290e4db0b3e509200a79221508bc9a` |
| activation JSON の bytes | `6a44b5b117d95539406d4d08b5f0f558424306b248574b16d7f92c04aceec34d` |
| active g1 の契約 | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| 未発効 g2 の契約 | `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c` |

source hash 単独では active 世代を示せず、activation hash 単独では契約の全 field を示さない。上記併記は再検証可能な候補であり、§5.1 の既裁定書式と断言はしない。

### B5. attestation 較正と動作点較正の hash 不一致だけでは矛盾にならない

- 判定候補: refuted
- 根拠: `C/loop.py:186` が契約の較正を load し、`C/execution_guard.py:601` がその SHA と `contract.calibration_ref.sha256` の一致を要求する。`:612` 以降で使うのは attestation profile。動作点側の records／threads／workload 照合は、例えば `C/floor_pair_driver.py:1182` 以降の別処理である。
- 親 brief への影響: **P3(b) 修正文:**「g1 本走の attestation は `753f535a…` に束縛される。しかし records の出所を別の accepted 較正に置くことと、hash が違うだけで機械的矛盾にはならない。attestation 用較正と動作点用較正を明記して区別する。」

これは g1 の健全性を保証しない。D1537 の自己不整合と世代発効順序は引き続き残り、別較正の profile を g1 の guard へ代入すれば拒否される。

### B6. 較正 JSON と argv の再計数は親の報告を支持する

- 判定候補: refuted
- 根拠: 3 JSON の tracked 状態と完全 SHA を独立照合した。records は rr95=`1,000,000`（`R/calibration-5c836a22eff9ab40.json:1617`）、rr50=`1,000,000`（`R/calibration-94a4b79fa31bba3c.json:1612`）、rr5=`2,000,000`（`R/calibration-2b7ba072b88023ae.json:1618`）。各末尾の workload は3 key、threads=48、rmw=`"0"`。全階層の key を再帰走査し、`extime`／`reps` key はともに0件。
- 親 brief への影響: **P2 はこの点で維持。**「`reps` の出現は `acquisition_receipt.walltime.formula` の文字列値内のみ。rr5 の長い説明も同じ値内であり、反復数 field ではない。」

3 job の tracked argv にも `--extime` は無い。`orchestrator/calibrator/cli.py:150` の既定3と合わせた復元は支持される。ただし `V/D2088.md:34` のとおり、取得当時の source bytes まで検証した復元ではない。

### B7. 「較正から供給できる」と「B-4 CLI に供給する経路がある」は別

- 判定候補: real
- 根拠: `C/floor_pair_driver.py:1154` は較正を読み、`:1182` 以降で**既に作られた** perf と比較する binder。`C/p2_2.py:338` も手書き定数との比較で、`:367` の `PerfConfig` は定数と呼び手の workload から作る。どちらも較正から B-4 設定を生成する経路ではない。base CLI は `C/p3_s4_loop.py:2745` で無条件に `default_perf()` を使い、`:1565` の値は records=100000／threads=4／extime=1／reps=2。
- 親 brief への影響: **P2 へ追加:**「較正3件は動作点の材料を供給するが、§5 の pin を実走 `PerfConfig` へ束縛する既存 base CLI 経路は確認できない。裁定と値の書式だけでなく、承認済み設定への差替え・消費経路が不足している。」

ここは **code で閉じる（実装は本 wave 外）**。専用 producer の新設が必須という意味ではない。

### B8. workload 3 key をそのまま完全な PerfConfig と呼べない

- 判定候補: real
- 根拠: `C/pipeline.py:184` の dataclass 自体は workload を検証しないが、`:209` の `performance_correctness_workload()` は `ycsb_max_ope` を含む exact 4 key を要求する。この検査の呼出しは `C/loop.py:160` の performance verify mode に限られる。floor 側は別型で、`C/floor_pair_driver.py:197` に max_ope を持ち、`:1589` で workload へ加える。
- 親 brief への影響: **P2 修正文:**「較正が供給する workload は3 key。B-4 の完全な設定には、取得構成から復元した `ycsb_max_ope="10"`、extime、B-4 用に承認された reps、および3 workload と設定の対応を明示する必要がある。」

`"0"` と `"false"` の差そのものが型拒否を起こすわけではない。しかし既定値で置換する根拠にもならない。較正の3 keyは逐語保持し、max_ope の追加規則を別に示すのが妥当。**「4 key 検査が全 B-4 本走で必ず発火する」とは一般化しない。**

### B9. 2欄の機械検査は弱く、複合値を通せても解除条件の証明にはならない

- 判定候補: refuted
- 根拠: `C/p3_b4_admission_record.py:663` は対象2欄について非空・予約 sentinel 不在だけを見る。`:704` 以降の専用解析は model／prompt／projection 欄。表構造は `:646` で `|` 分割される。
- 親 brief への影響: **P2／P3(d) 修正文:**「改行や `|` を含まず、sentinel を含まない `key=value; ` 複合値・複数 SHA は、この2欄の検査では拒否されない。ただし path の実在、hash 一致、設定への適用、確認者の授権は検査されない。」

`V/prereg-s0.md:6` の説明文・条件禁止と原子性は別に守る。`V/D1641.md:5` の指名を B-4 env_tag 確認者へ自動適用できることも、code からは証明できない。発効版への確認者併記は `V/prereg-s5-s5.1.md:183` の明示要件である。

### B10. 既存 base lock は記入可否を閉じない

- 判定候補: refuted
- 根拠: `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/campaign.lock:1` は親の再計数どおり records=100000／threads=4／pin=`028f34d`、`measurement_env` 無し。
- 親 brief への影響: **P2／P3:** 本題の記入可否には効かない。新しい較正済み設定や Pegasus resolver の証拠として使えない、という限界だけを記す。

## 裁定パッケージ候補

- B-4 本走の driver・site・tag を、床値についての D1641 と区別して確定する。導出記録には対象 checkout と base の実際の resolver 経路を残す。
- 契約の併記候補は、source path／bytes SHA、activation path／bytes SHA、generation／contract_sha256。発効時点の active 契約と照合し、g2 の前方参照を現行導出として扱わない。
- 完全な B-4 `PerfConfig` と3較正の対応、extime／max_ope の復元根拠、reps の選択・承認を確定する。確認者の識別子と委任範囲も発効版に残す。
- 承認済み設定を base CLI が消費する経路は **code で閉じる（実装は本 wave 外）**。literal／属性 resolver の二重定義も、恒久的一致を求めるなら **code で閉じる（実装は本 wave 外）**。
- admission が複合値を受理することを、§5.1 の意味的充足の根拠にしない。既存の正しさ条件は緩めない。

## 総括

- 親の較正値・SHA・契約世代・key 再計数に誤りは見つからなかった。
- `pegasus` は現 checkout の base resolver から機械導出できる。別 resolver との将来の同値性や live admission 成功までは示さない。
- 較正3件だけでは完全な B-4 `PerfConfig` は組めず、特に実走 CLI への反映経路が親の不足一覧から落ちている。
- 2欄とも今日記入しないという結論を支持する。静的検査と read-only probe のみ実施し、pytest・測定・記入は行っていない。