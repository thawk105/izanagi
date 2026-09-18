# 段 4 裁定 — [T-2746] (2026-09-18 06:58 JST)

裁定 inbox 再走査: wave 開始後の更新なし。main 先端 d2ebef7a4 のまま。

## 実走 (scope A) の状態

- attempt-0001 `4947.nqsv`: **親の操作ミス**で job body preflight 拒否 (`allocation qstat evidence is not fresh`、
  Elapse 7 秒、driver 未起動、campaign 未接触)。
- attempt-0002 `4954.nqsv`: `driver_rc=0`、variant `3dec27291054` (BACKOFF_FIXED=25)、`serializable` / `certified=true` /
  anomalies 0 (commits 445394 / aborts 71877)、median 687508.5 tps (`[692403, 682614]`、CV 1.0068%、settled)、
  abort 率 7.4% (T-2702 集約)、llc/ipc 欠測、`1 committed`、停止判定 **`continue`**、Elapse 432 秒。
- **投入は 2 本、評価は 1 本。** 相談 A#6 (real): 文言上の「再投入なし」からの逸脱として記録し、「再測定・再抽選ではない」と
  「再投入禁止への適合」を分ける。裁定本文は書き換えない。一般規則は設計しない。**裁定パッケージ候補 (事後承認)** として返す。
  親判断で継続する理由: 評価は 1 本しか走っておらず、preflight 拒否は測定・抽選のどちらでもない。
- `continue` により critic 1 回 → planner-3 / coder-3 各 1 回 → proposal-3 保存 (評価しない)。**3 巡目へ進まない。**

## 所見の裁定 (real / refuted、採否)

| # | 出所 | 判定 | 採否・処置 |
|---|---|---|---|
| A1 | `input_sha256` は実入力の証明でなく申告 JSON の hash | real | 採用。契約に「呼出し側が実入力として申告した保存 JSON の canonical hash」と明記、`mode` は記録方式。provenance に任意 `prompt_path` / `prompt_sha256` を足す |
| A2 | stage・入力・出力・WAL・digest の対応検査が閉じていない | real | 採用。取込み口で (i) stage↔output-key の対応、(ii) role 出力 schema (planner 5 key / coder K2 envelope or proposal)、(iii) `input_sha256` は harness が指定 file から再計算 (呼出し側は渡せない)、(iv) K2 `knowledge_input.knowledge_manifest_sha256` が campaign 受領証の digest と一致、(v) critic の `digest_sha256` は `--agent-digest` の bytes から再計算し入力 JSON 内の値とも一致、(vi) critic の `variant` は WAL に実在、を fails-closed |
| A3 | 入力側防壁テストが 3 関数だけ | real | 採用。`_prepare_knowledge_campaign` と planner-context 入口までを対象に含め、AO reader が入力生成経路で呼ばれたら失敗する検査 + 上流 helper が AO を読む変異で赤 |
| A4 | coder-2 実入力欠落のまま AO 5 件で固定 | real | 採用。**4 event を取り込み**、coder-2 の欠落を明記。`input_sha256: null` も再構成入力も採らない。件数式は `W + 1 + 4` |
| A5/B2 | brief の非 null delta・whiteboard 2 件が現行防壁に反する | real | 採用。brief を訂正 (delta は `_DELTA_PCT_LIVE=False` で null、本 campaign の whiteboard は 1 件)。非主張に「機序仮説は LLM の帰属記録であり機序の実証ではない」を追加 |
| A6 | attempt-0002 は「再投入なし」からの逸脱 | real | 採用 (上記) |
| A7 | AO 追加で admission 束縛が変わる | refuted | 取込み前後で WAL・lock・loop_state・digest・knowledge receipt の bytes 不変を親が実測し、テストにも置く |
| A8 | proposal-3 の variant 衝突 | refuted | `variant=null` 維持。非 null 指定は WAL 実在を要求 (A2-vi) |
| A9 | critic 節抽出が role 契約に反する | refuted | 見出し指定を保存入力に含めた (`critic-input-2.json` の `output_format_request`)。抽出は原文の範囲選択のみ、欠落・重複見出しは拒否、読取り時に raw から再抽出して一致検査 |
| A10 | 取込み口が「harness だけが書く」に違反 | refuted | A1/A2 の整合検査と主張限定で足りる |
| B1 | `commit_witness` の null 許容は verify_done の値域と不一致 | real | 採用。verification 用は両 count とも integer、property は optional |
| B3 | 件数式だけで取込み完了と双射を結ばない | real | 採用。renderer の期待側は report と独立に読んだ AO Counter。親の受入で各原本 (stage・入力 hash・出力全文・provenance) と AO を照合 |
| B4 | 変異候補の単一理由化 | real | 採用。下の事前登録表に反映 |
| B5 | 一次配置と view の二重計数 | refuted | plan どおり |
| B6 | `proof_surfaces` enum | refuted | X/P/I は 3 値 enum、`protocol` は string \| null |
| B7 | 較正不在で render 停止 | refuted | floor は `null` + `no-matching-env-record` で進む |
| B8 | 受入 5 分超過 | 未実測 | 最小 fixture。親が受入 wall を測る |
| B9 | pin 閉包の不足 | refuted (一覧は補完) | `conftest.py:329,492`、`test_real_repo_serialization.py:3310` を受入範囲に足す |
| B10 | v1 全文 reader と保存済み report の fresh 比較 (`autonomous_trial_completeness.py:4652-4721`) | real・scope 外 | **裁定パッケージ候補** 2 件。本 wave では解決済みとしない。旧 report の再生成・SHA 差替えはしない |

