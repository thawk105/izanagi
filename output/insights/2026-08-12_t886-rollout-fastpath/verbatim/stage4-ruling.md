# 段 4 裁定 — [T-886] rollout 探索の fast path

親 = dev-wave manager。入力 = brief.md / stage2-plan.md / stage3-sol.md / stage3-luna.md /
premise.json / divergence.json / glob_scaling.json。

---

## §0 親の誤りの撤回 (5 件)

段 3 が崩した親自身の主張を先に撤回する。**以後の記録では撤回後の表現だけを使う。**

- **R1 (撤回)** brief の「受理集合の変化は重複だけ」。**誤り。** fast path は非候補 file を
  開かないため、全走査なら伝播する**未捕捉例外も観測しなくなる**。sol §1・luna §5 が独立に
  同じ反例 (`rollout-0-poison.jsonl` に 10,000 桁整数) を構成した。
  → 正しい表現 = **「非候補 file の重複**および**未捕捉例外を観測しないことによる一方向拡大」**。
- **R2 (撤回)** brief P1「fast path は決して拒否しない」が plan の分岐で成立するという想定。
  **誤り。** plan は `ValidationError` と通常の filesystem failure だけを fallback にしていた。
  sol §2 が `verify_source*=False` 経路で `_verify_rollout_sha` の `read_bytes()` が
  `MemoryError` を出す反例を構成した (現行はその経路で file 全体を読まない)。
  → P1 は **fast attempt 全体を speculative にして初めて成立する**。
- **R3 (撤回)** 「5 呼出 × 4.4s = 約 21.8s が受入全走から消える」。**誤り。** その値は
  **worker 1 個の fixture 1 回**分である (luna §1)。`benchmark_snapshots` は `scope="module"`
  だが xdist worker 間では共有されない。全走 wall の主張には使わない。
- **R4 (撤回)** 裁定パッケージの「比例走査の除去」。**誤り。** `Path.rglob` は archive を
  歩き続ける (親が段 3 前に自己訂正、luna §3 が独立に同結論)。
  → 正しい表現 = **「warm な metadata walk の係数を約 270 倍下げる」**。比例項は残る。
- **R5 (撤回)** premise.json と divergence.json を同一 snapshot の証拠として併記したこと。
  **2,941 file と 2,945 file で別時点である** (sol §3・luna §4 が独立に指摘)。
  → 測定時の corpus manifest を記録し、両者を同一母集団として引用しない。

---

## §1 中心裁定 — 未捕捉例外の迂回 (sol §1 / luna §5、BLOCKER)

**判定: real。認可範囲内であり実装する。ただし記録に明記する。**

理由は 3 つで、いずれも既存の確定裁定に接地している。

1. **必然である。** sol §1 が「回避可能な余分な拡大ではない」ことを論証した — poison が無い
   世界と、未読 file の bytes だけを poison に変えた世界は fast path から同一に見える。
   区別には全 file を読むか信頼済み索引が要り、前者は (a) の否定、後者は裁定 scope 外。
   **ユーザーは (a) を裁定した。(a) を実装する以上この差は不可避である。**
2. **同じ方向をユーザーが既に認可している。** 先行 wave の Q3 で、`_json_lines` →
   `_session_meta_rows` により「無関係な行の病的 bytes で停止していた入力が成功する」変化を
   **(a) 認める**で確定済み。理由 3 点 (正しさゲートではない / 同一性の錨は SHA pin /
   返り path は 1 bit も変わらない) は本件へそのまま妥当する。
3. **正しさゲートではない。** 停止していたのは設計された検査ではなく、無関係 file の
   病的 bytes による偶発例外である。

**ただし brief の記述が狭かったのは親の誤りである (R1)。** worklog・insight・ユーザー報告に
「重複だけでなく未捕捉例外も観測しなくなる」を明示する。ユーザーが不同意なら revert 可能な
単独 commit に保つ。

---

## §2 採用する所見と実装への反映

