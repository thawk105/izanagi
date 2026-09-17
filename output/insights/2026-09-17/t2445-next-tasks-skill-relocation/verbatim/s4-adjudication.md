# 段 4 裁定 (親) — dev-wave-t2445-next-tasks-skill-relocation

## 裁定 inbox の再走査

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` と main (`b4631a92e`) の decisions.md を再読。wave 開始後の
関連更新は「第 20 回 /rulings 項 37 の fold (D2104)」のみ。新事実として brief を補正済み。

## 引数の前提を覆す新事実 → 再裁定

- 「checker 側は登録済み」は command の予算・interface pin のこと。D1890 (1) / T-2680 (entry 1538) の**終端 pin**
  `REQUIRED_SELF_HEADINGS[3]` に next-tasks は無い (レンズ A が現物で追認、反証なし)。
- 契約文書 5,999 / 6,000 bytes、既存 3 skill は個別 guard 登録 (レンズ A 追認)。
- **裁定:** `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` への最小登録を Codex author で行う
  (P3 採用)。これは既存 gate の 4 件目への登録であり新設ではない (DW-O13 の「新設」に当たらない)。
  「docs / skill 文書のみ」は候補生成ロジック・追加ガードレール・next-tasks 実行を含めないという scope の
  限定として保ち、checker 登録は裁定 2 件 (D1890 (1)、D2104 項 37) の中身として scope 内とする。

## レンズ A (受理集合・恒真 pin)

| # | 判定 | 採否 |
|---|---|---|
| 1 fixture 変更漏れ | refuted | plan どおり合成 self_doc へ `### next-tasks` を足す |
| 2 growth hold で実 repo 検査は通常走で省略 | real | 親が `python3 tools/check_docs.py` を実走し、pytest 緑と別に記録する (受入分離を維持) |
| 3 literals・予算・YAML | refuted | — |
| 4 SELF_LIMITS 超過 | refuted (nit: LF 計数規約) | 親案は 5,997 bytes。計数は末尾 LF 込みの file 全体 bytes で書く |
| 5 routing / 既存 pin 破壊 | refuted | — |
| 6 command 既存契約違反 | refuted | exact byte pin は author が新現物 26,950 へ更新 |
| 7 変異の専属性 | refuted (実走未) | 段 6 で expected node を probe → 本走で照合 |
| 8 実測値の一般化 | refuted (nit: D744 の射程) | D744 の射程は SKILL.md と `agents/*.yaml` に限定して書く |

## レンズ B (義務落ち・意味保存)

| # | 判定 | 採否 |
|---|---|---|
| 1 D2051 の主体対応・文責 | **real (must-fix)** | 採用。adapter に「D2051 は Claude 起動が前提。Codex 起動時の対応付けは本 Skill の設計判断であり再掲ではない」と明記し、事実 = 起動主体 (Codex) の実測、選定判断 = Codex、Claude の見解 = 独立検査、Claude が挙げた/未確認の候補は実測せずに外さない、2 巡目 1 回、3 巡目なし、件数合わせ禁止、文責 = 起動主体、を箇条書きで固定。plan の「事実は Claude」は不採用 (相談先は read-only・15 分・裏取り 3 件の制約下で事実の権威になれない。D2051 の理由 = repo を実測できる側が事実を持つ)。新 D として記録 |
| 2 不一致明記の複製要否 | refuted | command から辿れる。adapter は「不一致の明記は command に従う」の 1 句のみ |
| 3 旧版だけの義務 | **real (must-fix)** | 採用。Codex overlay 節「Codex 側で保持する出力の義務」に 5 件 (投げ文の自己改善終端、CC 不採用の理由、既存 patch・OID・handoff の束ね、補助 artifact・検証済み単独行、半角番号) を収容。Claude command は拡張しない (scope 外、記録のみ)。旧「1 往復で終える」は D2051 決定 5 が上書き、旧「独立に評価」は主体が逆向きで別物 (所見 9) — 逐語は移さず義務は上記で保持 |
| 4 道具追加を裁定待ちへ変える | **real (must-fix)** | 採用。command L31 は `<tools>` 置換だけにし「足りなければ同 directory へ足して次回から使う」を保持。契約の next-tasks 終端は「短い手順是正は入口の編集条件で command の該当節、道具は runbook の道具置き場、`docs/` は裁定パッケージ」 |
| 5 `<tools>` の一意性 | refuted | 「7 箇所」は出現数、道具は 5 本と書き分ける |
| 6 探索順 (二重権威) | 未確認 | P4 どおり land 後に退避。切替完了は退避後に `~/.agents/skills/` から消えたことと repo 側の存在で報告し、探索順の実測は主張しない |
| 7 予算超過 | refuted (nit) | 「既存 3 件共通の比率」とは書かない。limit = ceil(bytes × 3000 / 2999) の rulings 型 |
| 8 hash の証明範囲 | 未確認 | 退避時に home 原本の sha256 を再計算して複製と一致することを記録する |
| 9 brief の一般化 | **real** | brief の P1 の理由から「D2051 が却下した文言を含む」を外し、薄い adapter の根拠は (a) 既存 3 skill の共通 dispatcher 型、(b) 単一権威 (command)、(c) 予算の同じ扱い、に置く |

