# [T-675] 実測台帳 (親が実 repo で測った値だけ)

環境: Pegasus login node (`check_docs`)、計算ノード dispatch (`pytest`)。
worktree = `dev-wave-t675-pin-semantic-gap`、base main = `7c3ac3e9`。

## M1 — pin 閉包 (`DW-O09`)

command 側 3 箇所:
- `tools/check_docs.py:389` `CLEANUP_COMMAND_SHA256`
- `orchestrator/tests/test_check_docs.py:264` `_EXPECTED_CLEANUP_COMMAND_SHA256`
- 同 `:318` `_SYNTHETIC_CLEANUP_COMMAND` (command の全文逐語コピー)

Skill 側 3 箇所 (段 2 プランの指摘で追加確認):
- `tools/check_docs.py:378` `CODEX_CLEANUP_BRANCHES_SKILL_SHA256`
- `orchestrator/tests/test_check_docs.py:261` `_EXPECTED_CLEANUP_SKILL_SHA256`
- 同 `:267` 付近 `_SYNTHETIC_CLEANUP_SKILL`

**族全体では 6 箇所。**test が 3 者一致を assert する (`:6536-6547`)。

## M2 — 安全文の削除だけ

`.claude/commands/cleanup-branches.md` から
「正本は `docs/failures.md` F26。」(35 bytes 相当) を削除。

- `check_docs` **rc=1**、違反ちょうど 1 件
- 内容: `.claude/commands/cleanup-branches.md: whole-file SHA-256 が契約と不一致`
- **失われた義務を名指す検査はゼロ**
- bytes 3959 → 3924

## M3 — 削除 + pin 3 箇所を同時再 pin (F173 の穴の実証)

sha256 `a92d960c…4722e3` → `5d0087f8…16586a` へ 3 箇所を同時更新。

- `check_docs` **rc=0 / 違反なし**
- `orchestrator/tests/test_check_docs.py` **357 passed / rc=0**
  (計算ノード request `900462.nqsv`、queue `gen_S`、elapse 12S)

**意味の欠落を含む bytes が「正しい bytes」として固定された。**

## M4 — 対案 (意味検査) の生死確認

`tools/check_docs.py` へ 2 レンズを一時実装 (probe、即時復元):
(i) 必須 literal 3 本、(ii) 本文の `F<n>` が `docs/failures.md` に `### F<n>.` として実在。

- clean tree → **rc=0 / 違反なし** (偽陽性ゼロ)
- M3 の攻撃状態 → **rc=1**、
  `安全義務への到達手段がない — '正本は `docs/failures.md` F26。'`
- `F51` → `F901` 差し替え → `F901 が docs/failures.md に実在しない` が追加発火

復元後の command sha256 = `a92d960c…4722e3` (pin 定数と byte 一致)、`check_docs` rc=0、
`git status --porcelain` 空。

## M5 — 機械化の置き場所に docs byte 予算は掛からない

M4 の実装面は `tools/check_docs.py` (Python) にあり `TextLimit` 対象外。
F173 恒久対応の「機械化は `docs/dev-wave/**` の byte 予算に阻まれており」は、
**この形の機械化には当たらない**。

## M6 (訂正済み) — 「pin と意味検査は交差ゼロ」は誤り

段 2 プランが反例を出し、親が `tools/check_docs.py:4104-4107` を直接読んで確認した。

```
if (rel != ".claude/commands/dev-wave.md"
        and "docs/skill-self-improvement.md" not in text):
    findings.append(f"{rel}: docs/skill-self-improvement.md への到達性がない")
```

**pin 済みの cleanup-branches command は、既に正本ポインタ 1 本の到達性を検査されている。**
したがって (a) は新機構の新設ではなく、**既存契約の対象一覧に F26 のポインタが
入っていないという欠落**である。frontmatter key 集合・`$ARGUMENTS` 件数も同ループで検査済み。

## M7 (精密化) — byte headroom

- 生の予算: 3959 / 4000 bytes = raw headroom 41 (`tools/check_docs.py:170`)
- `test_cleanup_command_invalid_backtick_info_is_rejected` が 17 bytes 追記する
- 判定 helper `_assert_cleanup_digest_violation` は **`_violation_count(res) == 1`** を assert する
  → 追記後に予算超過すると 2 件目の違反が出て赤くなる
- したがって**実質上限 3983 bytes / headroom 24 bytes は定数ではなく創発的に強制されている**。
  段 2 プランの「checker が強制する現行値ではない」は不正確。

## M8 — 合成 repo に `docs/failures.md` は存在しない

`check_docs._ENUMERATED_DOCS` に `docs/failures.md` は含まれない (Python で直接確認、False)。
`_build_min_repo()` は placeholder すら作らない。

