単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s1-brief.md` — 親 brief (scope、成果物影響、不変条件、実アンカー表、provisional 裁定 (P1)〜(P5))
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/c1a-s4-adjudication.md` — **直前 wave (C1a) の段 4 裁定。3 節が terminal 証拠の契約 v2 の正本 (exact 24 field の表、cross-field 不変条件、再導出 6 枝、E2 の 4 語、crash 後の権威)、5 節が C1b / C2 / D2 の境界、6 節が裁定パッケージ**。本 plan はこの契約を再設計せず実体化する
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/c1a-README.md` — C1a の成果 (起動層の raw facts 面) と閉じていない窓 7 節、裁定パッケージ 8 節、次 wave の出発点 9 節
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/decisions-verbatim.md` — 確定裁定の逐語 (特に D1113 / D1114 / D1341 / D1522 / D1533)

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` である。コードはすべてこの worktree の中を読む。base commit は本 branch の HEAD `9c1951179` で、C1a の実装 `35ba02e1a` と local main `086694d8c` の両方を含む。

## 依頼

単位 C の第 2 checkpoint **C1b** の実装プランを file:line 粒度で起草せよ。scope は次の 4 つである。

1. **contract leaf の新設** `orchestrator/campaign/s8b_terminal_evidence.py`: 契約 v2 の exact 24 field を持つ frozen dataclass、launcher 私有の issuer `seal_terminal_evidence(reservation, opened, terminal)`、consumer 側の `require_sealed_terminal_evidence(value) -> ValidatedTerminalEvidence`、E1 再導出 (campaign と同順の 6 枝) の pure 関数、canonical bytes と digest。
2. **profile の開放** `s8b_attempt_profile.py`: `_reject_unsealed_s8b_v2_terminal` (`:556-563`) を封印証拠を要求する validator へ、`S8B_V2_RETRYABLE_FAILURE_REASONS` (`:533`、現在は空 frozenset) に E2 の 4 語を入れる。
3. **core の capability 経路** `attempt_registry_core.py`: `terminal_row_validator` (`:214`、呼出し `:1407-1408`) が証拠を受け取れる形。`record_attempt_terminal` (`:1971-2031`) の受理集合をどう変えるか。
4. **adapter の封印 API** `s8b_attempt_registry.py`: `record_sealed_attempt_terminal(observation, evidence)` の新設 (`record_attempt_terminal :2544` の隣)、証拠文書の create-only 公開 (`floor-attempt-registry-receipts/terminal-evidence/<digest>.json`)、terminal 行への `terminal_evidence_sha256` 束縛。

**C2 (campaign `_Runner._run_session` の launcher 配線、producer capture、`RESULT_SCHEMA` v5 切替、resume) と D2 (consumer 3 面) は実装しない。** 境界 (symbol・引数・戻り型) だけを固定する。

## 起草の要件

- **file:line 粒度**で、新設 symbol は signature と field 集合、既存 symbol は現行の行と変更後の形を書く。行番号は現物で確かめて書く (推測しない)。
- **規模を実測して見積もれ。** leaf / profile / core / adapter / 各 test の追加行数を別々に。C1a の実績は production +245 / test +567 で、実装子 1 本・fix 3 巡だった。
- **(P1) の分割を評価せよ。** 親案は「leaf を 1 本目で固定 → unit1 (launcher 側の発行 + launcher test) と unit2 (core + profile + adapter + その test) を並列」の実装子 3 本・依存 1 段である。規模が上限を超えるなら、どこで切るか (leaf のみ / leaf + unit1 / leaf + unit2) を根拠付きで提案せよ。**切った場合に v2 terminal が開かないままになる点を明示すること。**
- **(P2) を現物で確かめよ。** `campaign_record` の exact key 集合は `s8b_floor_campaign.py` の `_finish_session` (`:6346`) が emit する現物から取る。親は 29 語を数えたが裁定 3 節は「27 key」と書いている。どちらが正しいか、`records` や `event` のような枠外 key を含むかを判定せよ。
- **(P3) 到達性 (DW-O13)。** `launch_floor_attempt()` の production 呼び手は 0 件である。したがって 24 field の値域を実環境で実測できない。**どの field が「C2 が供給するまで値域不明」なのかを列挙し、その field に対して本 wave で置ける述語の強さを判定せよ。** 到達不能な値を要求する述語は採用しない。
- **(P5) pin 閉包。** 新しい成果物名 (`terminal-evidence` の path 断片、schema literal `s8b-floor-terminal-evidence/v1`、新 field 名 `terminal_evidence_sha256`) を key にして `git grep` し、bytes を pin する台帳・test・trust root を全列挙せよ。path 検索だけで 0 件と結論しない。
- **既存の受理集合をどう変えるか**を、v1 / v2 それぞれについて「変わる点」と「変わらない点」に分けて書け。v1 の event key 集合と受理集合は不変でなければならない。
- **変異候補を 12〜18 件**挙げよ。各候補に (a) 変異箇所 (file: symbol)、(b) KILLED を期待する node の性質、(c) 他の gate に遮られない理由、を書く。
- 各主張に **[実測] / [推測]** を付けろ。行番号・件数・key 集合は必ず [実測] にする。

## 制約

- 読取専用である。実装しない。pytest を走らせない (走らせられない)。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、(P1)〜(P5) の採否、規模の見積り、実装子の本数と所有 file、変異候補の件数を 12 行以内で書け。
