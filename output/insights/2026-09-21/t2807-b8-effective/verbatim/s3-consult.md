## 検査範囲

指定資料を静的に照合した。書込み・テスト・job 投入はしていない。以下の略記を用いる。

- `brief`：本 wave の `s1-brief.md`
- `runner`：前 wave の `probe/verify_phase_runner.py`
- `登録`：`docs/b8-final-candidate-longrun-verify-preregistration.md`
- `試走 insight`：`output/insights/2026-09-20/t2807-b8-prerun/README.md`

**投入手順の修正を推奨する。high は P7 の再開経路欠落 1 件。runner の再 author や追加のユーザー承認を要求する所見ではない。**

## 1. 発効の形 — 成立

- [mid] brief:21 — 「承認を記録した commit」と「承認対象の commit」の役割が曖昧 — 成立 — 根拠：登録:493、`3016f22ee` の裁定原文「提示時点の main は `285477c00`」。
  `3016f22ee` は裁定記録、`2afb39768` は D 番号付与を含む fold、`285477c00` は承認対象資料を提示した時点の snapshot であり、同じ意味の「承認 commit 群」ではない。
  3 SHA の併記自体は妥当。field を役割別にし、承認対象は「提示 snapshot 内の insight §7.1 と登録 v1、およびその実値」と明記する。`3016f22ee` を承認対象そのものとして主 field に置く読みには反対する。

P3 の「1 値も変えない」は、**実験構成の既存値を維持し、既存 `status` は置換する**という意味なら妥当。文字どおりの全値不変とは両立しないので、そのように書き直す。

発効 commit 自身の SHA を、その commit に入る bundle へ書かない判断は正しい。後続の記録で発効 SHA を指せばよい。

`validate_bundle` は `status`・承認情報を検査しない（runner:195–213）。ただし、新 gate の必要性までは成立しない。親が投入前に固定 checkout 内の tracked bundle の `effective`・D 番号・内容を確認し、その path を argv に固定すればよい。集計にも既存の `--accept-bundle-sha` と `--accept-ruling-sha` を各 1 値渡せる。既定の「単一 SHA」は、**全件が同じ誤った draft**である場合を拒否しない点には注意が要る。

## 2. 発効 commit と固定 checkout — 不成立

- [low] brief:8 — wave branch 上で発効してから detached checkout で走らせること自体は規則違反ではない — 不成立 — 根拠：D2186 項 1 の固定 checkout 要求、登録:21–38。
  裁定は発効 commit が投入前に main へ着地することを要求していない。発効 SHA の checkout を `--repo-root` にする手順で満たす。
  発効 commit を祖先として保持する通常の merge 後に main を ff-only で進めれば、その SHA は履歴に残る。rebase・squash・cherry-pick で置換する経路では残らないので、発効後はその経路を採らない。

追加する submit-tree も**保存した発効 SHA**から作る必要がある。先例 `mk-submit-trees.sh` は作成時の `HEAD` を使うため、校正結果の記録 commit 後にそのまま流用すると別 checkout になる。これは本 wave の script が未提示なので現存欠陥とは断定しないが、実装時に明示 SHA へ変更すること。

## 3. 校正から本走への決定と walltime — 一部成立

- [mid] brief:25 — `F 上限 2400` を機械的な実行時間上限として扱うと根拠を過大化する — 成立 — 根拠：runner:660–662、試走 insight:96。
  2400 秒は setup・hydrate・build が終わった後の検査であり、その時刻に処理を強制終了する watchdog ではない。count・preserve にも全体 deadline は無い（runner:152–160、511–548）。
  P6 の式は予約の妥当性を検査する見積式として維持し、count・preserve の採用値、倍率、余裕を記録する。「厳密な上限保証」とは書かない。runner 改修は不要。

各攻撃の結果は次のとおり。

- **(a) `stage_B_allowed` の規則逸脱：不成立。** 共通部分・予算内の最大 extime は runner:450–468、校正 bench 失敗は1245–1246、anomaly・構造エラー・job 段失敗による禁止は1362で処理する。使うのは `select_extime` 内部の同名値ではなく、`summarize` の最終出力。
- **(b) 本走式の timeout 不一致：不成立。** bench 120 秒、本走 verifier 1800 秒、4 rep は実装と一致する。式は `10,380 + 4 × (count + preserve)` 秒となる。再検証の予約はこの式とは別に決める。
- **(c) 校正03:30:00の算術不足：不成立。** 外挿をそのまま計算すると、`(32.2 + 45.5) × (1 + 10/6) = 207.2` 秒。したがって `2400 + 2×120 + 207.2 + 2×3600 + 300 = 10,347.2` 秒で、12,600 秒まで2,252.8秒ある。`4063×3 = 12,189` 秒も収まる。約10,340秒という記述との差は概算の丸め幅であり、欠陥に数えない。
- **(d) 本走構成の不一致：不成立。** workload 3種について `(job-index, rep-start)=(1,1),(2,5)`、各4 repで一致する（runner:860–861、1262–1265、2077–2080）。全jobに同じ `chosen_extime` を渡す。

