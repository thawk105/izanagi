### 所見 1: 実測済み root から build まで通る成功系列が存在資料で閉じていない
- 深刻度: must-fix
- 保証が消える経路: 実測済み `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` からは canonical 101 file を生成して oracle PASS まで到達できる。しかし floor/build はその親の `masstree-src` を実 source として読む。実測 root の basename は `masstree` なので同じ path ではなく、提示資料には実在する `masstree-src` を使った oracle PASS 後の build 成功例がない。新 gate が死んでいるとは断定できないが、production 全成功集合の非空性は未証明である。
- 根拠: `MEASUREMENTS.md`「依存 root には 2 つの形がある」「build 境界が見る root は oracle が見る root と同じ path ではない」、`orchestrator/campaign/s8b_floor_campaign.py:2810-2815,3888-3903`、`orchestrator/campaign/buildcache.py:945-948`、`s2-plan.md:167-177`
- 成果物影響: `sort_best` binary が作れなければ certified 選択集合は床値 arm なしのまま、材料レポートは preflight/build failure、試行台帳には当該 cell が入らない。
- 提案: 実在する `<base>/masstree-src` について、generator、oracle PASS、`buildcache.build_v2` の cache miss、cache hitまでを同じ系列で確認する受入項目を必須化する。

### 所見 2: `s8b_oracle_n_pilot.py` は canonical root を受け取らず、build capability も付けない
- 深刻度: 裁定パッケージ候補
- 保証が消える経路: プランどおり `_prepare_floor_oracle_dependency` が `oracle_root` を追加しても、pilot は戻り値から `source_root` を取り出して oracle へ渡す。通常は196 file rootなので oracle は UNAVAILABLEとなる。仮に seam が canonical root を `source_root` として返して oracleを通しても、続く `build_fn` 呼出しには FetchContent receipt、archive hash、post-oracle capabilityのいずれも渡らず、oracleとbuildの束縛が黙って消える。
- 根拠: `orchestrator/campaign/s8b_oracle_n_pilot.py:806-834,872-899,943-959`、`s2-plan.md:63-84`。同 module `:2-6` は成果物を非 authoritative と明記する。
- 成果物影響: n-pilot材料レポートは生成不能、または canonical 判定と束縛されない binaryを記録し得る。certified選択には直接入らない。
- 提案: 非 authoritative pilotを本 waveで直すか、canonical保証の対象外として故障を維持するかを明示裁定する。直す場合は `oracle_root` と二根 capabilityを両方伝播させる。

### 所見 3: ambient環境変数から fixtureを直接受理するproduction入口が残る
- 深刻度: 裁定パッケージ候補
- 保証が消える経路: `p3_s4_loop_sort.quarantine`、またはfloor以外から呼ぶ `s1_direct_comparison.prepare_cell` で `dependency_root=None` とし、`IZANAGI_SORT_SWO_MASSTREE_ROOT` に test fixtureを設定する。resolverはそれを選択し、既存exact verifierもfixtureを正当に受理するため、production sourceから導出したというP4保証なしでoracle PASSになる。floor本体は明示引数を渡すので、このfallbackは使わない。
- 根拠: `orchestrator/campaign/sort_swo_oracle.py:2366-2376,2407-2449,2753-2763`、`orchestrator/campaign/p3_s4_loop_sort.py:167-186`、`orchestrator/campaign/s1_direct_comparison.py:672-710`、`s2-plan.md:115-126`
- 成果物影響: S1系のWALやoracle receiptはfixture由来PASSを記録できるが、現行floor certified選択、材料レポート、試行台帳へ直接流入する経路は確認できない。
- 提案: 「floor fresh経路だけの保証」と明記するか、他production consumerもprovenance付きcanonical capabilityへ移すかを裁定する。

