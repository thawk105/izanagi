# 段 4 裁定 — [T-2632] 順序 (2) precheck (§5 の 2 欄)

親 (Claude、role=integrator)。段 3 の 2 レンズ (A = 裁定整合、B = 機械導出) の所見を real / refuted で裁定し、
brief の P1〜P5 を plan v2 相当の結論へ改める。実装は無い (実装差分ゼロ)。変異事前登録は免除 (実装面差分ゼロ)。

## 所見の裁定

| 所見 | 判定 | 採否と反映 |
|---|---|---|
| A1 「D1483 以後改訂なし」は広すぎる | real | 採用。「この 2 欄の記入順序を解除する後続裁定は無い (D1812 (a) は primary outcome 欄の既存記入の維持、D1871 は開始時刻だけの例外)」に限定 |
| A2 §11.1 手順 4・5 を先行記入の許可と読む反論 | refuted | P1 維持。導出・校正・証拠準備は先行できるが値セルは記入できない (手順 8「確認結果だけでは §5 を変更しない」) |
| A3 床値用 reps の承認を本走へ包括委任と読む反論 | refuted | P2 / P5 維持。承認対象は値だけでなく、その出所を §5.1 の要件にどう位置付けるかを含める |
| A4 extime は「calibrator が決めた出力値」ではない | real | 採用。records / threads / workload 3 key = 較正出力、extime / max_ope = 取得構成からの復元 (D2088 は取得当時の source bytes まで検証していない)、reps = 設計上の選択、の 3 種に分ける |
| A5 床値の site を本走 site の指名と読む反論 | refuted | P3 (a) 維持・精密化。「既存の床値計画・較正を使うなら Pegasus が整合する候補だが、一致要件から本走 site の指名済みまでは導けない」 |
| A6 確認者の不足は identity でなく委任の担当範囲 | real | 採用。裁定パッケージを「thawk105 名義の AI 委任を今回 2 欄の確認・記入へ及ぼすか (担当範囲の追加)」へ改める。D1641 だけで確定済みとは扱わない |
| A7 世代の選択と artifact の同定を分ける | real | 採用。今の導出証拠は g1。発効版には発効時点で有効な契約と整合する証拠を併記し、g2 登録を activation 済みと読まない。model snapshot 欄の陳腐化検査が env_tag 欄にもあるとは書かない |
| A8 複合セルの書式は新裁定待ちにしない | real | 採用。書式は裁定パッケージから外す (確定値の `key=value; ` 列挙は AI が作れる。書式の自由は reps や契約証拠の不足を補わない) |
| A9 login の resolver 呼出しで示せる範囲が限定されるという反論 | refuted | P4 維持。site が確定していれば login からの静的導出は可能。live admission・単独性・将来の active 世代は証明しない。計算ノード dispatch は本 precheck に不要 |
| A10 2 欄の記入で結合証拠の不足が解けるという反論 | refuted | 維持。2 欄は必要条件であって十分条件ではない |
| B1 literal 写像と registry 属性の同値は現世代限り | real | 採用 (記録)。B-4 sanctioned 経路 (`p3_b4_launcher.py:166` → `p3_s4_loop.py:138`、wrapper は `p3_s4_loop_pegasus.sh:581` → `p3_s4_loop.py:2678`) は literal の tag を引く。恒久一致を求めるなら code (本 wave 外) |
| B2 compute 分類は `bnode*` hostname (NQSV marker は不要) | real | 採用 (親の記述を訂正、`site_policy.py:40`) |
| B3 precheck に計算ノード dispatch が必須という反論 | refuted | 採用 (記録)。較正 receipt の hostname (bnode027 / bnode048 / bnode013) は allocation の証拠であって「B-4 resolver が計算ノードで `pegasus` を返した記録」ではない。較正 argv の `--env-tag pegasus` も明示入力 |
| B4 契約の 3 種の hash を混同しない | real | 採用。source bytes sha256 / activation bytes sha256 / contract_sha256 (canonical JSON) を区別して併記する候補。未発効 hash は `env_contract.py:901` が ever-active でないとして拒否 |
| B5 attestation 較正と動作点較正の hash 不一致を矛盾と読む反論 | refuted | 採用 (記録)。`execution_guard.py:601` は attestation profile の較正 (g1 = 753f535a) を束縛し、動作点側 (records / threads / workload) は別処理。機械的矛盾ではないが g1 の健全性 (D1537) は保証しない |
| B6 較正 JSON / argv の再計数 | refuted (親と一致) | 維持。`extime` / `reps` key は全階層で 0 件、`reps` 文字列は `acquisition_receipt.walltime.formula` 内のみ |
| B7 較正からの供給と B-4 CLI への供給経路は別 | **real (親 brief の落ち)** | 採用。base CLI は `p3_s4_loop.py:2745` で無条件に `default_perf()` を使い、§5 の pin を実走 `PerfConfig` へ束縛する既存経路が無い。§5.1 の「差し替えるまで記入しない」の「差し替え」は実装 wave を要する。code で閉じる (本 wave 外、専用 producer 新設が必須という意味ではない) |
| B8 3 key workload をそのまま完全な PerfConfig と呼べない | real | 採用。完全な B-4 設定には `ycsb_max_ope="10"` (取得構成からの復元)、extime、B-4 用 reps、3 workload と設定の対応が要る。4 key 検査 (`performance_correctness_workload`) は `loop.py:160` の performance verify mode に限る — 全 B-4 本走で必ず発火するとは一般化しない |
| B9 機械検査は弱く複合値を通す | refuted (親と一致) | 採用 (記録)。`p3_b4_admission_record.py:663` は非空・sentinel 不在だけ。改行や `|` を含まない `key=value; ` 複合値・複数 sha256 は拒否されないが、path 実在・hash 一致・設定への適用・確認者の授権は検査しない。意味的充足の根拠にしない |
| B10 既存 base lock は記入可否を閉じない | refuted | 維持。効かない |

