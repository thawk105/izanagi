# [T-675] 住所 (address edge) の構造 lint — 逐語と変異台帳

wave: `dev-wave-t675-address-edge-lint` / 実装 commit `1ea9d03f`、docs `c162408d`、
記録 `ef8928e2`、lease merge `c22610d1`、fold `ccbed760`。
裁定の正本は `output/insights/2026-08-10_t675-pin-semantic-gap/package.md` (R1〜R4)、
経緯は同日の worklog エントリ、呼称と位置づけの正本は同日 fold の decisions エントリ。

## この wave が何を変えたか

whole-file SHA-256 pin は bytes しか守らない。安全義務の文を削って pin 3 箇所を同時再同期すれば
検査は通る (F173)。その穴のうち、cleanup-branches command から F26 への到達 edge 1 件だけを
`tools/check_docs.py` の既存 command guard の中に 1 分岐で塞いだ。

- 対象は `.claude/commands/cleanup-branches.md` の**本文のみ** (frontmatter は走査しない)
- `F26` は ASCII 英数字に隣接しない出現だけを数える (`\b` は日本語文字を word 文字とみなすため、
  「正本はF26。」のような空白なし表記を偽陽性にする)
- path は backtick 込みの exact code span `` `docs/failures.md` `` で照合する
- 可視行は raw HTML block まで不可視化する既存 helper で取る
- 専用関数・定数 registry・新台帳・新 gate を作らない。族一般化もしない (`DW-G03`)

## 敵対レビューが暴いたもの (逐語は `verbatim/`)

| 出所 | 内容 | 帰結 |
|---|---|---|
| `s3-lens-a.md` 所見 1 | 単純部分文字列一致は `F260` × `archive/docs/failures.md.bak`、link definition、表セル横断で**偽 edge を作れる** | ASCII 隣接判定 + backtick 込み exact code span |
| `s3-lens-a.md` 所見 2 | 親の (P1)「可視行 = code fence / comment 除去」は誤り。dispatch 用 helper なら raw HTML block も除ける | helper を差し替え |
| `s3-lens-a.md` 所見 5 | 親 brief の「同一可視行共起の既存被覆 0 件」は**誤り**。dispatch inventory が既に同型の typed edge 検査を持つ | 純増は検査パターンでなく対象だけ、と記録を訂正 |
| `s3-lens-b.md` 所見 5 | F173 の恒久対応「機械化は byte 予算に阻まれており」は**誤り**。実装面は Python 側で `TextLimit` の対象外 | F173 へ supersede 追記 |
| `s6-lens-c.md` 所見 3 | 負例 helper が finding の**対象 path を検証していない** — 対象 command を差し替える変異が素通りする | needle に path prefix を固定 |
| `s6-lens-c.md` 所見 3 | 負例 n2 が 2 つの guard を**同時に**破る二重欠陥で、M2/M3 を 1 件も殺せない | guard ごとに独立した 2 負例へ分割 |
| `s6-lens-c.md` 所見 1 | frontmatter の `description:` に偽 edge を置いて本文の到達手段を消せる | 本文だけを走査 + 専用負例 |
| `s6-lens-d.md` 所見 2 | 親が書いた D の trust root が「人間レビューと敵対監査」と広すぎる | trust root は人間レビューに限定 |

**段 3・段 6 の 4 本すべてが NO-GO で、所見ゼロは 1 本も出ていない。**

## 塞いでいないもの (既知限界)

「協調改変を防ぐ防壁」ではない。次はすべて素通りする。

- 同一 commit で期待値ごと消す協調改変
- inline の hidden HTML
- 4-space indented code block、link definition の quoted title、打ち消し線
- 「この住所を参照してはならない」のような否定形の prose
- **`check_docs` を明示的に走らせない層** — hooks・CI・pre-commit は呼ばず、land も fold 経路だけ

また、同一可視行 + backtick code span という**形**を要求するので、見出しと本文に分けた 2 行形、
key/value の 2 行表、backtick の無い Markdown link は赤になる。偽陽性ではなく契約である。

## 変異 matrix

`mutation-spec.json` / `mutation-ledger.json`。走行スコープは新テスト 8 本 + meta-test の 9 nodeid。
**8/8 KILLED、baseline rc=0、全件 expectation 一致。**

| ID | 変異 | 赤になった node |
|---|---|---|
| M1 | 分岐を丸ごと無効化 | 負例 6 本 |
| M2 | ASCII 隣接判定を単純部分文字列へ | ID 隣接 decoy 1 本 |
| M3 | backtick 要求を外す | 非 code-span path decoy + link definition |
| M4 | 可視行 helper を生テキストへ | raw HTML block |
| M5 | 条件を反転 | 負例 6 本 + 正例 2 本 |
| M6 | 対象 command を差し替え | 負例 6 本 + 正例 2 本 |
| M7 | 可視行 helper を raw HTML 非除去版へ | raw HTML block |
| M8 | frontmatter 除去を無効化 | frontmatter decoy |

**M2 と M3 は当初の事前登録では殺せなかった。**負例が 2 つの guard を同時に破っていたためで、
親の検算と `s6-lens-c.md` が独立に同じ結論へ達した。負例を分割して初めて成立した。
期待 node と記録 node は**集合の完全一致**で判定されるため、走行スコープの取り方が結果を決める。

## 受入と land

受入全走は 2 走した。1 走目 = 作り直し前の tip で 8285 passed / 20 skipped / 521.07 秒 / rc=0。
**本走 (2 走目) = 最終 tip `c22610d1` で 8397 passed / 20 skipped / 502.53 秒 / rc=0。**

1 度目の land は provenance 全履歴監査が rc=1 で拒否した。原因は親が peer の land 通知を受けて
手動で作った merge commit で、両親がともに `tools/check_docs.py` と
`orchestrator/tests/test_check_docs.py` を変更していたため merge 結果がどちらの親とも異なり、
`DW-O17` の Codex `role=author` を要した。親は `role=integrator` だけを書いた。
merge 直後に `check_ai_provenance` を回さず `check_docs` しか見ていなかったのが漏れである。
Codex の merge 監査 (`verbatim/s9-merge-audit.md`) を通した merge commit へ作り直して解消した。
