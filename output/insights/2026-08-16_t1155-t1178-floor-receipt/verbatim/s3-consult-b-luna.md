```text
[severity: must-fix]
[取り残し] `s8b_holdout_freeze.py` は ratified とは別の result consumer であり、独自の exact-key・schema・verify 呼出しを持つ。さらに `s8b_oracle_driver.py` は receipt 束縛自体は scope 外でも、portable binary の直接検査は scope 外にできない。
[根拠 file:line] `orchestrator/campaign/s8b_holdout_freeze.py:55-62,1317-1320,1377-1395`; `orchestrator/campaign/s8b_oracle_driver.py:930-964`; `orchestrator/campaign/s8b_floor_campaign.py:4156,5341-5382`
[提案] U2 に holdout の `FLOOR_RESULT_KEYS`、v4、live inspector、`expected_holdout_admission` 伝播を明記する。oracle driver は新 receipt の発行はしないが、sort_best conditional key を受理する互換検査と回帰テストを追加する。

[severity: must-fix]
[取り残し] P1 は raw receipt を private staging にだけ保存し、成果物には絶対パスを除いた射影と raw 全体の hash だけを載せる。しかし ratified closure は private staging を捕捉せず、再検証時に raw を読めない。したがって downstream は `receipt_sha256` と射影の対応を再計算できず、hash は実質的に型検査になる。
[根拠 file:line] `plan.md:7-8,112-126`; `orchestrator/campaign/s8b_floor_campaign.py:2579-2598`; `orchestrator/campaign/s8b_ratified_freeze.py:2932-2958,3168-3170`; `orchestrator/campaign/sort_swo_oracle.py:202-216`
[提案] raw を到達可能で integrity-bound な evidence に含めて全 consumer が照合するか、絶対パスを含めない canonical 射影そのものを hash するかを裁定に戻す。現状の「full raw hash + raw private only」は保証として閉じていない。

[severity: must-fix]
[取り残し] portable 射影に残す `compiler_version` は外部 compiler の出力を最大 4096 bytes まで任意文字列として取り込む。ratified の JSON pointer 走査は新 subtree を許可していないため、全 subtree を許可すれば軸情報漏洩の迂回路になる。`_portable_argv` の placeholder 化も receipt にはそのまま流用できず、予約語検査との契約が別である。
[根拠 file:line] `orchestrator/campaign/sort_swo_oracle.py:1342-1355`; `orchestrator/campaign/s8b_ratified_freeze.py:2382-2434`; `orchestrator/campaign/s8b_floor_campaign.py:2645-2682`
[提案] `compiler_version` を hash または厳格な許可文字集合へ縮約し、許可 pointer は固定 enum/hash フィールドだけに限定する。`/binaries/*/sort_swo_oracle` 全体の allow は認めない。

[severity: must-fix]
[取り残し] `PORTABLE_BUILT_KEYS` の変更だけでは全波及を閉じない。central validator の現行 `validate_portable_binary_record` は top-level exact key を検査しておらず、exact 検査は呼出し側に分散している。一方 runtime record には `store_path`、`_ccbench_root`、`_fetchcontent_base_dir` の有無があり、central validator に portable 集合をそのまま入れると runtime 検査を壊す。
[根拠 file:line] `orchestrator/campaign/s8b_binary_admission.py:36-40,232-330`; `orchestrator/campaign/s8b_floor_campaign.py:2697,2755-2762,3429-3449,3606-3643`; `orchestrator/campaign/s8b_ratified_freeze.py:1653-1655`; `orchestrator/campaign/s8b_floor_stats.py:915-916`
[提案] portable 用 `portable_built_keys_for` と、configuration・stored/fresh・FetchContent を含む runtime 用 helper を分離する。floor campaign の live admission、resume store、ratified、stats、oracle driver を受理集合の表に入れ、sort/non-sort の正負例を各 consumer で固定する。

[severity: should-fix]
[取り残し] `_render_result_md` は result を再描画する独立経路で、normal と `M-finalize-pending` の二箇所から呼ばれる。計画の順序どおり inspector を result assembly 前に置けば変更不要だが、その前提と両経路の検査が acceptance scope に明示されていない。resume は現行 schema v2 を読むため、通常 resume と finalize-pending の双方で旧 manifest を拒否する必要がある。
[根拠 file:line] `orchestrator/campaign/s8b_floor_campaign.py:4442-4539,5151-5167,5276-5308,5341-5382`; `orchestrator/campaign/s8b_oracle_report.py:1827-1848`
[提案] renderer は「検査済み result のみ入力」とする契約テストを追加し、両 finalization 経路、report の ratified 伝播、resume v2 拒否を明示する。`s8b_materialization.py` と oracle driver の `PreparedCell` は新 receipt 発行対象外と明記し、誤って全 sibling に gate を広げない。

[severity: must-fix]
[取り残し] 静的に少なくとも 10 箇所の fixture/golden 定義が新 gate で壊れる。fake `PreparedCell` は 6 箇所、result/artifact fixture は 4 箇所ある。加えて direct call の signature 更新漏れが 2 箇所ある。
[根拠 file:line] `test_s8b_floor_campaign.py:297,1284,2997`; `test_s8b_materialization.py:477,453-567`; `test_s8b_freeze_io.py:326`; `test_s8b_ratified_freeze.py:406`; `s8b_v2_freeze_fixture.py:275-299`; `test_s8b_ratified_verify.py:421-436`; `test_s8b_floor_stats.py:381-435`; `test_s8b_floor_campaign.py:3387-3392,5362-5383`
[提案] U0 の共有 `s8b_floor_evidence_fixture.py` に独立計算の deterministic PASS receipt と admission filesystem を置く。sort_best の fake だけが receipt を返し、非 sort は key 自体を持たないようにする。`test_s8b_materialization.py:565-567` の literal SHA は独立 canonical calculator で更新し、`_real_output_snapshot` は schema golden と混同しない。

[severity: should-fix]
[取り残し] brief の A→B 逐次分割は三共有ファイルを二度所有する。plan の U0→U1/U2 は改善案だが、U2 の所有表に oracle driver の binary consumer とそのテストがなく、U1 の `test_s8b_floor_campaign.py` は並行 wave t1142 の編集面と衝突する。
[根拠 file:line] `brief.md:32-33,113-122`; `plan.md:440-454`; `orchestrator/campaign/s8b_floor_campaign.py:2697,3429-3643`
[提案] U0 に schema・key helper・共有 fixture、U1 に producer/resume/render、U2 に stats・ratified・holdout・oracle driver の consumer 検査を置く。U0 完了後だけ U1/U2 を並列化し、最後に acceptance を一度行う。t1142 の変更は U1 の開始時点で再確認する。
```

## 総括

最重要の漏れは `s8b_oracle_driver.py:930-964` の直接 binary consumer と、独立した `s8b_holdout_freeze.py:1317-1395` である。

schema/P2 変更で壊れる fixture は少なくとも 10 箇所。fake `PreparedCell` 6 箇所、合成 result/artifact/golden 4 箇所で、direct call の更新漏れも 2 箇所ある。

分割は brief の A→B より、plan の U0→U1/U2 を支持する。ただし U2 に oracle driver 互換検査を追加する。