## plan v2 (確定)

1. docs (親、D744): `.agents/skills/next-tasks/SKILL.md` = `$J/draft-SKILL.md` (5,458 bytes、最長行 223)、
   `agents/openai.yaml` = 原本 208 bytes と同内容、`docs/skill-self-improvement.md` = `$J/draft-self-improvement.md`
   (5,997 bytes、routing byte 同一)、`.claude/commands/next-tasks.md` = `$J/draft-next-tasks.md` (26,950 bytes、最長行 83、
   絶対 path 0)、`docs/pegasus-runbook.md` §7.2 末尾に道具置き場 3 行。
2. 実装面 (Codex author): `tools/check_docs.py` — `REQUIRED_SELF_HEADINGS[3]` += "next-tasks"、
   `CODEX_NEXT_TASKS_SKILL_LIMITS` = {SKILL.md: TextLimit(5_460, 400), openai.yaml: TextLimit(300, 160)}、`_FILES`、
   `_LITERALS` (親が最終本文から 23 件を指定)、`_OPENAI_YAML` (原本と bytes 一致)、guard 呼出し (rulings と cleanup の間)。
   `orchestrator/tests/test_check_docs.py` — 合成 skill 2 file、合成 self_doc に `### next-tasks`、exact byte pin
   26,903 → 26,950、`test_codex_next_tasks_skill_contract_pins_exact_surface` (手書き期待値)、負例 5 case。
   `SELF_LIMITS` / `COMMAND_LIMITS` / `COMMAND_INTERFACES` は不変。
3. 段 9 land 成功後: `~/.agents/skills/next-tasks/` を `~/.agents/skills-retired/next-tasks-2026-09-17/` へ移動
   (sha256 再計算、削除しない)。

## 変異事前登録 (対象は `tools/check_docs.py` のみ、B-057)

| ID | 変異 | 期待 |
|---|---|---|
| M0 | 新規定数直前の comment の句読点だけ変更 | SURVIVED (等価) |
| M1 | `REQUIRED_SELF_HEADINGS[3]` から `"next-tasks"` を除去 | KILLED (PIN + 合成 fixture の孤児 H3) |
| M2 | next-tasks の guard 呼出しを除去 | KILLED (PC[openai_changed] 等) |
| M3 | SKILL.md の TextLimit を 5_460 → 546_000 | KILLED (PIN + PC[byte_over]) |
| M4 | `_OPENAI_YAML` の `Next Tasks` → `Next Taskx` | KILLED (PIN) |
| M5 | `_LITERALS` から `"AGENTS.md"` を除去 | KILLED (PIN) |
| M6 | `_FILES` から yaml path を除去 | KILLED (PIN) |

probe 走で観測 node を集めてから本走で expected_nodes を固定する (前 wave と同じ手順)。

## 成果物影響 (DW-G05)

放置時の影響: Codex 起動の `$next-tasks` が D2051 前の旧規定 (1 往復・独立評価) で候補を出し続け、研究 wave の
選定入口が Claude 側と食い違う。certified 選択・レポート・台帳の値は変わらない (docs / 運用面のみ)。
