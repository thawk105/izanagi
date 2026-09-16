## producer が出しうる失敗 report の網羅表

以下、`P`＝`orchestrator/campaign/p3_autonomous_workload_trial.py`、`C`＝`orchestrator/campaign/autonomous_trial_completeness.py`、`PT`＝`orchestrator/tests/test_p3_autonomous_workload_trial.py`、`B`＝指定の `brief.md`、`S`＝指定の `s2-plan.md`。

静的検査のみ。表の「受理」は、journal 整合など先行検査を満たす場合。対象は `P:3988` から publish される `report.json`。

| producer の経路・形 | 根拠 | 現行 root 無し |
|---|---|---|
| provider／transport 初期化失敗、最初の workload 前の wall-budget。cells 空、fatal 有り | `P:3618–3643`, `C:5054` | 既存免除で受理 |
| cell 保存前の例外。campaignless 6-key fallback、fatal 有り | `P:3691–3705`, `P:3314–3335` | 既存免除で受理 |
| cell 保存後の例外＋admission 失敗。identity、error、disposition を持つ単一 cell | `P:3679–3690`, `P:3705` | root 要求で拒否 |
| 正常 return＋admission 失敗。role-invalid、通常の終了理由など。fatal 無しもある | `P:3740`, `P:3814`, `P:4246–4252` | root 要求で拒否 |
| cell 内 wall-budget＋admission 失敗。内部一時 key は除去、fatal 有り | `P:4117–4133`, `P:3779–3802` | root 要求で拒否 |
| 上記 identity 付き失敗に diagnosis が付く。render の `Layer3ReportError` が条件 | `P:3115–3128`, `P:3324–3335` | root 要求で拒否。diagnosis の有無は免除を変えない |

追加の境界は次のとおり。

- **複数 workload を要求しても admission-failure は最後の一つだけ。** 最初が失敗なら単一 cell の failure-only、先行成功があれば admitted prefix＋failure になる。後者は root 必須で正しい（`P:3814–3815`, `C:3170–3185`）。
- **`_run_pending_critics` の例外は admission-failure に変換されない。** 呼出しは admission 成功後であり、変更するのは fatal／stop_reason／error。publish できても admitted cell を含むため root 必須（`P:3711–3737`, `P:3746–3778`）。workload 内の `_run_one_pending_critic` 例外は partial 回収側に入る（`P:4139`, `P:3679`）。
- registered の identity 付き admission-failure は、publish 前の digest 検査で拒否される。実在する publish 候補と混同できない（`P:3960–3964`, `C:1137–1141`）。
- budget-insufficient の別形は return されるが、この経路では `report.json` を publish しない。origin の最小 partial 辞書も同様（`P:5031–5057`, `P:5376–5384`）。

**穴は実在する。partial 例外だけという brief の一般化は狭すぎる。**

## must-fix (成果物影響を 1 行で書けるもの)

1. **helper の流用条件が、対象 producer の値域と両立しない。DW-O13 の実効的な失敗。**

   `S:111` は `C:4279–4314` と同じ条件の検査を要求するが、二つの障害がある。

   - role-attempt がゼロなら、流用元の `_cross_binding_role_events` が拒否する（`C:3436–3445`）。cell 保存直後の例外、ゼロ作業 wall-budget はここに当たる。
   - role-attempt があれば、`provider_artifacts` を必須にする（`C:4282–4287`）。しかし producer がこれを記録する条件は `arm_binding_digest is not None` かつ provider の artifact root が `Path` であること（`P:2760–2798`）。exploratory では invocation digest は `None`（`P:4172–4178`）。一方、registered identity failure は先行 digest 検査で拒否される。

   **成果物影響：cell 述語自体は到達可能でも、plan を文字どおり実装すると、救済対象の実 producer report は helper を通過できない。**

   role 未実行・raw 書込み前失敗・exploratory の成果物契約を区別し、実在する参照だけに対応した診断検査へ修正すべき。producer や既存 cross-binding の契約変更で埋めないこと。`preserves_provider_binding`（`S:172`）も、対象 producer が生成しない field を注入した人工例にしないよう再設計が必要。

2. **diagnosis を許す新機構に、生成器を通る正例がない。**

   `S:79–82` は diagnosis 付き二形を許す一方、正例二つは campaign 作成前／reports 不在であり、`P:3110–3111` で終了する。diagnosis を生成する `P:3115–3128` に届かない。`diagnosis-extra`（`S:168`）は負例にすぎない。

   **成果物影響：許容 key 集合から diagnosis 付き二形を削除する変異が生存し、構造化診断を持つ実失敗 report だけ拒否されても計画の正例は検知しない。**

   実 finalizer の render 失敗から diagnosis を生成する正例を追加し、生成された diagnosis、files API の receipt、CLI 成功を確認すること。新 nodeid も台帳へ追加する。

