# 段 4 裁定 (親、2026-09-21 00:5x JST)

段 2・3 は DW-C00 の軽量版で省略 (設計択一なし、正しさ防壁非接触、受理集合は exact pin の置換 1 → 1)。
敵対所見は段 6 の read-only レビュー 1 本へ寄せる。裁定 inbox (`dev-wave-jobs/rulings-inbox/`) は再走査済み — 本 wave の
scope を変える更新は無い (`2026-09-20-k2-loop-originals-lost-downstream.md` §2 の付随項は pair 走 worktree の lock で、command 本文と無関係、
「gate・台帳は足さない」)。

## 裁定

- (P1) 採用: (b) は §3 に置く。§3 は「worktree の削除手順」であり、command 自身が撤去しない dirty worktree でも、§5 で引き渡す script が
  従うべき手順は §3 が正本である。§5 には足さない (§5 は push 系の引き渡し列挙に限る)。
- (P2) 採用: F1034 のポインタを本文に書く (routing 4「長い事故説明は F ポインタ」)。command file は living docs でなく D/PATH 腐敗検査対象外。
  合成 fixture の F placeholder は不要の見込み — `python3 tools/check_docs.py` 直叩き (login、背景) と `test_check_docs.py` 焦点走で実測して確定する (DW-O12: 実際に発火した手順を書く)。
- (P3) 採用: 削減は「意味を変えない縮約」だけ。安全義務・F 参照・check_docs の構造 literal (§3 exact 2 行、F26 と `docs/failures.md` の共起行、
  `docs/skill-self-improvement.md` 到達行、`$ARGUMENTS` 1 件) は保つ。段 6 レビューが文単位で新旧を対応づける (先例 T-2813 と同じ検査)。
- (P4) 採用: SKILL.md は command 本文を不可分に適用する overlay なので、command の 2 命令は Codex にも効く。overlay には Codex 固有の縮退 2 項だけ足す。
- 実装面: `tools/check_docs.py` の 2 定数と `orchestrator/tests/test_check_docs.py` の fixture (`_SYNTHETIC_CLEANUP_COMMAND` / `_SYNTHETIC_CLEANUP_SKILL` /
  `_EXPECTED_CLEANUP_COMMAND_SHA256` / `_EXPECTED_CLEANUP_SKILL_SHA256` / `len == 6_181` の値) の追随は Codex author 1 本。gate・検査の新設はしない (DW-O13 不成立)。
  順序は先例 T-2813 と同じ: 親 docs commit → Codex author (unit 木は docs が HEAD と一致) → 統合 commit。
- T-2601: `完了` (remaining: none) で閉鎖。本文は「不在の実測 (worktree list 38 本・branch・admin dir・directory・到達不能台帳のいずれにも無い)、
  撤去の実行記録は検索範囲に無く実行者・日時は不明、D2044 項 17 の残り (t2267 は施錠を尊重して残す) も対象不在で実行対象が無い」。
- F1034: supersede 追記 1 行 (恒久対応末尾の「[T-2814] で別 wave」が本 wave で実施済み)。
- scope 外 real 所見: なし。裁定パッケージ: なし (上限 6,204 は動かさない前提で収容できた場合。収容できなければ D782 の 2 段目 (独立 3 例) を判定し、
  3 例に満たなければ「実施しない」へ落として報告する — 上限引き上げは本 wave では行わない)。

## 変異事前登録 (DW-M01、実装前)

runner: `orchestrator/tests/test_check_docs.py` の単独走 (`-rf` 必須)。期待 node は login self-run で観測して final spec に転記する (メモリ「変異 final の期待 node は login self-run で観測できる」)。

| id | category | 位置 (replacement) | 期待 | 単一理由 |
|---|---|---|---|---|
| m0-equivalent-comment | positive | `tools/check_docs.py` の comment 1 行に等価な語を足す | SURVIVED | 生成 argv・判定に触れない (harness の SURVIVED 検出の正例) |
| m1-cmd-sha-old | negative | `tools/check_docs.py` `CLEANUP_COMMAND_SHA256` を旧値 `7cc008fa…` に戻す | KILLED | 定数 ≠ fixture 定数 (pin test) + 合成 fixture 走で whole-file SHA 不一致 finding (同一理由 = 定数の不一致) |
| m2-skill-sha-old | negative | `tools/check_docs.py` `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` を旧値 `268a32ae…` に戻す | KILLED | 同上 |
| m3-fixture-cmd-sha-old | negative | `test_check_docs.py` `_EXPECTED_CLEANUP_COMMAND_SHA256` を旧値に戻す | KILLED | fixture literal の sha ≠ 期待 sha (pin test 1〜2 node) |
| m4-fixture-bytes-old | negative | `test_check_docs.py` の `len(...) == <新 bytes>` を `6_181` に戻す | KILLED | bytes assert 1 node |
| m5-docs-plus-one-byte (手動 probe、DW-O19) | — | `.claude/commands/cleanup-branches.md` 末尾に 1 byte、`SKILL.md` 末尾に 1 byte (別々) | check_docs 直叩き赤 (whole-file SHA 不一致) | 実 repo 正例 test は growth hold で skip のため pytest では殺せない (先例 T-2813 と同じ)。即時復元 |

## 焦点走 (DW-O18 / DW-O26)

変更 test file `orchestrator/tests/test_check_docs.py` (単独走) + `tools/check_docs.py` (production) の consumer (`git grep -l check_docs orchestrator/tests/`) + inventory 4 群
(`test_campaign.py` / `test_official_perf_closure.py` / `test_p3_exploration_namespace.py` / `test_p3_b4_wiring_probe.py`)。計算ノード 1 job。
