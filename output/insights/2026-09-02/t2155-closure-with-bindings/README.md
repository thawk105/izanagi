# [T-2155] 閉包検査の誤った到達不能証明を直す — 一次資料

静的閉包検査 (`orchestrator/tests/test_ccbench_spawn_sites.py`) が誤って除外していた
2 経路を実際に被覆する形へ直した wave の実測記録。

- base (着手時の local main): `c1531d43b11cb4435d44a814bcc5f7d712ae2991`
- 実装 commit: `f1af403898263e193e161e43e63391ca8c04372b`
- probe の source は repo 外に保全した:
  `/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2155-closure-with-bindings/`
  (`probe_baseline.py` / `probe_blast_radius.py` / `probe_ab.py` / `probe_controls.py` /
  `probe_safeside.py` / `probe_failclosed_named.py`)。
  いずれも repo を読むだけで、実行時に検査関数を差し替えて数える。repo へは書かない。

## file の対応

| file | 内容 |
|---|---|
| `baseline-classification.txt` | 着手時 (base) の sink x macro 分類の全内訳 |
| `measured-ab.txt` | 欠陥 (a) のみ / (b) のみ / (a)+(b) の分類変化 |
| `measured-controls.txt` | 提案された正例・負例の判別力 (sink 採取の有無、行番号近似との差) |
| `measured-safeside.txt` | 依存判定を安全側へ倒す成分ごとの repo 全体への波及 |
| `measured-after-impl.txt` | 実装後の分類 (clean process) |
| `mutation-spec-pass1.json` / `mutation-pass1.json` | 変異 1 巡目 (17 変異) の spec と結果 |
| `mutation-spec-pass2.json` / `mutation-pass2.json` | 変異 2 巡目 (6 変異) の spec と結果 |

## 分類の推移 (sink 53 x macro 22 = 1166 セル)

| 状態 | proven-unreachable | covered | deferred | failures |
|---|---:|---:|---:|---:|
| base | 947 | 130 | 89 | 0 |
| 欠陥 (a) のみ | 943 | 134 | 89 | 0 |
| 欠陥 (b) のみ | 947 | 152 | 67 | 0 |
| 実装後 | 943 | 156 | 67 | 0 |

対象 2 sink:

| sink | base | 実装後 |
|---|---|---|
| `s1_direct_comparison.py <module>.run_role` 1215 campaign | proven-unreachable 22 | **covered 4 / proven-unreachable 18** |
| `s8b_oracle_driver.py <module>.run_block` 1788 campaign | deferred 22 | **covered 22** |

**s1 は 22/22 が被覆されたのではない。** 到達可能 domain の 4/4 が被覆され、
残り 18 は「この file の macro inventory に無い」という既存の証明で落ちている。
この inventory 証明の妥当性は本 wave の scope 外で、裁定パッケージとして返した。

## 裁定文の実測欄が現行 base で再現しなかった

`docs/archive/worklog-phase3-0901-1153-1154.md` の T-2155 原文は
「(a) を直すと s1 既定枝の 22 セルが `proven-unreachable` から `unresolved` へ移り、
(b) が無ければ赤になる」と書いている。**base `c1531d43b` では再現しない。**
実測では 4 セルが `covered`、18 セルが `proven-unreachable` になり、failure は 0 のままだった
(`measured-ab.txt`)。段 2 の plan も独立に同じ結論へ到達した。
当時の測定は当時の記録として保持し、現行 base の事実としては引用しない (規律 7)。
2 欠陥を 1 commit にまとめたのは確定済みユーザー裁定が同一変更単位を指定したためであり、
「片方が赤になるから」ではない。

## 正例・負例の判別力を実装前に確かめた

`measured-controls.txt`。合成 source 6 件すべてから campaign sink が実際に採取されることを
確認した (sink 0 件だと `failures == []` が恒真になる)。さらに、支配性を**行番号順で近似した
実装**では「分岐内にしか検査が無い」「検査後に同名を再束縛」の 2 負例が誤って通ることを実測し、
これらが支配性の実装を実際に判別することを確かめてから登録した。

## 縮退条件は構文でなく名前を鍵にした

`measured-safeside.txt` と `probe_failclosed_named.py`。
「file に class 定義があれば安全側へ倒す」のような構文を鍵にした条件では、
53 sink 中 27 sink (対象 2 file を含む) を巻き込み本題が壊れる。
checked 名 / helper 名を対象とする `global` / `nonlocal` と `import *` を鍵にすると、
触れる production file は 3 本だけ (`s8b_floor_campaign.py` の `resolved_contract`、
`silo_ladder_rung1.py` の receipt 定数、`t316_sandbox_backend_probe.py` の `max_threads`) で、
いずれも無関係な名前であり、**対象 2 file はどちらも該当しない**。

## 変異走行

1 巡目 17 変異: KILLED 12 (登録どおり) / MISMATCH 4 / SURVIVED 1。
MISMATCH 4 件は変異自体は効いており、落ちるテストの集合が親の予測より広かっただけである
(例: match guard の state 処理を外すと guard 系 3 本すべてが落ちる)。実測に合わせて訂正した。

**SURVIVED 1 件は冗長な防壁だった。** helper 乗っ取りの検出で「正規 import 以外の束縛があるか」の
層を無効化しても負例は落ちない。もう一層 (正規 import が呼出しより前にあること) が独立に
同じ入力を拒否しているためである。実効 gate へ再照準し、2 巡目で
(i) もう一層の単独無効化 → SURVIVED (事前登録どおり)、
(ii) 両層同時の無効化 → 狙った負例 2 本がちょうど KILLED、を確認した。
**初回の SURVIVED は消さず本記録に残す。**

2 巡目 6 変異: 6/6 一致。

事前登録から外した変異が 1 件ある。「checked-name を sink 行以降の呼出しからも取る」変異は、
「sink より後の検査を数えない」性質と「分岐内の検査を数えない」性質が
**同一の機構** (フロー順に積まれる state と sink 直前の snapshot) で実現されているため、
前者だけを壊す置換を作れない。冗長 gate と明記して単独変異の証拠から外した。