## plan v2 (契約の確定。plan.md `## 契約` を次で上書き)

- **新 module `orchestrator/campaign/agent_outputs.py` (単位 A0 が所有)**: `AgentOutputError(ValueError)`、
  `STAGES = ("planner_proposed", "coder_proposed", "critic_attributed")`、`canonical_bytes(obj)` / `canonical_sha256(obj)`
  (UTF-8、`sort_keys=True`、`ensure_ascii=False`、`separators=(",", ":")`、非有限数拒否)、
  `validate_envelope(env) -> None` (exact 5 key、stage 白名簿、variant str|null (critic は str)、env_tag str、ts 有限 float、
  payload 必須 key、provenance 必須 key、critic の output 5 key)、`read_agent_outputs(path) -> list[dict]`
  (存在判定は呼出側、空行・未終端最終行・不正 UTF-8・duplicate key・不正 JSON・envelope 違反・完全重複・semantic 重複
  (`stage + input_sha256 + canonical(output)`) は例外)、`append_agent_output(path, env) -> str` (flock 内で既存全行検査 →
  重複検査 → 1 行 append → fsync file + dir、canonical sha256 を返す)。`wal.py` は編集しない。
- `layout.py`: `CampaignLayout.agent_outputs_file` property (A0 所有)。
- **envelope**: `{ts, stage, variant, env_tag, payload}`。payload 必須 = `output` (役割出力全文)、`input_sha256` (申告入力 JSON の canonical sha)、
  `provenance` (`mode` ∈ {live, ingested}、`source_path`、`source_sha256`、`input_path`、`input_file_sha256`、任意 `prompt_path` / `prompt_sha256`)、
  `refs` (`wal:` ref の配列、実在検査は renderer)。critic 追加必須 = `digest_sha256`、`output` = `{raw_markdown, attribution, recommend, avoid, uncertainty}`。
- **harness (単位 A1、`p3_s4_loop.py` + `test_p3_s4_loop.py`)**: (a) live 経路 `--agent-inputs INPUTS.json` (`{planner, coder}` の実入力) 指定時に
  `drive_iteration` の入口停止後・`_run_one_iteration_resolved` 前に planner/coder 2 event を live 追記 (variant null)。未指定は互換 (記録なし)。
  (b) 取込み口 `--record-agent-output {stage} FILE --agent-campaign-dir DIR --agent-input INPUT.json [--agent-output-key {planner,coder}]
  [--agent-variant V] [--agent-digest FILE] [--agent-wal-ref wal:SHA ...] [--agent-prompt FILE]`、`main` の parse 直後に専用分岐、
  評価用 option と排他、site 解決より前に return (login で呼べる)。`env_tag` は対象 campaign の WAL/lock から。A2 の整合検査 (i)〜(vi)。
  (c) 入力側防壁テスト (A3)。(d) 取込み前後で WAL・lock・loop_state・digest・receipt bytes 不変のテスト。
