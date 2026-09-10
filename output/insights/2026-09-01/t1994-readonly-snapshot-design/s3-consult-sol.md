## 1 鎖の裏取り

1. **裏が取れた。** D863 は、層 3 必須経路・宣言 arm と実走 arm の同一性・計測対象一致の 3 件を正式系列の着手条件としている。[docs/decisions.md:32029-32038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:32029)

2. **裏が取れた。** archive 959 は `[T-1749]` を「D863 第 2 条件の実体」として新規起票している。[worklog-phase3-0826-959.md:776-780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0826-959.md:776)

3. **文字列同一性までなら裏が取れた。** commit `1e10a081fae603a70ef38e71df3d3ac77704ac72` は現 HEAD の祖先で、E1/E2/E3 を実装している。ただし worklog 979 自身が「実行到達性は閉じていない」と限定している。[worklog-phase3-0826-978-979.md:886-888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0826-978-979.md:886)

4. **T-1805 の実装までは裏が取れたが、完全閉鎖は取れない。** D966 は A→B→A を含む 4 経路を閉じると明記し、commit `55900c9bc8ae5b8b54ea8017764ad307dc587db8` と worklog 1033 が実装を記録している。[docs/decisions.md:34428-34444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:34428) [worklog-phase3-0827-1033.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0827-1033.md:48)  
   しかし同じ worklog が owner による A→B→A の残余を `[T-1994]` として起票している。[同:24-29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0827-1033.md:24) [同:953-955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0827-1033.md:953)

5. **契約側の更新は裏が取れた。** D967 と commit `ddc74279c0f4f859f030dac26022c25523c0f008` により、契約 JSON と判定器の双方へ 13 番目の field が追加されている。[docs/decisions.md:34446-34459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:34446) [s8c_preregistration_evidence.py:2223-2252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8c_preregistration_evidence.py:2223)  
   ただし worklog 1141 自身が、C10 は値束縛を判定せず恒真化した実装も `SATISFIED` へ到達すると明記している。[worklog-phase3-0901-1141.md:41-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0901-1141.md:41) したがってこれは契約 drift/readiness の閉鎖であり、因果束縛本体の代替ではない。

6. **D1289 の逐語は裏が取れたが、決定打という推論は成立しない。** 「唯一の未解決項」は確かに書かれている。[docs/decisions.md:41534-41549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:41534)  
   一方、先行する対象固有裁定 D1201 は、D966 の A→B→A を引用して `[T-1994]` を閉じるまで正式受入を成立させないと明記している。[docs/decisions.md:39963-39978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:39963) D1289 の決定本文は層 3 hard failure だけで、D1201 を supersede していない。

7. **機構は閉じているが、親が挙げた SHA は現 HEAD の祖先ではない。** `a4957893...` と同一内容の現 main 着地 commit は `6f85d7c836c65d506f56b6053183986bcd72b3f0` で、両 commit 間の対象 2 file の差分はゼロだった。現コードの hard failure は [trial_registry.py:6070-6085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/trial_registry.py:6070) に実在する。

8. **誤り。** archive 959 は最後の実体ではない。現 carry [docs/worklog.md:2378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/worklog.md:2378) を遡ると、最後の本文は entry 1115 で、第 1 条件を実装待ちとしている。[worklog-phase3-0901-1115.md:124-126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0901-1115.md:124) stale であること自体は正しいが、stale 元を 959 とする説明は違う。

## 2 機構の実在と必須経路性

`proposal_build_source_bindings` は実在する。ただし現行関数名は依頼にある `_cross_binding_build_receipt` ではなく `_cross_binding_source_bindings` である。

- field は [autonomous_trial_completeness.py:215-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/autonomous_trial_completeness.py:215) にある。proposal bytes を再読して wire から述語を再導出し [同:3453-3577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/autonomous_trial_completeness.py:3453)、preimage の完全多重集合、digest、WAL source、`build_start` identity を照合する。[同:3639-3693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/autonomous_trial_completeness.py:3639) [同:4048-4075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/autonomous_trial_completeness.py:4048)
- 正式受入はこれを `accepted.append` より前に無条件で呼ぶ。[trial_registry.py:6095-6104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/trial_registry.py:6095) build cell の campaignless fallback はさらに手前で hard failure になる。
- `set(bindings) == set(S8C_CROSS_BINDING_FIELDS)` は単独なら構造的な恒真検査だが、実際の値検査はそれ以前に発火するため、この等式だけに保証が依存してはいない。[autonomous_trial_completeness.py:4566-4588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/autonomous_trial_completeness.py:4566)
- topology と execution の証明種別は実装自身が `producer-self-consistency` / `producer-execution-contract` と限定している。[同:4151-4161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/autonomous_trial_completeness.py:4151)
- 静的な正例テストと個別変異負例は存在する。[test_autonomous_trial_completeness.py:4044-4072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_autonomous_trial_completeness.py:4044) [同:4075-4184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_autonomous_trial_completeness.py:4075)

