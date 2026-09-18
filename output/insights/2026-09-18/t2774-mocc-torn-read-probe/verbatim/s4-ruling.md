# 段 4 裁定 — [T-2774] (2026-09-18 07:10 JST、親)

前置き: 対象は DB 研究ベンチマーク CCBench の並行性制御 MOCC の直列化可能性検査 (非直列化可能な実行の再現と原因究明)。

## 所見の裁定 (real / refuted、採否、scope)

| 所見 | 判定 | 採否 | 根拠 (親の実測) |
|---|---|---|---|
| A-MF1 現行 verifier は mocc で X/P `evidence-present` を integrity clean の条件にする。素の e9e477ca は全走 `indeterminate`、discriminator も `indeterminate` | **real** | 採用 (設計変更) | `orchestrator/verifier/model.py:77〜82, 450〜467` (`certification_gate_satisfied`)、`core.py:53〜59`。導入 commit `e4c949f08` (2026-09-03)。T-1943 job (08-28) はこれより前。emitter は `patches/instr-mocc-lock-coverage.patch` (D1686、TRACE 専用、D1687 で TRACE=0 同一性) にしか無い。P 行は違反時のみ発火 (patch 25〜45 行) → stock は silent で discriminator の C/R/W/E parser と両立 |
| A-MF2 「supported ⇔ (ii) のみ / contradicted ⇔ (i) も」「どちらも実装由来」は不成立 | real | 採用 | plan §2 の限定表 (discriminator `:284〜298, 575〜592, 648〜653`) を insight の対応表にそのまま使う。分岐 2/3 を排除しない |
| A-MF3 / B-M4 「診断 0/K ⇒ 必要性 ⇒ 根因」は撤回 | real | 採用 | 結論文の上限 = 「名指し条件で診断 build が未再現 / 検出率差を観測。寄与の分離・必要性・根因は確定しない」。0/24 の片側 95% 上限 0.117、Fisher の検出力 K=24 で 14.9% |
| A-S1 P1 の成立条件を明文化 (cold・RLL 空・別 key・W が y を R 施錠前に検査…、tid 差 1 は帰結であって必然でない) | real | 採用 | insight §順序論証に被覆境界表を置く |
| A-S2 (i) の発生と commit を分ける | real | 採用 | insight に明記 |
| A-S3 診断 patch = validation 再読 + cold 側 abort (retry でない)、保証は attempt 単位 | real | 採用 | 「abort のみ増加、commit 総数の単調減少は主張しない」 |
| A-N1〜N3 | real | 採用 (記述) | — |
| B-M1 T-1943 mode は verifier rc 0/1 を許容し G2 でも job-result.json | real | 採用 (記述訂正) | pilot `:2238〜2291`。腕 A 自体は本裁定で撤回 (下記) |
| B-M2 生死確認の成功条件は最終化まで | real | 採用 (runner に読み替え) | runner の compute smoke (`--pairs 1`) は集計 JSON 出力・退避まで到達で緑 |
| B-M3 verifier timeout 300 s 明示、走ごとの逐次保存、walltime 02:30:00 | real | 採用 | 4 node × 11 組で最悪 22 × 303 s ≈ 111 分 + build |
| B-M5 verifier の G2 検出集計と discriminator の識別成功率を分離、「未実行 / 入力拒否」列 | real | 採用 | runner の集計 JSON schema に反映 |
| B-S1 base_dir は worktree の submodule repo (`.git/worktrees/<wave>/modules/external/ccbench`) を第一候補、実行時解決を記録 | real | 採用 | login で両 path から e9e477ca 解決可 (親も実測済み) |
| B-S2 単独性・selftest の具体例 | real | 採用 | selftest に 7 例 + `_assert_single_tenant` 相当 |
| B-N1 1493 行の compiler gate も素の python3 で repo import | real | 記述訂正 | 4936 は通過。一括置換しない |
| B-N2/N3 | real | 記述 | — |

