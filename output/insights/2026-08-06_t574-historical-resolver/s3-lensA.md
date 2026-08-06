結論から言うと、**このプランのままの land は不可**です。必須資料はすべて読めました。以下は実装前の静的レビューです。

## 所見 A-1 — Blocker: historical resolver が oracle の新規実走 admission へ漏れる

**根拠 (path:line)**

親 brief は拡大を read-only に限定していますが、プランは public `launch_validate()` 自体を historical resolver 固定 wrapper に変えます（[s1-brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s1-brief.md:8)、[s2/out.md:30](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:30)）。

しかし `LaunchValidatedFreeze` は「実走前検証済み型」であり、oracle driver が要求する admission token です（[s8b_ratified_freeze.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:765)）。`run_block()` は `launch_validate()` を通した後、current の manifest contract を検査するだけで、floor protocol の resolved contract との一致は要求しません（[s8b_oracle_driver.py:1066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:1066)、[s8b_oracle_driver.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:753)）。通過後は campaign/WAL/予算台帳を書き、`pipeline.evaluate()` を実行します（[s8b_oracle_driver.py:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:1216)、[s8b_oracle_driver.py:1343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:1343)）。

受理差分は次のとおりです。

| 経路 | 以前拒否・変更後受理となる入力 |
|---|---|
| C1 | 同一 env の登録済み非 current hash を持つ整合した floor protocol |
| C2 | その世代の calibration bytes と receipt に整合する journal |
| C3 | 現行の有効 successor では値が同じなので実質差分なし |
| C4 | 登録済み旧 hash とそれに整合する receipt を持つ manifest |
| floor producer/resume | 新規受理なし。current のまま |
| oracle producer | **g1 floor/freeze + current g2 run_contract** の組合せが新たに実走へ進める |

**成立条件**

current=g2、active ratified freeze の floor protocol=g1、manifest run contract=g2、env_tag が同一で、g2 calibration・binary store・attestation が有効な場合です。g1→g2 が calibration 参照だけの successor なら、この組合せは十分成立します。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

historical floor を入力にした新しい oracle WAL・予算台帳・測定行が生成され、後続レポートと certified 選択へ流入します。

**推奨**

read-only 用と execution admission 用を分離してください。`launch_validate()` は current-bound のまま残し、report 専用 historical wrapper を新設するのが安全です。旧 floor と新 contract の併用を意図するなら、黙って env 一致だけで通さず、明示的な世代互換述語を裁定・実装してください。`run_block()` 公開経路で「g1 floor/current g2 は side effect 前に拒否」を固定するテストが必須です。

## 所見 A-2 — Blocker: C4 では未署名の自己申告 hash が世代選択権限になる

**根拠 (path:line)**

`GenerationEntry` は明記どおり data であって authority ではなく、D176 も逆引き index を権限にしてはならないとしています（[env_contract.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:163)、[docs/decisions.md:8694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:8694)）。

resolver が証明するのは形式・index 登録・一意性・env 一致だけです（[env_contract.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:355)）。一方、oracle manifest 側は `contract_sha256` の形式しか検査せず、`VerifiedManifest` 自身も provenance 証明ではありません（[s8b_oracle_manifest.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_manifest.py:64)、[s8b_oracle_manifest.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_manifest.py:386)）。

防壁になっているものは次の範囲だけです。

- 任意の contract 値は選べず、trusted source に登録された同一 env の世代に限定される。
- C1〜C3 は ratified commit/approval chain と artifact raw hash に束縛される（[s8b_ratified_freeze.py:2839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2839)）。

C4 には「その世代が artifact 作成時に active だった」ことの権威的束縛がありません。D196 自身も receipt の自己申告値は publisher 実行の証明でないとしています（[docs/decisions.md:9524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:9524)）。D197 の識別子はまだ生成されず、プランも追加しない方針です（[s2/out.md:218](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:218)）。

**成立条件**

複数世代が index に登録され、artifact writer が旧世代 hash と整合する manifest/receipt を記録できる場合です。旧 calibration profile の方が当該観測を通しやすければ、current では落ちる記録を historical と自己申告して通せます。未活性化の登録候補も index だけでは区別できません。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

