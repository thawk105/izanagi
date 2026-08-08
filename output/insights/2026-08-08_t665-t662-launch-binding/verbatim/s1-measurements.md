# 段 1 追加実測 — 事後検査案の検出力と取りこぼしを過去 wave で再現した

すべて 2026-08-08 に本 worktree / 実 rollout に対して測定した。docs は根拠にしていない。

## 実測 A — 素の `codex exec` は実効 model / effort を残す

`~/.codex/sessions/2026/08/08/rollout-2026-08-08T19-19-49-019fe0e2-...jsonl` (wave `dev-wave-t627-noop-binding`) の実読:

- `session_meta.payload`: `session_id`, `cwd` (= wave worktree 絶対パス), `originator="codex_exec"`,
  `cli_version="0.146.0"`, `source="exec"`, `model_provider="openai"`, `timestamp` (UTC, `Z`)
- `turn_context.payload`: `model="gpt-5.6-sol"`, `effort="max"`, `sandbox_policy={"type":"read-only"}`,
  `cwd`, `workspace_roots`, `approval_policy="never"`,
  さらに `collaboration_mode.settings.{model,reasoning_effort}` に**同義の第 2 の値**がある
- `event_msg/user_message` に prompt 全文が残る
- 1 session あたり `turn_context` は 1 件 (このセッションでは実測 1)
- 保持: `~/.codex/sessions/2026/07/` から現存。回転で消えていない
- `CODEX_HOME` は未設定 → 既定 `~/.codex/sessions`。`codex_worker_launch.py:2575-2581` も同じ既定

**帰結:** 起動側を一切変えなくても、事後に実効値を機械可読に取れる。案 B は原理的に成立する。

## 実測 B — 過去 wave [T-181] を遡って走査すると worklog の申告を再現できる

`cwd` に `t181` を含む rollout を時刻順に並べた (全 13 セッション、model / effort は `turn_context` から):

| 時刻 (UTC) | cwd (basename) | model | effort | 段 (親が同定) |
|---|---|---|---|---|
| 08-07T22:45:15 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | max | 段 2 |
| 08-07T23:02:34 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | max | 段 3 レンズ A |
| 08-07T23:02:35 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | max | 段 3 レンズ B |
| 08-08T08:33:04 | **`dw-t181-impl`** | gpt-5.6-sol | high | 段 5 実装子 |
| 08-08T08:49:42 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | high | 段 6 レビュー A |
| 08-08T08:49:42 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | high | 段 6 レビュー B |
| 08-08T09:03:03 | **`dw-t181-fix`** | gpt-5.6-sol | high | 段 6 fix 1 |
| 08-08T09:18:24 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | high | 段 6 焦点再レビュー 1 |
| 08-08T09:29:32 | **`dw-t181-fix2`** | gpt-5.6-sol | high | 段 6 fix 2 |
| 08-08T09:40:55 | `dev-wave-t181-stage6-high` | gpt-5.6-sol | high | 段 6 焦点再レビュー 2 |
| 08-08T09:54:18 | **`dw-t181-fix3`** | gpt-5.6-sol | high | 段 6 fix 3 |
| 08-08T10:00:31 | **`dw-t181-fix3`** | gpt-5.6-sol | high | 段 6 fix 3 再投 |
| 08-08T11:15:10 | **`dw-t181-merge`** | gpt-5.6-sol | high | 段 9 merge (role=author) |

worklog (315) の申告「段 6 レビュー 2 本と焦点再レビュー 2 巡はすべて `reasoning=high` で起動した」は
**この走査で独立に再現できた** (該当 4 本すべて `effort=high`)。
→ **事後検査の検出力は実在する。現在この照合を行っている機構は 0 件である。**

## 実測 C — cwd による wave 帰属の取りこぼしは 46%

13 セッションのうち **6 本 (46%)** が wave worktree 以外の cwd で走っている
(`dw-t181-impl` / `-fix` / `-fix2` / `-fix3` ×2 / `-merge`)。
これは `DW-S05-A` / `DW-S06-B` が実装子・fix 子を**別 worktree**へ隔離することの直接の帰結であり、
運用ミスではなく契約どおりの挙動である。

**取りこぼす 6 本には、[T-665] が名指しする段 6 fix 子 4 本がすべて含まれる。**
`dw-t181-*` という接頭辞は親のその場の命名であり、契約に規定がない
(`docs/dev-wave/workers.md` の `DW-S05-A` / `DW-S06-B` は worktree を分けよとしか書いていない)。

## 実測 D — 時刻窓だけでは 5.4 倍に過剰包含する

[T-181] wave の時間窓 (08-07T22:45Z 〜 08-08T11:20Z) に存在する rollout を cwd 別に集計:

```
  12  dev-wave-t529-activation          6  dev-wave-t530-contract-hash-binding
   9  dev-wave-t627-noop-binding        5  dev-wave-t639-admission-scope
   8  dev-wave-peer-land-coordination   3  dev-wave-t642-s04-scope
   8  dev-wave-t182-luna-stage3         2  dw-t181-fix3
   7  dev-wave-t181-stage6-high         1  dw-t181-impl / -fix / -fix2 / -merge (各 1)
   6  dev-wave-t139-addendum-a
  合計 70 セッション / 14 cwd
```

T-181 に属するのは 13 / 70。**時刻窓を単独の selector にすると 5.4 倍の過剰包含**になる。
並行 wave が常時 4〜9 本走っているため、時刻は wave を分離しない。

→ **cwd が唯一の per-wave 判別子であり、その cwd を段 5 / 段 6 が壊している。**
これが本 wave の設計択一の実質的な中心である。

## 実測 E — 権威は時間変化する (事後検査の false positive 源)

