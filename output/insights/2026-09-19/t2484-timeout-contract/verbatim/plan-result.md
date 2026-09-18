## 総括

**P1は成立します。** collection gateには元の`spec.timeout_seconds`を渡し、実際の待機だけを`max(spec値, 全区間予算)`へ延ばせば、D2044(b)の既存gate維持とD2148(a-1)+(a-3)を両立できます。変更はharness内の局所helperと3 caller、非拒否の診断、テスト・文書に限定できます。

ただし、**有限のPによる絶対的な先行発火防止は証明できません。** 今回確認したのは静的な契約と呼出し経路です。編集・テスト実行・commit・子起動は行っていません。

**前提のreal／refuted**

| 前提 | 判定・根拠 |
|---|---|
| P1：実効値のmaxと既存gateは共存できる | **real**。gateはoverrideが存在するときだけ、元のspec値を`Q+G`と比較する。[mutation_harness.py:1451](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:1451)。max後の値をここへ渡す案は**refuted**。既存拒否を消してしまう。 |
| P2：P=2秒で十分 | **refuted**。実測のdispatcher前段最大は15.9秒で、harness側起動時間は別。[source-insight.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/source-insight.md:37)、[同:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/source-insight.md:47)。有限の余裕を選ぶ必要性はrealだが、実測最大は上限保証ではない。 |
| walltime overrideは短縮専用 | **refuted**。説明は短縮用だが、実装は非空文字列をそのまま転送し、walltime parserは1時間超も許す。[run_tests.py:1343](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/run_tests.py:1343)、[dispatch_compute.py:507](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/pegasus/dispatch_compute.py:507)。 |
| collectionにもwalltime overrideが効く | **refuted**。collectionはdispatcher CLIへ直接入り、転送するのはQ/Gだけ。Wは既定3600秒。[mutation_harness.py:1470](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:1470)。 |
| `P+Q+W+G+A+C`が厳密な実行上限 | **refuted**。RUN初観測で期限を再設定し、期限確認はsleep・qstatを挟む。成果物回収にも期限外の処理時間がある。[dispatch_compute.py:4200](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/pegasus/dispatch_compute.py:4200)、[同:4245](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/pegasus/dispatch_compute.py:4245)。全区間の**運用予算**として扱う。 |

**最小実装案**

1. **harness内にtimeout選択helperを1つ置く。**
   dispatchでは`B=P+Q+W+G+A+C`、実効値は`max(spec.timeout_seconds, B)`。Q/Gは既存override解釈を再利用し、W/A/Cの既定値はdispatcherの定数から得ます。collectionか実行かはcallerから明示し、argvの一般的解析には広げません。
   - collection：W=3600。
   - baseline・mutation：有効な`IZANAGI_DISPATCH_WALLTIME_OVERRIDE`があればそのW。
   - local：従来値をそのまま返し、dispatch環境変数を解釈しない。
   - 不正walltimeに対する新しいharness拒否は追加しない。診断して既定Wを予算計算のfallbackとし、既存dispatcherの不正値処理へ渡す。collectionではこのoverride自体を参照しない。

2. **本番の全3 callerへ適用する。**
   - [collection:1518](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:1518)：`_collection_command(...outer_timeout_s=spec.timeout_seconds)`は維持し、`_run_tests`に渡す値だけ変更。
   - [baseline:2127](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:2127)：同helperを使う。
   - [mutation:2247](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:2247)：dispatchは`hang_risk`にかかわらず上記実効値。localだけ従来の短いhang値を使う。

   `_run_tests`自身のtimeout発火・回収処理は変更しません。実際の待機点は[1994行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:1994)。resumeでcollectionが省略されても、baseline・mutation側で計算されます。

3. **Pは180秒を提案する。**
   実測15.9秒＋harness起動差に加え、5秒poll・最大30秒のqstat呼出し、終端処理の遅れを吸収するための工学的余裕です。実測から一意に導いた値ではありません。これなら既定予算は**5130秒**、Q=3600/G=600/W=3600なら**8130秒**。任意のI/O停止まで覆う保証とは記述しません。

4. **D2044(c)はstderrの早期診断で実装する。**
   通常起動・resume双方で、最初の実行前にspec値、区間内訳、実効値、dispatchではhang値を外側に使わない理由を示します。小さい値を理由とする新しい拒否は加えません。警告は「補正前の値では区間を覆えない」と説明し、補正後にも同じ確率で発火するかのような表現は避けます。台帳・sidecarのschemaは変更しません。

文書は[DW-M06/M07](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/docs/dev-wave/mutation.md:37)を、dispatchの内側walltime委譲・外側実効max・既存collection gate維持へ更新します。phase完了、成果insight、spool worklogは親が更新し、旧実測資料は保持します。

**検証案**

- 新テストでは3 callerから渡るtimeoutを捕捉し、最終的な`communicate(timeout=...)`まで配線を確認する。collection・baseline・通常mutation・hang mutation、specが予算未満／超過、Q/G片側override・ゼロを含める。
- W=120秒と7200秒で、collectionは3600秒、baseline・mutationはoverrideを使うことを確認する。不正Wは新しい起動拒否にならないことも確認する。
- 既存gateの境界を維持する。Q/G=1800/600ではspec=2399を起動前拒否、2400は通過。override未設定なら小さいspecも従来どおり通す。既存の[対応テスト:138](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:138)を保持する。
- [local hangの復元テスト:1541](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/orchestrator/tests/test_mutation_harness.py:1541)、dispatch timeout時のhold・変異残置、receipt束縛、失敗node完全一致、resume検証を回帰対象にする。内側rc=16を外側TIMEOUTやKILLEDへ読み替えない。

**事前登録する変異候補**

各変異は専用fixture・選択nodeへ絞り、期待失敗nodeを完全一致で登録します。

| 変異 | 単一の検出理由 |
|---|---|
| 各callerでhelperを迂回する3変異 | 当該callerの待機値だけが予算未満になる |
| dispatch hangに短い値を復活させる | hang callerだけが短縮される |
| Q／W／G／A／Cを各1項ずつ落とす | 対象項を必要とする境界で待機が不足する |
| maxを予算固定へ変える | 予算より大きいspec値が短縮される |
| collection gateへmax後の値を渡す | spec=2399が誤って起動される |
| collectionのWを短縮overrideにする／実行側の延長overrideを無視する | 対象経路のWだけが不足する |
| local hangにもdispatch予算を使う | localの短いhang停止契約が失われる |

他の拒否で先に止まるfixtureは使いません。診断欠落・文言変更は**diagnostic sensitivity pin**とし、killには数えません。

**残る不確実性**

P=180秒の妥当性と、補正後にdispatcherの終端証拠まで回収できることは親の実測事項です。有限timeoutだけでorphan holdの消滅を保証する案ではありません。また、helperの単体検査だけではcallerの配線漏れを検出できないため、3 callerを通す検査を完了条件に含める必要があります。