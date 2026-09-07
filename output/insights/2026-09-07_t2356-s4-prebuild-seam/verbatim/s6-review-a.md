## 裁定項目の充足

| 項目 | 判定 | 根拠 |
|---|---|---|
| C1 | 充足 | job は source を `<base>/<name>-src` に複製し、base を同じ root に統一している。[p3_s4_loop_pegasus.sh:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:323) |
| C2 | 充足 | `run_campaign` の最初の実行文が 5 値・`env_contract` gate。[loop.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:279) |
| C3 | 充足 | receipt を `lstat`、`O_NOFOLLOW`、`fstat`、inode 一致で読む。[p3_s4_loop.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:187) |
| C4 | 充足 | 10 key exact schema、source 集合、canonical path、config hash、型を検査している。[p3_s4_loop.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:242) |
| C5 | 充足 | proposal と fixture の双方が同じ `fetchcontent_options` を production 経路へ渡す。[p3_s4_loop.py:2485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2485)、[p3_s4_loop.py:2524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2524) |
| C6 | 充足 | base は `bool(base)`、source 3 本と receipt は `is not None` で presence 判定。[pipeline.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:894) |
| C7 | 充足 | copy destination と base equality が required fragment と復帰変異の双方にある。[test_p3_s4_loop_job_contract.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:252)、[test_p3_s4_loop_job_contract.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:447) |
| C8 | 充足 | receipt option と後続 option の連続 fragment を両分岐で pin している。[test_p3_s4_loop_job_contract.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:302) |
| C9 | 充足 | production `_v2_commands` を wrap し、fixture/proposal ごとに fresh layout で捕捉 argv を直接検査する。[test_p3_s4_loop.py:8064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8064) |
| C10 | 親作業待ち | 現差分に docs はない。依頼文どおり親担当なので、この段階の手順違反とはしない。ただし commit 前には未充足。 |

C1〜C9に must-fix の実装欠陥は見つからなかった。

## gate の署名

禁止 1 は署名どおり発火する。base と source 3 本が present、receipt が absent なら `any=True/all=False` となり `ValueError`。[pipeline.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:894)

禁止 2 も署名どおりで、5 値がすべて present かつ `env_contract=None` なら次の分岐で `ValueError`。[pipeline.py:906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:906)

順序も正しい。gate は [loop.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:279) にあり、authorization は同 :394、layout 作成は :411、WAL recovery は :423、source identity 解決は :503。したがって禁止 1 / 2 の入力ではこれらへ到達しない。

禁止 3 は receipt loader より前に `argparse.ArgumentParser.error()` を呼ぶ。[p3_s4_loop.py:2323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2323) に対し loader は同 :2332 以降なので、存在しない receipt path を併用しても rc=2 の組合せ拒否が先になる。

must-fix / nit とも所見なし。

## 正例の成立

5 値ありの正例は静的には成立する。

- `run_campaign` gate が full tuple を受理し、`evaluate_options` に 5 値を追加する。[loop.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:553)
- `evaluate` が同じ 5 値を `_prepare_evaluation_core` へ渡す。[pipeline.py:1937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1937)
- core が値を `common` へ入れ、production `buildcache.build_v2` を呼ぶ。[pipeline.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1298)、[pipeline.py:1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1341)
- job の proposal/fixture 両分岐が receipt を渡す。[p3_s4_loop_pegasus.sh:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:433)

既定経路も成立する。5 値の既定値では validator が `False` を返し、`evaluate_options`、`fetchcontent_options`、`common` の追加分岐をすべて通らない。[pipeline.py:910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:910) `buildcache.py` 自体に差分がないため、既定 caller の configure argv と cache identity を変える変更もない。

静的確認のみであり、これらの正例を実走したとは報告しない。

## テストの歯

