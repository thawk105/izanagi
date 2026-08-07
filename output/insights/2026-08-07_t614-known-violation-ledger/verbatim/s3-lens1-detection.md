## 所見

### 1. 既定監査の revision 列挙には、履歴形状依存の盲点がある

- **判定:** `real`
- **根拠:** 既定範囲は `git rev-list --ancestry-path policy..HEAD` である。[tools/check_ai_provenance.py:706-713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:706) 親 brief は、現時点で素の `rev-list` と件数が一致したことだけから「列挙に穴は無い」と一般化している。[brief.md:18-20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:18)
- policy 導入前の commit から branch を切り、そこで違反 commit `X` を作り、policy 導入後の main に merge すると、`X` は `HEAD` の祖先だが policy の子孫ではない。素の `policy..HEAD` には入る一方、`--ancestry-path` からは落ちる。ancestry bitset は選択済み commit しか監査しないため、この欠落を回収しない。[tools/check_ai_provenance.py:857-870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:857)
- plan が流用する worker/ancestry 等価テストは、既に選ばれた list を直接 `_audit_history()` に渡しており、`_commit_range(None)` を検査しない。[plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:92)、[test_check_ai_provenance.py:3883-3904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:3883)
- **成果物または受理集合への影響:** 台帳分類より前に新規違反が列挙から消える。既知違反を除外して rc=0 にできても、pre-policy fork から流入した新規違反を受理するため、監査の受理集合が意図せず拡大する。
- **推奨対処:** 既定範囲を原則 `[policy, *rev-list --reverse policy..HEAD]` とし、pre-policy fork・post-policy violation・後日 merge の synthetic default-range テストを追加する。別の legacy 境界が必要なら、`--ancestry-path` を残すのではなく明示的に裁定する。

### 2. P1 は機構の単体動作を示せても、repo の gate を復旧しない

- **判定:** `real`
- **根拠:** 実測は既知候補 6 件に加えて `3f2c43d7…` が新規違反で、合計 7 件である。[brief.md:17-20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:17) P1 とテスト計画はこの 7 件目を意図的に新規のまま残し、既定監査を rc=1 に固定する。[brief.md:31-34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:31)、[plan.md:88-90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:88)、[plan.md:127](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:127)
- DW-O17 は full-history が赤なら停止すると定める。[docs/dev-wave/operations.md:89-96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/dev-wave/operations.md:89) 自動 dev-wave も provenance を既定 check に含め、非零を失敗にする。[tools/dev_waves/cli.py:188-195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_waves/cli.py:188)、[tools/dev_waves/checker.py:317-348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_waves/checker.py:317)
- **成果物または受理集合への影響:** operational gate は従来どおり常時赤で、8 件目が 7 件目に紛れる。range 単体で「既知のみ rc=0」を示しても、repo の通常列では新旧分離が利用されない。
- **推奨対処:** landing 前に `3f2c43d7…` の扱いをユーザーへ再裁定する。台帳へ入れる論拠は「既に共有済みで rewrite 不能、かつ常時赤を解消するという同じ incident 条件を満たす」こと。一方、元裁定は 6 件なので無断追加は不可である。追加、別の承認済み correction、または他の解消策のいずれかで、既定監査が「既知 N・新規 0・rc=0」になることを受入条件にすべきである。

### 3. finding と kind の平行 tuple は、照合不変条件を fail-closed にしていない

- **判定:** `real`
- **根拠:** plan は `normal_findings` と「同順」の `normal_finding_kinds` を別 tuple とするが、長さ一致、非台帳対象 finding の sentinel、ずれた場合の失敗方法を定めていない。[plan.md:16-23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:16) 現コードは base、scope、CAB、waiver、implementation の複数発生源を順次連結する。[tools/check_ai_provenance.py:816-838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:816)
- 提案テストは同種 finding の重複を扱うが、期待種別 1 件と別種 finding が同じ commit に共存するケースや、tuple cardinality 不一致を扱わない。[plan.md:68-75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:68)
- また、短縮 SHA entry は registry 不正として rc=2 にする契約と、単に「既知扱いされない」とするテスト記述が曖昧に競合する。[plan.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:14)、[plan.md:68-70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:68) module 上部で validation すると、現在の `RuntimeError` 捕捉範囲より前に例外が出る点も未指定である。[tools/check_ai_provenance.py:1790-1830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1790)
- **成果物または受理集合への影響:** `zip()` 等による実装では、kind のない末尾 finding が黙って落ち、新規違反を rc から消せる。
- **推奨対処:** 平行 tuple ではなく `Finding(text, ledger_kind: Kind | None)` の単一構造にする。内部不変条件違反と不正 registry は history 分岐の `try` 内で必ず rc=2。期待 finding＋異種 finding、cardinality 破壊、短縮 registry entry の rc=2 を別々に固定する。

