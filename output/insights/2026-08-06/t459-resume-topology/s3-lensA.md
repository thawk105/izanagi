結論から言うと、現プランはそのまま採択できません。blocker 候補は 3 件です。必須 8 ファイルはすべて読了し、追加で layout／主要 consumer を静的確認しました。書き込み・pytest 実行はしておらず、緑は主張しません。

## 所見 1 — WAL flock は attempt 回復を認可する owner lock ではない

severity: **blocker 候補**

根拠:

- `wal.append` の `LOCK_EX` は 1 frame の書き込みから fsync までしか保持されません。[wal.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:324) [wal.py:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:343) [wal.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:412)
- `campaign.lock` の `O_EXCL` は identity の初回作成だけです。競合敗者も同一 identity なら正常復帰し、実行全体の所有権は得ません。[ident.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:213) [ident.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:228)
- recovery の flock も repair 終了時に解放され、その後の replay→evaluate を覆いません。[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:67)
- プラン自身も旧 evaluator の生死を証明できないと認め、運用前提へ送っています。[s2-plan.md:336](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:336)

攻撃シナリオ:

```text
P1: start(A) → build 中（WAL flock は既に解放）
P2: identity 照合 → recovery-abort(A) → start(B)
P1: build_done(A) → verify_done(A) → commit(A)
```

`build_done(A)` は既に abort 済みの inactive attempt なので、次の topology 検査で拒否されます。別の競合列もあります。

```text
start(A) → recovery-abort(A)
P2/P3 がともに clean snapshot を見る
→ start(B) → start(C)
```

この列は「recovery abort が 1 件だけ」という予定テスト条件を満たしながら、二つ目の start で壊れます。

成果物影響:

- 後続 replay／artifact admission は campaign 全体を拒否します。[wal.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:942) [artifact_admission.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:646)
- 両 process はそれ以前に `committed` と summary 表示できるため、certified 選択・Layer3 report・台帳参照が事後失効します。
- P1 が recovery 後に WAL を一切書かず動き続けた場合は admission を通り得ますが、台帳上は生きていた A を「中断済み」と偽って閉じたことになります。

提案:

campaign 専用の別 lock fd を `LOCK_EX|LOCK_NB` で取得し、repair 前から全 WAL 書き込み・provenance checkpoint 終了まで保持してください。全 early-writer entry point も同じ lease capability を必須とし、nested `run_campaign` へ渡す構造が必要です。生存 owner がいれば resume は WAL を 1 byte も変えず拒否すべきです。

## 所見 2 — recovery record の「正規 writer 由来」を admission が証明できない

severity: **blocker 候補**

根拠:

- WAL は hash chain を持たず、真正性を保証しないと明記されています。[wal.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:14)
- `_validate_attempt_topology` は abort の active ID／receipt SHA 一致を見るだけで、誰が、どの lease 下で、なぜ書いたかを検査しません。[wal.py:975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:975)
- post-policy admission の `wal_sha256` は検査時の現在 bytes から新たに計算されるだけで、期待済み prefix や recovery authority とは比較されません。[artifact_admission.py:540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:540) [artifact_admission.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:696)
- trigger 用 `recovered_attempts` も、同じ可変 campaign 配下の文書と reason を照合するだけの計画です。[s2-plan.md:176](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:176)

攻撃シナリオ:

```text
元の拒否列:
start(A, RA) → start(B, RB) → build_done(B, RB) → commit(B, RB)

混入後:
start(A, RA)
→ fake recovery-abort(A, RA)
→ start(B, RB) → build_done(B, RB) → commit(B, RB)
```

前者は二重 start で拒否されます。後者は topology を通ります。trigger campaign なら A を `recovered_attempts` に追加し、同じ fake abort を指せば、計画された union equality も通せます。

成果物影響:

`artifact_admission` は変更後 bytes に対して `admitted-new-schema` を発行し、B を commit 済みとして consumer へ渡します。admission receipt、Layer3 report、critic digest は「偽 recovery を含む現在 bytes」を正規台帳として再 pin します。

提案:

- runtime 側は所見 1 の owner lease を必須化する。
- recovery record は exact key 集合、回復直前の WAL size／prefix SHA、active attempt ID、campaign lock SHA、lease epoch を束縛する。
- 偽造まで脅威モデルに含めるなら、campaign 内だけの自己記述では証明不能です。外部の不変台帳・署名済み recovery receipt・正式 acceptance ledger のいずれかへ pin できない回復済み campaign は non-certifying とすべきです。

## 所見 3 — correctness／bench シグナルが attempt 非局所で、回復後に別 attempt へ流用できる

severity: **blocker 候補**

根拠:

- `BuildAttemptState` が追跡するのは build/commit/abort だけです。[model.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:112)
- `_validate_attempt_topology` は `verify_done` と `bench_done` を処理せず、commit は `build_done` だけを前提にします。[wal.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:942)
- 実際の `verify_done`／`bench_done` payload には attempt ID も receipt SHA もありません。[pipeline.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:862) [pipeline.py:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:428)
- artifact admission は start の receipt/source を検査しますが、commit と verifier signal の対応は検査しません。[artifact_admission.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:646) [artifact_admission.py:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:666)
- プランはこの validator を変更しない方針です。[s2-plan.md:204](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:204)