| # | 出所 | 深刻度 | 判定 | 実装への反映 |
|---|---|---|---|---|
| A1 | sol §2 | BLOCKER | **real・採用** | fast attempt 全体を `try: ... except Exception: pass` で包み、**fallback 本体は catch の外**に置く。`BaseException` は捕捉しない。全走査の例外は握り潰さない |
| A2 | sol §4 | MUST-FIX | **real・採用** | eligibility 判定を**最初**に置く。不成立なら escape・separator 判定・glob へ一切入らず旧全走査へ直行。`thread_id` は `str` 検査しかされておらず UUID 保証がない |
| A3 | luna §6 | MUST-FIX | **real・採用 (親が実測で確認)** | `test_prompt_replacement_count_zero_expected_and_excess:1529` の `lambda *_: rollout` は kwargs を受けず `TypeError`。親が再現確認済み。**seam を `lambda *args, **kwargs:` へ直す。期待値は変えない** |
| A4 | sol §5 | MUST-FIX | **real・採用** | M05 (`len==1`→`>=1`) 用 fixture を「**同一 pinned bytes を持つ名前一致 file 2 本**」にする。結果だけで殺せる |
| A5 | sol §6 | MUST-FIX | **real・採用** | SHA 内部照合の kill を呼出回数でなく**結果**で区別する。fixture = `c` (名前一致・内容一致・SHA 不一致) + `d` (名前不一致・内容一致) → 正実装は `RC_SESSION=21`、M08 は `c` を受理、M09 は SHA mismatch を伝播 |
| A6 | sol §7 / luna §8 | MUST-FIX | **real・採用 (独立 2 例)** | F90 型。tmp candidate を `root/a/b/c/d/e/` の任意深度に置き、別階層へ同内容の非定型名 duplicate を置く。**非再帰 glob / 固定深度 mutant は fallback して duplicate 拒否になる skip 不能な outcome test** |
| A7 | sol §8 | MUST-FIX | **real・採用** | M07 / M12 は既存 gate が先取り → **新規テストの効力に数えない**と明記。M04 は 2 変異へ分割 (pin 存在 / label-id 対応) |
| A8 | luna §7 | MUST-FIX | **real・採用** | 既存 `_find_rollout` テストは全て pinless。pinned 版にも nested / UTF / bad candidate / ValueError / parse count の負例を置く |
| A9 | luna §2 | MUST-FIX | **real・採用** | 測定手順を**事前登録**する (§5) |
| A10 | sol §3 / luna §4 | MUST-FIX | **real・採用 (独立 2 例)** | corpus manifest を記録。「form A = 0 / 2,945」は**当該時点の観測**として書き、仕様・不変条件として書かない |
| A11 | sol §9 / luna §10 | NIT | **real・記録のみ** | fallback は narrow + broad の二重 walk になりうる。SHA も二重読み (**親実測 = pin 5 file 合計 4.91MB / hash 約 7ms**、削減量に対し 0.03% で無視可能)。**正しさのために fallback を候補集合へ狭めない** |
| A12 | luna §9 | MUST-FIX | **一部 refuted** | 「認可が filename duplicate のみなら scope 外」は**誤り**。裁定パッケージ Q1 の逐語は「重複があるが**名前一致の SHA は正しい**入力を、現行は拒否し fast path は受理する」であり、**content duplicate を明示的に指している**。認可範囲内。ただし divergence 同型 fixture の固定は採用 |
| A13 | luna §1 | BLOCKER | **real・採用 (R3)** | 「全走 21.8s 改善」を主張しない。fixture 単位の実測と全走 wall を分けて報告 |
| A14 | luna §3 | BLOCKER | **real・採用 (R4)** | 主張を「warm metadata walk の係数削減」に限定。10 倍規模の外挿値を併記 |

**refuted (実装しない):**

- sol §3 の「述語削除を将来正当化しうる」→ 懸念は妥当だが実装差分ではない。A10 の記録規律で閉じる。
- luna §3 の「真の比例除去には index / path 契約が要る」→ **正しいが本裁定の外** (§3 へ)。

---

## §3 scope 外の real 所見 → 裁定パッケージ (実装しない)

1. **`thread_id` 経路は subagent を産んだ親 session を拒否する** (親の段 1 発見)。
   `_find_rollout` の述語が `id` と `session_id` の**いずれか**一致なので、親 id で引くと
   親本体 + 全子 rollout がヒットし `RC_SESSION` になる。**実 corpus に該当 id が 2 件実在**
   (`019f690c` → 2 file、`019fd52d` → 4 file、いずれも subagent / fork)。
   `:2879` は例外を refusal reason に積むため、codex 子が subagent を産むと正当な作業を
   拒否しうる。**裁定は pin 無し経路の全走査維持を明示しているので触らない。**