### 4. SHA 以外の一致や「同じ commit の全 finding 吸収」は、plan 上は成立しない

- **判定:** `refuted（plan レベル。実装は未検証）`
- **根拠:** brief は full 40-hex SHA と期待 finding 種別の両方を要求する。[brief.md:22-26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:22) plan は full SHA の dict equality、entry 当たり 1 finding だけの移動、別種・別 SHA・短縮 SHA の非抑止を明記する。[plan.md:25-32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:25)
- **成果物または受理集合への影響:** このアルゴリズムをそのまま実装する限り、同じ subject/path/message や finding 文字列の前方一致で新規違反が吸収される経路はない。ただし所見 3 のデータ構造ずれは別問題である。
- **推奨対処:** 同一 subject/path の別 SHA、期待 finding＋異種 finding の negative testを追加し、文字列解析による kind 推測がないことを実装レビューで確認する。

### 5. 現在の固定 6 件では correction・waiver による二重抑止は成立しない

- **判定:** `refuted`
- **根拠:** correction target は固定 `6b64d217…` で、6 件の台帳案には含まれない。[tools/check_ai_provenance.py:127-129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:127)、[plan.md:5-14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:5) correction は target の exact missing finding だけを相殺し、他を残す。[tools/check_ai_provenance.py:900-953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:900)
- plan は correction 判定後に台帳分離し、correction finding 自体は常に新規側とする。[plan.md:25-32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:25) carrier の通常 green 判定も台帳抑止より前なので、台帳で carrier を rehabilitate できない。
- `--message-file` と merge preflight は history 分岐と分離されており、plan も台帳を history のみに限定する。[tools/check_ai_provenance.py:1795-1827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1795)、[plan.md:34-36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:34) waiver も有効時には implementation finding 自体を発生させないため、台帳一致と二重には効かない。[tools/check_ai_provenance.py:833-838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:833)
- **成果物または受理集合への影響:** 固定 6 件の範囲では correction／waiver と台帳が同じ finding を二重に消して rc=0 にする経路はない。
- **推奨対処:** 既存 correction テストを「変更しない」だけでなく、synthetic registry と correction target を意図的に重ね、target missing だけが correction、stale／他 finding が新規に残る composition test を追加する。

### 6. stale と部分 range の rc 条件は、plan 上は両立している

- **判定:** `refuted`
- **根拠:** selected set 内で correction 後の実効 finding が 0 なら stale を新規 finding にし、期待種別と違う finding はそのまま新規に残す。範囲外 entry は stale にしない。[plan.md:27-32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:27) selected-clean と outside-range の両テストも予定されている。[plan.md:76-82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:76)
- **成果物または受理集合への影響:** selected entry の期待 finding が消えれば、他 finding があればそれ自体で赤、何もなければ stale で赤となる。6 件を含まない部分 range は stale で誤って赤にならない。
- **推奨対処:** `_audit_history()` 単体だけでなく、`main --range` で selected-stale rc=1／outside-range rc=0 を固定する。

### 7. exact pin テストは「ユーザー裁定の強制」にはならない

- **判定:** `real`
- **根拠:** brief は台帳追加に pin テスト編集とユーザー裁定が必要だと主張する。[brief.md:27-29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:27) しかし planned pin は production tuple と同じ repository 内の literal expected tupleで、同じ実装担当が checker と test を所有する。[plan.md:60-66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:60)、[plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:129)
- 1 件追加するには production tuple、literal expected、実 commit 件数を変更すればよく、`3f2c…` なら専用 negative testも変更するだけである。[plan.md:64-66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:64)、[plan.md:88-90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:88) `PR-A02` は機構の一般契約だけを記録する計画で、entry ごとの裁定 ID を要求しない。[plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:38)
- **成果物または受理集合への影響:** production と期待値を同じ patch で更新すれば全 planned test を通せる。これは片側の偶発 drift を見つける review tripwire ではあるが、受理集合拡大の権限確認ではない。
- **推奨対処:** `KnownViolationSpec` に incident／ruling ID を必須化し、別の承認台帳との exact 対応を検査する。機械的な人間承認強制がないなら、「pin が裁定を強制する」とは記述せず、protected review／CODEOWNERS 等の外部 gate を明示する。