- **renderer (単位 A2、`layer3_report.py` + `layer3_schema.json` + `test_layer3_report.py`)**: `canonical_record_ref` に `ao`、
  `agent_outputs` 区画 (3 stage 全 envelope を一次配置)、`mechanism_hypotheses` = critic の二次 view `{variant, attribution, source_ref, refs, digest_sha256}`、
  `mechanism_hypotheses_provenance` ∈ {absent, agent_outputs}、双射の期待側は独立に読んだ AO Counter、view は独立再射影と一致、
  `refs` は WAL ref に実在、critic variant は WAL variant に実在、`raw_markdown` からの再抽出が `attribution` 等と一致。
  schema: `verifications.items` に `commit_witness` (integer 2 key) / `proof_surfaces` (protocol string|null、X/P/I 3 値) を optional 追加、
  `mechanism_hypotheses` items 定義、`agent_outputs` / `mechanism_hypotheses_provenance` optional (新 renderer は常に発行)、
  source-ref pattern `^(wal|wb|ao):[0-9a-f]{64}$`、`schema_version` v3 据え置き、top-level `required` 不変。docstring 12 行目更新。
- 不変: `test_t126_pegasus_tools.py` の exact 文字列 (764 / 800 / 843 行相当)、`_validate_schema`→`validate_perf_observation`、
  `run_campaign` 呼出し 1 本、`_git_head` の spawn 1 本、`test_layer3_report.py:439,1820` の fixture。hooks 変更なし。

## 変異の事前登録 (段 6 で spec 化、B4 の照準を反映)

| id | 述語 (壊すと赤) | 単一理由の照準 |
|---|---|---|
| M1 | reader の stage 白名簿 | `read_agent_outputs` 直接負例 (schema enum とは別 test) |
| M2 | 未終端最終行の拒否 | AO reader の framing 経路 (wal.iter_lines を流用するなら AO 側の呼出しを変異) |
| M3 | semantic 重複 (ts だけ変えた再取込み) | canonical envelope hash が異なる正例で重複判定を外す |
| M4 | planner/coder を一次配置から落とす | report 本体と `source_refs` を同時に欠落形へ、入力 Counter 不変 |
| M5 | critic view の一次走査混入 (二重計数) | `_report_primary_refs` が view を走査する変異 |
| M6 | 期待 Counter を report 側から作る | planner/coder の有効 envelope を等件数置換し `source_refs` も揃える |
| M7 | view の別 critic 付替え | 有効 critic 2 件で view 対応だけ入替え |
| M8 | 不在時 provenance | 不在で `"agent_outputs"` を発行する変異 |
| M9 | 入力 builder が AO を読む | `planner_context_payload` / `_prepare_knowledge_campaign` に reader 呼出しを足す変異 |
| M10a | K2 外側 metadata の欠落 | output から `knowledge_use` 等を落とす変異 |
| M10b | `input_sha256` を出力 hash に替える | 取込み口の計算元を替える変異 |
| M11 | verification の `commit_witness` integer 型 | schema の integer → `["integer","null"]` |
| M0 | 等価 (positive) | コメント変更、SURVIVED 期待 |

## 記録の scope

insight `output/insights/2026-09-18/t2746-k2-loop-round2/` (README・materials・verbatim・evidence 射影・layer3 材料レポート)、
spool fragment (worklog、T-2681 の見送り解除、失敗台帳は attempt-0001 を F 候補として段 8 で routing)、
裁定パッケージ候補 3 件 (attempt-0002 の事後承認、v1 reader、保存済み report の fresh 比較)。
