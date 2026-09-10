## 検査した範囲

- merge commit `813c660333425670adccbb8222278df0d8f77add`
- wave 親 `053ddb2734391fcbf32a4968052f3dc409482861`
- main 親 `9388a6d399d3b541277e9620012d48d57f005022`
- 両親から HEAD への差分、対象 2 file、schema、改名先 gate の定義と呼出経路を静的検査した。
- pytest は実行していない。親の 377 件成功も所見の根拠にはしていない。

## real 所見

なし。

## refuted 所見

- 改名の取り残しはない。合成後は import と呼出しがともに `require_certified_commit_evidence` へ揃っている (`orchestrator/campaign/layer3_report.py:66,888`)。wave 側から追加された差分にも旧名参照はない。
- 関数・fixture の名前衝突はない。両親が追加した top-level 定義名の共通部分は空だった。wave 側が拡張した `_campaign` の引数はすべて既定値付きであり (`orchestrator/tests/test_layer3_report.py:206`)、main 側の `_certifying_campaign` はその契約と整合している (`:268`)。`_record` の env 既定値変更も main helper の明示設定と矛盾しない (`:269-270,581`)。
- certified 経路で pin 不在が新たな硬い赤になる懸念は refuted。`build_accepted_report` は `build_report` を経由するが、pin 不在時は `_validated_pin_path` が `None` を返し (`orchestrator/campaign/layer3_report.py:412-417`)、候補なしとして直下候補の照合を継続する (`:494-507`)。authority/WAL の env 不一致も同様に候補なしとなる (`:358-363`)。SHA 不一致と境界違反だけは従来どおり硬い赤である。
- schema と main 側受入経路の矛盾はない。producer は一致した floor に 3 種の根拠値を載せ (`orchestrator/campaign/layer3_report.py:591-603`)、schema は同じ 3 値を許可する (`orchestrator/campaign/layer3_schema.json:257`)。field は必須化されておらず、既存 artifact の後方互換も維持される。accepted report の再検証もこの schema を通る (`orchestrator/campaign/layer3_report.py:916`)。
- 合成後だけの fail-open はない。wave 側の pin/path/SHA 条件を通過した後、main 側の COMMIT 証拠 gate が独立して掛かる (`orchestrator/campaign/layer3_report.py:874-897`)。合成後の certified 受理集合は両条件の積であり、片親より広い入力は生じない。zero-COMMIT は引き続き拒否される。

## 総括

merge 合成に限定した real 所見は 0 件。旧名、fixture 合成、pin 不在、schema、受理集合の各境界に、両親では正しく合成後だけ壊れる箇所は確認できなかった。