### 8. 既知 SHA の公開は、自動 dev-wave 層では沈黙する

- **判定:** `real`
- **根拠:** checker 内では既知 SHA と件数を stdout に出す計画だが、予定テストは rc=0 経路だけである。[plan.md:34-36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:34)、[plan.md:84-86](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:84) 現在の既定走行は P1 により rc=1なので、既知＋新規の赤経路で公開されることはテストされない。
- 自動 dev-wave は provenance check を起動するが、stdout/stderr を両方 `DEVNULL` に捨て、非零か否かだけを保持する。[tools/dev_waves/cli.py:188-195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_waves/cli.py:188)、[tools/dev_waves/checker.py:317-348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_waves/checker.py:317) task-run 台帳にも exit status しか記録されない。[tools/task_run_check.py:28-47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/task_run_check.py:28)
- **成果物または受理集合への影響:** 自動検査が rc=0 を受理しても、どの例外を何件消費したかが receipt に残らない。「公開が抑止」という契約がこの層では成立しない。
- **推奨対処:** 既知＋新規の rc=1 でも stdout に既知一覧、stderr に新規だけが出る exact testを追加する。自動層では bounded structured result または task-run event に既知 SHA／件数を保存する。これを scope 外にするなら「常に公開」の射程を direct CLI に限定して明記する。

### 9. gate 層のうち、land 本体は full-history を消費していない

- **判定:** `real（scope 外所見）`
- **根拠:** 各層の実態は次のとおり。

| 層 | 実際の消費 | plan の被覆 |
|---|---|---|
| 手動 post-commit | CLAUDE/AGENTS/DW-O17 が既定 full-history の rc と端末出力を読む。[CLAUDE.md:120-123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/CLAUDE.md:120)、[AGENTS.md:26-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/AGENTS.md:26) | checker の rc 変更は届くが、所見 1・2の影響を受ける |
| message-file／merge preflight | checker の別分岐。fold land もこれだけを呼ぶ。[tools/dev_wave_land.py:1387-1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_wave_land.py:1387) | 意図どおり台帳対象外 |
| 自動 dev-wave verification | full-history rc を消費するが出力は破棄 | rc は被覆、公開は未被覆 |
| Pegasus dispatch | child rc を返し、stdout/stderr を元 stream へ中継する。[tools/pegasus/dispatch_compute.py:1766-1773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:1766) | transport として被覆 |
| Bash hook | sanctioned な起動経路・site だけを判定し、監査結果は消費しない。[hooks/guard_bash.py:307-321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/hooks/guard_bash.py:307) | 受理 gate ではない |
| `dev_wave_land.py` の post-land | full-history 呼出し自体がない。insight も land は message preflight のみと認定している。[README.md:73-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/output/insights/2026-08-07_red-test-audit/README.md:73) | brief の A/B scope 外 |

- **成果物または受理集合への影響:** land の受理集合は変更されない。手動 full-history が省略されれば、新しい違反を main へ入れる経路は残り、台帳実装だけでは閉じない。
- **推奨対処:** 本 wave で広げないなら明示的な残余リスクとして裁定へ返す。閉じるなら、land transaction 内または ref 更新前の隔離 checkout で authoritative full-history を必須化する別 scope が必要である。

## 総括

現 plan はこのままでは **NO-GO**。最重大なのは `--ancestry-path` による将来の列挙漏れと、P1 が既定 gate を赤のまま残す点である。  
固定 6 件について、SHA exact・1 finding限定・correction／waiver・部分 range／stale の rc 攻撃は plan 上は反証できた。  
一方、finding-kind の平行 tuple、ユーザー裁定を強制しない pin、自動層での出力破棄は未閉鎖である。  
land の full-history 非強制は本変更の scope 外だが、「全 gate 層を覆った」とは評価できない。  
read-only の静的検査のみで、pytest は実行しておらず緑は主張しない。