→ **F 番号到達性レンズを足すと、合成 repo を使う既存負例テスト群
(`_assert_cleanup_digest_violation` を使う 8 件前後) が「違反ちょうど 1 件」を破って
一斉に赤くなる。**fixture 拡張が必須の実装コストである。

対して**必須 literal レンズ (a1) は fixture 拡張が要らない** — 合成 command / Skill は
実ファイルの全文逐語コピーなので、必須 literal は定義上すべて含まれている。

## M10 — 「到達性は機械検査、意味は機械検査しない」は既に repo の実装方針である

`docs/skill-self-improvement.md:84` の「義務本文の文言と意味の保存は lint に固定せず、
敵対監査と人間レビューで担保する」は、**到達性の機械検査を禁じていない**。
実装がそれを示している。

- `tools/check_docs.py:4104-4107` — pin 済み command に対する正本ポインタ到達性検査 (M6)
- `tools/check_docs.py:4697-4713` — `docs/archive/` の**双方向到達性 lint**。
  archive の実在物が README 索引から辿れること、および README の各行が実在物または
  規約どおりの「墓標行」であることを検査する (`docs/archive/README.md` にも
  「到達性 lint = check_docs.py が墓標様式を認識する」と明記)。

**したがって (a-narrow)「lint が固定するのは義務の住所であって文言ではない」は、
親の読み替えではなく既存の実装方針の追認である。**新しい原則を導入しない。

## M11 — token 存在形は迂回できる / edge 共起形は迂回を殺す (段 3 レンズ A の裏取り)

`tools/check_docs.py` へ 2 形式を同時に probe 実装し、4 状態を実測した (即時復元済み)。

- **token 存在形** (段 2 プランの案): 可視本文に `docs/failures.md` と `F26` が
  それぞれ存在するか
- **edge 共起形** (レンズ A の対案): **同一の可視行**に両方があるか

| 状態 | command | token 形 | edge 形 | `check_docs` |
|---|---|---|---|---|
| (i) clean | 現行のまま | 緑 | 緑 | **rc=0 / 違反なし** |
| (ii) F173 の削除 + 再 pin | 安全文を削除 | (未計測・下記) | **赤** | rc=1、edge 違反 1 件 |
| (iii) **token 移動攻撃** + 再 pin | 安全文を削除し、§6 本文へ `docs/failures.md` を 1 行追加 | **緑 (発火せず)** | **赤** | rc=1、**edge 違反 1 件のみ** |
| (iv) 正当な言い換え + 再 pin | 「F26 (`docs/failures.md`) が正本。」へ書き換え | 緑 | 緑 | **rc=0 / 違反なし** |

- **(iii) が決定的である。**token 形は違反ゼロ、edge 形だけが発火した。
  段 3 レンズ A の所見「必須 token 分解では参照 edge を検査できず、token 移動で迂回できる」は
  **real** であり、実測で確定した。
- **(iv) が偽陽性面を測る。**語順・助詞を変えた正当な言い換えで両形とも緑。
  edge 形は**日本語の文言を pin しない**。
- 各状態で command の sha256 を再 pin してから測っているので、
  **whole-file pin は 4 状態すべてで緑**である (pin は 1 件も止めていない)。
- 復元後: sha256 = `a92d960c…4722e3` (pin 定数と byte 一致)、
  `check_docs` rc=0、`git status --porcelain` 空。

## M12 — pin は既に安全な追記を 1 件抑止していた (一次資料)

`docs/failures.md` の F26 本文 (§「追加事象 (2026-07-30)」) に次がある。

> 運用則 = **1 worktree ずつ削除し、必要なら timeout を延ばす**。command 本文への反映は
> `.claude/commands/cleanup-branches.md` が Codex skill との whole-file SHA-256 parity 契約下に
> あり checker 定数の同時更新を要するため未実施 (次の一手へ登録)

**同じ pin が、(1) 安全則の command への反映を「コストが高い」として止め、
(2) その未反映のせいで bare `F26` の到達先が非一意になり、F173 で削除を許した。**
pin の費用は片側 (追記の抑止) に、盲点は反対側 (削除の看過) に出ている。

## M9 — OOM (運用の実測)

`/sys/fs/cgroup/user.slice/user-31609.slice/memory.max` = **17179869184 (16 GiB)**、
`memory.events` の `oom_kill` = 1308 (観測時点)。この上限は**同一ユーザーの全並行 job で共有**する。

本 wave では codex 子が **3 回**、`.done` を書かずに無音で消えた
(段 2 の 1 本目、段 3 レンズ A・B の初回)。いずれも log は途中で切れ、error 文字列はなし。
巨大ファイル (`tools/check_docs.py` 4500 行超、`docs/decisions.md`) を子が丸ごと表示した
直後に落ちている。**pid 監視の待ち手だけが検出でき、`.done` 待ちだけの待ち手は無音でハングする。**