攻撃シナリオ:

```text
run 1, do_bench=True:
start(A) → build_done(A) → verify_done(A) → bench_done(A, fitness=X)
→ commit 直前 crash

run 2, 同じ campaign、do_bench=False:
recovery-abort(A)
→ start(B) → build_done(B) → verify_done(B) → commit(B, note=no-bench)
```

`do_bench` は campaign identity に入らない runtime 値です。[pipeline.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:482) この列は現在の topology と artifact admission を通ります。

成果物影響:

- critic は variant 単位で「最後の bench signal」と「commit が一つでもある」を結合するため、A の fitness/LI を B の commit で採用します。[digest.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/critic/digest.py:208)
- plotting も variant 単位の pending bench を任意の後続 commit で確定するため、A の測定を certified として描画します。[plot_backoff.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/tools/plotting/plot_backoff.py:133)
- Layer3 は全 `bench_done` を `runs` に載せ、variant に commit が一つあれば reject を作りません。さらに view から attempt ID を落とします。[layer3_report.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layer3_report.py:254) [layer3_report.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layer3_report.py:471)
- verifier 統計は variant ごとの先勝ちなので、retry B ではなく回復済み A の signal が次手入力になります。[digest.py:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/critic/digest.py:415)

提案:

新 schema では `verify_done`／`bench_done` に attempt ID と receipt SHA を必須化し、validator が attempt 内の順序と commit 前の certified verify 集合を検査すべきです。consumer は「commit された attempt の records」だけを射影し、plotting も `require_admitted_campaign` を通す必要があります。mutation test は「A の verify/bench を残し、B のものを削除して B を commit」を必須にしてください。

## 所見 4 — receipt SHA の値検査は強いが、receipt body の後付けは通る

severity: **must-fix**

根拠:

- receiptless attempt の abort で禁止されるのは `build_admission_receipt_sha256` だけです。[wal.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:987)
- abort payload の exact key 集合や `build_admission` body の禁止はありません。
- artifact admission が receipt を収集するのは `build_start` だけです。[artifact_admission.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:668)

攻撃シナリオ:

```text
receiptless start(A)
→ recovery-abort(A, {
     id=A,
     reason=recovery-abort-incomplete-attempt,
     build_admission=<別 attempt からコピーした body>
   })
```

SHA を載せなければ topology は通ります。trigger receiptless でも、計画どおり recovery reason を閉集合へ追加すると同様です。

成果物影響:

admission decision の `attempt_receipt_sha256s` は空のままですが、Layer3 の abort view は `build_admission` body を残すため、「receiptless attempt に receipt がある」ような矛盾した report／台帳になります。

提案:

recovery abort は receiptless なら `{reason, build_attempt_id}`、receiptful ならそれに SHA を加えた exact key 集合だけを許可してください。`build_admission` body、fitness、verify、その他の余剰 key は admission 側でも拒否すべきです。

なお、SHA 自体への攻撃は破れませんでした。receiptful A に別 attempt の SHAを載せる、SHAを欠落させる、receiptless A に SHAを載せる列は [wal.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:922) と [wal.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:987) で拒否されます。

## 所見 5 — 決定的 crash は無限に「recovery abort + 新 start」を増やす

severity: **must-fix**

根拠:

- recovery reason を retryable 集合へ入れる計画です。[s2-plan.md:48](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:48)
- loop は retryable abort を terminal 集合から外し、再評価します。[loop.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:170)
- retry 上限、回復回数、同一 crash fingerprint の停止条件はありません。
- trigger provenance 同期の予定位置は `_run_one_iteration_resolved` の帰還後なので、新 attempt が再び process death すると到達しません。[s2-plan.md:196](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:196) [p3_s4_loop_trigger_gating.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:729)

攻撃シナリオ:

```text
run1: start(A) → OOM kill
run2: abort(A,recovery) → start(B) → OOM kill
run3: abort(B,recovery) → start(C) → OOM kill
...
```

trigger campaign では各新 start の前に binding record も増えます。

成果物影響（1 行）: **certified 選択は永久に空、Layer3 の abort/events と admission の `attempt_receipt_sha256s` は run ごとに増え、`wal_sha256` と provenance／台帳参照は毎回更新・旧 receipt 失効となる。**

提案:

variant ごとの recovery 回数を WAL から決定的に数え、上限到達時は新 start を書かず、明示的 `recovery-exhausted` で campaign を停止または人間判断待ちにしてください。沈黙 skip ではなく summary/report に回数・最後の stage・想定 crash class を構造化して出す必要があります。

## 所見 6 — M1〜M6 の一般化と brief の事実記述に修正が必要

severity: **must-fix**

