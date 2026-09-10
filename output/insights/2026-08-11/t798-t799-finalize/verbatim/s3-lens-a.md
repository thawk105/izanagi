## 総括

**P5 は原案のままでは受理不可**です。ただし、緩めない場合の復旧不能も real です。

- 緩めない場合: `git commit` 成功直後、`mark_fold_committed()` 前に死ぬと、`phase=applied`・main=`fold child` が残り、plan の旧受理表では land/CLI とも復旧不能になります。
- 緩める場合: phase 以外の「観測可能な事実」がまだ不足しています。現状案では、手動 commit、異なる audit cutoff、未束縛の file mode、standalone 由来 state を fold commit として受理できます。

したがって、**「phase は権威にしない」という原則は採用しつつ、P5 の事実集合を強化する**のが妥当です。最低でも exact commit tree/mode、commit metadata、audit cutoff、audited closure、land-origin を束縛する必要があります。

書込み・pytest・checker 実走は一切行っていません。以下は静的検査結果です。

## state 存在時の予定受理集合

`H = origin.tested_tip`、`C = H を唯一の親とする fold commit` とします。

| state / tree | `_discover` / `check_docs` | land |
|---|---:|---:|
| `applied`, main=`H`, target before/after 混在、GC 全 present | 拒否 | resume |
| `applied`, main=`H`, target 全 after、GC present/missing 混在 | 拒否 | GC を収束 |
| `applied`, main=`H`, target 全 after、GC 全 missing | 受理 | commit へ |
| `committed`, main=`C`, complete | 受理 | postcondition + finalize |
| **P5: `applied`, main=`C`, complete** | **新たに受理** | **phase repair/finalize** |
| target 第三 bytes、before target + missing GC、rotation collision | 拒否 | 拒否 |
| state/target/GC が symlink・directory、v1、field 欠落・余分・型違い | 契約上は拒否 | 拒否 |
| fragment 再出現・新 fragment | closure 検査時点では拒否 | 拒否 |

部分適用・GC 途中・rotation 途中の content-addressed な収束自体には、静的に明白な受理拡大は見つかりませんでした。穴は commit identity、mode、validator の利用文脈、最終検査後の再出現にあります。

## 所見

### A-01 — P5 は path-shaped な手動 commit を fold commit として受理する

- **判定:** real
- **根拠:** state target は存在と bytes hash しか持たず、mode を束縛しません。[s2b-plan.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:42)、[s2b-plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:101)。`verify_declared_fold_commit()` の拡張は明示的に scope 外です。[s2b-plan.md:480](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:480)。現行 target 検査も regular-file と bytes hash だけです。[tools/spool_fold.py:2300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2300)。
- **再現状態:** 正規の `phase=applied` state が complete になった時点で、`docs/worklog.md` を `chmod +x` し、全 target を任意 author/message で手動 commit します。main は clean、親は `H`、bytes は全 after、GC は missing、closure/transaction ID は不変です。SIGKILL 等で phase を `applied` のまま残すと、P5 の全条件を通ります。
- **成果物影響:** 未計画の mode と正規 fold provenance を持たない commit `C` が certified fold の参照として採用されます。

P5 には `C^{tree}` の expected tree OID、exact diff path/mode、fold author/message/trailer の照合が必要です。

### A-02 — recovery request の audit cutoff と audited closure が state に束縛されない

- **判定:** real
- **根拠:** origin/transaction payload に `trusted_main_cutoff_sha` と audited commit 列がありません。[s2b-plan.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:20)、[s2b-plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:76)。active recovery は外部 provenance audit を skip する予定です。[s2b-plan.md:319](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:319)。一方、fold 検査へ渡す cutoff は再投入 request の `tested_main` です。[tools/dev_wave_land.py:2251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2251)。
- **再現状態:** 履歴を `B0 -> B1 -> H` とします。`tested_main=B0` の request で state を作り、commit `C` 後に crash。次に同じ `H`/wave ref だが `tested_main=B1`、audited 列も `B1..H` だけの request で resume します。stored base は「H の ancestor」なので通り、P5 は `C` を finalize できます。
- **成果物影響:** certified 選択の fold が、state 作成時とは異なる trusted cutoff／provenance closure の下で受理されます。

`locked_main` とは別に、元 request の `trusted_main_cutoff_sha` と ordered audited-list digest を transaction ID と receipt に束縛すべきです。

### A-03 — `origin.kind="land"` は観測値でなく public caller の申告値

