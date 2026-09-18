---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2746-k2-loop-round2
seq: 2
---

## {{D:layer3-mechanism-layer-v3-agent-outputs}}. 層 3 機序仮説層 v3 は `runs/agent_outputs.jsonl` を loop harness の 2 口 (live / 取込み) だけが書き、renderer は critic の帰属記録を非 certifying の二次 view として決定論射影する — schema 版は v3 据え置き

**決定:** `output/insights/2026-07-16_layer3-mechanism-wiring-design.md` §2 を次の契約で実装した (wave
`dev-wave-t2746-k2-loop-round2`、見送り台帳の「層 3 機序仮説層 (v3) を実装する」項の着手条件 = agent 出力を生む loop 再走が
D2120 項 1 の 2 巡目で成立)。

1. **永続面** `runs/agent_outputs.jsonl` (append-only、WAL 同形 envelope `{ts, stage, variant, env_tag, payload}`、stage は
   `planner_proposed` / `coder_proposed` / `critic_attributed` の 3 種のみ)。reader / writer / 検証は
   `orchestrator/campaign/agent_outputs.py` (空行・未終端最終行・不正 UTF-8・duplicate key・完全重複・semantic 重複
   (`stage + input_sha256 + canonical(output)`) を fails-closed、flock 内で既存検査 → 単一 write → file/dir fsync)。
   `runs/` 配下は `guard_write` の既存判定で防護済み (hooks は変えない)。
2. **書き手は loop harness だけ。** 2 口を持つ: (a) live = `--run-iteration --agent-inputs` 指定時に `drive_iteration` の入口停止後・
   評価前に planner / coder を追記 (variant null)、(b) 取込み = `--record-agent-output STAGE FILE --agent-campaign-dir DIR --agent-input INPUT.json`
   (harness の外で生まれた役割出力を取り込む口。critic は常にこれ。site 解決より前に return し login で呼べる)。取込み口は
   stage↔出力の対応・役割 schema・K2 manifest digest と受領証の一致・critic digest の一致・variant の WAL 実在・`--agent-wal-ref` の実在を
   fails-closed で検査し、`input_sha256` は harness が指定入力 JSON から計算する (呼出し側から値を渡す口は作らない)。
3. **provenance の意味は申告である。** `mode` は記録方式 (live / ingested)、`ts` は記録時刻、`input_sha256` は呼出し側が実入力として申告した
   保存 JSON の canonical sha256、`prompt_sha256` は指定 file の bytes sha256 であり、いずれも役割への実送達の証明ではない。
   docstring と schema description に明記する。
4. **critic の 4 節** (`## attribution` / `## recommend` / `## avoid` / `## uncertainty`、各ちょうど 1 回) は
   `agent_outputs.extract_critic_sections` が原文の範囲選択 (見出し行の次行から次の unfenced `## ` 直前まで、前後空白 strip、
   fenced code block 内の行は見出し候補から除外) で抽出し、harness の保存と renderer の再抽出が同じ関数を使う。`raw_markdown` 全文を併記する。
5. **入力側防壁は不変。** `planner_context_payload` / `whiteboard_for_planner` / `project_whiteboard` / `_prepare_knowledge_campaign` は
   `agent_outputs` を読む API を持たない (実行検査・3 状態不変・AST の 3 本で固定)。v3 は報告層の記録であり、critic 診断を次生成の
   型付き入力へ還流する経路ではない。
6. **renderer** (`layer3_report.py`) は AO を whiteboard と独立に読み、全 envelope を `agent_outputs` 区画へ一次配置し、`critic_attributed` だけを
   `mechanism_hypotheses` (`variant` / `attribution` 逐語 / `source_ref: ao:<canonical sha256>` / `refs` / `digest_sha256`) へ決定論射影する。
   双射の期待側は report と独立に読んだ AO の Counter、view は独立再射影と exact 一致、`refs` は一次 WAL ref に実在、非 null variant は
   対象 WAL の任意 stage に実在 (harness と同条件)。不在は `mechanism_hypotheses_provenance = absent`、存在は `agent_outputs`。
   数値・verdict・参照を attribution の文章から作らない。`certifying_input=false` / `acceptance_receipt=null` の既定は変えない。
7. **schema は `layer3-material-report/v3` 据え置き** (D828 の同型: optional property の追加と `mechanism_hypotheses` の `maxItems: 0` 解除、
   top-level `required` 不変)。`verifications.items` に producer の現行 key `commit_witness` (integer 2 key) と `proof_surfaces`
   (X/P/I 3 値 enum、protocol string|null) を optional で足す (D829: view で消さない)。閉包検査は producer の AnnAssign と `update` /
   添字代入、`_view_row` の除外集合 (exact 2 key を pin)、qualification 分岐の key を AST で導出する (D830)。

**理由:**
- 設計文書の「v3 で bump」は identifier が admission 導入 (a21bf413e) で消費済みのため据え置きにし、v4 は作らない (D828 が前方互換を
  保証しないと定めた射程内)。
- 現行 renderer は `verify_done` の `commit_witness` (ee81c4311、2026-08-11) と `proof_surfaces` (e4c949f08、2026-09-03) を schema に持たず
  本 loop 型の campaign を描画できなかった。v3 の材料はこの受理が前提である。
- 1 巡目の記録で「critic の診断は次生成の型付き入力へ届かない」ことが実測されており、v3 はその欠落を報告層の記録として埋めるもので、
  入力側へ還流する機構ではない (規律 2/6 の入力側防壁を保つ)。

**却下した選択肢:**
- 未評価 proposal の `variant` に `diffq_variant_id` を流用する — reject / 評価済み variant との誤認を生むため `null` にした。
- 実入力が保存されていない役割出力を `input_sha256: null` や再構成入力で取り込む — 規律 6 と provenance を濁すため採らず、取込み不能として記録する。
- 取込み口を「harness だけが書く」違反として作らない — 設計条件は永続面の書き手と生成入力経路の分離であり、外部出力の受領を禁じていない。
- `mechanism_hypotheses` を機序の証拠として扱う — LLM の帰属記録であり、改善の実証・certified 選択には使わない。

一次資料: `output/insights/2026-09-18/t2746-k2-loop-round2/README.md`。