## 設計の確定 (plan v2 からの変更点)

1. **producer = e9e477ca + `patches/instr-mocc-lock-coverage.patch` (repo、D1686) を両 arm に適用する。** A-MF1 による。CC 論理は stock のまま (patch は `#if TRACE` 内の X/P 計装 + `#line` だけ)。binding には source_oid = e9e477ca と patch の sha256 を併記し、「stock mocc (RWLOCK 版) + 現行 certified 計装」と書く。
2. **腕 A (既存 pilot 経路) は撤回する。** pilot は X/P patch を当てないので 09-03 以降 mocc を certified にできず、加えて hydrate 段 (T-548 回帰) で落ちる。両欠陥は記録 (failures fragment 1 本 = hydrate 回帰、次の一手 T = pilot の `--t1943-g2-discriminator` mode 復旧: X/P patch 適用 + hydrate interpreter gate、設計は plan v2 §4 逐語)。**scope 0 (repo の job script 修正) は本 wave では実装しない** — 本題の成果物に不要になり、hydrate だけ直しても pilot の目的 (certified 判定) は回復しない。→ repo の実装面差分 0 → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。
3. **単一計器 = job dir の runner `t2774_probe.py` (Codex author、unit 2 のみ)。** T-2294 driver (`orchestrator/campaign/s3_mocc_lock_coverage.py`) の helper (`_load_policy` / `_resolve_toolchain` / `_prepare_dependencies` / `_common_configure_args` / `_build_variant(macro=None)` / `_run_trace` 相当 / `_verify`) を import して使う。arm = `instr` (e9e477ca + X/P patch) と `diag` (同 + 診断 patch)。両 arm を同一 node で交互 (AB/BA 交替)。各走: witness env (`IZANAGI_MOCC_G2_WITNESS=1`、`IZANAGI_MOCC_G2_WITNESS_DIR`) + `IZANAGI_TRACE_DIR` を走ごとの別 dir → verifier (`-m orchestrator.verifier <trace_dir> --json --protocol mocc --ccbench-root <その arm の source>`、timeout 300 s) → `total_cycles > 0` の走は manifest 2 種 (pilot 2085〜2160 と同 schema) を作り discriminator CLI を当てる (両 arm。diag arm の結論は観測のみと label) → 走ごとに JSON を逐次保存 → 最後に集計 JSON。
4. **標本: 4 compute job (node) × 11 組 = instr 44 / diag 44。** 各 job walltime `02:30:00`、`--queue-wait-timeout 3600 --overall-grace 4200`。これは探索的対照の予算であり、結果を見て延長しない。instr 44 は旧腕 A の N=42 の役も兼ねる (P(≥1 G2) ≈ 0.996 @ 0.119)。
5. **診断 patch** = validation の counter 検査後に版を再読し不一致なら abort (`M:1036` 後) + cold 読みの body 読み後に counter が W_LOCKED なら abort (`M:348` 後、retry でない)。X/P patch 適用後の source に対して作る (`git apply --check` を親が login で実測)。`#if TRACE` 行・stamp・emission を変えない。
6. **仮説 cell は追加しない** (plan §7、B-N3)。value size の向きは未実測と記す。
7. **集計 (B-M5)**: 走ごとに {job, node, ordinal, arm, rc, verdict, certified, total_cycles, integrity clean, elapsed run/verify, discriminator: {conclusion | 未実行 | 入力拒否, blockers, comparisons}}。集計 = arm ごとの N・m (判定可能)・k (G2)・欠測・k/m と Clopper-Pearson 両側 95%、discriminator 結論の件数。
8. **主張上限 (A-MF2/MF3、B-M4)**: 「固定 cell で instr は k/m、diag は k'/m'。G2 走の discriminator は supported x / contradicted y / indeterminate z。validation の別読みによる静的候補 (a) とは整合 / 不整合。実行順序の直接観測ではなく、寄与の分離・必要性・根因は確定しない。」
9. **記録**: insight `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` (+ verbatim)、worklog fragment 1、failures fragment 1 (hydrate 回帰、最小記述)、decisions fragment 0。
10. **順序**: unit 2 author → 親が probe を job dir へ退避 + login で `--selftest` と patch `--check` → compute smoke (`--pairs 1`、1 node) → 4 node 投入 → 集計 → 段 6 review 2 本 (runner と結果の両方を対象、実走 log を射影) → 段 7。