- **判定:** real（library API の受理集合）
- **根拠:** `plan_fold(..., origin=...)` は caller 提供 object を受け、land origin の `base` は「存在する ancestor」であることしか確認できません。[s2b-plan.md:218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:218)、[s2b-plan.md:226](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:226)。`plan_fold` は main lock を観測できないのに、brief は「申告値でなく観測値」としています。[s1-brief.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s1-brief.md:68)。
- **再現状態:** 通常 Python caller が、wave repo の実 HEAD/ref に合う `tested_tip`/`wave_ref` と、任意の古い ancestor `B_old` を使い、`FoldOrigin(kind="land", base=B_old, rollback_ref=B_old, ...)` を渡します。Git 検査を通った state bytes は正当に `"kind":"land"` を持ちますが、land lock は一度も取得されていません。
- **成果物影響:** receipt と state が偽の land 起源/base を durable fact として記録し、誤った main 帰属を proof chain に残します。

`kind=land` を通常データとして公開せず、lock-held な land 専用入口が main と wave の両方を直接観測する必要があります。

### A-04 — closure は rendering engine の bytes を束縛していない

- **判定:** real
- **根拠:** closure 列挙は docs、fragment、rotate-limit の値だけです。[s2b-plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:129)。しかし採番はコード定数・regex・helper に依存します。[tools/spool_fold.py:1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1137)、[tools/spool_fold.py:1316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1316)。land も tested wave の OID からではなく、実行中 checkout 隣の `spool_fold.py` を import します。[tools/dev_wave_land.py:1628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1628)。fresh apply の Git clean 検査は target paths のみです。[tools/spool_fold.py:2258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2258)。
- **再現状態:** HEAD=`H` のまま、uncommitted `tools/spool_fold.py` の `_max_task_number()` を `max(...) - 1` に変更します。standalone で plan/apply し、重複 T を含む complete `applied` state を作った後、tool bytes を `H` の版へ戻します。HEAD/ref、全 docs closure、state ID は一致し、land recovery が古い renderer の output を commit できます。
- **成果物影響:** certified ledger に現行 engine なら生成しない T/D/F 値が入り、既知の archive 跨ぎ重複なら checker も止めません。

少なくとも fold engine digest、parser/rendering protocol version、実行した `check_docs.py` digest を束縛するか、実行 checkout が記録 OID と完全 clean であることを強制すべきです。

### A-05 — legacy receipt の受理には cutover 境界がなく、新 field が永続的に fail-open

- **判定:** real
- **根拠:** parser は旧 exact set と新 exact set を時期に関係なく受理する計画です。[s2b-plan.md:200](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:200)。現行 parser/validator は receipt の行自体しか見ません。[tools/spool_fold.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1330)、[tools/spool_fold.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:968)。
- **再現 bytes:** cutover 後の `FOLDED.md` 末尾へ次を置きます。

```text
- {"allocations":{},"authored":"2026-08-11","content_sha256":"0000000000000000000000000000000000000000000000000000000000000000","seq":1,"wave":"dev-wave-t798-t799-finalize"}
```

旧 exact set なので、`base`、`tested_tip`、`wave_ref` が全欠落でも受理されます。

- **成果物影響:** post-cutover の fold receipt が origin 三値なしで正式 receipt 集合へ入り、台帳から main/wave 帰属を復元できません。

schema version と authenticated cutover marker、または旧 receipt を許す固定 prefix/hash が必要です。

### A-06 — 新 receipt の「観測 OID」も durable validator では単なる形式値

- **判定:** real
- **根拠:** `_receipt_records(text)` は repo を受け取らず、Git object/ref を観測できません。[tools/spool_fold.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1330)。plan も receipt parser には OID/ref の形式検査しか指定していません。[s2b-plan.md:202](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:202)。
- **再現 bytes:** 実在する新 receipt の三 field だけを次へ交換します。

```json
"base":"0000000000000000000000000000000000000000",
"tested_tip":"1111111111111111111111111111111111111111",
"wave_ref":"refs/heads/does-not-exist"
```

他 field を維持すれば exact schema と文字形は通ります。

- **成果物影響:** FOLDED receipt が存在しない base/tip/ref を proof-chain 参照として保持しても、`validate_spool_tree` は拒否できません。

生成時検査だけを保証するなら「receipt の durable 再検証」と表現を分けるべきです。証拠として扱うなら parser に repo/object relation 検査が要ります。

### A-07 — standalone complete state を一般 `check_docs` が健康形として受理する

- **判定:** real
- **根拠:** `accept_complete_active=True` を使う唯一の公開入口が `validate_spool_tree()` とされています。[s2b-plan.md:179](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:179)。同時に standalone は finalize せず state を残します。[s2b-plan.md:267](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:267)、[s1-brief.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s1-brief.md:54)。現行 `validate_spool_tree` は `_discover` の issue だけを返します。[tools/spool_fold.py:1041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1041)。
- **再現状態:** clean main `H` で standalone apply を完遂します。canonical は after、fragment は missing、state は exact v2 `phase=applied`、HEAD は `H` のままで fold commit はありません。この状態は予定表の complete-applied 条件を満たし、spool validator の issue 集合から消えます。check_docs 全体の rc は未実走です。
- **成果物影響:** proof chain に commit が無い canonical/report/receipt を、一般 docs gate が正規 tree として受理します。