T-1805 の compiler input / expected materialization 配線も実在する。

- floor は freeze entry から descriptor を作り、全 cell の `build_v2` へ渡す。[s8b_floor_campaign.py:4275-4302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_floor_campaign.py:4275)
- `build_v2` は declaration と admission digest を照合し、別 checkout で期待 tree を再実体化してから snapshot を照合・非書込化し、その context 内で build する。[buildcache.py:2950-3009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:2950)
- build 後は CMake depfile 群から compiler input manifest を採取・再検証し、snapshot digest を再照合する。[buildcache.py:2637-2709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:2637)
- binary receipt 発行は actual/expected digest の一致と manifest の live 検証を無条件に要求する。[s8b_binary_admission.py:183-246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_binary_admission.py:183)

ただし期待側と候補側は完全に独立した producer ではない。別 checkout ではあるが同じ materializer 実装を使い、module 自身が「同じ実装に仕込まれた挙動は両側で再現される」と限界を明記している。[s8b_expected_materialization.py:21-26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:21)

静的な正例・負例と、過去の実 compiler manifest 正例記録は存在するが、今回は pytest を実走していない。[test_s8b_expected_materialization.py:513-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_expected_materialization.py:513) [worklog-phase3-0827-1046.md:3-21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/archive/worklog-phase3-0827-1046.md:3)

## 3 残余の切り分け

`[T-1994]` を D863 第 2 条件の外へ切り離す判断は妥当ではない。

D1201 は「所有者自身による A→B→A」を閉じると決定し、その理由として D966 が build 中の source 差し替えを逐語で名指ししたことを挙げている。[docs/decisions.md:39963-39977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:39963) D966 はさらに、その検査不足では「D863 の宣言 arm と実走 arm の同一性を文字通り満たさない」としている。[docs/decisions.md:34434-34441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/decisions.md:34434)

現行 main の未認証部分は具体的である。

- snapshot と親 directory は mode bit を落とすだけで、owner は権限を戻せる。[s8b_expected_materialization.py:14-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:14)
- 実装は `chmod(mode & ~0o222)` による防護である。[同:541-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:541)
- したがって owner が build 中だけ B へ差し替え、終了前に A と mode を戻す経路は、D1201 が要求する read-only bind mount 相当の不変性では閉じていない。
- `[T-1994]` は現 worklog にも carry され、実装 commit は見つからない。[docs/worklog.md:2572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/docs/worklog.md:2572)

D1289 の理由文はこの残余と矛盾するが、その決定本文は層 3 の hard failure だけである。D1201 を無効化せず両裁定を守るなら、`[T-1994]` は未解決のまま残すほかない。

## 4 判定

**親の結論は誤り** — 第 2 条件にはまだ実装すべき実体が残る。

1. D1201 は `[T-1994]` の owner A→B→A を、D966 が名指しした D863 第 2 条件として閉じるよう命じている。
2. 現行実装は owner が mode を戻せることを明記しており、要求された実効的不変 snapshot ではない。
3. D1289 は D1201 を supersede せず、親の commit/carry の鎖にも `a495` 非祖先・最新実体 1115 という誤りがある。

## 5 台帳の是正案

親の結論が誤りなので、3 条件すべてを閉鎖済みとする置換は行ってはいけない。置き換えるなら次の非閉鎖本文が妥当である。

```text
- [T-822] **P2・一部実装済み**: D863 の 3 条件のうち第 1・第 3 条件は閉じた。
  第 1 条件は 2026-09-01 [T-2075]、commit 6f85d7c83 (a4957893b と同一差分)、D1289 で閉鎖。
  第 2 条件の文字列束縛は 2026-08-26 [T-1749]、commit 1e10a081f、D955 で閉鎖。
  build/実走束縛は 2026-08-27 [T-1805]、commit 55900c9bc、D966/D1134 で実装。
  契約 C10 は 2026-09-01 [T-1806]、commit ddc74279c、D967 で更新。
  ただし owner による A→B→A は [T-1994]/D1201 の実装待ちで、第 2 条件は完了にしない。
  第 3 条件は 2026-08-26 [T-822]、commit 2e523db1c、D863/D919 で閉鎖。
```

## 総括

**親の結論は誤り。D1201 と現行コードが `[T-1994]` を D863 第 2 条件の未解決残余として名指ししている。**  
最大の懸念は、D1289 の「唯一」を根拠に、より具体的な未 supersede 裁定 D1201 を黙示的に無効化すること。  
pytest は実走しておらず、本判定は現 HEAD `259e02209` の静的検査による。