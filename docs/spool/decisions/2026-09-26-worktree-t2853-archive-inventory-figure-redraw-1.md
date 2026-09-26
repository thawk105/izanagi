---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: worktree-t2853-archive-inventory-figure-redraw
seq: 1
---

## {{D:trace-archive-r1-inputs}}. 標準評価経路の trace 保全口の inventory に R1 の入力一式を D2160・B-8 の runner と同じ名前で足し、build 時の source evidence と照合できた記録だけを complete にする

**決定:** D2233 の opt-in 保全口 (env `IZANAGI_TRACE_ARCHIVE_ROOT`) が書く `inventory.json` に、保存 trace を後で verifier に掛け直す (R1) ための入力を足した (記録 `output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`)。

1. key は D2160・B-8 の runner v5 と同じ名前にする: `verifier_argv` (同じ trace を CLI で再判定する等価 argv。標準経路の判定は in-process なので `verifier_invocation: "in-process"` を並べる。commit witness の無い反復は null)、`repo_head`、`ccbench_pin`、`patch_sha256`、`verifier_module_sha256`。
2. patch は CCBench の source root の `git diff --binary HEAD --` の bytes を archive 内 (`patch/ccbench.diff.zst`) に保全し、sha256・長さ・path を記録する。build 時に束縛した `SourceEvidence.tracked_diff_sha256` も並べる。
3. 保全時に source root の HEAD が宣言 pin で始まること (build 側 `buildcache._verify_ccbench_commit` と同じ前方一致) と、patch の sha256 が `tracked_diff_sha256` と一致することを照合し、どちらか違えば inventory を `failed` にする。`ccbench_pin` は解決済みの完全 SHA、宣言値は `ccbench_pin_declared`。標準評価経路の反復は常に evidence を渡すので、その経路の `complete` は「build 時と同じ pin + patch」を意味する。evidence の無い直接呼出しでは source 系の項目を null にしたまま `complete` になり、この意味を持たない。
4. 照合と取得はすべて保全の内側に置く。env 未設定なら git・hash・zstd を呼ばず、保全の失敗 (照合の不一致を含む) は原本を残し評価結果・verdict・例外・WAL・受領証を置き換えない (D2233 項 4 のまま)。
5. git の起動は 1 helper (`pipeline._archive_git`、固定 argv、CCBench を実行しない) に寄せ、review 済み起動箇所の登録簿へ登録する。

**理由:**
- 同じ名前の組にすると、写し稿 (`output/insights/2026-09-23/t2853-repro-package-archive/README.md` §5.2) の R1 手順が D2160・B-8 と標準経路で共通になる。
- 標準経路の patch は template と穴埋めの合成で repo の file として残らないので、sha256 だけでは R1 の source を組めない。bytes を保全する。
- 保全は検証の後に生きた checkout から取るので、build 時の source と違いうる。照合しないと inventory が正常を名乗ったまま別の source を R1 に渡す (段 6 のレビュー 2 本が独立に指摘)。段 4 の「一致を gate にしない (記録だけ)」を撤回したが、照合は保全の status だけに効き、評価の受理集合は変えない。
- 現行 pin は 7 桁 (`pin.CURRENT_PIN`) で build 側は前方一致なので、完全一致の照合は本番で恒常的に failed を生む (F601 の再発として記録)。

**却下した選択肢:**
- sha256 だけを記録し patch の bytes を残さない — R1 の source を組めない。
- 照合を行わず、`patch_sha256` と `tracked_diff_sha256` の並記だけにする — inventory の `complete` が「build 時と同じ source」を意味しなくなる。
- pin の完全一致 — 現行 pin では全件 failed。
- verifier の in-process 呼出しを CLI の subprocess に変えて argv を実在させる — 判定経路を変え、D2233 項 4 と規律 2 の境界に触れる。
- verify fan-out の remote 反復と job body の opt-in 配線まで広げる — 依頼の外 (本題だけ、D320)。