## 4. 未完走の再開と再検証 — 成立

- [high] brief:26 — 本走の未完走を一律に `reverify` へ送ると、初回 verifier 未開始の枠を回復できない — 成立 — 根拠：runner:831–837、356–375、694–726。
  **判定への影響：保全済み trace の初回 verifier を実行できる枠まで未確定で閉じ、許された再開後に得られる pass／失格へ到達しなくなる。**
  P7 を「verifier 起動済みの operational 未完走」と「保全済み・verifier 未開始」に分ける。後者は元の `verify` argv に `--resume` を足し、初回1800秒で再開する。
  bench 失敗・保全未完了は bench を再生成せず開示する。完走済み verdict は再検証せず、特に anomaly または非 `serializable` は失格を維持する。

再検証の投入形は、固定 checkout から generic dispatch で次を実行する形になる。

```text
python3.10 -B <runner-v5> reverify
  --repo-root <発効SHAのcheckout>
  --scratch-root /scr
  --ruling <checkout内の登録v1>
  --bundle <checkout内のeffective bundle>
  --rep-dir <run/verify/workload-jN/rep-R/attempt-1>
```

`--rep-dir` は `rep-R` ではなく、`result.json` と保全 trace を持つ **`attempt-1`** を指す。`reverify` に `--output-dir` や `--third-party-cache` は渡さない（runner:2065–2067）。

許可条件は本走・初回 verifier 起動済み・未完走・operational `indeterminate`・bench完走・保全完了・bundle／登録／identity一致。`reverify-*` が既にあれば、予約だけで失敗した場合も2回目を拒否する（runner:828–855）。再検証の予約には3600秒だけでなく setup・復元・cleanup の余裕も必要。

## 5. 集計対象と再投入の残骸 — 成立

- [mid] brief:23 — run root の配置だけでは、退避 record や再投入残骸の集計混入を防げない — 成立 — 根拠：runner:1212–1220、1251–1259、1271–1278。
  `calib/*/calib.json` は校正を、`verify/*/rep-*` は本走枠を、`rglob('job-*.json')` は深さを問わず会計 record を読む。run 配下に退避用 directory を作ると、退避先も探索対象になり得る。
  本 cohort の正規成果物だけを run に置き、別 cohort・試走・コピーした会計 record は run の外に保全する。既に開始した失敗走の記録を、判定を通す目的で除去してはならない。
  現在すでに混入している事実は未確認。これは探索仕様から確認できる経路であり、P4 の配置そのものへの反対ではない。

同じ出力先への再投入は次の動作になる。

| command | 既存出力先の扱い |
|---|---|
| `calibrate` / `prerun` | `mkdir` が拒否。resume機能なし |
| `verify` | `--resume` 無しなら拒否。有りなら既存枠を照合・分類 |
| `reverify` | 元attempt内の `reverify-2` に保存。再予約は禁止 |

正規の reverify は集計が明示的に扱うので、単なる混入ではない。正規の resume でも `job-UUID.json` は増え、以前のjob段失敗recordや未完了会計は残る。**再投入が成功しただけでは全体が pass になるとは限らない。** 元requestの終端・receiptと併せて判断すること。

## 6. 仕分け (2) の限定の置き場 — 不成立

- [low] brief:20 — README の stale 注記へ限定を書く方針は凍結規則と整合する — 不成立 — 根拠：`docs/paper-story/README.md`:8–13、59–62、日付版:4326–4330。
  README は一項目の決着を届ける正式な入口であり、日付版自身も限定を発効 wave に委ねている。P1 に賛成する。
  「旧仕分け (2) に代えて独立processの自己シードを要件として認める。seed値・乱数列の独立性は検証していない」と明記し、発効記録を指す。

登録の判定規則を変更する話ではないため Erratum は不要。story 新版の作成も不要。決定記録だけでは story の入口へ届かないので、READMEへの掲載には意味がある。

## 7. scope の過剰と不足 — 成立

