## 変異ごとの判定

以下はすべて静的判定であり、pytest は実走していない。

| 変異 | 静的な結果 | 赤になる理由 |
|---|---|---|
| M1 base 射影削除 | N1、N2、N3 が RED。N4、N5 は GREEN | N1 は未射影 ID のままなので最初の不一致 assert で失敗する (`test_p3_b4_launcher.py:361`)。N2 は contract bind も消えるため失敗する (`test_p3_b4_launcher.py:384`)。N3 は raw ID を束縛した context が driver spy の射影済み ID と一致せず、最初の production validator で失敗する (`test_p3_b4_launcher.py:424`)。 |
| M2 marker のみ | N2 だけ RED。N1、N3、N4、N5 は GREEN | marker は campaign ID に入る一方、`bound_environment_contract` は正準 preimage に入らない (`ident.py:196`, `ident.py:212`)。したがって N1 の ID 比較と N3 の ID 授権は通り、N2 の直接比較だけが失敗する。marker は現 helper と同じく PEGASUS_COMPUTE だけへ加える変異として判定した。 |
| M3 base 条件を sort に拡大 | N5 だけ RED。N1からN4は GREEN | PEGASUS_COMPUTE では helper が `measurement_env` を加える (`p3_s4_loop.py:153`)。これは `search_config` 経由で ID に入るため (`ident.py:216`)、N5 の ID 比較が失敗する (`test_p3_b4_launcher.py:503`)。 |
| M4 site を literal OTHER にする | N1、N2、N3 が RED。N4、N5 は GREEN | N1 は compute marker が付かず raw ID のまま、N2 は PEGASUS contract ではなく OTHER contract、N3 は launcher の raw ID と spy の compute ID が不一致になる。N3 は G4 より先の validator で止まる。 |

M1 の追加 RED である N2 は、同じブロック削除を根に持つが、ID 欠落とは別の postcondition、すなわち contract bind 欠落を検出している。M4 の N2 も同様に別の postconditionで、追加の N3 は N1 と同じ ID 不一致を別経路で検出する。

## 所見 (real)

RA1. 最重要として、off arm だけ壊す変異が 5 node すべてを通過する。

具体的には実装条件を次へ変える。

```python
if driver_kind == "base" and context.arm == "on":
```

base 系の直接 test はすべて既定の arm `"on"` の `_test_context()` を使う (`test_p3_b4_launcher.py:36`, `test_p3_b4_launcher.py:339`, `test_p3_b4_launcher.py:382`, `test_p3_b4_launcher.py:465`)。N3 も `launch_bootstrap(..., arm="on")` だけである (`test_p3_b4_launcher.py:444`)。したがって N1 の「both arms」は reflux on/off config を列挙しているだけで、launcher context の arm は両方とも on である。

実 production では context の arm がそのまま `_driver_configs` へ渡る (`p3_b4_launcher.py:379`, `p3_b4_launcher.py:556`)。off launch では射影が消え、launcher の raw off ID と base main が再導出する compute ID がずれ、`drive_iteration` の exact validator に拒否される (`p3_s4_loop.py:2335`, `p3_s4_loop.py:2345`)。これは実装を壊す非等価変異である。

RA2. LOGIN/SUSPECT の fail-close を壊す変異も全 5 node を通過する。

例えば base 分岐で次を挟む。

```python
site = site if site in {"OTHER", "PEGASUS_COMPUTE"} else "OTHER"
```

その後は現行の `_admit_env_contract` と `_campaign_cfg_for_site` を呼ぶ。全 node の hostname は `bnode116` または通常ホストだけであり (`test_p3_b4_launcher.py:337`, `test_p3_b4_launcher.py:370`, `test_p3_b4_launcher.py:397`, `test_p3_b4_launcher.py:463`, `test_p3_b4_launcher.py:488`)、この変異に感応しない。

一方、現行の exact admission set は OTHER と PEGASUS_COMPUTE だけで、他は `ExecutionGuardError` で拒否する (`p3_s4_loop.py:133`, `p3_s4_loop.py:138`)。裁定も LOGIN/SUSPECT の早期拒否を実装結果としている (`s4-adjudication.md:82`)。したがって scope 内の SURVIVED mutant である。

RA3. N5 は sort の ID 不変しか検査せず、contract bind だけを混入させる変異を殺せない。

例えば sort に次の分岐を加える。

```python
elif driver_kind == "sort":
    site = p3_s4_loop._current_site()
    contract = p3_s4_loop._admit_env_contract(site)
    configs = tuple(
        ident.bind_environment_contract(cfg, contract)
        for cfg in configs
    )
```

