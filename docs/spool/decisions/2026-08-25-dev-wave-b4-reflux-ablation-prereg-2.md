---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-b4-reflux-ablation-prereg
seq: 2
---

## {{D:b4-reflux-ablation-estimand}}. B-4 還流 ablation の estimand を「詳細 anomaly の増分効果」へ狭め、広い主張を文書自身が禁じる

**背景:** 論文 §8 の B-4「規律 3 の還流 on/off ablation」を実行できる形にする wave で、
配線 (`make_critic_digest(reflux=)`、D39 決定 4) が既に存在することを実測した。
実証されていない理由は配線の不在ではなく、**off アームが「構造化された正しさシグナル全体」を
遮断していない**ことであった。段 3 の 2 レンズが独立に同じ結論に達した。

**決定 1 — estimand を「coarse outcome 共通のうえでの詳細 anomaly の増分効果」に固定する。**
両アームは `whiteboard.result` (success / fail / rejected) と緑 leading-indicators を共通で受け取る。
`whiteboard.result` は edge / reason を持たないが構造化された correctness outcome であり、
これを共通に残す限り測れるのは詳細 anomaly の増分である。**事前登録文書は広い主張
(correctness feedback 全体の on/off) を名乗ることを自らの本文で禁じる。**
広い主張には閉じた critic invocation と role-facing の型付き結果 projection が要り、
それらは実装されていない。

**決定 2 — 負の対照の合格文を「harness が生成する critic digest における loader 非呼出」に限定し、
「critic role の能力遮断を証明しない」ことをテスト docstring と事前登録の両方へ明記する。**
`.claude/agents/critic.md` は critic に `Bash` を与え、`orchestrator/critic/digest.py --campaign-dir`
の自己実行を**明示的に許可**している。同 CLI は reflux 引数を持たず、`make_critic_digest` が渡さない
screening 節まで含めて赤の全節を常に描画する。したがって off アームの遮断は role 契約により
正面から否定されており、テストでは閉じられない。**閉じた critic invocation は実走の前提条件とする。**

**決定 3 — primary を paired 1-step (同一の赤 precursor から各アームが行う次の 1 synthesis) に固定する。**
`check_stop` の `reverse-exhausted` は `reverse_recommendations` 単独で発火し、その値は
`prior_critic_reverse` から畳まれる。同値は proposal JSON から読まれるだけで arm・digest・
critic invocation receipt と束縛されていない。よって同一 iteration 上限だけでは予算が等価にならず、
差が treatment か停止 censoring かを分離できない。停止差は副次記録とする。

**決定 4 — screening rejection を treatment から明示除外する。**
`load_screen_rejections` は現行の `make_critic_digest` が**どちらのアームへも渡さない**。
差分ではないため treatment に含めず、「全 structured rejection の還流」とは書かない。
含めるには `orchestrator/critic/digest.py` の変更が要り、併走 wave と衝突するため本 wave では広げない。

**決定 5 — 事前登録は新規文書に置き、`docs/phase3-main-experiment.md` を 1 byte も変えない。**
同文書は S-1 freeze (`output/s1-freeze/known_axes_freeze.json`) が sha256 で bytes を pin する。
過去に同型の追記が受入を赤にし編集を撤回した (F78)。参照は新文書から旧文書への片方向だけとする。

**決定 6 — 既知結果台帳を置き、本書に基づく成果を「既知結果に informed された登録追試」と自ら宣言する。**
起草時点で還流 on アーム相当の実走結果が存在する (2026-07-12 の F 段で実 LLM 駆動 2 iteration が
certified、critic の tie と逆方向推奨まで記録済み)。前向き事前登録を名乗らない。

**決定 7 — 機械強制されていないことを「現在地」として正直に書く。**
全件報告規則に file-drawer の機械強制は無く、manifest・append-only registry・完全性 consumer は
存在しない。`run_one_iteration()` の戻り値には reject 時に `digest`、certified/aborted 時に
`records` (WAL payload 一式) が載り、sanctioned CLI は表示しないが Python API を直接呼ぶ controller
には見える。`policy_hint` は無加工で planner payload へ入る。これらを規範と前提条件で扱い、
機械強制されているかのように書かない。

**却下した選択肢:**
- **広い主張を維持したまま発効させる** — off が実際には赤に到達できるため、差が出なくても
  「還流に価値なし」と読めない。偽の negative を論文へ書く経路になる。
- **`whiteboard.result` を off の planner 射影から落として広い主張を保つ** — 内部 `LoopState` を
  維持したまま射影だけを変えることは技術的に可能だが、`p3_s4_loop.py` の変更を要し本 wave の
  編集面 (テスト 1 file) を超える。scope 外として裁定へ返す。
- **第 3 アーム reason-only を同時に採る** — 規律 5 (段階導入)。採らない代償は主張限界として明記した。
- **8c を B-4 の venue に転用する** — 8c の arm は descriptor on/off/swapped であり reflux は
  `True` 固定である。加えて 8c の critic 射影 (`apply_critic_feedback`) は自由文を捨て、
  planner へ届く critic 由来は `uncertainty_present` と `reverse_recommended` の 2 bit だけである。
  別 treatment であり交絡する。
