# [T-936] 段 1 brief — `_find_rollout` が subagent の親 session を拒否する件

base = main `ab3feb04` / branch `worktree-dev-wave-t936-rollout-identity` / 2026-08-16 JST

## 確定済みユーザー裁定

2026-08-16 一括裁定 #41 ([T-936]) = **「全走査を維持したまま判定式を直す ([T-886] と矛盾しない形で)」**。
控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full-43rulings.md` 74 行目。
[T-886] の裁定 (2026-08-12 第 2 束) = SHA pin を持つ label に限り名前 glob の fast path、
**pin 無しの呼出元は全走査維持**、fast path 後の SHA 照合は必須。
→ 走査範囲を狭める方向 (探索打ち切り・head 打ち切り・件数上限・filename 依存) は本 wave では採らない。

## scope

- 変更面 = `tools/codex_reasoning_ab.py` の `_rollout_matches_session` (:283-292) の判定式のみ。
  `_find_rollout` (:295-341) の走査構造・pin fast path・RC_SESSION の raise は形を変えない。
- テスト面 = `orchestrator/tests/test_codex_reasoning_ab.py` の `_find_rollout` 群。
- scope 外 = `_scan_session_rows` ([T-937])、消費側 `:3084-3122` の meta 行数検査、
  receipt 検証の他の refusal reason。

## 段 1 前提実測 (実 corpus `~/.codex/sessions`、3,602 file、全走査 225 秒)

probe は repo 外 (`/home/SFC/tanab/.claude/jobs/47eaa767/tmp/probe_t936*.py`)。模擬ではなく実 corpus。

- `session_meta.payload` に `id` を欠く行 **0 件**、`session_id` を欠く行 **0 件**。
- 現行述語 `id==X or session_id==X` で解決件数が 1 にならない id は **2 件**。
  - `019f690c-1682-7dd2-9cc5-a708cf68d46e` → 2 件。子 file (`019f6912…`) の
    `session_id` が親を指す。**単純な取り違え型**。
  - `019fd52d-fdac-7b73-9d3d-4aac9948ee55` → 4 件。子 3 file はいずれも
    `source={"subagent":{"thread_spawn":…}}` + `forked_from_id` を持ち、
    **2 行目に親の session_meta 行をそのままコピーして持つ** (`id==session_id==親`)。
- したがって **「`id` だけで照合する」修正では `019fd52d…` は 4 件のまま直らない** — 実測済み。
- fork/subagent file は corpus 全体で 4 件。うち 3 件が親行コピーを持つ。
- pin 付き 5 label (POS/NEG/fix1/fix2/author) は現行・候補とも同じ 1 file に解決。

## 不変条件 (緩めてはいけない)

1. pin 無し経路は**全 rollout の全走査**を維持する ([T-886] 裁定、#41 の明示条件)。
2. 受理集合は現行の**真部分集合**に留める。現行が拒否するものを新たに受理しない (規律 2)。
   実測: 候補述語は現行が解決できた 3,600 id すべてで**同一 file** を返し、
   残り 2 id を「拒否」から「正しい親 1 件」へ変える。緩和はゼロ。
3. 解決件数が 1 でないときの `RC_SESSION` fail-closed を残す。曖昧なら拒否する。
4. pin fast path の SHA 照合を必須のまま残す。
5. 判定は **file 内容**に基づく。filename の uuid を同一性の根拠にしない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 判定式。** rollout file F が session X を名乗る ⇔
  - ∃ meta 行 r ∈ F: `own(r) == X`、かつ
  - ¬∃ meta 行 r ∈ F: `own(r) != X` かつ `r.payload.session_id == X`
  - ここで `own(r)` = `r.payload["id"]` (str なら)、無ければ `r.payload["session_id"]`。
  - 第 2 条件の意味 = 「F が自分を X の子孫だと宣言しているなら、F は X ではない」。
    親行のコピーを持つ fork file を、順序に依存せず内容だけで排除する。
  - 実測: 3,602 id すべてが件数 1。現行が解決できた id では返り file が完全一致。
- **(P2) 既存テストの期待を 1 variant だけ反転する。**
  `test_find_rollout_session_meta_encoding_and_payload_field_equivalence` の
  `distinct-fields` (`{"id":"other","session_id":"target-session"}`) は
  **subagent 行そのものの形**であり、現在「親 id で引くと子 file が返る」ことを仕様として固定している。
  これが T-936 のバグ本体なので、期待を「解決件数 0 → RC_SESSION」へ変える。受理集合の縮小。
- **(P3) `session-id-only` variant (payload に `id` が無い) は受理を維持する。**
  実 corpus に該当 0 件だが、後方互換の縮小を最小にするため `own(r)` の fallback で保つ。
- **(P4) 命名の二義性を解く (D75)。** `_find_rollout(sessions_root, session_id)` の引数
  `session_id` は「探している session の識別子」、payload の `session_id` は「所属 root session」で
  同名別義。引数名を `target_session_id` 等へ改名し、payload key と混同できなくする。

## 成果物影響 (DW-G05)

実装しない場合: codex 子が subagent / thread_spawn を産んだ wave では、
`verify` / receipt 検証経路が `_find_rollout` の
`session <id> rollout count is N, expected 1` を `failure_reasons` に積む。
該当する親 id が実 corpus に 2 件実在するため、**その試行は台帳へ certified として載らず、
A/B の材料レポートから欠落する** (欠測が「拒否」として記録され、値が変わるのではなく試行が消える)。
[T-937] 側の律速化と違い、これは正当な作業の誤拒否である。

## 成果物の形

- コード = `tools/codex_reasoning_ab.py` の述語 1 箇所 (+ P4 の改名)。
- テスト = 実 corpus で観測した 2 型 (取り違え型 / 親行コピー型) の positive control、
  および P2 の期待反転、既存 `_find_rollout` 群の非退行。
- 記録 = worklog / decisions fragment、insight (逐語・変異台帳)。

## 分割方針

単一 file の単一述語なので実装 unit は 1 本。受理集合が変わり正しさ防壁 (RC_SESSION) に触るため
**軽量版は採らず**、段 2 プラン起草 + 段 3 敵対 2 レンズ + 段 6 敵対レビュー 2 本を立てる。

## 起動時の重複検査 (実測)

2026-08-16 07:50 JST 時点の稼働 worktree (t1112 / t257 / t523 / rulings-20260816 / t1049) と
07:58 時点で追加された t1131 / t1132 / t1140 / t419 のいずれも
`tools/codex_reasoning_ab.py` を編集していない (`git diff --name-only main...HEAD` と
`git status --porcelain` で実測)。編集面は重ならない。

## 段 4 へ持ち越す scope 外の real 所見

- 消費側 `:3090` は `len(meta) != 1` を拒否理由にする。compaction / resume で session_meta 行が
  複数になる親 rollout (実在: `019f690c…`、4 行) は、`_find_rollout` が直っても
  別の理由で拒否され続ける。T-936 の scope 外なので裁定パッケージへ返す。
