## 回帰の原因特定

回帰 2・3 で効かなくなった拒否 gate はない。両方とも、`drive_iteration` の呼出し先が公開 `run_one_iteration` から内部 `_run_one_iteration_resolved` へ変わり、既存テストの monkeypatch が呼出し経路から外れたことが原因である。

- 回帰 2: 基準版では `drive_iteration` が `run_one_iteration` を呼んでいた (`c7ed56589:p3_s4_loop.py:1881-1884`) ため、`test_p3_b4_closed_critic.py:2786` の `fixture_synthesis` が実行を止め、synthetic COMMIT を生成していた。変更後は [p3_s4_loop.py:1987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1987) が内部実装を直呼びするため、その patch は無効である。B4 drive gate `:1922-1934` と内部 B4 gate `:1435-1447` はともに通過し、実 `patchharness.applied`、quarantine、condition gate `:1520` まで到達して configure/compiler failure になった。
- 回帰 3: 同じ理由で `test_p3_b4_closed_critic.py:2920` の public seam patch が無効になり、[p3_s4_loop.py:1509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1509) の実 `applied` が `sub="unused-by-positive-control"` を開いた。[patchharness.py:255-257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/patchharness.py:255) から `git -C` が走り、同 `:189` の fail-closed で停止した。
- 最小修正は `test_p3_b4_closed_critic.py:2786,2920` の patch 対象を `_run_one_iteration_resolved` に変えること。前者の `fixture_synthesis` は `layout, contract, resolved_site` が positional で渡される内部署名に合わせ、同ファイル `:2674` の置換対象一覧も更新する。後者の fake は既に `*_args, **_kwargs` を受けるため対象名の変更だけで足りる。これは裁定 C2 の呼出し構造を保つ test consumer 修正であり、C10-1 の実装を要求しない。

拒否順序は次のように変わった。condition gate はいずれも `do_build=True` かつ patch/quarantine 通過後だけである。

- `main`: 基準版は CLI 整合 gate `:1957-1974` → emit 経路ならそのまま B4 marker gate `default_cfg:1071-1078`、通常 build なら coder authority `:2012-2013` → B4 marker gate → drive B4 gate `:1813-1825` → public B4 gate `:1398-1410` → condition `:1493`。site gate はなかった。変更後は CLI `:2066-2083` → 適用対象なら coder authority `:2088-2093` → site admission `:2095-2096` → B4 marker gate `default_cfg:1110-1117` → drive B4 gate `:1922-1934` → internal B4 gate `:1435-1447` → condition `:1520`。emit 経路は authority を引き続き要求しないが、site gate が B4 marker gateより先になった。
- `drive_iteration`: 基準版は B4 launcher `:1813-1825` → receipt/protocol gate `:1830-1856` → public B4 gate `:1398-1410` → condition `:1493`。変更後は site pair/admission/tag gate `:1897-1912` → B4 launcher `:1922-1934` → receipt/protocol gate `:1939-1965` → internal B4 gate `:1435-1447` → condition `:1520`。CLI と coder authority gate はこの入口にはない。
- 公開 `run_one_iteration`: 基準版は B4 launcher `:1398-1410` → condition `:1493` で、site gate はなかった。変更後は public B4 launcher `:1566-1578` → site admission `:1579-1583` → internal B4 launcher `:1435-1447` → condition `:1520`。
- 内部 `_run_one_iteration_resolved`: 基準版には別関数として存在せず、旧 `run_one_iteration` 本体を改名したもの。そのため現在は B4 launcher `:1435-1447` → condition `:1520` で、site・CLI・coder authority gate は持たず、呼び手が解決済み値を保証する。

B4 gate は現在、内部 `:1435-1447`、公開 wrapper `:1566-1578`、drive `:1922-1934` の3箥所にある。旧 public gate `c7ed56589:1398-1410` のコード上の後継は、改名された内部 gate `:1435-1447` である。公開 wrapper gate `:1566-1578` は新設された二つ目である。移植元も内部 [p3_s4_loop_trigger_gating.py:751](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop_trigger_gating.py:751)、公開 `:876`、drive `:1045` の3箥所であり、公開直呼びは public＋internal、drive は drive＋internal の二段検査になる。

## 所見

1. 対象 [test_p3_b4_closed_critic.py:2786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2786)、同 `:2920`、[p3_s4_loop.py:1987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1987)。`drive_iteration` の内部化に既存横断 test consumer が追随しておらず、public seam の fake が実行されない。放置すると B4 routing/receipt の正例が synthetic COMMIT または dry-pass を検査せず、実 source patch・condition compiler または無効 directory へ進む。重大度: must-fix。

2. 対象 [p3_s4_loop.py:1566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1566)、[test_p3_s4_loop.py:4574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:4574)。新しい公開 gate は `boundary="base public run_one_iteration"` だが、旧 gate の参照 `"base run_one_iteration"` をテストが期待したままである。放置すると拒否集合と副作用なしの性質は維持される一方、公開拒否 boundary の参照値と acceptance test が不一致のままになる。移植元の public boundary と同型なので、最小修正は regex を `"base public run_one_iteration"` に更新すること。重大度: must-fix。

対応済みの公開三入口について、意図した site 集合縮小以外の受理拡大は見つからない。複数条件を同時に違反した場合は、`main` と `drive_iteration` で site gate が一部の B4 gateより先になり例外の勝者が変わるが、拒否自体は維持される。回帰 2・3 は受理集合の拡大ではなく、テスト用実行 seam の到達性回帰であり、C11 の一箥所変異では捕捉されない。

## scope 外だが real な所見

裁定 C3 の拡大は残る。[p3_s4_loop.py:1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1128) の未束縛 `default_cfg` を再 export 済み `run_campaign` へ直接渡すと、[loop.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/loop.py:194) が呼出し側の認可契約を bind できる。基準版では異なる契約の再 bind が [ident.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/ident.py:113) で拒否されたため、これは C11 が捕まえない実際の受理拡大である。放置すると site admission と compute の `measurement_env` identity 分離を通らない直接 campaign が作成可能だが、C3 により本 wave の保証外である。

裁定 C10-1 の縮小も残る。[p3_b4_launcher.py:147-174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:147) は base cfg を site 射影せず、その raw ID を `:527-530` で context に bind する。一方、base `main` は compute で `measurement_env="pegasus"` を付ける `p3_s4_loop.py:2105`。したがって compute の正式 base B4 は drive/internal gateで campaign-ID 不一致となる。今回の回帰 2・3は OTHER 固定下でそれらの gate を通過しているため、この C10-1 とは別原因である。

## 総括

回帰 2・3の原因は gate 弱化ではなく、`drive_iteration` が既存 public mock seam を迂回したことにある。  
最小修正は `test_p3_b4_closed_critic.py` の残存2 patchを内部 resolved seamへ移すことで、変更本体は裁定 C2どおり維持できる。  
B4 gateの二重化は移植元と同型で、旧単一 gateのコード上の後継は内部 gateである。  
公開三入口では意図した site 縮小以外の拡大はなく、C3の直接 `run_campaign` 拡大とC10-1の compute B4縮小だけがscope外で残る。  
pytestは再実行しておらず、以上は指定された親実測を前提にした静的検査結果である。