新規または改変された記録が旧世代 artifact として completed 行になり、oracle judge の eligible/unique-best 判定を変え得ます。

**推奨**

C4 の hash を直接 resolver の権威入力にしないでください。activation を先行実装しない D196 の順序を守るなら、historical C4 は既存の trusted published-root allowlist・ratified root など、artifact 外部の不変な根に限定すべきです。少なくとも「登録済みだが一度も active でない世代」を拒否する負例が必要です。自己申告の D197 field を足すだけでは防壁になりません。

## 所見 A-3 — High: P2 は実際の versioned predicate dispatch になっていない

**根拠 (path:line)**

P2 は generation 別 predicate を置かず、resolved contract の値を渡すだけとしています（[s1-brief.md:70](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s1-brief.md:70)、[s2/out.md:213](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:213)）。

しかし historical calibration は現行の schema parser と現行 tolerance policy で検査されます（[env_attestation.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_attestation.py:1091)）。receipt consumer も receipt schema では分岐しますが、契約世代には分岐せず、現行の比較関数・policy を使います（[execution_guard.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/execution_guard.py:97)）。

`GenerationEntry` に predicate version はなく、有効 successor が変更できるのは calibration path/hash だけです（[env_contract.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:202)）。D176 が履歴 proof chain の再計算を versioned predicate dispatch の責務としたこととも未整合です（[docs/decisions.md:8696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:8696)）。

**成立条件**

calibration schema、tolerance、receipt comparison、run-command projection の意味が世代間で変わる場合です。同一 receipt schema の実装を緩和すれば旧 artifact の受理集合が拡大し、強化すれば正当な旧 artifact が失われます。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

同じ凍結 WAL が validator の現行 source により completed と protocol_violation の間を移動し、certified 選択の再現性を失います。

**推奨**

trusted `GenerationEntry` 側に immutable な predicate/profile ID を持たせ、closed dispatcher で schema・calibration・receipt predicate を選んでください。未知 ID は current fallback せず拒否します。今回の g1→g2 では predicate 実装不変と限定するなら、その不変条件と「変更時は schema/dispatcher 更新必須」を機械検査し、T-574 の保証を contract-value dispatch に明確に狭める必要があります。

## 所見 A-4 — High: historical calibration bytes の保存元と C4 の root が未解決

**根拠 (path:line)**

`load_verified_calibration()` は generation commit の blobではなく、渡された repo root の現 filesystem pathを読み、存在と SHA を要求します（[env_attestation.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_attestation.py:1060)）。

C2 は正しく `launch_validate(root)` の root を使いますが、C4 は module 定数 `ROOT` を固定使用しています（[s8b_ratified_freeze.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:1803)、[s8b_oracle_report.py:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1205)）。report CLI は別の `--repo-root` を受け取れるため、現在でも root が分裂しています（[s8b_oracle_report.py:1698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1698)）。プランの新 signature にも `repo_root` がありません（[s2/out.md:72](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:72)）。

D176 の「path と hash を対で変更」は同一 path 上書きを防ぎますが、旧 path の削除までは防ぎません（[docs/decisions.md:8687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:8687)）。

read-only 検証に bytes が必要かは mode で異なります。

- `required`: expected attestation profile の再計算に必要です。
- `none`: receipt predicate 自体には不要ですが、C2/C4 は現在も無条件に読み、存在を追加条件にしています。

**成立条件**

旧 calibration path が current tree から消える、bytes が変わる、または `--repo-root` が module checkout と異なる場合です。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

正当な historical freeze/report が再検証不能または全行 protocol_violation となり、certified 選択が indeterminate に落ちます。

**推奨**

全 registered generation の calibration bytes を immutable/content-addressed path に保持し、存在・SHA を検査する契約を追加してください。C4 には required `repo_root` を渡します。旧 path 欠落、SHA 不一致、別 repo root のテストを C2/C4 双方へ追加し、current calibration への fallback がないことを固定してください。

## 所見 A-5 — Major: fail-closed の設計意図は妥当だが consumer-level 証明が不足する

**根拠 (path:line)**

