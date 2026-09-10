## 合成監査の結果

両変更は正しく両立する。

- main は AST source segment 抽出用の `_split_source_lines` と `_get_source_segment` を追加し、`_FunctionCallVisitor` と `_analyze_source` から利用する変更である（合成後 `orchestrator/campaign/p3_b4_wiring_probe.py:722`, `:804`, `:888`, `:909`）。
- wave は `runtime.L.default_cfg()` の直後に環境契約を bind し、`bound_environment_contract` を読む前に非 `None` を保証する（合成後同 file `:1522`, `:1523`, `:1531`, `:1535`）。
- `p3_s4_loop.default_cfg` は admission policy だけを bind して返す（`orchestrator/campaign/p3_s4_loop.py:1128`）。site-aware 経路は `_campaign_cfg_for_site` で環境契約を bind する（同 file `:145`, `:159`）。
- main helper は静的解析前処理、wave の bind は fixture cfg 作成経路であり、同じ probe `main()` 内で順に実行されても状態を共有しない。`git apply --check` も rc=0 で、hunk の競合はない。
- `ident.bind_environment_contract` の既存契約は未束縛 cfg を bind し、同一契約の再 bind を許し、異なる契約を拒否する（`orchestrator/campaign/ident.py:100`, `:113`）。main はこれを変更していない。

## 親の前提を覆す新事実

なし。

`p3_s4_loop.py`、`test_p3_s4_loop.py`、`test_p3_b4_closed_critic.py` はいずれも merge base と main の blob ID が完全一致した。`ident.py`、`env_contract.py`、`site_policy.py`、probe の cfg 供給元となる launcher・critic・raw producer も同様に変更されていない。

補足として、固定 SHA 間の到達 commit 数は `git rev-list --count` では93件で、依頼文の76件とは一致しなかった。ただし意味論上の前提を覆す変更は見つからなかった。

## merge 後に赤くなりうる consumer

grep による参照閉包は次のとおり。

- `orchestrator/campaign/p3_b4_wiring_probe.py`: `main` → `_load_static_modules` → `_analyze_source` → 新 helper、および `main` → `_make_probe_view` → `default_cfg` → explicit bind → contract hash。
- `orchestrator/tests/test_p3_b4_wiring_probe.py:153`, `:267`, `:303`: main が追加した helper・guard wiring・分割回数の直接検査。
- 同 test file `:842`, `:1170`, `:1234`: `_make_probe_view` の署名と実 `P.main()` 経路。双方の変更を同時に通る主要 consumer。
- `orchestrator/tests/test_p3_s4_loop.py:158` と `:179`: raw `default_cfg` が未束縛で、site 射影後だけ契約を持つことを検査。
- `orchestrator/tests/test_p3_b4_raw_record_producer.py:149`: 未束縛 cfg を呼出し側で bind して lock hash を読む追随 consumer。
- `orchestrator/tests/test_p3_b4_closed_critic.py:2786`, `:2920`: wave が内部 resolved seam へ移した consumer。main 側の変更はない。
- production 側では `orchestrator/campaign/p3_b4_launcher.py:141`, `:152` と `orchestrator/campaign/p3_b4_closed_critic.py:1987` が base cfg の参照元。既裁定どおり compute launcher の site 射影漏れは carry だが、今回の main 取込みによる新規回帰ではない。

## merge message file

作成先: [merge-message.txt](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/output/insights/2026-09-03_t2231-s4-loop-site-env/merge-message.txt>)

`python3 tools/check_ai_provenance.py --message-file <上記パス>` は `check_ai_provenance: 1 件、違反なし`、rc=0。

## 総括

- 両 hunk は行範囲・責務・状態のいずれも独立しており、合成可能。
- main に `default_cfg` や環境契約 bind の前提を戻す変更はない。
- 主要 consumer は probe 本体と専用テストで、参照関係を grep で確認済み。
- merge、commit、コード・docs 編集は行わず、指定 message file のみ作成した。