- [mid] brief:9 — 本走前の記録と最終費用照合が省略されている — 成立 — 根拠：登録:478–483、503–508、537–547、runner:1367–1369。
  extime・B(E)・`stage_B_allowed` だけでなく、打切り行を含む校正6行、本走walltimeの倍率・上限式、manifestからの保全容量見積り、保存先の空き再確認を本走前に記録する必要がある。
  最終費用は **dispatch Elapse の和**で照合する。runner の `consumed_job_wall_s` と `budget_constraint_satisfied` は内部monotonic時間に基づく暫定値で、規則の費用判定を代行しない。
  既存のinsight・決定fragment・results稿へ追記すれば足りる。別のgateや汎用台帳を新設する必要はない。

発効束JSONに無い環境・校正walltime根拠・空き容量・configure全文の所在などは、発効READMEで試走 insight §7.1との対応を明示する。旧波の「job dir `run/`」や空き81 TBを、本waveの現在値として転記しない。

results稿には§13に従い、判定集合数、校正未完走・規約不適合の件数、保全先、seed未記録、extime、現行identityと旧pinとの差、verifierの限界を書く。投入後の予算超過は判定と別欄に残す。過剰なscope追加は見つからなかった。

## 8. 実測済み前提からの一般化 — 成立

- [mid] brief:24 — 「同 SHA なので再利用可」は必要条件だけで、運用状態を含まない — 成立 — 根拠：`docs/pegasus-runbook.md`:1556–1588、1603–1610。
  同じHEADでも未commit差分、動作中request、orphan hold、dispatch出力は異なり得る。親processの終了だけでは計算node側jobの終端を保証しない。
  P5に「校正requestの終端とreceiptを確認し、発効SHA・測定入力・hold状態を確認して再利用」と追記する。別木を作ってholdを迂回することも再利用条件の代替にならない。
  現在のsubmit-tree状態と今後の再利用成立は未確認。P5の無条件な一般化には根拠が足りない。

今回独立に確認できたものは次のとおり。

- 登録 raw SHA：`6ccb18c73b80ba42031f1373d48baa2e3fe441e0370a208836a6d75a9504f7c5`
- runner本体とv5複製のSHA：ともに `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`
- `3016f22ee`／`2afb39768`／`285477c00` の存在・時刻・役割、および提示mainを記した裁定原文
- `validate_bundle` が `status` を検査しないこと

現在の保全先空き容量、将来の発効tree、実dispatch、liveな各経路の成立は未確認。runnerがverifier hashをrecordへ記録すること（runner:613）と、そのhashを期待値と照合して起動拒否することも区別すべきである。固定checkoutと親の照合を機械強制済みとは報告しない。

## 総括

**投入前に直すhigh：P7を分岐させ、保全済み・verifier未開始には `verify --resume`、起動済みのoperational未完走には同一traceの `reverify` 1回を適用する。**

成立した所見は **high 1件／mid 5件／low 0件**。別途、攻撃不成立を示したlowの確認項目が2件ある。

| 攻撃項目 | 判定 |
|---|---|
| 1 発効の形 | 成立：承認記録と承認対象の区別 |
| 2 固定checkout・履歴保持 | 不成立：明示発効SHAと通常mergeなら満たす |
| 3 校正→本走・walltime | 成立：上限保証の過大化。算術不足・規則不一致は不成立 |
| 4 reverify・未確定 | 成立：初回verifier再開経路の欠落 |
| 5 判定集合の汚染 | 成立：探索範囲と再投入残骸の扱いが未記載 |
| 6 限定の置き場 | 不成立：READMEが適切 |
| 7 過剰・不足 | 成立：本走前記録・容量再確認・Elapse照合の不足 |
| 8 実測の一般化 | 成立：同SHAだけでは再利用可否を決められない |

| provisional 裁定 | 賛否 |
|---|---|
| P1 | **賛成**：READMEに限定を明記し、発効記録を指す |
| P2 | **反対**：3 SHAを保持しつつ、承認記録・fold・承認対象snapshotの役割を分ける |
| P3 | **賛成**：実験構成値は不変、`status`は置換。JSON外の発効束項目をREADMEで補う |
| P4 | **賛成**：本cohort専用rootとし、退避コピー・別cohortを探索範囲に置かない |
| P5 | **根拠不足**：request終端・入力状態・hold確認を再利用条件へ追加する |
| P6 | **賛成**：見積式として使用し、実測値・倍率・限界を記録する |
| P7 | **反対**：未開始の初回verifierと、起動済み未完走の再検証を分ける |