# 段 6 fix 仕様 — [T-675] 住所 (address edge) の構造 lint

親が段 6 の敵対レビュー 2 本 (C=sol / D=luna、両方 NO-GO) を裁定した結果である。
`plan-v2.md` を上書きするのはここに書いた項目だけで、それ以外は `plan-v2.md` が正本のまま。

## 採用した所見 (実装面。これを直す)

| # | 所見 | 裁定 |
|---|---|---|
| f1 | `_assert_cleanup_address_edge_violation` が finding の対象 path (`.claude/commands/cleanup-branches.md:` prefix) を検証していない。対象束縛の変異 (M6) を負例が誤って通す | **real・修正** |
| f2 | 負例 n2 が「`F26`→`F260`」と「backtick 付き exact path の破壊」を**同時に**行う二重欠陥で過剰決定。片方の guard だけを緩めても他方が拒否し続けるため、単一理由性が無い | **real・修正**。独立 2 負例へ分割する |
| f3 | 新 lint が frontmatter も走査するため、`description:` に偽 edge を置いて本文の到達手段を消す迂回が通る | **real・修正**。**本文だけ**を走査する |

## 実装しないと裁定した所見 (既知限界。親が docs へ書く)

触らなくてよい。**これらを塞ぐ実装を足してはならない。**

- 4-space indented code block、link definition の quoted title、打ち消し線、否定形の prose で
  偽 edge を作れる。いずれも Markdown の意味解釈が要り、`DW-G03` の族一般化にあたる。
- 同一 commit で期待値ごと消す協調改変、inline の hidden HTML。
- 見出し + 本文の 2 行形、key/value の 2 行表、backtick 無しの Markdown link は**赤になる**。
  これは edge の書き方を 1 つの形に固定する契約であって偽陽性ではない。

## 直すこと

### fix-1 (f3) — 本文だけを走査する

新 lint の走査対象から frontmatter を除く。`.claude/commands/*.md` の frontmatter は
先頭行の `---` から次の `---` までである。**最小の手段で行うこと** — 専用関数・定数 registry・
新 gate を作らない。既存の `_parse_frontmatter` の実装 (`tools/check_docs.py` 内) を読み、
同じ区切り判定に従うこと。分岐の位置自体は現状のまま (frontmatter 解析の手前) でよい。

### fix-2 (f1) — finding の対象 path を assert する

`_assert_cleanup_address_edge_violation` の needle に
`.claude/commands/cleanup-branches.md:` prefix を含める。
これにより、対象 command を別 command へ差し替える変異が負例をすり抜けなくなる。

### fix-3 (f2) — 負例 n2 を独立 2 本へ分割する

現在の `test_cleanup_address_edge_rejects_substring_decoys` を、guard ごとに 1 つずつ
独立に測る 2 本へ分ける。**それぞれ、破っている guard がちょうど 1 つ**になるようにする。

| 新負例 | 変形 (「正本は `` `docs/failures.md` `` F26。」の置換後) | 唯一の拒否理由 |
|---|---|---|
| ID 隣接 decoy | 旧 `` `docs/failures.md` `` の F260 は無効。 | `F26` の ASCII 隣接判定だけ |
| path 非 code-span decoy | 正本は docs/failures.md の F26。 | backtick 込み exact code span だけ |

前者は backtick 込みの exact path を**持っている**ので、隣接判定を単純部分文字列へ緩めると緑になる。
後者は境界付き `F26` を**持っている**ので、backtick 要求を外すと緑になる。
この 2 本があってはじめて、2 つの guard に独立の positive control が付く。

### fix-4 (f3 の負例) — frontmatter decoy の負例を足す

本文の「正本は `` `docs/failures.md` `` F26。」を消し、frontmatter の `description:` の値へ
`F26` と `` `docs/failures.md` `` を同一行で置いた合成 command が**赤**になることを検査する。
frontmatter の key 集合は変えないこと (`description` の値だけを変える)。

### fix-5 — meta-test の登録を更新する

`test_dev_wave_new_gate_case_registration_is_complete` の登録リストを、
追加・改名した test 名と一致させる。

## 禁止 (`DW-S06-B`)

- **既存テストの期待値を変更しない。**反転・緩和・skip・削除を禁じる。
  赤になったら実装側が誤りである。期待値のほうが誤りだと判断したら、実装を変えずに報告して止めよ。
- **production を fail-open にして辻褄を合わせない。**受理集合を広げて緑にする形は禁止。
- **docs を編集しない。**`docs/` 配下、`.claude/` 配下、`.agents/` 配下、`output/` 配下は不可。
  とくに `.claude/commands/cleanup-branches.md` の bytes は 1 byte も変えない。
- **commit しない。**`git add` も `git commit` もしない。
- 実 repo の `CLEANUP_COMMAND_SHA256`、`_EXPECTED_CLEANUP_COMMAND_SHA256`、
  `_SYNTHETIC_CLEANUP_COMMAND` を変更しない。再束縛してよいのは合成 repo 側の checker だけ。
- 既知限界 (上表) を塞ぐ実装を足さない。scope を広げない。

## 編集してよいファイル

- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`

以上 2 ファイルだけ。