## 追記 (07:46 JST、本走の結果を見る前に確定)
- smoke (`5065.nqsv`、bnode003、80 秒で完走、両 arm serializable、verify 17〜19 秒) の所要だけを根拠に、標本を **4 node × 14 組 = instr 56 / diag 56** へ引き上げる (レンズ B M4 の「率差の 80% 検出力なら各 arm K=56」に一致)。walltime 02:30:00 は据え置き。これ以降、結果を見ての増減はしない。
- 投入元 worktree: B1 = wave worktree、B2 = unit2 worktree、B3 / B4 = detached worktree (`.codex/worktrees/t2774-node3` / `node4`)。同一 worktree からの並行 dispatch は orphan hold で rc=16 (DW-O26) のため。

## 追記 2 (08:03 JST、Q1 の 3 block (B1/B2/B4 = instr 0/42、diag 0/42、smoke 0/1) を見た後、Q2 の走行前に登録)
- **Q1 (B1〜B4) の build は `BACK_OFF=1`** (T-2294 driver の `_common_configure_args` を流用した runner の実装。親の author prompt「T-1943 と同じ argv」が守られず、親も segment 5/6 で見落とした)。T-1892 / T-1943 の pilot は `BACK_OFF=0` (他の define は CCBench 既定と同値)。Q1 は「適応 backoff あり」の条件の観測として保持し、主解析にしない。
- **Q2 (主解析、事前登録)**: fix 2b で runner の configure を pilot と一致させ (`BACK_OFF=0` ほか)、5 arm を因子 1 つずつの鎖で走らせる (`probe/arms-q2.json`): `p058-plain` (058d0c4e = T-1892 の producer、witness code なし) → `e9-plain-nowit` (e9e477ca、patch なし、witness env off) → `e9-instr-nowit` (+X/P 計装) → `e9-instr-wit` (+witness on = discriminator 条件) → `e9-diag-wit` (+診断 patch、observational_only)。4 node × 10 round × 5 arm = **各 arm 40 走**。walltime 02:30:00。結果を見ての増減はしない。
- 問い: Q2-a = `p058-plain` で T-1892 の 5/42 (CI [0.040, 0.256]) と整合する率が出るか (環境の同等性)。Q2-b = witness on/off・X/P の有無で率が変わるか (計器が race を抑える観測者効果の検査、静的根拠 = S 行の書出しが publish (1195) と unlockCLL (1207) の間に入る)。Q2-c = `e9-instr-wit` の G2 走の discriminator 結論 (本題)。Q2-d = `e9-diag-wit` 対 `e9-instr-wit` (対照)。
- 主張上限は変えない (段 4 裁定 8)。率の比較は Fisher 片側を参考値として併記し、有意差を根因確定に昇格しない。

## 変異事前登録 (DW-M01)
repo の実装面差分 0 → 免除。probe は job dir、段 4 の変異登録から外す (memory `compute-probe-stays-out-of-repo`)。probe の fail-closed 挙動は `--selftest` で親が login 実走。

## 親 brief の訂正
- P1 「⇔」→ 限定表。P2 は「未実測」。P3 の K/node 配分 → 4 node × 11 組、walltime 02:30:00。
- 「supported/contradicted はどちらも実装由来」→ 撤回。
- 実行 argv の綴り → pilot 1974〜1980。
- 「T-548 後は compute 未実走」→ 「4936 で hydrate まで到達し失敗、後段は未到達」。