`bound_environment_contract` は変わるが (`ident.py:100`)、campaign ID の正準 preimageには含まれない (`ident.py:196`, `ident.py:212`)。N5 は ID しか比較しないため通過する (`test_p3_b4_launcher.py:501`)。これは「sort の挙動を 1 bit も変えない」という不変条件 (`s4-adjudication.md:152`) を破る。

RA4. 事前登録された death set と単一理由の記述は不完全である。

- M1 は N1/N3 だけでなく N2 も RED。
- M4 は prompt 表の N1、裁定表の N1/N2 に加えて N3 も RED。
- M1 は ID 射影欠落と contract bind 欠落という独立した postcondition を壊す。したがって suite 全体について「未射影 ID だけが理由」とは言えない。
- 各 node 内では、N1 の二つの比較は同じ ID 欠落の結果であり、独立した原因ではない。N2 の複数 arm/site も同じ bind 欠落である。node 単位の DW-M03 違反というより、death set 全体の過剰決定である。

単独変異の主証拠としては M1=N1、M2=N2、M3=N5、M4=N1 と読むのが明確であり、追加 RED は冗長な検出として扱うべきである。

RA5. N3 は M1/M4 に対する G4 の mutation-red 証拠にはならない。

driver spy は最初に `require_b4_production_context` を呼び (`test_p3_b4_launcher.py:424`)、その後に G4 を呼ぶ (`test_p3_b4_launcher.py:432`)。両者とも campaign ID を比較する (`p3_b4_launcher.py:362`, `p3_b4_launcher.py:516`) が、M1/M4 では前者が例外を投げるので G4 へ到達しない。

したがって N3 は正系列で「両実物 validator を通る」証拠ではあるが、単独変異から「G4 が M1/M4 を殺した」とする証拠からは外すべきである。差し替えが必要という所見ではなく、負の証拠の射程限定である。

## 所見 (refuted)

RA6. `require_any_context` や site admission が狙った比較より先に M1からM4を拒否する、という懸念は refuted。

base marker 作成時の `require_b4_any_context` (`p3_s4_loop.py:1411`) は seal、evidence class、driver kind までしか検査せず、campaign ID を比較しない (`p3_b4_launcher.py:296`)。各 fixture は対応する driver kind の context を渡している。使用する compute/OTHER site も admission 済みなので、直接 node は目的の assert まで到達する。N3 も campaign mismatch については最初の exact validator まで到達する。到達しないのは、その後段の G4 だけである。

RA7. helper 差し替えを等価変異とする裁定は正しい。

base の `_campaign_cfg_for_site` (`p3_s4_loop.py:147`) と trigger の同名 helper (`p3_s4_loop_trigger_gating.py:458`) は、signature、docstring、全 body が逐語的に同一である。参照する `_SITE_ENV_TAGS`、`_CAMPAIGN_ENV_KEY`、`_lookup` も同じ値・関数へ設定されている (`p3_s4_loop.py:117`, `p3_s4_loop_trigger_gating.py:101`)。launcher は `_contract` も明示的に渡すため、差し替え先固有の admission 呼び出しにも入らない。SURVIVED が正しい期待値である。

RA8. N3 の「launcher 分岐の証明であり base main 全体の実走証明ではない」という自己申告は、実質的に正確である。

N3 は実 `launch_bootstrap` を通り、context 発行、base config 作成、campaign bind、sidecar、context activation、registry dispatch を実行する production 経路を対象にしている (`p3_b4_launcher.py:551`, `p3_b4_launcher.py:571`)。さらに spy 内で実物の production validator と G4 を呼ぶ。

一方、registry の base entry は spy に置換されている (`test_p3_b4_launcher.py:442`) ため、`p3_s4_loop.main`、proposal 読み込み、`drive_iteration`、実 COMMIT からの G4 routing は実走しない。「launcher 分岐」はやや短い表現だが、過大・過小な証明主張にはなっていない。

## scope 外だが real (裁定へ返す候補)

該当なし。RA1からRA3はいずれも、段4裁定が明示した両 arm、site admission exact set、sort 不変の範囲内である。

## 総括

5 node は M1からM4を予定どおり殺すが、death set は事前登録より広い。特に M1 は N2、M4 は N3も追加で RED になる。

一方で、次の三つの非等価変異が全 5 node を通過する。

- base projection を context arm=on に限定する
- LOGIN/SUSPECT を OTHER へ丸める
- sort に campaign IDを変えない contract bind だけを加える

したがって「実装された 5 node が必要な変異検出力を持つ」という主張は成立しない。N3 は実 launcher/context の有用な正系列証拠だが、M1/M4では最初の production validator が G4 を遮るため、G4固有の mutation-red 証拠ではない。静的検査のみで、pytest は実走していない。