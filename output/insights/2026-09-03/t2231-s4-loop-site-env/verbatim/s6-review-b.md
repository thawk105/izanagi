## 変異 M1〜M13 の検証

`yes` は「指名テストが変異を殺す」を表す。単一性は、同じ変異を別の検査層も検出する場合を過剰決定とした。

| 変異 | 実装子の主張どおりか | 赤になる根拠または反証 | 赤理由 |
|---|---|---|---|
| M1 | yes | `return True` では候補 5 件すべてが admitted となり、[test_p3_s4_loop.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:153) の exact-set 比較が赤になる。加えて M11 の login 注入も gate を通過して runner sentinel に到達する。 | 過剰決定 |
| M2 | yes | `return site == PEGASUS_COMPUTE` では集合から OTHER が欠落し、同じ exact-set 比較が赤になる。さらに autouse fixture が通常 caller を OTHER にするため、公開入口群も `_admit_env_contract` で先に拒否される。 | 過剰決定 |
| M3 | yes | compute 分岐を消すと contract bind は identity に入らないため、[ident.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/ident.py:196) により compute と OTHER の ID が同一となり [test_p3_s4_loop.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:176) が赤になる。自動経路の marker 検査も別途赤になる。 | 過剰決定 |
| M4 | yes | marker を常時付与すると OTHER に `measurement_env` が入り、[test_p3_s4_loop.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:172) が最初に赤になる。その先の golden ID と B4 context の ID 照合も同じ変異を検出する。 | 過剰決定 |
| M5 | yes | sentinel contract の `env_tag` は `linux-baremetal` と異なるため、[test_p3_s4_loop.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:289) の sink 引数辞書で `env_tag` だけが不一致となる。`run_campaign` は spy なので内側の拒否はない。 | 単一 |
| M6 | yes | sentinel clock は 4242、`CLK` は 1800 なので、同じ sink 辞書の `clocks_per_us` だけが不一致となる。 | 単一 |
| M7 | yes | sentinel numactl と legacy `NUMA` が異なり、sink 辞書の `numactl` だけが不一致となる。 | 単一 |
| M8 | yes | `authorize` は recorder stub であり拒否しないが、[test_p3_s4_loop.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:296) の記録 tag が `linux-baremetal` となって赤になる。 | 単一 |
| M9 | yes | `default_cfg` で bind を復活すると、まず [test_p3_s4_loop.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:162) の `is None` が赤になる。これを除いても compute contract への再 bind は [ident.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/ident.py:113) で `ValueError` になる。 | 過剰決定 |
| M10 | yes | paired 拒否分岐を外して注入値へ進ませる変異では、None の admission と tag mapping がテスト内で正例化されているため、唯一残る失敗は `_run_one_iteration_resolved` の runner sentinel 到達となる。 | 単一 |
| M11 | yes | 注入 site gate を削除すると、login 用 tag mapping がテスト内で補われているため tag 照合を通り、runner sentinel へ到達する。`_campaign_cfg_for_site` は contract 注入時に再 admission しない。 | 単一 |
| M12 | yes | OTHER は受理済みで、`bind_environment_contract` は site と tag の関係を検査しないため、tag gate 削除後は runner sentinel だけが赤理由になる。 | 単一 |
| M13 | yes | compute の `env_contract` 転送を消すと spy の `kwargs.get("env_contract")` が None となり、sink 引数辞書の一項目だけが不一致となる。 | 単一 |

## 検出力の穴

- 文字どおりの定数恒真 assert は追加差分にない。ただし [test_p3_s4_loop.py:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:286) の `actual_cfg == campaign_cfg` は wrapper の返値と spy の受領値を比較する自己由来検査で、同値な clone でも通る。要求された contract object 同一性は直後の `actual_cfg.bound_environment_contract is contract` が別途守っている。

- [test_p3_s4_loop.py:413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:413) は AST 内の呼出し個数と式だけを見るため、3 呼出しを dead branch に置いても通る。現実装の各 reject branch は到達可能だが、このテスト単体は到達性を証明しない。

- 自動 compute 正例は hollow ではない。patch 前に保存した実 `_admit_env_contract` と `_campaign_cfg_for_site` を wrapper から呼び、`_current_site`、`_lookup`、helper の呼出し回数、実際に sink が受けた cfg、`bound_environment_contract is contract`、marker を同時に確認している。stub されるのは site 機構より外側の patch、resume、campaign sink である。