land 内部だけの capability-bearing validation と、一般 `validate_spool_tree` を分離すべきです。

### A-08 — ordinary branch と standalone adoption では wave identity が束縛されない

- **判定:** real
- **根拠:** fragment `wave` と branch-derived identity の照合は `refs/heads/dev-wave/dw-` 以外で即 return します。[tools/dev_wave_land.py:1597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1597)。さらに standalone-origin recovery は stored main ref と land wave の tip だけを照合する計画です。[s2b-plan.md:321](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:321)。
- **再現状態:** main `H` 上で `wave: wave-a` の fragment を standalone apply し、origin を `wave_ref=refs/heads/main` とします。別の通常 branch `refs/heads/worktree-dev-wave-b` を同じ `H` に置き、その request で resume します。supervised check は no-op、tested tip は一致するため受理されます。P5 なら `H` の手動 child `C` から直接 finalize も可能です。
- **成果物影響:** receipt の `wave=wave-a`、origin の `wave_ref=refs/heads/main`、land result の wave-b が三分し、certified report の wave 帰属が非一意になります。

P5 の phase repair はまず `origin.kind=land` に限定し、standalone adoption は明示的な別 protocol にすべきです。

### A-09 — fragment GC の directory fsync がなく、reappearance が durable state を追い越す

- **判定:** real
- **根拠:** GC は `unlink()` だけで、fragment parent directory を fsync していません。[tools/spool_fold.py:2348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2348)。直後に fsync するのは Git admin 内の state parent だけです。[tools/spool_fold.py:2357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2357)。receipt replay 検査は `plan_fold` にあり、`validate_spool_tree` の `_discover` にはありません。[tools/spool_fold.py:1974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1974)。
- **再現状態:** fragment `F` を unlink、fold commit と state 削除を durable にした直後に電源断させ、fragment directory の unlink だけが未永続だった filesystem 状態を復旧します。state は absent、main は fold commit、`FOLDED.md` は F の receipt を持つ一方、同じ bytes の `F` が元 path に再出現します。
- **成果物影響:** docs gate は folded 済み fragment の再出現を受理し得ますが、次の plan は `receipt-replay` で停止し、台帳 fold が wedge します。

全 GC parent directory を fsync してから commit/phase 遷移へ進み、replay 検査も `validate_spool_tree` に入れる必要があります。

### A-10 — finalize の unlink→fsync 失敗は rollback に state を残せない

- **判定:** real
- **根拠:** `finalize_fold()` は state unlink 後に parent fsync します。[s2b-plan.md:267](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:267)。その例外は既存の広い fold catch から rollback へ入ります。[tools/dev_wave_land.py:1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1965)。一方 plan は rollback 不完全なら state を保持すると主張します。[s2b-plan.md:362](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:362)。
- **再現状態:** `phase=committed` の正常 state で、state `unlink()` は成功、直後の directory `fsync()` が `EIO`。既存 catch が rollback を開始し、ref CAS または path restore も失敗します。state 名は既に消えているため「観測 phase をそのまま残す」ことは不可能です。
- **成果物影響:** fold commit／canonical の rollback が不完全なのに journal が absent となり、元の T-798 型の復旧証拠喪失を再生成します。

`finalizing` tombstone への durable rename を挟むなど、unlink 後エラーを復旧可能な相として設計すべきです。

### A-11 — dangling state symlink は `_discover` だけ fail-open のまま残る恐れ

- **判定:** 疑い（現行 real、plan の契約では拒否予定だが実装指示・test が不足）
- **根拠:** 現行 `_discover` は `state_path.exists()` だけで分岐します。[tools/spool_fold.py:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:949)。dangling symlink は false です。一方 `load_active_plan` は `exists() or is_symlink()` 相当で拒否します。[tools/spool_fold.py:2248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2248)。plan のテスト表には dangling symlink の nodeid がありません。
- **再現状態:** Git admin の `izanagi-spool-fold-state.json` を存在しない target への symlink にし、spool 本体を正常 bytes にします。現行 validator は state 無しとして進み、land は invalid state として拒否します。
- **成果物影響:** check_docs と land の受理集合が分裂し、前者が壊れた transaction journal を見落とします。

実装時は outer predicate 自体を `exists() or is_symlink()` に変え、専用 test を追加すべきです。

## closure の実追跡

