**約980件まで減らす案は不十分です。大部分を日付配下へ移し、実在する保留理由を持つ少数だけ旧位置に残す案を推奨します。** 静的検査のみ実施し、実装・pytest は行っていません。

1. **重要度: 高 — 件数の受入条件が目的に届いていません。**
   **根拠:** [plan.md:78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-insights-date-layout/plan.md:78) は「直下1000未満」だけを要求しています。979件なら21件、988件なら12件の増加で再び1000件です。基準コミット `c68d08d9e` の Git tree では、直下1077件、日付72種類、同日最大52件を再確認しました。
   **最小対処:** 日付付き1075件を原則移動対象とし、保留対象を理由付きで差し引いてください。旧文書の code span や固定 `commit:path` の存在だけでは保留しません。直下件数は `1077 − 移動件数 ＋ 作成する日付フォルダ数 ＋ 新設案内数` で確定し、大部分の日付化と残存例外の全件説明を受入条件にします。独立 key 集合に束縛された5文書などは保留が妥当です（[test_frozen_artifacts.py:98](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/orchestrator/tests/test_frozen_artifacts.py:98)）。

2. **重要度: 高 — 接頭辞除去を必須にすると、移動可能な資料まで保留します。**
   **根拠:** [図への相対リンク:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/output/insights/2026-09-02_cicada-adaptive-three-constants.md:54) は、日付付き figures ディレクトリ名を参照し、対象画像は実在します。文書と画像を同時に移しても、figures 名から日付を除けばリンクは壊れます。一方、計画が保留理由に挙げた [逐語記録:31](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/output/insights/2026-08-11_t813-acceptance-sharding/verbatim/s3-luna-out.md:31) のリンク先は、移動前から不在でした。
   **最小対処:** 日付フォルダ化を優先し、相対リンク維持に必要な子名は接頭辞を残してください。図の例は文書・figures を同日フォルダへ移し、figures の旧名を維持すれば本文不変で解決できます。リンクは「既存不達」「移動で新規破損」「正常維持」に分け、既存不達を移動阻止の根拠にしないでください。

3. **重要度: 高 — raw の全件閲覧を必須成果物にする必要があります。**
   **根拠:** [handoff.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-insights-date-layout/handoff.md:36) は分割索引を「必要なら」としていますが、Git tree でも該当 raw の1422件・1424件を確認しました。上位ディレクトリへのリンクだけでは、下位の一覧欠落を解消しません。また、observer は run root からの相対パスを証拠台帳へ記録します（[signal_observer.py:540](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/output/insights/2026-08-03_t361-t362-cluster-probes/driver/signal_observer.py:540)）。
   **最小対処:** raw 内部配置は維持し、証拠ツリーの外に各500件以下、計6ページの閲覧索引を作ります。入口から各ページ、各ページから2846ファイルそれぞれへ直接リンクしてください。Git tree の対象集合とリンク先集合の一致、リンク先の実在、入口からの到達を検査します。単一巨大索引や raw ディレクトリへのリンクだけでは受入にしません。

4. **重要度: 中 — 新規 producer と既存継続出力の区別が具体化されていません。**
   **根拠:** [plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-insights-date-layout/plan.md:70) は方針だけです。実際には、文字列を分割して旧出力先を組む producer があり（[p3_b4_wiring_probe.py:48](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/orchestrator/campaign/p3_b4_wiring_probe.py:48)）、新しい evidence set のディレクトリをそこで作成します（[同:1816](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/orchestrator/campaign/p3_b4_wiring_probe.py:1816)、[同:1856](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/orchestrator/campaign/p3_b4_wiring_probe.py:1856)）。完全パスのリテラル検索だけでは拾えません。
   **最小対処:** この producer は既存継続出力の例外として明記し、移動で旧ディレクトリを再生成させないでください。新規 wave の記録主体である親の手順（[core.md:105](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/docs/dev-wave/core.md:105)）にも新規配置の正本への導線を置きます。汎用 resolver や新たな防壁は不要です。

5. **重要度: 中 — 保存・閲覧・checker の検収集合を分けて固定してください。**
   **根拠:** 親の17330ファイル・1600下位ディレクトリに対し、同じ基準コミットの Git tree は17328ファイル・1599下位ディレクトリでした。差の原因は未確定です。また、既存 checker は直下 `*.md` を列挙します（[check_docs.py:2618](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/tools/check_docs.py:2618)、[同:2654](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/tools/check_docs.py:2654)）。
   **最小対処:** 保存・索引の母集団を基準 Git tree に固定し、ローカル実体との差は別途説明してください。checker は移動表を逆適用した旧検査対象集合が一致することを確認します。新しい正常例だけでは、旧対象の脱落を検出できません。深い逐語記録への無条件な検査拡大は不要です。

## 総括

**推奨は「大部分の日付化＋必要な旧basename維持＋少数の明示的保留＋raw分割索引」です。** 旧資料の bytes・hash、固定 `commit:path`、実験の受理集合を維持したまま進められる構成です。

最終移動集合と pin 閉包は未確定のため、大部分を安全に移せると確認済みとは報告しません。約980件案への後退ではなく、例外を具体化して移動数を確定することが次の作業です。外部旧URLの全維持は保証できず、移動対応表はその代替転送にはなりません。