- `_campaign_cfg_for_site` が cfg をそのまま返す実装は通らない。単体検査では bound contract 同一性が赤になり、自動正例でも `campaign_cfg is not raw_cfg` と bound contract 同一性が赤になる。

- 自動経路の負例がない。predicate 単体と `drive_iteration` の注入 gate は検査するが、公開 `run_one_iteration` の `_current_site()` が login/suspect を返した際に、実 `_admit_env_contract` が `ExecutionGuardError` を出すことは検査していない。

- OTHER の projected identity は reflux on の `8ee68c0c` だけが helper を通る。off の `95a32c3e` は raw `default_cfg` では既存テストが守るが、`_campaign_cfg_for_site(..., OTHER)` を通した値では守られていない。

- 新規期待値に working tree hash、日時、実 workspace の絶対 path はない。`/sentinel/dependency-prefix` はテスト自身が入力した固定 sentinel の forwarding 比較であり、揮発値ではない。

## 所見

1. 対象 [test_p3_b4_closed_critic.py:2786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2786) および [test_p3_b4_closed_critic.py:2920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2920)。`drive_iteration` は既に `_run_one_iteration_resolved` を呼ぶのに、2 正例が旧公開 seam を stub している。前者は target を替えるだけでは fixture の keyword-only `layout` 署名も新しい positional 呼出しに合わない。成果物影響: B4 continuation の正例が合成 stub に到達せず実機械経路へ逸れ、親実測どおり 2 テストが赤のままで positive proof が成立しない。重大度: must-fix。

2. 対象 [p3_s4_loop.py:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1577) と [test_p3_s4_loop.py:4576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:4576)。公開 B4 gate の boundary を `base public run_one_iteration` に変えた一方、既存契約は `base run_one_iteration` を要求しており、先行する公開 gate で文字列が不一致になる。成果物影響: 拒否集合は同じでも既存の外部診断参照が変わり、親実測の単独テスト 1 件が赤になる。重大度: must-fix。

3. 対象 [test_p3_s4_loop.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:145)、[test_p3_s4_loop.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:341)、[p3_s4_loop.py:1579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1579)。負例は predicate 単体または注入専用の重複 gate しか通らず、自動解決経路で実 `_admit_env_contract` が負例を拒否する証明がない。成果物影響: `_admit_env_contract` が predicate を無視して既定契約を返す退行でも追加テストが通り、login/suspect が公開入口の受理集合へ混入しうる。重大度: must-fix。

4. 対象 [test_p3_s4_loop.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:157)、[test_p3_s4_loop.py:4531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:4531)、[ident.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/ident.py:196)。`canonical_preimage` が bound contract を除外するため現実装では両 arm とも不変だが、off の `95a32c3e` は projected cfg に対して検査されない。成果物影響: OTHER の off arm だけに search key を加える退行が、実行時 campaign ID と layout を変えても検出されない。重大度: must-fix。

5. 対象 [test_p3_s4_loop.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:162)。M9 は `default_cfg` の未束縛 assert が最初に失敗し、狙った compute 再 bind の `ValueError` まで到達しないため、実装報告の「再 bind 検査が単一原因」は成り立たない。成果物影響: M9 の失敗ログから compute 射影機構の破損か単なる構築方針違反かを一意に判定できない。重大度: nit。

## scope 外だが real な所見

- C3 の公開 `run_campaign` 直接 seam は残っており、未束縛 cfg を直接渡す caller は site admission を迂回できる。本 wave 由来ではない。
- C6 で除外された resume 制約と provenance 移植は未実装のまま。本レビューから scope 内へ昇格させる追加根拠はない。
- C10-1 の base B4 launcher site 射影漏れにより、compute では projected campaign ID と launcher context が不一致になる。
- C10-2 の layout 一致検査移植漏れ、C10-3 の sort driver の固定 linux 契約、C10-4 の evidence 無し OTHER fallback はいずれも real だが、裁定どおり今回の must-fix には含めない。

## 総括

M1〜M13 はすべて指名テストで赤になるが、単一原因と確認できるのは M5〜M8、M10〜M13 の 8 件で、M1〜M4 と M9 は過剰決定である。  
compute 自動正例は実 helper と contract object 同一性を通っており、no-op cfg helper も検出できる。  
一方、自動解決の負例と projected OTHER off identity に検出穴がある。  
既存 assert、golden、skip は緩められていないが、旧 seam 2 件と boundary 1 件が親実測の赤を説明する。  
このレビューでは pytest を再実行していない。