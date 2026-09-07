## blocker

- formal consumer の公開 API だけ更新され、唯一の production caller が未更新である。[p3_autonomous_workload_trial.py:1862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1862) は、[reflux_formal_consumer.py:1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:1223) の必須 3 引数 `campaign_output_root`、`origin_run_plan_sha256`、`attempt_capability_sha256` を一つも渡していない。module 名による consumer grep でも production caller はこの 1 件だけだった。焦点走の 4 件はすべて、この呼出し時の同じ `TypeError` が直接原因であり、現時点の失敗原因に別例外は混ざっていない。

  成果物影響: 全 origin 実行が formal 判定前に止まり、formal receipt と terminal projection を作れず、certified 選択、材料レポート、試行台帳の origin 成果物を成立させられない。

- envelope の保存 root と再読 root が一致する契約になっていない。[p3_autonomous_workload_trial.py:4900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:4900) は envelope を `run_root` に書く一方、[p3_autonomous_workload_trial.py:1873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1873) は別の caller 入力 `producer.evidence_root` を consumer へ渡し、consumer はその root から固定 path を読む。[reflux_formal_consumer.py:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:385) 実際の public fixture でも両 root は別である。[test_p3_autonomous_workload_trial.py:10834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:10834) [test_p3_autonomous_workload_trial.py:11000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:11000)

  成果物影響: 必須 3 引数だけを足しても disk envelope 検査が FC03 になり、期待する `P6Unavailable` receipt の代わりに拒否 projection が試行台帳へ入る。

## must-fix

- observation 開始を lifecycle start 後へ動かした結果、その失敗を terminalize できない。[p3_autonomous_workload_trial.py:5064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:5064) の失敗時は projection がまだ `None` のまま terminal 記録を試みるが、[trial_registry.py:4932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4932) が origin binding と projection の不一致を拒否する。その後 [p3_autonomous_workload_trial.py:5290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:5290) が非永続の partial dict を合成するため、追加テストは start の存在だけを見て通る。[test_p3_autonomous_workload_trial.py:11257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:11257)

  成果物影響: 試行台帳に terminal のない start が残り、再試行を阻止しながら acceptance は成立せず、返却された partial と disk 上の材料レポートも食い違う。

- R1 の iff は API、terminal、最終 acceptance では強制されるが loader では強制されていない。API は [trial_registry.py:4682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4682)、terminal は [trial_registry.py:4932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4932)、acceptance は [trial_registry.py:5381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:5381) で照合する。一方 loader は 2 種の key set を無条件に許し、[trial_registry.py:4511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/trial_registry.py:4511) で `origin_terminal_projection` の有無を origin binding の代理にしている。したがって originless start に有効な digest を足した start-only 台帳、または terminal projection も足した完結台帳は loader を通る。これは変更前の exact-key 拒否を弱める具体的入力である。

  成果物影響: originless の writer bytes は不変だが、試行台帳 loader の受理集合は拡張され、偽の optional key を持つ行が履歴検査や重複 start 判定へ入り込む。最終 acceptance は拒否するため certified 選択までは広がらない。

- caller 修正後に露出する第二の fixture 不整合がある。[reflux_origin_fixture_builder.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/reflux_origin_fixture_builder.py:626) は provenance に `fixture-run-*` を入れ、[test_p3_autonomous_workload_trial.py:10583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:10583) は論理 campaign 値だけを更新して physical identity を更新しない。また [test_p3_autonomous_workload_trial.py:10909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:10909) は ledger を stub で seal するだけで、producer 導出 identity の canonical root に lock/WAL を作らない。[reflux_formal_consumer.py:892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:892) が次に FC03 を返す。

  成果物影響: 現在の 4 件から `TypeError` を除いても public-path test の `P6Unavailable` receipt は得られず、材料レポート用の参照値は拒否値のままになる。

## nit

- 発火しない、または入力から恒真になる検査がある。[p3_autonomous_workload_trial.py:1310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1310) の ordinal 順は直前の `range` から直接作っている。[p3_autonomous_workload_trial.py:1314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1314) は同じ決定的関数を直後に再実行し、テストは関数を呼出し途中で変化させる monkeypatch だけで発火させる。[test_p3_autonomous_workload_trial.py:10465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:10465) preimage 相異検査 [p3_autonomous_workload_trial.py:1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/p3_autonomous_workload_trial.py:1324) も q が preimage に入るため恒真で、仮に同一なら直後の identity 相異検査も同じ入力を拒否する。さらに [reflux_formal_consumer.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:429) の decoded preimage 再比較と、[reflux_formal_consumer.py:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:945) の `path != computed_root` も前段型検査から恒真である。

  成果物影響: 現行成果物の値は変えず、変異台帳が実在入力で発火する防壁数を過大表示する。

- 変異テストの単一理由性が不足する。[test_reflux_formal_consumer.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:737) は envelope digest と in-memory bytes の両方を同時に壊すため、片方の述語を外しても他方が拒否する。「別 trial」と「過去 attempt」のテスト [test_reflux_formal_consumer.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:796) [test_reflux_formal_consumer.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:826) も WAL を plan の canonical root 外へ移すので、attempt 値検査や論理 identity 検査を外しても [reflux_formal_consumer.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/campaign/reflux_formal_consumer.py:942) が先に拒否する。

  成果物影響: 現行の受理値は変わらないが、対象述語を無効化してもテストが赤くならず、将来の certified 選択の弱体化を検知できない。

- 受入要件 18 を実装しない scope に対し、originless report へ架空の `campaign_runs` を加える試験が追加されている。[test_reflux_originless_compatibility.py:1286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_originless_compatibility.py:1286) しかも実際の拒否理由は同時に削除した既存 `cells[0].campaign_root` であり、`campaign_runs` の有無は検査していない。仮想リスク向け test であり scope 逸脱である。production に受入要件 12、18、R2 の実装逸脱は見つからなかった。

  成果物影響: production 成果物は変えないため現時点では nit だが、試験面だけが未実装 report grammar を既成事実化する。

- 現行 hash の差込みは [test_reflux_formal_consumer.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_reflux_formal_consumer.py:347) からの自己整合 fixture と、更新された canonical golden にある。揮発 payload を期待値へ焼き込んだ追加箇所は見つからなかった。ledger producer は [test_p3_autonomous_workload_trial.py:10909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-r1r4/orchestrator/tests/test_p3_autonomous_workload_trial.py:10909) で stub され、production 機構を通らない。

  成果物影響: 現行成果物は変えないが、これらを end-to-end 結線の証拠に数えると材料レポートの保証範囲を過大評価する。

## 総括

判定: **fix 必要**。静的検査のみで、test は実行していない。  
最大点 1: formal consumer の必須 3 引数が唯一の production caller に未結線で、焦点走 4 件の直接原因。  
最大点 2: envelope root と evidence root が分裂し、物理 fixture も新 identity/layout に未整合なので、単純な caller 修正後も FC03 が残る。  
最大点 3: post-lifecycle failure が start-only 台帳を残し、loader の R1 iff も origin binding ではなく別 key から推測して受理集合を広げている。