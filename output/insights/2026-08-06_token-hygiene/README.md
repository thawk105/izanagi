# dev-wave token-hygiene の逐語・変異台帳 (2026-08-06)

依頼: 「トークン衛生チェック。claude, codex ともにトークンの使用ペースが大きい。開発品質を
落とさずにトークン消費量を減らせるところがあるかどうか調べて、良い施策があればやってほしい」

branch `worktree-dev-wave-token-hygiene`、tip `b14e37ee` (local main `5a322447` 取り込み済み)。

## 何を land したか

`tools/claude_session_ledger.py` と `orchestrator/tests/test_claude_session_ledger.py` **だけ**。
claude セッション側の read-only トークン台帳である。

**削減施策そのものは 1 つも land していない。** 段 3 と段 6 が、親の観察値では削減判断を
支えられないと判定したためである。詳細は下記。

## 段 0 の計測と、その誤りの記録

親は使い捨てスクリプト (`analyze_v2.py` / `analyze_codex.py` を凍結) で消費を測り、
ユーザーへ次を報告した。**このうち複数が誤りだった。**

| 主張 | 判定 | 誤りの内容 |
|---|---|---|
| 蓄積内訳 tool_result 33.5% / thinking 26.8% / tool_use 17.9% / text 2.0% | **撤回** | 同一 block を `assistant:tool_use` と `in:<tool>` の両方へ加算し分母にも両方を入れた二重計上。token 比でも traffic 寄与でもない |
| codex は tool 1 回あたり 105,774 tok | **撤回** | 数えていたのは `token_count` event (= 観測 model call) であり tool call ではない。さらに ratio-of-medians で同一 session の比ですらない |
| 6 日で 11,860 M (claude 7,787 M / codex 4,027 M) | **限定付き** | 単一 encoded cwd の subtotal。旧 checkout 38 本 (94 MB) と `subagents/*.jsonl` (87 requests / 入力 5,548,966 / 出力 63,208) が欠落。codex の「937 子」は TUI 5 本 (入力 1,312,282) が混入 |
| 固定 base 46,641 tok | **限定付き** | 初回 request の入力中央値であり、依頼文・添付を含む。固定 base ではない |
| effort max は high の 2.02 倍 | **因果としては不可** | 現契約が plan/consult=max、author=high なので stage・難易度・turn 数と交絡している |
| 入力:出力 = 500:1 | **限定付き** | raw token traffic 比としてのみ。cache read/write は単価が異なり、課金比・枠消費比ではない |
| 平均 context 297,806 tok/応答 | **限定付き** | 20 応答未満の session を除外した標本の算術平均。中央値でも分位でもなく、介入後も不変な換算率ではない |

**方向として堅いと確認できた事実:**

- claude 側は完全に未計装だった (`grep -rln "claude/projects" tools/ orchestrator/ docs/` は
  archive 1 件のみ)。codex 側は `tools/codex_worker_ledger.py` / `tools/codex_reasoning_ab.py` /
  D100 で計装済み。**大きい方が見えていなかった。**
- `docs/dev-wave/workers.md` DW-S02・DW-S03 が `reasoning=max` を明文規定している (DW-S05-A は high)。
- codex の `total_token_usage` は累積値で、rollout 全期間なら最後の有効値を採るのが正しい
  (全件合算すると 21 倍の過大計上になる。実測で確認)。
- dev-wave 4 文書の aggregate 予算は 25,200 bytes に対し現状 25,187 bytes = **余地 13 bytes**。

## なぜ削減施策を land しなかったか

段 3 (`s3-lens-out.md`、NO-GO、must-fix 6 件) と段 6 (`s6-revA-out.md` / `s6-revB-out.md`、
ともに NO-GO) の裁定は `s4-ruling.md`。要点:

1. **codex 側の集計は既存 ledger と二重管理になる。** 親は着手前の既存被覆検索 (DW-S01) を怠った。
2. **effort 引き下げは交絡した観察値では決められない。** これは `tools/codex_reasoning_ab.py`
   (T-184 所有、paired・blind・非劣性、primary endpoint は arm を隠した親の意味裁定) が持つ問い。
   規律 2 の精神に従い、検出力を下げる変更は evidence なしに入れない。
3. **固定換算率を `CLAUDE.md` へ書くのは有害。** stale 化し、依存のある呼び出しまで無理に
   束ねさせ、診断証拠を切る誘因になる。しかも「独立 tool を束ねよ」「Bash 出力を絞れ」は
   既に harness の system prompt に存在し、書き足しても無効である。
4. **`workers.md` へ 1 行も足せない。** 予算余地 13 bytes で、削除先を特定していない。