2. **真の比例除去** (session-id index または直接解決可能な path 契約、luna §3)。
   本 wave は係数を下げるだけで比例項は残る。

---

## §4 変異事前登録 (DW-M01 / M03 / M04 / M08)

**kill 枠 (受理集合または fail-closed 挙動が変わる)** — 10 件。

| # | 変異 | fixture の要点 | 正実装の結果 | mutant の結果 |
|---|---|---|---|---|
| M1 | 内容照合を削除し名前 + SHA だけで返す | 名前一致・SHA 一致 (pin を monkeypatch)・内容 id は別。別に非定型名の内容一致 file | 全走査へ落ち後者を返す | 前者を返す |
| M2 | `len(candidates) == 1` → `>= 1` | **同一 pinned bytes の名前一致 file 2 本** (A4) | `RC_SESSION=21` | いずれかを受理 |
| M3 | fast path 内の `_verify_rollout_sha` を削除 | `c` 名前一致・内容一致・SHA 不一致 + `d` 非定型名・内容一致 (A5) | `RC_SESSION=21` | `c` を返す |
| M4 | SHA mismatch を fallback せず伝播 | 同上 | `RC_SESSION=21` | `RC_SNAPSHOT` sha mismatch |
| M5 | eligibility の **pin 存在**検査を削除 | pinless 相当 + 内容 duplicate | `RC_SESSION=21` | 受理 |
| M6 | eligibility の **label-id 対応**検査を削除 | label A の pin を session B の名前一致 bytes へ cross-wire、B に内容 duplicate (A7) | `RC_SESSION=21` | 受理 |
| M7 | `rglob` → 非再帰 `glob` (または固定深度) | candidate を `root/a/b/c/d/e/`、別階層に同内容 duplicate (A6) | candidate を短絡 | fallback して `RC_SESSION=21` |
| M8 | fast return の `.resolve()` を外す | sessions root 外への file symlink | resolved target | symlink path |
| M9 | fallback を glob 候補だけに狭める | glob 0 件・非定型名に内容一致 | それを返す | `RC_SESSION=21` |
| M10 | `except Exception` を narrow catch へ戻す (A1 の逆) | candidate を `chmod 000` (実 chmod。monkeypatch 不可) + 非定型名に内容一致 | fallback して後者を返す | `PermissionError` 伝播 |

**diagnostic sensitivity pin 枠 (受理集合を変えない。DW-M08 に従い kill に数えない)** — 3 件。

| # | 変異 | 検出手段 |
|---|---|---|
| P1 | fast path ブロックを削除 (常に全走査) | 候補 probe 回数 |
| P2 | `derive_independent_golden` から `pinned_label` を外す | 配線 assert |
| P3 | `render_prompt` で `verify_source=True` のときだけ label を渡す | 配線 assert |

**登録しない (既存 gate が先取り、A7)** — `payload.id` のみ化 (既存 encoding テスト)、
`_session_meta_rows` の catch 拡大 (既存 ValueError テスト)。**新規テストの効力に数えない。**

期待 node は **fix 後の最終 commit で完全集合を再導出する** (DW-M07、memory の実害 2 例)。

---

## §5 測定手順の事前登録 (A9 / A13 / A14)

- **主要指標 = fixture 単位の `_find_rollout` 実費**。同一 checkout・同一 login node で
  before/after を**連続**して測り、**順序を counterbalance** する (A→B / B→A の 2 走)。
- **全走 wall は別系列**として受入全走の値だけを引用し、fixture 実測から外挿しない (R3)。
- 測定時に corpus manifest (file 数・総 bytes・測定時刻) を記録する (A10 / R5)。
- cold cache 倍率は**測定できないので報告しない** (両レンズが独立に「算出不能」と判定)。
- 主張の定型 = 「warm metadata walk の係数を約 N 倍削減。比例項は残る」(R4)。

---

## §6 段 5 への指示 (実装 scope)

**編集してよい 2 file だけ:**
- `tools/codex_reasoning_ab.py` — `_find_rollout` 周辺と 2 呼出元の配線のみ
- `orchestrator/tests/test_codex_reasoning_ab.py` — 新規テスト + A3 の seam 修正のみ

**実装してはならない:** `:2879` の `thread_id` 経路、フラグ既定値、外側 `_verify_rollout_sha`
の削除・条件化、`_session_meta_rows` の走査・例外境界、RC 値・既存 failure message、
docs・pin 値・commit。
