# 段 1 brief — [T-665] + [T-662] 起動値束縛の設計 wave

wave = `dev-wave-t665-t662-launch-binding` / branch = `worktree-dev-wave-t665-t662-launch-binding`
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t665-t662-launch-binding`
base commit = `3ae4856c` (local main と同一、clean、submodule 初期化済み)

## scope

**設計のみ。実装しない。** dev-wave が起動する codex 子の **model (`-m`)** と **reasoning effort** を
docs の権威行と機械照合する層について、**launcher 集約 / receipt 事後検査**の設計択一を
裁定パッケージで返す。[T-662] (model) と [T-665] (段 6 の effort) を束ねる。
**scope 外:** served model の attest (F56、[T-189] 所有)、A/B の evidence ([T-595])、docs pin の対象拡大 ([T-667] 見送り済み)。

## 確定済みユーザー裁定 (一次資料 = `rulings-inbox/2026-08-04-rulings-session-5rulings.md`)

- §47「**[T-665]/[T-662] = 束ねた設計 wave 起票可** (launcher 集約か receipt 事後検査かをパッケージで返す)」
- §47「**[T-667] = 見送りで終端**」 — docs pin の対象を広げる案は否定済み。再提案しない。
- §45「**[T-658] = 見送り** (受領証の全書込み口配線は防御的堅牢化、再訪 = durable receipt の実需)」 —
  網羅配線それ自体を目的にしない。実需を示せる範囲だけを設計する。
- D207 / D243 = 段 2・3 は `reasoning=max`、段 6 (DW-S06-A / DW-S06-C) は `reasoning=high`。

## 段 1 実測 (すべて本 worktree で本日測定。docs は根拠にしていない)

1. `hooks/guard_bash.py` / `hooks/guard_agent.py` に文字列 `codex` は **0 件** →
   Bash の PreToolUse は codex の argv を一切見ていない ([T-662] の前提を確認)。
2. `tools/codex_worker_launch.py` を参照する非 output ファイルは
   `orchestrator/tests/test_codex_worker_launch.py` **のみ** → production caller は依然 0 件
   ([T-595] 裁定 3-1 を再測で確認)。
3. `tools/check_docs.py:265-322` が pin するのは docs の literal だけ
   (DW-O01 の model 権威行、DW-S02/S03/S06-A/S06-C の `reasoning=` literal)。
4. **素の `codex exec` も実効値を機械可読に残す** (`~/.codex/sessions/2026/08/08/rollout-*-<session_id>.jsonl` を実読):
   `turn_context.payload.model="gpt-5.6-sol"` / `.effort="max"` / `.sandbox_policy` / `.cwd`、
   `session_meta.payload.cwd` = wave worktree 絶対パス、`originator="codex_exec"`、`cli_version="0.146.0"`、
   `session_id`。prompt 全文も `event_msg/user_message` に残る。保持は 2026/07 から現在まで (回転で消えていない)。
   seam: `CODEX_HOME` 未設定 → 既定 `~/.codex/sessions`。launcher も同じ既定を使う (`codex_worker_launch.py:2575-2581`)。
5. **cwd による wave 帰属には穴がある。** 2026-08-08 の rollout を cwd 別に集計すると、wave worktree 名
   (`dev-wave-t627-noop-binding` 等) のほかに `dw-t181-fix3` (2 件) と `dw-t181-merge` (1 件) がある。
   段 6 fix は `DW-S05-A`/`DW-S06-B` により**別 worktree**で走るため、wave worktree だけを filter する
   事後検査は**段 6 fix 子を取りこぼす** — これは [T-665] の本丸そのもの。
6. 先例: `tools/collect_wave_usage.py` は `--cwd-under` で **Claude 側** session log を段 9 に事後収集する。
   codex 側の同等物は存在しない。`tools/check_codex_agents.py` は adapter の静的契約検査で、起動 argv は見ない。
7. **docs 予算の残**: dev-wave aggregate = 25,184 / 25,200 (**残 16 bytes**)、
   `.claude/commands/dev-wave.md` = 9,457 / 9,500 (**残 43 bytes**)。契約文の純増余地はほぼ無い。

## 既存被覆と純増検出力 (性質で検索した結果)

性質「**起動された子の model / effort が権威と一致すること**」を検査する既存機構:
docs literal pin (docs の文面だけ)、launcher の要求↔実効一致検査 (production 未使用)、
`check_codex_agents.py` (Claude named agent の静的契約)。
→ **実起動値に対する検査は 0 件。純増検出力 = 実効 model / effort の権威不一致を検出する能力 (現在ゼロ)。**

## 不変条件

- 実装差分ゼロ。段 5・6 を飛ばし `4→7→8→9`。台帳は `docs/spool/` fragment。insights は直接書く。
- 権威の単一性を壊さない。model の正本は `DW-O01`、effort の正本は各 worker 節。二重正本を作らない。
- 正しさゲートを緩める案・網羅配線を目的化する案は提案しない ([T-658] 裁定)。
- push しない。local main 取り込みは段 9 の `DW-O23` のみ。

## 成果物の形

`output/insights/2026-08-08_t665-t662-launch-binding/` に
(a) 裁定パッケージ `package.md` (R1..Rn の択一 + 親推奨 + 各案の取りこぼし率・予算コスト)、
(b) 逐語 (`s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-adjudication.md`)。
worklog / decisions は spool fragment。

## provisional 裁定 (親の暫定判断であり攻撃対象)

- **(P1)** 択一は 2 案でなく **3 案**に整理できる。A=**launcher 集約** (`DW-O01` の実行雛形を
  launcher 経由へ置換し、段から model/effort を導出させる)。B=**receipt 事後検査** (起動側は不変。
  段 9 で rollout jsonl を走査し権威と照合)。C=**宣言 + 事後照合** (親が投入前に
  stage/model/effort/成果物 path を wave-local manifest へ宣言し、段 9 で rollout と突合)。
- **(P2)** trust root は 3 案とも **self-attest** (同一 account が書換可能) であり、
  trust の強さでは択一を決められない。決め手は **(i) 取りこぼし率** と **(ii) docs 予算コスト**。
- **(P3)** 最大の取りこぼし源は段 6 fix 子の別 worktree cwd (実測 5)。A は起動口を 1 本にするので
  構造的に閉じ、B は cwd 列挙の網羅性に依存する。C は宣言漏れが検出できるかが分かれ目。
- **(P4)** docs 予算残 16 bytes は、いずれの案でも契約文の純増を許さない。
  予算捻出 ([T-664]) が **前提条件**であり、本 wave はそれを解かない。
- **(P5)** [T-662] と [T-665] は同一機構で同時に閉じる (model と effort は同じ `turn_context`、同じ argv)。
  別々に実装する案は取らない。
- **(P6)** 段 3 は 2 本で model が異なる (sol → luna) ため、権威は「段 → 単一値」ではなく
  「段 → 期待多重集合」で表現する必要がある。

## 段 1 追記 (brief 後・段 2 投入後に判明した新事実。段 4 で再裁定する)

`s1-measurements.md` の実測 F〜J を参照。要点だけ:

- **F**: `tools/codex_worker_ledger.py` が rollout から model/reasoning を既に決定的に集計する
  (`--cwd-contains` / `--manifest` exact selector / `--stage-map` / `--strict`)。
  **欠けているのは「権威と突き合わせる」層だけ**である。
- **G**: その stage 分類は prompt 先頭行の文言正規表現に束縛されており、
  実測で 33 session 中 30 が `unclassified`。**既に drift で壊れている**。
- **H**: `--cwd-contains` は別 wave・別 checkout まで拾う (33 件中 20 件が別 wave)。
- **I**: F56 が「不正 effort 値は rc=0 で通り rollout に記録される」を実測済み。
  **恒久対応は「起動前に落とす」**と書かれており、純粋な事後検査では満たせない。
- **J**: `docs/phase3.md:694` は **stage matrix の所有を [T-184]** と明記。
  本 wave が段→期待値の写像を新規定義すると所有を侵す。

→ **(P1) の 3 案は「新規実装」ではなく「既存 3 部品 (収集層・selector・権威行) の結線」**として
再定式化すべき可能性が高い。段 4 で裁定する。

## 並列分割方針

段 2 = codex 1 本 (`gpt-5.6-sol`、`reasoning=max`、`sandbox=read-only`)。
段 3 = 2 本並列 (レンズ A = `gpt-5.6-sol`、レンズ B = `gpt-5.6-luna`、いずれも `reasoning=max`、read-only)。
実装子なし (実装しないため)。