## 結論 (plan v2 相当)

1. **2 欄とも今日は記入できない。** 第一の理由は、この 2 欄の記入順序 (D1483: 床値の 12 行裁定・測定・成果物の採用裁定の後) を
   解除する後続裁定が無いこと。12 行裁定は D1641 で済み、測定 (A-5 の spec 凍結を含む) と採用裁定は未了。
2. **順序が解けた後に PerfConfig 欄を埋めるために要るもの:** (i) B-4 用 `PerfConfig` の採用範囲の裁定 — 較正出力 (records /
   threads / workload 3 key)、取得構成からの復元 (extime=3 / ycsb_max_ope=10)、設計上の選択 (reps) の 3 種を分けて承認主体を
   決める、(ii) 記入者の担当範囲、(iii) 承認済み設定を base CLI が消費する経路 (code、本 wave 外)。書式は裁定不要。
3. **env_tag 欄を埋めるために要るもの:** (i) B-4 本走の driver・site・tag の確定 (床値の D1641 決定 3 とは別)、(ii) 確認者の
   担当範囲、(iii) 環境契約の artifact の読み (source / activation / contract_sha256 の 3 種併記、発効時点の active 世代と照合、
   g2 の前方参照を現行導出として扱わない)。tag `pegasus` の機械導出は今日できる (base の resolver、現世代限りの literal 写像)。
4. **本 wave では何も記入・実装・新設しない。** 規律 2 は緩めない。

## 裁定パッケージ (ユーザーへ返す)

既裁定で閉じる (返さない):
- 記入の順序 — D1483 / D1510 (§5 全欄は床値の鎖の後)、g2 発効の順序 — D1484。本 precheck を理由に前倒しを求めない。
- 床値の担当者・床値用 PerfConfig 承認・床値 3 cell と較正選択 — D1641 / D1812 (c) / D2088〜D2090。再裁定へ返さない。
- 複数較正を 1 セルに置けること・確定値の複合表記・部分記入禁止 — D1854 / §0 / 対象 driver 欄と model snapshot 欄の先例。書式案は AI が作る。

返す (いずれも順序 D1483 が解けた後に効く。今日の記入を求めるものではない):
1. **B-4 本走の driver・site・tag の確定。** 床値の D1641 決定 3 と区別して、B-4 本走の site を Pegasus 計算ノード (gen_S) と
   確定するか。推奨: 確定する (床値が対象動作点で測られる以上、別 site・別 tag では floor 欄が対象動作点を指さない)。
   導出記録には対象 checkout と base の実際の resolver 経路 (literal 写像) を残す。
2. **B-4 用 `PerfConfig` の採用範囲と承認主体。** 3 較正の出力値 (records 1M / 1M / 2M、threads 48、workload 3 key 逐語) を採ること、
   取得構成から復元した extime=3 / ycsb_max_ope=10 を採る読み、B-4 用 reps (候補 5 — `PerfConfig` 既定・床値 spec と同値、
   **AI 候補**) の承認。推奨: D1641 決定 3 と同型の委任 (thawk105 名義で AI が承認し D に残す) を B-4 本走の PerfConfig へ
   明示的に拡張する。「reps=5 でよいか」だけに縮めない (出所の位置付けを含める)。
3. **確認者・記入者の担当範囲の追加。** identity は thawk105 (D1266 / D1641)。未確定なのは、今回 2 欄の確認・記入まで AI 委任を
   及ぼすか。推奨: 及ぼす (新規人物の指名でも床値担当の再裁定でもない)。実走認可は含めない。
4. **環境契約の artifact の読み。** 併記候補 = `orchestrator/campaign/env_contract.py` (path + bytes sha256)、
   `env_contract_activations/<serial>.json` (path + bytes sha256)、generation + contract_sha256 (canonical JSON hash)。発効時点の
   active 契約と照合し、世代・契約 bytes・activation が変われば記入前 / 発効前に再導出する。推奨: この 3 種併記を採る。
   新 producer は前提にしない。

次の一手候補 (裁定でなく実装 T の候補、本 wave では開かない):
- 承認済み `PerfConfig` を base CLI が消費する経路 (`p3_s4_loop.py:2745` の `default_perf()` 無条件使用の差し替え)。§5.1 の
  「差し替え」の実体。専用 producer 新設が必須という意味ではない。
- literal 写像 (`p3_s4_loop._SITE_ENV_TAGS`) と registry 属性 (`lookup_required_attestation_contract`) の二重定義の解消 —
  恒久一致を求めるなら。
