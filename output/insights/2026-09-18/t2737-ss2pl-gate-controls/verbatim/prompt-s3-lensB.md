単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls

## レンズ B — 整合と実効性: 材料が裁定に足りるか、計算ノードで 1 job で取れるか

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s1-brief.md` — 親の段 1 brief (**親自身も検査対象**。P1〜P6 は攻撃対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s2-plan.md` — 段 2 plan (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/verbatim-d2120-item12.md` — ユーザー裁定の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/verbatim-t2644-s5.md` — 一次資料 (不整合 7 件)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/orchestrator/campaign/condition_meaning_gate.py` — gate。plan が名指しする範囲 + 1587-1632 (`_run_process`)、1670-1745 (configure)、1781-1812 (`_select_owner_entry`)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/tools/pegasus/run_ss2pl_lock_study.py` — runner。40-110、802-960、1061-1095、1334-1500、1928-2050、2091-2172
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/output/insights/2026-09-17/t2644-ss2pl-wfg-connect/verbatim/probe.md` — 前 wave の probe 逐語 (計算ノードで通った手順の現物)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/output/insights/2026-09-17/t2644-ss2pl-wfg-connect/verbatim/s6-fix-b2-facts.md` — 前 wave の実機事実 (path の `wfg` 偽陽性、gate の drift 拒否の逐語、所要)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/tools/pegasus/dispatch_compute.py` — generic dispatch。`--task generic` の env / cwd / stdout の置き場を `grep -n generic` で確認
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/patches/ss2pl-lock-protocol-study.patch` — 現行 patch (plan が名指しする範囲だけ)

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls`。上記以外も repo 内を読んでよい。**大きい file を全文 `cat` しない。** `grep -n` → `sed -n` で 200 行以内ずつ。

## この段の仕事

plan を守らせず検査する。次を攻撃する:

1. **cell matrix が裁定に足りるか。** ユーザー裁定 D2120 項 12 は「代表的な inert / 非 inert arm で gate 不変のまま必要な比較 (stock 側 target / owner TU の成立を含む) が成立すること」を示せと言う。plan の cell で (a) inert arm の stock 比較が「どの層の変更で」成立するかが一意に読めるか (patch だけ / 登録簿 target / companion)、(b) 非 inert arm の 4 軸それぞれの drift がどの patch 変更で閉じるかが 1 対 1 で読めるか (IMPL ← header 無条件化、WFG ← wfg.cc 無条件化、DLR ← marker 固定、KIND ← 既に green)、(c) (iii) の対 (pristine → warm-up 後) が同じ staging・同じ木で取れているか (順序、staging の複製)、(d) 冗長 cell と欠落 cell。cell の予測 `reason_code` を gate の判定順で自分でも導き、plan と食い違う cell を挙げる。
2. **runner の静的契約との整合。** 試作 patch を runner がそのまま食えるか: `validate_abort_counter_ownership` (token 走査は `#if` を無視して増分を数える → `#if` で囲んだ増分は「二重」と数えられるか)、`_study_lock_header_declarations` / `validate_default_stock_lock_absence` (無条件 include で S arm の前処理に study lock の識別子が残らないか。`#if SS2PL_LOCK_IMPL == 1` の中の class 宣言は前処理で消えるが、runner は **header file 自体**をも走査するか)、`_validate_compile_definitions` / `CACHE_TO_DEFINE` (`DLR1` 固定 + `SS2PL_DLR=0` の組で矛盾検査があるか)、`INERT_DECLARED_DIFFERENCES` / `_inert_witness_claim` (試作で宣言済み差分が消えたら runner の inert witness (`collect_inert_witness`) は「宣言と実体の不一致」で赤になるか → これは本 wave では走らせないが材料に書くべき)。probe が login で走らせられる pure-Python 契約はどれか。
3. **計算ノード運用の穴。** generic dispatch は clean env・cwd = 投入 worktree。probe の絶対 path・job dir の書込権・`TMPDIR` 無し (`tempfile` は /tmp → gate の `tempfile.TemporaryDirectory(prefix="izanagi_condition_supply_")` も /tmp に作る。/tmp の容量と、並列 job との衝突)、`c++` / `cmake` の解決、`FETCHCONTENT_SOURCE_DIR_*` の絶対 path、staging の `cp -a` 複製 (pristine を保つ) と `wfg` を含まない path、warm-up の対象 (試作 clone の build dir で `masstree_build` を回すと共有 staging の masstree source に config.h ができる → stock clone の configure にも効くか。両 clone が同じ `FETCHCONTENT_SOURCE_DIR_MASSTREE` を指すことの確認)、所要 (gate 1 要求 ≈ configure 2 + 前処理 2、cell 数 × 4 軸 → walltime 00:30:00 に収まるか。plan の見積りを自分で検算)、`PBS_JOBID` の採取、失敗 cell が後続 cell を止めない設計 (1 cell 1 try/except、途中結果を都度 atomic write)。
4. **shadow module の読み込み。** `importlib.util.spec_from_file_location` + `__package__="orchestrator.campaign"` で相対 import が repo の実 module へ解決されるか、`sys.modules` に shadow が別名で入るか、`_patch_changed_paths` の `Path(__file__).resolve().parents[2]` が shadow root を指すか。`dataclasses` の `ConditionArmRecord` 等が shadow と repo で**別 class** になるので、probe が両者の record を混ぜて `require_condition_gate_family` に渡すと `type(record) is not ConditionArmRecord` で `admission-contract-invalid` になる — plan はそれを避けているか (shadow の cell は shadow の family 関数で閉じる)。
5. **前 wave の既知の罠の再発。** T-2644 の §5.4 (path の `wfg`)、F29 (probe と production の差の明記)、`compute-visible.json` の `PBS_JOBID`、`_run_process` の stderr 非空 = 失敗 (CMake の deprecation 警告が stderr に出る版があるか)、`configure-failed` の detail が 500 byte で切れて原因が読めない (probe は configure の stderr を自前で全文保存すべきか)。
6. **insight の表の形が「採否を書かない再提示材料」になっているか。** plan の表が採否を先取りしていないか、逆に「何を変えれば通るか」が層別に読めない曖昧さがないか。
7. **scope 逸脱と所有。** plan が repo 内 file を変えていないか、runner / gate / 登録簿の本改修を実装に含めていないか、試作 patch に新しい lock 意味論を足していないか。

## 出力形式

所見ごとに: 番号、**分類 (裁定充足 / runner 契約 / 運用 / shadow / 再発 / 表 / scope)**、**real か refuted かの自己判定と根拠 (file:line)**、**放置時に成果物 (insight の採否材料) がどう変わるか 1 行**、是正案 (plan の変更として)。所見ゼロの分類はそう書く。最後に `## 総括` (必須、無いと不採用) を 10 行以内: real 所見の件数、最重要 1 件、cell 数と総所要の自分の見積り、plan を止めるべきか続けてよいか、予算が尽きた場合の途中結論。

## 禁止

file を作成・編集しない。git の状態を変えない。pytest を走らせない (静的検査でよい)。走らせていない結果を緑と書かない。gate の判定 logic を変える提案、gate の適用範囲を絞る提案 ((i)、D2120 項 12 で不採用確定) をしない。予算が尽きそうなら途中結論を出力形式どおり書いて終わること (無出力が最悪)。

## 親の段 4 方向 (provisional、これも攻撃対象)

plan の総括を受けて親は次を考えている。(1) 試作 patch は plan の 8 変更群に加えて **S arm の transaction.cc 前処理 bytes を stock と一致させるまで stock 経路を復元する 1 版 (revS)** に絞り、8 群だけの版は別に作らない。abort 無条件除去の対照版は plan どおり (4 cell)。(2) cell は plan の 60 から 44 へ絞る: revS×{O,T+,T−}×S (12)、revS×{O,T−}×phase1 (8)、現行×O×{S,phase1} (8)、現行×T−×S (4)、pristine 対 = 現行×O×phase1 + revS×T−×S (8)、abort 無条件版×T−×S (4)。T+×phase1 は O と同じ比較なので落とす。(3) walltime は 00:40:00。(4) author は login で `g++ -E -P` + `cmp` により S 一致を自分で検算してから納品する。この絞り込みで裁定に要る比較が欠けないか、44 cell の所要が walltime に収まるか、を検算せよ。
