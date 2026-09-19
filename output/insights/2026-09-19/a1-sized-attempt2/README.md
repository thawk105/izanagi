# A-1 balanced5 sized 本走 attempt-0002 — 既存 submit 経路は qsub の前に拒否した (投入せず・測定値なし・記録と裁定パッケージ) (2026-09-19)

- authority: none
- default_effect: no-state-change
- ユーザー裁定 (2026-09-19、dev-wave 引数の逐語): 「A-1 sized attempt-0002 を独立再現として 1 attempt 認可する。非認証 lane を維持し、
  formal 昇格は含めない。どこかの層で落ちたら再投入せず報告して止める」。付帯: 既存 submit 経路 (`paper_story_a1_paired.py submit
  --study-id paper-story-a1-20260901-balanced5-sized-v1`、hydrate 済み third-party source root 必須)、attempt-0001 と同じ policy・n=30・配置、
  比較可能条件を投入前に照合して記録、成果 = attempt-0002 の results 系列稿と 2 attempt の並記 (プールしない、D1993 項 6)、規律 2 を
  緩めない、scope 外 = formal lane・要件充足判定・追加 gate。
- 対象 study: `paper-story-a1-20260901-balanced5-sized-v1` (policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`、
  sha256 `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`; 事前登録
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`、sha256
  `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2`)。attempt-0001 の記録は
  `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md`、結果節は
  `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`。
- **本 wave は投入準備・投入前照合・既存経路の 1 回実走・記録だけを行った。実装面の差分はゼロ (変異 matrix 免除)。**
  事前登録・policy・source 契約・追補・patch・job body・attempt-0001 の公開 leaf と稿と図 9 の bytes は変えていない。
- **成果物の縮小:** attempt-0002 の測定値は存在しないので、results 系列稿 (attempt-0002 稿・2 attempt の並記) と図は作っていない。
  `docs/paper-story/README.md` の results 表にも行を足していない (stale 注記を 1 件だけ追加)。

## 1. 結論 (1 行ずつ)

1. **attempt-0002 は投入されていない。** 既存 submit 経路を 1 回実走したところ、qsub に達する前に
   `paper-story A-1 refused: prior attempt reached the bench barrier; group rerun is prohibited` (rc 2、22:05:30 → 22:05:36 JST) で拒否された。
2. **拒否は driver の gate `_assert_no_prior_v3_bench_start` (規律 2 由来) による。** policy 固定の durable base 直下にある attempt-0001 が
   bench barrier に到達した証拠 (`barrier/bench-go.json`・`barrier/ready/*.json`・`barrier/bench-start/*.json`) を持つため、同じ study の
   group 再投入を拒否する。認可済みの独立再現と、失敗後の再走を区別する入力をこの gate は持たない (§2)。
3. **副作用なし。** 拒否は intent 作成・attempt root 作成・qsub のいずれよりも前に起きる。実走後も durable base は `attempt-0001` と
   `attempt-0001.intent.json` だけ、新しい request は無く、submit-tree は clean (untracked 含む 0 行) のまま (§3)。
   計測 attempt は開始されていない (qsub 未到達) が、**認可された実行手続は submit 層で停止条件に達した**ので、次の実行には改めて
   認可が要る (相談 C 所見 8、D2120 項 3 と同じ形)。
4. **ユーザー裁定に従い再投入せず、ここで止める。** gate の緩和・先行 attempt の証拠の移動/削除・policy/base の変更のいずれも行っていない
   (段 4 裁定 `verbatim/adjudication.md`)。
5. **通す手段は 3 つとも本 wave の scope 外で、うち 1 つは規律 2 の射程にある。** 設計択一と推奨案を裁定パッケージ (§7) としてユーザーへ返す。
6. 投入前照合 (§4) は、submit-tree・CCBench pin・束縛 file・hydrate 5 pin・durable base のいずれも attempt-0001 と同じ条件で投入できる状態に
   あったことを示す。落ちたのは環境ではなく gate である。

## 2. 承認前提を覆した新事実 — submit の gate