既存 resolver は malformed・unknown・非一意・wrong-env を例外にします（[env_contract.py:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:361)）。C1 の callback 例外は `FloorContractError` へ変換され、C2 の calibration 失敗も `RatifiedFreezeError` へ変換されます（[s8b_floor_contract.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_floor_contract.py:140)、[s8b_ratified_freeze.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:1803)）。

C4 は例外を report 全体の throw にせず `global_issues` へ入れますが、後段で全行を `protocol_violation` にするため certification 上は fail-closed です（[s8b_oracle_report.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1364)、[s8b_oracle_report.py:1529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1529)）。

`_run_cmd_matches_portable_session()` の `run_cmd is None -> True` は目立ちますが、resolver/C2 はそれ以前に必ず発火し、valid session は run_cmd 文字列を要求するため、未知 hash の迂回にはなりません（[s8b_ratified_freeze.py:2082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2082)、[s8b_ratified_freeze.py:2276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2276)）。

一方、プランの consumer テスト表には非一意 hash、C4 dishonest resolver、calibration 欠落がありません（[s2/out.md:133](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:133)）。data-layer の非一意テストだけでは caller の `except` や fallback を固定できません。

**成立条件**

実装時に resolver 例外を current fallback、`None`、または空の expectations へ変換する分岐が入った場合です。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

不正 hash が completed 行へ落ちる回帰を consumer-level テストが検出せず、report と certified 選択へ混入し得ます。

**推奨**

C1/C4 の公開経路で `malformed / unknown / ambiguous / cross-env / dishonest-return / missing-calibration / hash-mismatch` を全件撃ってください。C4 は helper の例外だけでなく、`build_observations()` の全行が `protocol_violation`、judge が `indeterminate` になるところまで固定します。

## 所見 A-6 — Major: 親 probe から「4 consumer は同型」と一般化できない

**根拠 (path:line)**

probe が実際に測ったのは次だけです。

- producer wrapper `s8b_floor_campaign.validate_protocol()` を read-only leaf の代理として呼んだ current 拒否（[probe_g2_consumers.py:37](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py:37)）。
- shared leaf の historical 正例（[probe_g2_consumers.py:46](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py:46)）。
- 最小 mapping を private `_receipt_expectations()` へ渡した current 拒否だけ（[probe_g2_consumers.py:58](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py:58)）。

C2/C3、C4 historical 正例、VerifiedManifest/WAL/report、oracle driver は測っていません。brief 自身も `launch_validate` 未到達を認めています（[s1-brief.md:42](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s1-brief.md:42)）。

さらに C3 が使う clocks/numactl は有効 successor では変化できず、プラン自身が registered positive では C3 の current lookup を検出できないと認めています（[env_contract.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:219)、[s2/out.md:145](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:145)）。したがって C3 は反例で、4 consumer 同型ではありません。

また probe の「g2=current」は fuse を緩めて世代列末尾を current にした模擬ですが、D176 は末尾の無条件 current 化を明示的に却下しています（[docs/decisions.md:8684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:8684)）。

**成立条件**

probe の2 leaf結果を、full `launch_validate`、report、producer admission の根拠として用いる場合です。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

未測定の producer/report 経路を緑と誤認し、WAL・台帳・certified 選択に関わる回帰を land 前に取り逃がします。

**推奨**

probe は「2 leaf の counterfactual」と書き直してください。full `_launch_validate` component integration、完全な C4 report、oracle `run_block` の side-effect-free refusal を別々に検査し、C3 sentinel test は「引数が load-bearing」という構造検査であって valid-successor の受理正例ではないと明記すべきです。

## 総括

最も重い所見は次の3件です。

1. **A-1:** public `launch_validate` の historical 化が oracle の新規実走 admission を広げる。
2. **A-2:** C4 で artifact 自身の hash が、active/issued の証明なしに世代選択権限になる。
3. **A-3:** resolved contract 値の引回しだけでは、将来の historical predicate semantics を固定できない。

したがって、**現プランの land は不可**です。少なくとも execution/read-only API の分離、historical 世代の権威的束縛、predicate version または強制された不変契約、calibration bytes/root の保存契約をプランへ戻し、公開経路の fail-closed matrix を追加してから再レビューする必要があります。