3. **brief の成功条件と根拠を、plan の訂正に合わせて確定する必要がある。**

   `B:56–57` の根拠テストは completeness・digest・chain を stub し、render は **admitted** を返す（`PT:8808–8837`）。identity 付き admission-failure の publish 証拠にはならない。

   また `B:62`／`B:95–97` の「path identity だけ省略」は standalone 全体では成立しない。root 有りでも、campaign directory 不在なら `C:4255`、Layer-3 不在なら `C:4374` が拒否する。Layer-3 が存在すれば failure chain が拒否する（`C:4911`）。

   **成果物影響：この前提を残すと、既存 cross-binding 成功を証明していない receipt を「path 束縛だけ省略した成功」と誤って報告する。**

   `S:141–155` の訂正を正式な完了条件に反映し、「root 引数不要の非 certifying 診断検証」として裁定する必要がある。

## real だが scope 外

- **正式 registered 系列の publish 前拒否。** `P:3960` → `C:1137–1141` が identity failure を拒否するため、files API だけの修正ではこの系列の失敗 report は生成されない。
  **成果物影響：exploratory 診断が成功しても、brief 冒頭が動機に挙げる正式系列の report／台帳参照が回復するとはいえない。**

- **admitted prefix＋identity failure。** `C:5069` の root 必須は維持すべきだが、root 指定後も `C:4374` と `C:4911` の条件が両立しない。
  **成果物影響：一つだけ成功した複数 workload の部分失敗 report は、今回の failure-only 分岐では救済されない。**

確認できた consumer は、`C:5110` の CLI 呼出し、その起動元 `C:5122`、および `PT:3096` の root 省略 API テスト。producer は files API ではなく個別検査を直接呼ぶ（`P:3956–3981`）。

**リポジトリ全体の consumer 二段追跡と凍結 pin 閉包は未検証。** 「指定の 6 ファイルだけを読む」という制限により、外部 consumer、`B:69–73` の evidence contract／source 集合／HEAD 読取りテストを再読できない。「他 consumer／pin は無い」とは結論しない。

## 反証した攻め

- **「穴は既に全て閉じている」：反証した。** identity 付き失敗は既存免除に一致せず、`C:5069` で拒否される。
- **「新 cell 述語の値が到達不能」：述語単体について反証した。** `P:4083` の基本形に finalizer が decision／disposition を足し、一時 key を除去する。`partial` も `P:3816–3834` で生成される。問題は後段 helper。
- **「pending critic の例外も新免除すべき」：反証した。** admission 成功後の例外は admitted decision を保持する。
- **「台帳追記の計画がない」：反証した。** `S:181–206` に 19 nodeid が列挙され、現物の `nodeid_count` は `acceptance_duration_ledger.json:23122` の 23118。
- **「正例が両側 stub を許している」：反証した。** `S:163`／`S:177` は実 finalizer・検査の無効化を禁止している。ただし前記 helper 問題により、その正例は現案では成功しない。
- **「不要な一般 gate／台帳を追加している」：成立せず。** receipt は検証範囲の表示、所要台帳は既存受入への追記。いずれも明示された成果物に対応する。

変異と assertion の対応は次の評価となる。

| 変異 | 赤になるべき assertion |
|---|---|
| opt-in 条件を恒真化 | `requires_explicit_opt_in` の例外期待 |
| cell key を部分集合判定へ変更 | `nonexact_shape[cell-extra]` の例外期待 |
| chain 呼出し削除 | persisted file／symlink／独立 admitted の例外期待 |
| CLI 引数転送削除 | CLI 正例の終了値 0・receipt 検査 |
| 診断 dispatch 無効化 | 実 producer 正例の成功・receipt 検査 |
| diagnosis 付き形を不許可化 | **現計画に対応する正例なし** |
| provider 検査削除 | **対象 producer 由来の正例成立が未解決で、kill を認定できない** |

## nit

- `B:19–22` の「編集面は 2 file」と `B:107` の台帳追記は記述上矛盾する。`S:137` の 3 file 表記へ統一するとよい。
- consumer／pin 閉包については、資料制限下の未確認を確認済みへ繰り上げないこと。漏れの実在を示せていないため、所見として断定しない。

## 総括

穴は実在し、正常 return 後の admission 失敗も対象になる。
最も重大なのは `S:111`：流用する role/provider 条件が実 producer の対象出力と両立せず、新経路が実効性を持たない。
診断 helper の契約修正と、diagnosis を実生成する正例の追加が必要。
親の択一は、**exploratory の非 certifying 診断検証として条件を修正して進めるか、正式系列の publish 回復も目的なら scope を再裁定するか**。
前者なら既存 verifier／producer の受理集合を維持できるが、正式系列まで直ったとは報告できない。
実走・編集は未実施。consumer 全体と凍結 pin 閉包の再監査は、指定資料制限のため未完了。