- 場所: `orchestrator/campaign/paper_story_a1_paired.py` の `_assert_no_prior_v3_bench_start(base, study_id, current_attempt)`。
  `_run_submit_v3` が、`intent_path` / attempt root / 受領証 namespace の lexists 検査の後、intent の `_exclusive_write` と `qsub` の**前**に呼ぶ。
- 判定: `base` (= policy `execution.durable_measurement_base` =
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement`) 直下の `*.intent.json` と `barrier` を持つ
  先行 attempt を走査し、`barrier/bench-go.json` の `study_id` が一致、または `barrier/ready/` に 3 workload が揃う、または
  `barrier/bench-start/` に同 study の記録がある場合に `prior attempt reached the bench barrier; group rerun is prohibited` を raise する。
- 現物 (`verbatim/precheck.log`): attempt-0001 は `bench-go.json` (study_id = 対象 study、ready 3 本の sha256 を束縛)、`ready/{write-heavy,
  balanced,read-heavy}.json`、`bench-start/{同 3 本}.json` をすべて持つ (2026-09-18 06:32〜06:33 JST 作成)。
- 出自: commit `abff80d1b` (2026-09-03、「A-1 pilot を workload 単位の 3 job へ割った — 分割で開く規律 2 の穴と、未 gate の build 流路を塞いだ」)。
  同 commit message の逐語: 「(b) いずれかが bench を開始した後は列挙理由による group 再投入を拒否する。受理を狭める方向のみで、
  rerun.allowed_reasons は広げていない」「ready 三揃いまたは bench-go を持つ先行 attempt は、bench-start が空でも欠落でも拒否する」。
  事前登録 §6.4 (再走理由は bench 前失敗の閉じた列挙、性能の出力は再走を正当化しない) を機械化した防壁である。
- なぜ段 1 前の実測で見落としたか: 親は `run_submit` の先頭 (`_validate_attempt_root` まで) と `_run_submit_v3` の末尾だけを読み、
  「attempt root が durable base 直下の未存在 dir なら成立」と一般化した (相談 B 所見 1 が指摘、F29 型 = 部分抜粋から経路全体の成立を推測)。
- durable base は policy の field で、policy の bytes は事前登録・source 契約 v2・driver の定数 `V3_SIZED_POLICY_SHA256` が束縛する。
  base を変えるには policy を変える必要があり、それは束縛の全面改版になる。

## 3. 実行した手順と時系列 (JST。`date` / mtime から。推定値なし)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 21:39 | wave worktree `.claude/worktrees/dw-a1-sized-attempt2` (main `a99425b66`) と submodule 再帰初期化 rc 0 | date |
| 21:49 | 起動 gate `check_wave_startup.py --mode fresh --external-handoff` rc 0。裁定控えを rulings-inbox へ | date |
| 21:52 | 段 1 brief (`verbatim/brief.md`) | mtime |
| 21:55:32 → 21:59:02 / 21:59:09 | 段 3 相談 A (正しさ境界、sol) / B (手順、luna)。read-only、`reasoning=medium`、model call 8 / 13、CLI reported token 76,842 / 78,522、両方 accepted・`check_codex_output` OK | `consultA.pid`/`.done` mtime、launcher receipt |
| 21:56:52 → 21:57:32 | submit-tree = `<job dir>/submit-tree` (detached `a99425b66`、add 33 秒、submodule 再帰初期化 rc 0、`worktree lock`) | `verbatim/mktree.log` |
| 21:59 | third-party cache 5 本 `verify` rc 0 (pin は attempt-0001 の hydrate.json と同一) | date |
| 22:03:47 | 段 4 裁定 (`verbatim/adjudication.md`)。裁定 inbox 再走査 (本件の更新なし。main は `657e1e5a7` へ前進、A-1 経路の file に差なし) | mtime |
| 22:03:57 → 22:04:13 | hydrate 2 箇所 rc 0 (`verbatim/hydrate.log`、`hydrate-default.json`、`hydrate.json`) | mtime |
| 22:04:42 → 22:04:52 | 投入前照合 21 項目 (`verbatim/precheck.log`、§4) | mtime |
| 22:05:30 → 22:05:36 | **submit 実走 rc 2、stderr は `verbatim/submit.stderr` の 1 行。stdout 空** | `verbatim/submit.log`、mtime |
| 22:05 | 副作用の実測: durable base は不変 (`attempt-0001`、`attempt-0001.intent.json` のみ)、`qstat` に新 request なし、submit-tree porcelain 0 行 | date |
| 22:07:31 → 22:10:32 | 相談 C (裁定パッケージの点検、sol、read-only、model call 7、CLI reported token 55,280、accepted・`check_codex_output` OK) | `consultC.pid`/`.done` mtime、launcher receipt |

- submit の argv (逐語、cwd = submit-tree): `python3 -B -m orchestrator.campaign.paper_story_a1_paired submit --study-id
  paper-story-a1-20260901-balanced5-sized-v1 --expected-head a99425b66258911973785b11fd7d194884aeec64 --attempt-root
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002 --third-party-source-root
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/third-party-hydrated`。
- 起動 script (`run-mktree.sh` / `run-hydrate.sh` / `run-precheck.sh` / `run-submit.sh` / `run-consult{A,B,C}.sh` / `detach.sh`) と probe
  (`peek_stats.py` / `peek_receipt.py` / `precheck_paths.py`) は実行可能 file なので repo へ複製せず job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/` に残す。
- 監視・complete・materialize は起動していない (submit で止まったため)。

## 4. 投入前照合 — attempt-0001 の条件との対応 (投入前に確かめた範囲)

| 項目 | attempt-0001 (2026-09-18) | attempt-0002 の準備 (2026-09-19) | 判定 |
|---|---|---|---|
| study / policy | `…-sized-v1` / v3-sized.json sha `a6228bcd…` | 同じ file、現物 sha `a6228bcd…` | 同一 |
| 事前登録 / source 契約 v2 / 追補 | sha `6047eff0…` / `b50a4edf…` / `6093de24…` | 現物 sha 同値 | 同一 |
| patch / job body / driver / a1_source / pipeline / calibrator runner | working sha `a5e0710c…` / `3c2b734d…` / `62c10187…` / `f7adc8e9…` / `472cc7a2…` / `afa697ee…` | 現物 sha 同値 (束縛 9 file の blob は `d2ebef7a4` と `a99425b66` で `git diff --stat` 0 行) | 同一 |
| CCBench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec`、tracked-clean | submit-tree で HEAD 同値、`status --porcelain --untracked-files=no` 0 行 | 同一 |
| third-party 5 source | masstree `b3c5d054`、mimalloc `02a2f5df`、googletest `f8d7d77c`、gflags `e171aa2d`、glog `8f9ccfe7` | cache verify rc 0、hydrate 2 箇所とも同 5 pin | 同一 |
| workload 3 key | write-heavy rr5 `fixed10`−`no-backoff` / balanced rr50 `fixed5`−… / read-heavy rr95 `fixed2`−… | policy の `workloads[].arms` (同 file) | 同一 |
| n / k / planned sigma / 配置 / root seed | reps 30、k 2.8315…、σ 66403.45 / 56697.44 / 74668.49、`balanced-a5b5-b5a5-v1`、事前登録 §2.1 の 3 seed | 同 policy・同事前登録 (seed は study に固定なので物理順も同じ) | 同一 |
| 環境契約 | site `pegasus-compute-only`、queue `gen_S`、`elapstim_req 06:00:00`、node は job ごと 1 | 同 policy・同 job body | 同一 (実 node は投入されていないので無し) |
| durable base | `…/measurement` (attempt-0001 が直下) | 同じ base、書込可、`attempt-0002` と `attempt-0002.intent.json` は不在 | 同一 base |
| source commit (submit-tree HEAD) | `d2ebef7a407dc6be61622ed596cf08b8b518f606` (当時の local main) | `a99425b66258911973785b11fd7d194884aeec64` (着手時の local main、416 commit 後) | **異なる** |
| 束縛外で変わった driver の import 先 | — | 直接 import: `condition_meaning_gate.py` (+15、MOCC define 登録)、`layout.py` (+5、agent_outputs property)、`trial_registry.py` (±252、attempt registry 履歴検査)。間接: `agent_outputs.py` (新規)、`materializer_admission.py` (+5)、`autonomous_trial_completeness.py`、`s8c_acceptance_receipt.py`。他の直接 import 先 17 file は差分なし | **A-1 到達性は未評価** (相談 A 所見 1・2) |
| 投入時刻帯 / queue | 06:30 JST、投入時 cluster QUE 36 / RUN 32、3 job は 8〜28 秒で開始 | 22:05 JST、gen_S RUN 29 / QUE 12 / HLD 24 (21:45)、149 host 中 65 host が load ≤ 2。自分の他 job 8 本 (floor-pair 3、受入 shard 5) | 参考値 (開始保証ではない) |

- 「同じ測定条件・同じ解析規則」と「同じ測定値が出る」は別であり、後者は本表から言えない (相談 A 所見 2)。
- 本表は「投入できる状態にあったか」を確かめたものであり、attempt-0002 は投入されていないので、実 node・job 時刻・build 成果物の比較は存在しない。

## 5. 相談 3 本の要約と裁定

段 3 相談 A (正しさ境界と整合) / B (実効性・手順の欠落・過剰)、段 4 後の相談 C (裁定パッケージの点検)。全所見の裁定は
`verbatim/adjudication.md` の表。要点:

- **B1 (real、決定的):** 既存 submit は先行 attempt の bench 到達で拒否する → 親が現物で確定し、§1〜§2 の結論になった。
- **A1 (real):** 「import 閉包で変わった file は 2 本だけ」という親の実測は誤り → §4 の表で訂正。
- **A3 (refuted):** 事前登録 §6.1 から「study 全体で公開は一度」とは導けず、submit-tree を `d2ebef7a4` に置く案を迂回と断じる根拠は弱い →
  brief の理由を訂正。ただし B1 により、どの tree でも submit 層で拒否されるため commit の選択は結果に影響しない。
- **A4 / B7 (real):** raw `result.json` と公開 leaf の差は `materialization_evidence` だけでなく `limitations` もある → brief を訂正。
  今回は materialize に達していないので帰結なし。
- **A6 / B10 (refuted):** D2120 項 3 の再認可条件には抵触しない。図なし (P3) は過剰な制限ではない。
- **B6 (根拠不足):** idle host 数から即時開始は導けない。barrier timeout (600 秒) の起点は各 job が ready を書いた後 → §4 の文言を訂正。
- **B9 (real):** 拒否は予測でなく実走で実測する (F29)。MANIFEST は自身を hash 対象にしない (F36)。未実施の検査を成功と書かない。
- **C1 / C3 (成立):** 択 2 は固定表 1 行では実現せず、D2096 項 5 の明示的な裁定変更が要る → §7 で訂正。
- **C2 (成立せず):** 新 study を正しく登録した後なら 2 つの gate 本体の変更は不要 (base・公開先が別なら走査対象に旧 attempt が無い)。
- **C4 / C5 (成立):** 「結果を見た再投入」の危険は両案に残る。択 1 は規律 2 由来の防壁の保護範囲を変えるが、exact な認可対象に限れば他の
  attempt の拒否は機械的に維持できる → §7 の比較を対称にした。
- **C6 (成立):** §6.4 への追加は誤記訂正ではなく将来の規則変更 → 「追補 (別版)」として明示裁定する形に訂正。
- **C7 (成立):** 新 seed でも物理順が変わる保証は無い。「同じ配置」を文字どおり満たすのは同 seed → §7 で訂正、推奨の根拠にした。
- **C8 (成立 / 根拠不足):** submit 拒否を「落ちた」と数えて止めた判断は妥当。「認可未消費」は断定できない → §1 を訂正。

## 6. 言わないこと

- **A-1 の充足・formal 化・昇格・再認可は判定しない。** attempt-0001 の結果・限定・lane (`formal=false` / `promotion_prohibited=true` /
  `result_authority=sized-preregistered-descriptive-only`) は本 wave で 1 byte も動いていない。
- **反復間の安定性については何も言えない。** 2 本目の測定は存在しない。attempt-0001 稿の限定 L-A1S-4 はそのまま残る。
- **gate の是非を判定しない。** `_assert_no_prior_v3_bench_start` は規律 2 の穴を塞ぐために入った防壁であり、本 wave はそれを緩めず、
  緩める案の採否はユーザー裁定 (§7)。
- **submit-tree と job dir は撤去しない** (原本の所在)。submit-tree は lock 済み・clean。durable base に attempt-0002 の痕跡は無い。

## 7. 裁定パッケージ (ユーザーへ返す設計択一。本 wave では実装しない)

相談 C (`verbatim/consult-C.out.md`) が段 4 の起草 (`verbatim/adjudication.md` 末尾) を 4 点訂正した: (i) 択 2 は「固定表 1 行の追加」では
実現せず、identity の固定分岐 (`_policy_identity`、v3 ID 集合、`ident.py` の非認証 identity)、job shell の study dispatch、`CONTRACTS`、
policy / 契約 / 事前登録の新 file、test の pin を変える; (ii) 「結果を見た後の再投入」を機械が区別できない危険は択 1 にも択 2 にも同じく
残る (択 1 だけに帰属させた非対称な比較は不成立); (iii) 新 seed でも物理順が変わる保証は無い (各 workload 3 bit)。今回の要求
「同じ policy・配置」を文字どおり満たすのは同 seed・同物理順の再実行である; (iv) 「1 attempt の認可は消費されていない」は断定できない —
計測 attempt は開始されていない (qsub 未到達) が、認可された実行手続は submit 層で停止条件に達したので、**次の実行には改めて認可が要る**
(D2120 項 3 と同じ形)。下は訂正後のパッケージである。

**何を決めるか:** 同じ study の 2 本目 (以降) の認可済み独立再現を、どの経路で投入可能にするか。いずれの択も本 wave の scope 外で、
実装は Codex author + 敵対レビュー + 変異 matrix を要し、ユーザーの明示裁定なしには着手しない。

- **択 1 — 認可記録付きの gate 入力 (同 study の attempt-0002 のまま):** durable base に認可 record (study_id・attempt 名・source sha・
  裁定日 / D 番号を exact に持つ file) を置き、`_assert_no_prior_v3_bench_start` は**その exact な attempt 名に限って** bench 後の group
  再投入禁止を解除する (他の attempt 名は従来どおり拒否)。`_exact_materialization_destination` は attempt 別の公開先
  (例 `…-sized/attempt-0002`) を受理する形に広げる。事前登録 §6.1 (一度しか作れない宛先) と §6.4 (再走理由の閉じた列挙) は、既存
  凍結物と attempt-0001 の判定を保持したまま「将来の観測に適用する追補 (別版)」として明示的に裁定する (erratum の名では正当化しない)。
  **帰結:** 規律 2 由来の rear gate と公開先 gate の受理集合が 2 箇所広がる (変更面は小さい: 2 関数 + test + 追補)。policy・seed・
  物理順は attempt-0001 と同一 (文字どおり「同じ配置」)。認可対象の識別は機械化できるが、認可者が性能値に影響されたかは識別できない
  (この点は択 2 も同じ)。
- **択 2 — 独立再現を別 study として登録:** 新 policy JSON (study_id・durable base・公開先・事前登録束縛・(新 seed 案なら)
  `schedule_root_seed` ×3 を変え、測定条件・arm・n・k・sigma は同一)、新 source 契約 JSON、元の事前登録を sha で引用する短い事前登録、
  `_policy_identity` / v3 ID 集合 / `ident.py` / `CONTRACTS` / job shell の study dispatch と hydrate 分岐への追加、test の pin 更新
  (相談 C「択 2 の変更面」の表)。**帰結:** 2 つの gate 本体は変えないが、第三 study を受理する複数の実装変更を伴い、D2096 項 5
  (「3 study 目の枠組みは作らない」) の明示的な裁定変更が要る。公開先と base が別なので attempt-0001 の leaf・束縛に触れない。
  seed を同じにするか新しくするかの下位選択が要る (同 seed = 同じ物理順の再実行、新 seed = 同じ配置規則の別走。新 seed でも物理順が
  同じになりうる。順序を見て名前や接頭辞を選び直してはならない)。「結果を見た後に study N+1 を登録する」経路は残る。
- **択 3 — 独立再現を行わない:** attempt-0001 の単一 attempt を限定 L-A1S-4 (反復間の安定性へ一般化しない) 付きのまま論文素材にする。
  **帰結:** 反復間の再現性を観察する機会を失う。attempt-0001 の記述的価値は失われない。実装は不要。
- **先に決めるべき研究設計 (相談 C の第 4 案):** 「同一配置 (同 seed・同物理順) の反復」と「順序を変えた再現」のどちらを目的にするかを
  確定してから、有限回 (例: 1 回) の将来計画を裁定する。目的が前者なら択 1 が自然、後者なら択 2 (新 seed) が自然。

**推奨: 研究目的を「同一配置の反復」と確定し、択 1 を 1 attempt 限定で採る。** 理由: 変更面が最小 (2 関数 + 追補 + test)、policy・seed・
物理順が attempt-0001 と同一で「同じ policy・配置」を文字どおり満たす、認可を人手の文書から機械可読の exact record へ移す (D2120 項 3
「再投入には改めて認可が要る」の機械化)。蹴った帰結: 択 2 は第三 study の受理という広い実装変更と D2096 項 5 の改訂を要し、
gate 本体を保つ利点は「結果を見た再投入」の危険を消さない。択 3 は L-A1S-4 を残す。
**留意:** 択 1 は規律 2 由来の防壁の受理集合を広げるので、AI は自律採用しない。採るなら「exact な認可 record 以外は従来どおり拒否」を
負例 (別 attempt 名・別 study・別 source sha・record 不在) の変異で示すことを実装条件にする。
**返答例:** 「研究目的は同一配置の反復。択 1 を attempt-0002 の 1 attempt 限定で認可する。認可 record の形式は実装 wave で起草し、
§6.1 / §6.4 の追補は将来の観測にのみ適用する」。

## 8. 一次資料

- 本 dir の `verbatim/` (brief・裁定・相談 3 本の prompt と出力・照合 log・hydrate 出力・submit の log と stderr・mktree log)。
  各 file の byte 数・sha256 は `MANIFEST.tsv` (MANIFEST 自身は含めない)。
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/` (原本、起動 script、codex launcher receipt
  `codex/dev-wave-a1-sized-attempt2/consult-{a,b,c}/receipt.json`)。
- durable base `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/` (attempt-0001 の証拠。本 wave は
  読んだだけで書いていない)。
- gate の実装: `orchestrator/campaign/paper_story_a1_paired.py` (`_assert_no_prior_v3_bench_start`、`_run_submit_v3`、`_durable_measurement_base`、
  `_exact_materialization_destination`)、導入 commit `abff80d1b85dc1e2e0f6f0de7ac0d893a8405b46`。
- 裁定: ユーザー裁定 (2026-09-19、本 README 冒頭に逐語。decisions fragment `{{D:a1-sized-attempt-0002-refused-at-submit}}` に記録)、
  D2120 項 3、D2096、D1993 項 6、D1986 前文、D1323、事前登録 §2.1 / §6.1 / §6.4 / §7.2。

## 9. 段の記録 (dev-wave 軽量版)

- 段 1 brief = `verbatim/brief.md`、段 3 = 相談 A / B、段 4 裁定 = `verbatim/adjudication.md` (実装しない、変異免除、射程判定 (c))、
  段 4 後に相談 C (パッケージの点検)。段 2・5・6 は無し (実装面ゼロ、results 稿を作らないため独立レビューの対象も無し)。
- 実測は親 (submit-tree 作成・hydrate・照合・submit 1 回)。codex 子は read-only 3 本、author 0 本。
- 受入全走は記録 commit 後の tip で 1 走 (結果は land の受領証と worklog)。
