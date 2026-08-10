# [T-695] + [T-700] — 変異台帳 (2026-08-11)

wave = `dev-wave-t695-t700-l2-routing`。対象 commit は `a06bf729` (段 6 fix 3 巡統合後)。
runner は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_check_docs.py -q -rf`、
`--runner-mode dispatch`。

## 採用値

- `mutation-spec-final.json` / `mutation-ledger-final.json` = **11/11 KILLED、rc=0**。
  spec sha256 = `080f2cdfd0c5f301cb8168d98ae7665df613fa5f517b86c2e45fff058139fab3`。

内訳:

| ID | 変異 | 期待検出 |
|---|---|---|
| M2 | 条件 25 行を削除 | 実 repo を読む検査 3 本 |
| M3 | 条件 25 の trigger を条件 23 と同文へ広げる | 同上 |
| M4 | 段 6 の C 行から `DW-O25` を削る | 同上 |
| M5 | `DW-O25` の「480 秒以内の rc=0 を必須とする」を弱化 | 同上 |
| M6 | 入口の wave 開始 item を wave 前の形へ戻す | 同上 |
| M7 | Codex Skill の item 4 を wave 前の形へ戻す | 同上 |
| M8 | self doc の routing 3 を wave 前の形へ戻す | 同上 |
| M9 | `DW-O25` 節を `DW-O01` の前へ移す | 同上 |
| M10 | 入口の wave 開始 item を blockquote 化 | 同上 |
| M12 | 順序 pin の heading 探索を修正前 (題込み前方一致 + 黙って通す) へ戻す | 専用 negative control 1 本 |
| M13 | raw/可視 slice 一致検査を無効化 | 専用 negative control 1 本 |

実 repo を読む検査 3 本 =
`test_dev_wave_model_pins_accept_current_docs_contract` /
`test_normative_exact_section_pins_accept_real_repo` / `test_real_repo_clean`。

M6・M7・M8 は wave 前の実コードの形と同型、M12 は fix 前の checker の形と同型である。

## erratum (採用しない実測)

`DW-M02` に従い初回結果を消さずに残す。

- `mutation-spec-v2.json` / `mutation-ledger-v1.json` = 13 変異。M12・M13 は KILLED、
  M1〜M11 は MISMATCH。うち M1 (`_OPERATION_NUMBERS` から 25 を抜く) は **228 node**、
  M11 (節 exact pin を無条件 finding へ倒す) は **225 node** の連鎖赤だった。
  M2〜M10 の MISMATCH は親の静的予測が 2 node で、実測が 3 node
  (`test_real_repo_clean` を落としていた) という予測差だけである。
- `mutation-spec-discovery.json` / `mutation-ledger-discovery.json` = M1 / M11 の再照準候補。
  条件 trigger 定数の書き換えと期待逐語定数の 1 文字ずらしを測ったが、いずれも **226 node** で
  過剰決定のままだった。

**機序:** `tools/check_docs.py` の契約定数は global で、合成 fixture が持つ handwritten literal と
**両方向で照合**される。したがって production 定数を 1 文字でも変えると、合成 repo を作る
すべてのテストが一斉に不一致になる。`DW-M01` の「無効化時の赤理由が一つに絞れる」を
満たせないため、`DW-M03` に従い**冗長 gate として単独変異の証拠から外した**。

過剰拒否 (over-rejection) の検出そのものは失われていない。M1/M11 系の変異が
226 node を殺した事実が、実 repo を読む検査群の感度を示している。単一理由でないため
matrix から外しただけであり、無検査になったわけではない。