`DW-O01` の model 権威行 (`段 3 のみ 2 本で gpt-5.6-sol→gpt-5.6-luna`) は
commit `16e0bbb9` = **2026-08-08 18:27 JST** に land した (`git blame -L 13,13`)。
[T-181] の段 3 は 2026-08-08 08:02 JST に走っており、当時の権威は sol 単独だった。
実測 B の段 3 が両方 `gpt-5.6-sol` なのは**当時の契約に適合している**。

→ 事後検査は **HEAD の権威ではなく wave の base commit 時点の権威**と照合しなければ、
過去 wave に対して偽の赤を出す。案 B / C はこの時制を設計に含める必要がある。

## 実測 F — 収集層は既に実装済みで、production で使われていない

`tools/codex_worker_ledger.py` (1150 行、[T-179]/[T-180] が実装) は **rollout jsonl を決定的に集計する
read-only 台帳**であり、次を既に持っている。

- `--sessions-root` / `--cwd-contains SUBSTR` (部分一致 OR filter)
- `--manifest MANIFEST` — `CodexWorkerSessionManifest` による **exact session selector**
  (= 宣言方式。[T-180] が「cwd 部分一致の限界」への答えとして追加したもの。`docs/phase3.md:682`)
- `--stage-map JSON` — `{"<session_id>": "<stage>"}` の手動 override
- `--worklog` / `--worklog-entry` / `--strict` (rc=2)

実走 (`python3 tools/codex_worker_ledger.py --cwd-contains t181 --json`、rc=0) すると、
session ごとに `model` / `reasoning` / `cwd` / `timestamp` / `session_id` / `prompt_hash` /
`model_calls` / `turn_contexts` / token 内訳 / `outcome` が出る。

**つまり「実効値を集める」層は既にあり、欠けているのは「権威と突き合わせる」層だけである。**

## 実測 G — stage 分類は prompt 文言の慣習に束縛され、既に drift で壊れている

`tools/codex_worker_ledger.py:574-587` の `_stage_prefix` / `_classify_stage` は
**prompt の先頭の非空行 1 行**に対する正規表現照合で段を決める。規則 (`STAGE_RULES`, 同 45-80 行) は
`段2の read-only Codex planner` / `段3の read-only adversarial consultant` /
`段5の Codex implementation worker (role=author)` / `段6の Codex fix worker` /
`段6の read-only focused adversarial reviewer` といった **[T-179] 当時の文言**を要求する。

実測: `--cwd-contains t181` の 33 session のうち **30 session が `stage="unclassified"`**、
`focus` に分類できたのは古い wave (2026-07-29/30) の 3 件だけだった。

原因を裏取りした。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t*/s2-prompt.txt` と `s3*prompt.txt` の
**先頭行は完全に自由文**であり、実測で 10 種類以上の異なる書き出しがある
(「あなたは izanagi 開発 wave の段 3 敵対検証者」「…プロジェクトの**防御レビュー担当**」
「…リポジトリの読み取り専用の」「…の dev-wave 段 2 のプラン起草者」…)。
**規則が要求する英語 role 語を含むものは 1 件も無い。**

→ **段の同定機構は実装済みだが、契約に無い文言慣習へ束縛されており、実効被覆はほぼゼロである。**
これは「謳うだけで発火しない gate」の実例であり、案 B が段を同定する方法を
prompt 文言に置く限り同じ運命をたどる。

## 実測 H — `--cwd-contains` は wave も repo も跨いで過剰包含する

同じ実走で返った 33 session のうち、13 が `[T-181] 段 6 high` wave のもので、
残り 20 は **別の wave** (`dev-wave-t181-reasoning-ab`) であり、しかもその cwd は
`/home/SFC/tanab/github/izanagi/...` という**別 checkout の path** だった。
`docs/phase3.md:682` が [T-180] へ送った「wave 受理集合の確定 (cwd 部分一致の限界)」は
未解決のまま残っており、実測で再現できる。

## 実測 I — 起動値の不正は既に実害として記録済み (F56)

`docs/failures.md:1304-1341` の **F56** が [T-182] wave で実測している。

- `-c model_reasoning_effort="ultra"` (**存在しない値**) は `gpt-5.6-sol` / `-luna` / `-terra` で
  **rc=0 のまま成功**し、rollout の `turn_context` に `reasoning=ultra` が記録される。
- model により reasoning の受理集合が異なる (`gpt-5.4-mini` は `max` を拒否)。
- 根本原因として「`DW-O01` は `model_reasoning_effort="<効いた値>"` と書いて**起動者の注意に委ねて
  おり**、『効いたか』を検査する経路がどこにも無い」と明記されている。
- **恒久対応 (c) = 「未知の reasoning 値と model×reasoning の非対応組は起動前に落とす」** と
  既に記録されている。実体化の所有は [T-183] / [T-184]。

→ **「実装しない (現状維持)」の害は仮想ではなく実測済み**である。ただし恒久対応が
「**起動前**に落とす」と書いてある点は、純粋な事後検査 (案 B) では満たせない。

## 実測 J — 所有の衝突に注意 ([T-184])

`docs/phase3.md:694` は **「`DW-O01` の結線と stage 別上限値は [T-184] の所有」** と明記する。
[T-184] は「model/reasoning/resource/retry の **stage matrix** を `DW-O01` と worker 契約へ
一度だけ反映する」タスク (P1、[T-180]〜[T-183] 後)。

→ 本 wave の設計案が「段 → 期待 model/effort の写像 (stage matrix)」を**新規に定義**するなら、
それは [T-184] の所有を侵す。本 wave は**既存の権威行を読む照合層**に留めるか、
[T-184] との境界を裁定パッケージで明示的に問う必要がある。
