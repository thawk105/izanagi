## 受理集合の不変性

- 所見: WW 理由の整列は SCC、cycle、anomaly 件数を変えない。`_sccs()` と `_shortest_cycle()` は `_reasons()` より先に完了し、理由列は選ばれた辺の説明にだけ使われる。プランの「分類まで先に完了」という含意だけは不正確で、`phenomenon` は理由再構成後に決まる。 / 判定: refuted / 根拠: `orchestrator/verifier/dsg.py:569-590`、`s2-plan.md:18` / 成果物への影響: 検出される SCC 数、報告 anomaly 数、cycle 選択は不変。 / 直し方: 実装変更は不要。プランの説明を「cycle 選択までは理由再構成前、分類は後だが型集合不変」に直す。

- 所見: `phenomenon` も不変である。`CycleEdge.types` は理由型を重複除去し、`_classify()` は全辺の型をさらに集合化する。WW 理由同士の順序変更は型集合に影響せず、WW、WR、RW の枝間順序も変わらない。 / 判定: refuted / 根拠: `orchestrator/verifier/model.py:375-389`、`orchestrator/verifier/dsg.py:523-545`、`orchestrator/verifier/dsg.py:548-567` / 成果物への影響: G0、G1c、G2 の分類は変わらない。 / 直し方: なし。

- 所見: `integrity.notes` の空理由枝も発火条件が変わらない。整列前後で走査する共通 key 集合と各 key の判定式は同一なので、`reasons` の長さがゼロかどうかは不変である。また `Integrity.clean()` は notes 自体を判定材料にしていない。 / 判定: refuted / 根拠: `orchestrator/verifier/dsg.py:524-546`、`orchestrator/verifier/dsg.py:583-589`、`orchestrator/verifier/model.py:450-467` / 成果物への影響: integrity の判定、verdict、certified は変わらない。 / 直し方: なし。

- 所見: 同一 key に複数の WW 理由は現行式では構成不能で、key 単独の整列で全順序になる。`u_writes` と `v_writes` はそれぞれ `key -> transaction commit` なので、交差集合の各 key は一度だけ現れる。各 key について判定は一度、追加も高々一度である。さらに一 transaction の全 write は同じ `Txn.commit` を版として使う。 / 判定: refuted / 根拠: `orchestrator/verifier/dsg.py:517-531`、`orchestrator/verifier/model.py:320-335` / 成果物への影響: `(key, u_ver, v_ver)` に広げても出力は変わらず、key だけで決定性を満たす。 / 直し方: なし。

## 親の実測と一般化の点検

- 所見: 「wr 枝は rw 枝と同じ `Txn.reads` list を走査する」という説明は、そのままでは不正確である。WR は宛先 transaction の `vt.reads`、RW は始点 transaction の `ut.reads` を走査する。同じ型の field ではあるが、同じ list object ではない。さらに公開 compact 経路では `_txn_from_columns()` が `Txn` を再構成するため、read の構築順保証は射影資料だけでは確認できない。 / 判定: real / 根拠: `orchestrator/verifier/dsg.py:31`、`orchestrator/verifier/dsg.py:507-515`、`orchestrator/verifier/dsg.py:533-545`、`orchestrator/verifier/model.py:327-335`、`s1-probe.md:37-50` / 成果物への影響: WW 以外に実在する非決定性を確認したわけではないが、「同じ list だから全 WR 入力も安定」という一般化の証明が閉じていない。 / 直し方: `_txn_from_columns()` と compact parser について、read index を昇順に appendすること、trace file の選択と row 順が決定的であることをプランの根拠に追加する。証明できなければ、複数 WR 理由を持つ trace の seed 横断テストを加える。

- 所見: `workers>1` の完了順そのものが理由列を並べ替える経路は見当たらない。子の outcome は `task_index` 順へ戻され、理由再構成はその後、親側の `_txn_for_id()` から行われる。 / 判定: refuted / 根拠: `orchestrator/verifier/dsg.py:99-107`、`orchestrator/verifier/dsg.py:320-347`、`orchestrator/verifier/dsg.py:367-382`、`orchestrator/verifier/dsg.py:507-518` / 成果物への影響: worker のスケジュール差だけで WR/RW の理由順が変わるとは判断できない。残る確認点は parser 内の `Txn.reads` 構築順である。 / 直し方: worker 数によらない理由再構成であることをプランに明記する。

## 見落とされた束縛