| helper | 実際に読む入力 | plan closure | 判定 |
|---|---|---|---|
| `_max_task_number` | worklog の rotation 後、phase deferred、全 archive | 全て含む | bytes 面は閉じる |
| `_extract_latest_active` / `_global_ordinal_entries` | worklog、archive、parser constants/regex | docs bytes のみ | engine semantics が欠落 |
| `_receipt_records` | `FOLDED.md` bytes、parser grammar | FOLDED bytes のみ | parser version が欠落 |
| `_rotate_worklog` | original/projected worklog、archive README、limit、derived archive path の存在 | docs/archive と limit を含む | bytes 面は概ね閉じる。mode/type は未束縛 |
| `_load_rotate_limit` | `tools/check_docs.py` を実際に `exec_module` し、その `WORKLOG_ROTATE_BYTES` | 戻り値だけ | module bytes/side effect が欠落 |

`_extract_latest_active` と `_global_ordinal_entries` の定義末尾は追加読取り上限のため未確認です。ただし両者は repo/path 引数を持たず、確認範囲では worklog/archive とコード grammar に依存しています。

## 恒真・自己比較の保証

- P5 で `phase ∈ {"applied","committed"}` を確認しても、strict `_state_plan()` が既に同じ domain 以外を拒否するため、その枝は発火しません。[s2b-plan.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:56)、[s2b-plan.md:237](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:237)。これは **nit** ですが、phase が commit identity を補強しないことの裏返しです。
- 現行 caller は同じ `fold_commit` を `fold_commit_sha` と `landed_main_sha` の両方へ渡します。[tools/dev_wave_land.py:1946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1946)。callee 内でこの二値を比べても caller から独立した保証にはなりません。成果物影響は A-01 と同じです。
- `test_receipt_v2_contains_observed_*` と `test_land_passes_exact_observed_origin_*` は、同じ `origin` object の伝播だけを確認すると、申告値を receipt へ正確にコピーする実装でも通ります。[s2b-plan.md:411](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:411)、[s2b-plan.md:414](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:414)。
- 既存テスト案 `test_applied_state_with_already_advanced_fold_child_is_rejected` は P5 と正面衝突します。[s2b-plan.md:422](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:422)。P5 採用時は「正規 crash state は受理」「manual/mode/audit mismatch commit は拒否」の二本へ置換が必要です。

## 層の取りこぼし

| 層 | 取りこぼし |
|---|---|
| standalone CLI | non-noop 成功後に terminal/finalize がなく、一般 validator は complete applied を受理する |
| land 新規 apply | origin の land 性が capability でなく申告値。engine code も closure 外 |
| land recovery | trusted cutoff/audited closure 未束縛。ordinary/standalone wave identity の adoption が広い |
| `check_docs` / `validate_spool_tree` | complete active、timeless legacy receipt、偽 OID receipt、dangling symlink、receipt replay の受理差 |
| rollback | unlink 後 fsync failure と rollback failureの組合せで state 保持不能 |
| GC durability | fragment directory fsync がなく、finalize 後の再出現が可能 |

[T-800]/[T-801] の rollback 細部は plan が明示的に scope 外としています。[s2b-plan.md:471](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s2b-plan.md:471)。scope 外であること自体は正直ですが、その状態で「単一 finalize protocol が rollback まで fail-closed」と一般化してはいけません。

## 親 brief 自身への反論

1. **「残骸は完全に健全」と「postcondition は一つも走っていない」は両立しません。** brief 自身が両方を書いています。[s1-brief.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s1-brief.md:32)、[s1-brief.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s1-brief.md:39)。言えるのは「その fixture では commit/tree が durable かつ clean」までであり、「certified に健全」ではありません。

2. **「現行の窓は commit で閉じている」は過剰一般化です。** watcher による単一注入点・一回の走行は、その schedule の存在を示すだけです。将来の `git commit → mark_fold_committed` 間を決定的に注入した測定ではなく、rotation、mode、別 audit request、GC directory durability、postcondition failure を覆っていません。

3. **archive 跨ぎ T 重複の測定は、有力な存在証明ですが普遍命題ではありません。** 実際に示したのは、その一行 bytes の T 重複が rc=0 だったことです。[s1-brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/s1-brief.md:41)。D/F、phase deferred、receipt identity、別配置の T 重複まで「下流で止まらない」と一般化できません。

4. **P5 を緩めない場合の運用詰みは real です。** commit `C` 成功後・phase 書換え前に死ぬと、state は `applied`、main は `C`。旧表は明示的に拒否し、standalone apply も HEAD=`H` 前提を満たさず、正規 phase repair 手段がありません。

結論として、P5 は次の条件付きなら採れます。

- `origin.kind=land` のみ自動 phase repair
- state に trusted cutoff と audited-list digest を追加
- commit の exact tree OID、mode、diff closure、author/message/trailerを照合
- GC parent fsync 完了を commit 相の条件にする
- standalone-origin は別の明示的 adoption/finalize protocolへ送る

この補強なしの P5 は、停止を解く代わりに certified commit の受理集合を実際に広げます。