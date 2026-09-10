```text
[severity: must-fix]
[攻撃シナリオ: 測定完了後に不都合な session の throughputs を空にし、run_cmd=null、excluded_reason=competing_process または launch_failure、rep_observations=[]、rep_integrity_failures=null へ書き換える → resume と artifact verifier は「未測定の免除行」と解釈し、rep 証跡なしで通す。probe_before/probe_after は測定済みの形のままでも検査されない]
[根拠: orchestrator/campaign/s8b_floor_campaign.py:3919、orchestrator/campaign/s8b_floor_stats.py:662、orchestrator/campaign/s8b_ratified_freeze.py:2300]
[成果物影響: 不利な測定済み session を丸ごと除外でき、n_valid、cell medians、床値および certified 選択の受理集合が変わる]
[提案: 免除判定を共通 helper にし、pre-probe competing は probe_before.competing=true かつ probe_after=null、measure 例外は測定段階を表す固定 enum と整合する場合だけ許す。run_cmd=null と理由の自己申告だけを免除根拠にしない]

[severity: must-fix]
[攻撃シナリオ: 正当な pre-probe competing 行の exclusion_class を rep_integrity_failure などへ改変し、journal、result.sessions、excluded、attempts を同じ値へそろえる → exact key と mirror は通り、証跡免除分岐が class の再導出まで飛ばす]
[根拠: orchestrator/campaign/s8b_floor_stats.py:662、orchestrator/campaign/s8b_floor_stats.py:689、orchestrator/campaign/s8b_ratified_freeze.py:2224]
[成果物影響: 床値が同じでも、レポートと台帳の除外件数が competing_process から rep_integrity_failure などへ改竄され、原因別集計と参照が変わる]
[提案: exclusion_class の期待値計算と一致検査を免除分岐の外へ出し、全 session で必須化する。direct verifier の _REQUIRED_SESSION にも追加する]

[severity: must-fix]
[攻撃シナリオ: official journal と result の reps_expected を "5" または 5.9、exec_failures を "0" または 0.9 にそろえる → int() が 5 と 0 に丸め、ratified verifier は型違反を拒否せず正常 session として再計算する]
[根拠: orchestrator/campaign/s8b_floor_stats.py:424、orchestrator/campaign/s8b_floor_campaign.py:2793]
[成果物影響: schema v3 の受理集合が型違反 artifact まで拡大し、certified 選択が参照する試行台帳に、検証時の値と保存値の型が異なる session が残る]
[提案: SessionRecord 構築前に seq、reps_expected、exec_failures は非負 exact int、retry は exact bool と検査し、int()/bool() による正規化を廃止する]

[severity: should-fix]
[攻撃シナリオ: _run_session の rep_integrity_failures 分岐を削除する → qualified throughputs が reps 未満なので assess_session は同じ nonfinite_or_partial_output を返し、_finish_session は failure count から同じ exclusion_class を作る。それでも AST テストだけが赤になる]
[根拠: orchestrator/campaign/s8b_floor_campaign.py:2532、orchestrator/campaign/s8b_floor_campaign.py:2545、orchestrator/campaign/s8b_floor_campaign.py:2597、orchestrator/tests/test_s8b_floor_campaign.py:2824]
[成果物影響: 床値、certified 選択、レポートの受理集合は変わらない一方、変異台帳が M7 を KILLED と過大計上し、防壁の検出力を誤表示する]
[提案: M7 は diagnostic sensitivity pin へ降格するか、valid、median、exclusion_class のいずれかを実際に変える単一理由の変異へ再定義する]
```

## 総括

- 独立所見は must-fix 3 件、should-fix 1 件である。
- rep 完備判定へ throughput、median、CV の大小を直接混ぜる経路は見つからなかった。
- no-touch の列挙対象と `output/` は差分ゼロで、固定 4 理由、protocol builder、formula・protocol・manifest schema も不変だった。
- 変更 source の旧・新 SHA-256 を `output/` へ限定検索した範囲でも pin は見つからなかった。
- 既知の resume 赤は、v2 target の有無を調べる前に測定 event を拒否する順序が原因である。v3 は早期 return し、測定済み v2 の拒否は維持すべきである。
- pinned holdout caller の赤を `expected_use_perf=True` の既定値追加で消すと A3 を再度開く。no-touch の再裁定または人間による再 seal が必要である。
- `use_perf` call-site meta-test は新しい別用途 keyword まで拾っているため、keyword を削るのではなく対象関数を限定すべきである。
- pytest は実行しておらず、以上は未 commit 差分に対する静的検査結果である。