|観測|この観測から言えないこと|
|---|---|
|M1 [brief:14](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:14)|API probe は二重 start の拒否を示すだけで、A が crash 済みか、生きた peer か、二重 resume の interleaving かは識別しません。実 process death、receipt matrix、trigger provenance、artifact consumer は未測定です。|
|M2 [brief:18](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:18)|同一 variant の通常 `run_campaign` 経路は確認できますが、旧 process の死亡、全 early writer、source 変化時の variant ID、全 entry point までは示しません。|
|M3 [brief:22](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:22)|post-policy の admission-aware consumer が campaign 単位で落ちることは正しい一方、全 consumer が同じ防壁を通るとは言えません。plotting は raw WAL を直接 parse します。[plot_backoff.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/tools/plotting/plot_backoff.py:110)|
|M4 [brief:26](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:26)|repo `output/` の 30 本に限定した結果です。external exploration root と明示 `output_root` は対象外です。[layout.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layout.py:285) [layout.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layout.py:479)|
|M5 [brief:28](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:28)|pin の列挙は網羅的ではありません。admission decision 自体と Layer3／autonomous completeness も WAL SHA を比較します。[artifact_admission.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:99) [autonomous_trial_completeness.py:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/autonomous_trial_completeness.py:1165) また plotting の `wal_sha256` は実際には 16 hex prefix です。[plot_backoff.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/tools/plotting/plot_backoff.py:165)|
|M6 [brief:32](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:32)|`run_campaign` が生成するものについては正しいですが、「今後の campaign すべて」は導けません。`wal.log`／`write_lock` は公開 writer であり、P4 自身が `run_campaign` より前の独立 writer を列挙しています。[wal.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:542)|

追加の事実誤認:

- P2 の「`wal.replay` は read-only のまま」は誤りです。現行は trigger orphan tombstone を書きます。[wal.py:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1014) プランがここを訂正した点は正しいです。
- brief の「既存 WAL bytes を変えない」と「未終端 attempt に terminal record を追記する」は逐語的に両立しません。[brief:37](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:37) プランは無断で「既存 prefix を保存」に意味を変更しています。[s2-plan.md:251](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:251)

攻撃シナリオ:

外部 `IZANAGI_EXPLORATION_OUTPUT_ROOT` に active WAL と既存 Layer3/plot receipt があり、explicit resume が recovery abort を追記する。repo `output/` の M4 scan には現れません。

成果物影響:

既存の WAL SHA pin、Layer3 admission decision、autonomous completeness の exact comparison、plot provenance が失効します。なお今回の read-only probe では、現在の repo `output/` は 30 WAL／`build_attempt_id` 保有 0、repo exploration WAL 0、環境変数は未設定、job root 内 WAL 0 でした。これは外部 root 不在の証明ではありません。

提案:

不変条件 2 を「valid prefix は不変、明示 resume は owner lease 下でのみ suffix を追記、read path は無変更、正式に seal 済みの campaign は resume 禁止」に書き直してください。M4 は走査した root の manifest と環境変数値を記録し、未走査 root を明記すべきです。

## 攻撃したが破れなかった項目

- **`wal.replay` read-only 化:** trigger tail orphan は現在も validator が「tail orphan」として受理します。[wal.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:796) 現行 tombstone は state projection から除外されるため、書き込みを外しても replay state は同じ resumable 形です。[wal.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1027) Layer3／critic は元から replay ではなく artifact admission、plotting は直接 parser なので、自己修復除去による新規例外は静的には確認できませんでした。artifact admission が既に拒否していた入力は引き続き fail-closed です。
- **prospective validation の恒真性:** 恒真ではありません。`start(A,RA)` に誤って `abort(A,RB)` を生成すれば prospective validator が発火し、既存列 `start(A)→start(B)` は pre-validation が発火します。したがって二段 validation 自体には実効性があります。
- **trigger recovered provenance gate:** `recovered_attempts[A]` に対して abort reason が `identity-error`、または attempt ID が別なら、計画された exact recovery check は発火可能です。
- ただし `test_concurrent_resume_appends_one_recovery_abort` という条件だけでは所見 1 の `abort(A)→start(B)→start(C)` を落とせません。loser process が recovery recordにも新 start にも一切触れないことと、最終 artifact admission 成功までを受入条件へ追加すべきです。

## 規律 2 / 3 との整合

validator のソース行を変更しなくても、正規 writer が生成可能な record 列を増やせば topology の意味は変わります。owner 不在の recovery と、commit attempt に束縛されない verifier signal は、正しさゲートを producer／consumer 間で緩めています。[CLAUDE.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/CLAUDE.md:67)

また A の correctness／bench signal を B の commit へ後付けで結合する射影は、規律 3 に反します。[CLAUDE.md:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/CLAUDE.md:73) recovery reason 自体の記録だけではこの欠落を補えません。

## 総括

- **blocker 候補あり（3 件）**: owner lease 不在、recovery authority 不在、attempt 非局所な correctness/perf signal。
- `wal.replay` の read-only 化と prospective validation は維持してよい。
- 現プランは採択せず、campaign-wide lease と attempt-local stage binding を先に設計へ追加することを勧告する。
- 外部 output root を含む M4 再監査と、不変条件 2 の文言修正も実装前に必要。
- 書き込み・pytest 実行はしておらず、以上は静的根拠のみ。