### 所見 4: manifest作成済みresumeはcanonical gateを一度も通らない
- 深刻度: 裁定パッケージ候補
- 保証が消える経路: 禁止導入前に作られたM-prestart/M-runningのrunを`resume_dir`で再開する。resumeはdurable manifestからbinaryを復元し、admission receiptとbinary/store hashだけを照合する。generator、oracle、`build_v2`、二根検査はいずれも呼ばれず、既存binaryで測定を継続する。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:7156-7248,5316-5353,7589-7625`、`ADJACENT-ITEMS.md` [T-1804]
- 成果物影響: 旧`sort_best` binaryの測定値を試行台帳とresultへ追加できる。resumeはrefreeze不適格になるが、durable材料レポート上の受理集合自体はcanonical導入前のまま残る。
- 提案: なし。本件は[T-1804]のユーザー裁定待ちとして分離する。

### 所見 5: 同一uidのA→B→A変更と共有base再入は二根再検査をすべて通過できる
- 深刻度: 裁定パッケージ候補
- 保証が消える経路: process Aがcanonical Aを作成した後、同一uidのprocess Bまたはbuild内custom commandが実sourceをBへ変更し、compilerがBを読んだ後、次の検査前にAへ戻す。プランのcache lookup前、configure前後、build後の各再照合はすべてAを観測してPASSする。`0o700`は別uidを排除するだけで、同一uid process間の排他にはならない。
- 根拠: `s2-plan.md:147-151,211-215`、`ADJACENT-ITEMS.md` [T-1799]、[T-1802]、[T-1805]
- 成果物影響: receiptと材料レポートはcanonical Aを参照する一方、binaryはBをcompileしたbytesになり、そのbinaryの測定値が試行台帳と選択計算へ入る。
- 提案: なし。immutable build snapshotまたはcompiler input manifestは[T-1805]、再生成禁止は[T-1799]、process間lockは[T-1802]として裁定対象に分離する。

### 所見 6: 提案テストはproduction全系列が空でも緑になり得る
- 深刻度: must-fix
- 保証が消える経路: generator単体は実root、floor配線はmonkeypatch material、buildcacheは合成二根で別々に緑にできる。opt-in real-repo testもmanifestとfixture bytesの比較までで、未設定時は通常suiteから外れる。したがってproduction prebuildが作る`masstree-src`、oracle PASS、post-oracle capability、cache miss/hitを一度も同一実行で通さなくても全提案テストが緑になり得る。
- 根拠: `s2-plan.md:169-198`、特に`:176-177,178-197`、`MEASUREMENTS.md`「親が確かめていないこと」
- 成果物影響: 偽緑のままlandすると、certified選択は床値armなし、材料レポートは失敗、試行台帳は未到達という現行状態を解消しない。
- 提案: 1本のproduction系列テストまたは親の必須実測を受入条件にし、`source_root`誤配線、capability省略、cache-hit検査省略の各変異がその系列を赤にすることを確認する。

### 所見 7: 新設test fileの自走契約がプランにない
- 深刻度: nit
- 保証が消える経路: `test_sort_swo_dependency_material.py`を自走harnessもallowlist登録もなく作ると、直接`python3`実行は0件実行でexit 0になり得る。全走のmeta-testでは赤になるが、焦点走だけでは露出しない。
- 根拠: `s2-plan.md:171`、`orchestrator/tests/test_plain_runner_coverage.py:25-41,60-86`、`docs/failures.md:1593-1637` F42
- 成果物影響: certified選択、材料レポート、試行台帳への直接影響はない。受入確認の偽緑または全走の空振りだけである。
- 提案: `pytest.main`を呼ぶ`__main__` harnessを付けるか、`orchestrator/tests/README.md`のpytest専用allowlistへ登録し、meta-testも焦点走へ含める。

### 成功経路の実在確認 (1 本書き下し、または切れる箇所)

確認できるのは途中までである。

`source_root=/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree`、`HEAD=b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`、tracked 99 path、`config.h=e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a`、生成`PIN=HEAD+"\n"`から101 pathを作れば、manifestは`8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875`となり、oracle PASS入力は実在する。

そこで系列が切れる。floor/buildが使う実rootは`<base>/masstree-src`であり、上記実在rootは`<base>/masstree`である。提示資料には、実在する`masstree-src`を使ってoracle PASS後にbuildまで通った値がない。従ってproduction全系列の実在は未確認である。

### 取り残した入口の一覧

- `s8b_floor_campaign.build_cells` fresh/L-resume: プラン上はcanonical配線対象。
- `buildcache.build_v2` cache miss/hit: capabilityがある場合だけ対象。floorは付与予定。
- `s8b_oracle_n_pilot.build_binaries`: `source_root`のままで、build capabilityも欠落。
- `s1_direct_comparison.prepare_cell`: floor callerは明示canonical予定。その他callerは引数またはambient環境を受理。
- `p3_s4_loop_sort.quarantine`: ambient `IZANAGI_SORT_SWO_MASSTREE_ROOT`を直接使用。
- `resolve_oracle_environment`: 明示引数がある場合は環境へfallbackしないためfloorではfail-closed。ただし引数なしのproduction入口は任意のpin適合rootを受理。
- M-prestart/M-running/finalize-pending resume: durable binaryとstore hashだけを受理し、canonical rootを再構成しない。
- test receipt memo: fixture固定だがtest専用であり、production入口ではない。

## 総括

fresh floor経路について、明示canonical引数、既存manifest pin、build前後とcache hitの二根検査という骨格はfail-closedであり、恒真PASSになる直接経路は見つからない。ランダムlease、排他的作成、非再利用により、SIGKILL残骸が次回の成功入力として採用される経路もプラン上はない。

ただし、実在する値でbuildまで閉じた成功系列がなく、提案テストもその空白を検出しない。さらにpilot、ambient resolver consumer、resume、同一uidの時間窓はcanonical保証の外に残る。後三者のうちresumeとbuild中A→B→Aは既存の裁定待ち項目へ分離すべきである。

pytestは実行していない。Web検索、書き込み、性能測定も行っていない。