## 変異 matrix — 3 走の記録 (erratum を消さない)

anchor は `562dade4`。runner は `python3 tools/run_tests.py orchestrator/tests/test_claude_session_ledger.py -rf`。

| 走行 | spec | sha256 先頭 | 結果 |
|---|---|---|---|
| 1 | `mutation-spec.json` | `7ce462bf` | KILLED 5 / MISMATCH 6 / **SURVIVED 1** / baseline PASSED |
| 2 | `mutation-spec-v2.json` | `53f4254f` | KILLED 11 / MISMATCH 1 / SURVIVED 0 / baseline PASSED |
| 3 | `mutation-spec-v3.json` | `263ddcd2` | **KILLED 12 / MISMATCH 0 / SURVIVED 0 / baseline PASSED / rc=0** |

**1 走目の M7 SURVIVED が本 wave で最も重い所見である。**

M7 = `_select_balanced_paths` の `selected_sidechain = min(base_sidechain, len(sidechain_candidates))`
を `selected_sidechain = 0` へ置換する変異。段 6 レビュー A の must-fix A1
(「root だけで `--max-files` を使い切ると sidechain が 0 になる」) に対応する検査だったが、
既存テストが検出できなかった。

親は等価変異かどうかを実測で判定した。**root 0..7 × sidechain 0..7 × max_files 1..8 の
全 512 通りのうち 185 通りで正しい配分と変異後の配分が食い違う。** 代表例:

| root 候補 | sidechain 候補 | max_files | 正 (root/side) | 変異後 |
|---|---|---|---|---|
| 2 | 1 | 2 | 1/1 | **2/0** |
| 2 | 2 | 2 | 1/1 | **2/0** |
| 3 | 1 | 2 | 1/1 | **2/0** |

よって等価変異ではなく実在の検出力欠落と裁定し、
`test_reserved_balanced_quota_precedes_reassignment_when_candidates_compete` を新設した
(`562dade4`)。**実装は変更していない** — 配分ロジックは元から正しく、欠けていたのは検査だけである。

**MISMATCH 6 件 (1 走目) と 1 件 (2 走目) はすべて親の登録ミスであり、変異自体は初回から
検出されていた** (rc=1、複数 node が落ちた)。F87 の再発である。原因は 2 つ:
(a) 親が expected_nodes を真部分集合で登録した、
(b) 2 走目で新テストを足したため、配分・件数を変える変異 (M9・M11) の failed node 集合が増えた。
**v1 / v2 の spec と台帳は消さず erratum として残す。**

この欠陥は段 6 レビュー B が事前に予告していた — M8 / M10 / M12 が「JSON は検査されるが
利用者が読む既定テキストは無検査」という理由で生存すると指摘し、実測でもそのとおり生存した
(1 走目)。fix 後は 3 件とも KILLED。

## 受入

- 焦点走行: 段 5 直後 13 passed → 段 6 fix 後 33 passed → 段 6 fix 2 巡目後 34 passed。
- 受入全走: tip `b14e37ee` で **6837 passed / 20 skipped** (request 893648.nqsv、933.91s、rc=0)。
- `tools/check_docs.py` 違反なし。

## 既存の赤 (本 wave の差分ではない)

`python3 tools/check_ai_provenance.py` は **local main の時点で既に赤**である。
他 session `worktree-rulings-20260806-a` の merge commit 5 本
(`88f0f9f0` `85dacc27` `6e69ca5c` `16affe16` `905c867a`) に `AI-Agent` trailer がなく、
それが local main の祖先に入っている (`git merge-base --is-ancestor` で確認)。
本 wave の 3 commit はいずれも trailer を持ち clean。**他 session 所有物なので触らず裁定へ返す。**

## 逐語

- `brief.md` — 段 1 brief v1 (段 3 が NO-GO を出して破棄したもの。訂正前の主張を含む)
- `s3-lens-out.md` — 段 3 敵対レンズ (max/read-only、NO-GO、must-fix 6 件)
- `s4-ruling.md` — 段 4 裁定 (確定 scope と変異事前登録 M1〜M12)
- `s5-impl-out.md` — 段 5 実装子 (high/workspace-write)
- `s6-revA-out.md` / `s6-revB-out.md` — 段 6 敵対レビュー 2 本 (max/read-only、ともに NO-GO)
- `s6-fix-out.md` / `s6-fix2-out.md` — 段 6 fix 2 巡
- `analyze_v2.py` / `analyze_codex.py` — 段 0 の使い捨て計測スクリプト
  (**上表の誤りを含んだまま凍結する。訂正の証拠として残す**)