| test | 削除時に素通しになる欠陥 |
|---|---|
| `test_prebuild_receipt_loader_returns_exact_atomic_five_tuple` [7795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7795) | 返却 tuple の順序・値の誤り、または `pbs_jobid` 等を transport に混入する変更 |
| hash mismatch [7809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7809) | M5、現物と違う config hash の受理 |
| top-level keys [7817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7817) | M6、未知 key や欠落 key の受理 |
| source names [7829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7829) | source 名の重複・欠落の受理 |
| path cases [7843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7843) | noncanonical root、source/config symlink の受理 |
| receipt symlink [7867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7867) | M7、symlink receipt の受理 |
| invalid field type [7875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7875) | `configure_argv` 内の非文字列を受理 |
| CLI incompatibility [7891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7891) | M9、`--no-build` / planner-context 併用の受理、または拒否前の loader 到達 |
| run_campaign gate [7902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7902) | M10、partial tuple や contract 欠落が authorization/layout/source 解決へ到達 |
| pipeline gate [7940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7940) | M13、直接 pipeline caller の partial tuple が build/WAL へ到達 |
| default loop spy [7982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7982) | 意図上は M14、既定時の `evaluate_options` 汚染 |
| default pipeline spy [8028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8028) | M14、既定時の production `build_v2` kwargs 汚染 |
| production 両 route [8064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8064) | M8/M11/M12、fixture/proposal の片側断線、loop/pipeline 転送欠落、configure define 欠落 |
| terminal pin [8157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8157) | R1 の既存 duplicate-skip 挙動が無意識に変わる変更 |
| static job contract [346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:346) | C1/C7/C8 の実 job fragment 欠落 |

テスト上の弱点は次のとおり。

- **nit:** default loop spy は `evaluate_spy` の呼出し回数を確認しない。具体的には、入力 `[genome]` が誤って全件 skip されても `observed == {}` のまま `isdisjoint` が通る。[test_p3_s4_loop.py:8000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8000)、同 :8025。production 実体到達を証明しない正例である。
- **nit:** `assert len(volatile_nontransport_fields) == 3` は固定 literal の要素数確認で、production のいかなる変異も殺さない恒真 assert。[test_p3_s4_loop.py:7798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7798)
- **nit:** gate test の `tmp_path` は実行へ渡されていない。具体的には、別の output root に副作用が出ても `tmp_path` は空のままで :7937 が通る。authorization/layout/source の明示 mock は有効だが、この空 directory assert 自体には歯がない。[test_p3_s4_loop.py:7908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7908)、同 :7937。
- **nit:** 新しい M1〜M4 mutation case は `source.count(fragment) <= 1` のため、fragment が最初から 0 件でも「mutation 後に expected missing」として緑になる。[test_p3_s4_loop_job_contract.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:447)、同 :498。ただし baseline の `test_job_body_static_contract` が欠落を別途赤にするため、suite 全体の受理穴ではなく mutation 証人単体の弱さである。

## 受理集合の緩み

must-fix に当たる緩和は見つからなかった。

追加された validator は partial tuple と contract 欠落を新たに拒否するだけで、既存 exact 検査を緩めていない。[pipeline.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:883) production を test double に合わせる互換分岐もない。

`quarantine` と `_require_condition_gate` の述語・順序には差分がなく、従来どおり quarantine 通過後に condition gate、その後 `run_campaign` である。[p3_s4_loop.py:1668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1668) admission や `buildcache.py` にも変更はない。

## scope の混入

scope 外の実装混入はない。

- R1: terminal duplicate skip は変更せず、現行挙動の test 追加だけ。[test_p3_s4_loop.py:8157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8157)
- R2: `pbs_jobid` は非空文字列検査だけで、現在の job ID との一致検査はない。[p3_s4_loop.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:314)
- R3: build identity 実装を持つ `buildcache.py` に差分なし。
- D1679 見送り 4 件: 依存内容の完全 identity、`make/ar/git/nm` identity、condition gate durable 化、`TMPDIR` 検査のいずれも実装差分にない。

変更は裁定どおりの 6 file に限定されている。

## 総括

must-fix は 0 件。C1〜C9、禁止 1〜3、2 つの正例はいずれも差分上成立しており、受理集合の緩和や scope 外実装も見つからなかった。

nit はテストの歯に関する 4 件。特に default loop 正例は production `evaluate` 到達を保証せず、mutation test の fragment 存在確認も弱い。ただし、現実装が certified 選択・レポート・台帳の値を誤らせる実在欠陥までは示さない。

C10 の docs 更新は現在未実装だが、依頼文で親担当と明示された範囲である。pytest その他のテストは実行していない。