- 所見: 「現行 blob SHA の完全一致が0件」「path memberとしての参照」という調査だけでは、役割名、closure group 名、schema 名、集約 closure digest を key にした束縛を排除できない。集約 digest は個別 blob SHA と一致せず、利用側に `dsg.py` の path literalが現れない場合もある。射影資料には検索の生結果や、それらの key から辿った結果がない。 / 判定: real / 根拠: `s2-plan.md:180-193`、`brief-s1.md:31-34`、`D1817.txt:3-6`、`D1388.txt:3-5` / 成果物への影響: 隠れた束縛が実在すると断定はできないが、「path 以外の束縛も無い」という独立確認は成立していない。commit 後に追加 pin や期待値更新が必要になる可能性が残る。 / 直し方: closure の役割名、group 名、schema field、集約 digest fieldを起点に逆参照し、該当 hit と除外理由を証拠として残す。

- 所見: 凍結成果物調査は JSON / JSONL の構造化 anomaly に限られているが、verifier には reason 順をそのまま出す text renderer もある。追跡済み text report、その digest、そこから派生した receipt が探索対象に含まれた証拠は射影資料にない。 / 判定: real / 根拠: `brief-s1.md:26-30`、`orchestrator/verifier/report.py:144-154`、`orchestrator/verifier/report.py:179-185` / 成果物への影響: 「多重 WW を持つ凍結成果物は0件」から「再発行不要」へ進む証拠範囲が不足している。実在を確認した指摘ではなく、探索面の欠落である。 / 直し方: 追跡済み text report、digest-only record、receipt/reference の入力系譜も調べ、多重 WW reason を含む元 report がないことを確認する。

- 所見: D1388 は source bytes変更で旧 campaign の live resume が drift になることを支持するが、「commit 前の指定焦点テストが必ず `contract-loader-drift` で落ちる」までは証明しない。プラン自身も「発火しうる」と条件付きなのに、brief は赤になると断定している。 / 判定: real / 根拠: `D1388.txt:3-5`、`s2-plan.md:187-188`、`brief-s1.md:33-34` / 成果物への影響: closure の安全方針には影響しないが、焦点テストの赤を無条件に無視すると、本物の回帰を取り違える余地がある。 / 直し方: 実測前は「発火しうる」に統一し、実装段で exact nodeid、失敗 reason、commit 前後の結果を分けて記録する。

## 規律 2 の向き

- 所見: 提案された一行変更に、判定を通りやすくする向きはない。隣接グラフ、SCC、cycle 数、理由型集合、空理由判定は変わらず、reason 配列の WW key 順だけが決まる。 / 判定: refuted / 根拠: `orchestrator/verifier/dsg.py:517-546`、`orchestrator/verifier/dsg.py:569-592`、`CLAUDE.md:67-71` / 成果物への影響: anomaly を消す、分類を弱める、indeterminate を serializable にする経路はない。 / 直し方: なし。

- 所見: 新テストは恒真ではない。未修正実装では seed 1 と777の report bytesと digestが異なり、WW key 列も昇順ではない。JSON の `sort_keys=True` は reason 配列を並べ替えず、report serializerも list順を保持する。 / 判定: refuted / 根拠: `s1-probe.md:21-27`、`s2-plan.md:79-96`、`s2-plan.md:101-117`、`orchestrator/verifier/report.py:26-32` / 成果物への影響: 元の集合走査、降順、versionだけの整列を検出できる。SHA-256比較は bytes比較から数学的に従うため冗長だが、検出力を弱めない。 / 直し方: 必須変更なし。

- 所見: ただし、テストは「phenomenon と正しさゲートが不変」を直接固定していない。anomaly 1件と `total_cycles == 1` は確認するが、`phenomenon`、`serializable`、`verdict`、`certified` の期待値は確認しない。異なる seed 間の bytes一致だけでは、両方で同じように弱体化した場合を検出できない。 / 判定: real / 根拠: `s2-plan.md:85-96`、`orchestrator/verifier/model.py:470-520`、`orchestrator/verifier/report.py:96-101` / 成果物への影響: 今回の一行差分の安全性は静的に証明できるが、追加テスト単体はプランが掲げる受理集合と分類の不変条件を完全には固定しない。 / 直し方: 各 report で `phenomenon == "G2"`、`serializable is False`、`verdict == "non-serializable"`、`certified is False` も assertする。

## 総括

WW 交差だけを key 文字列順にする実装は、受理集合、anomaly 件数、cycle 選択、phenomenon、integrity 判定を変えず、規律 2 に抵触しない。key単独の整列も十分である。

real な問題は実装式ではなく、証拠閉包にある。WR/RW の一般化は parser における `Txn.reads` 構築順まで閉じておらず、束縛調査は role/group/schema/集約 digest、成果物調査は textおよび派生 digestの面が未証明である。また正例テストには phenomenon と gate 値の固定を足すべきである。

pytest や subprocess は実走しておらず、緑とは判定していない。