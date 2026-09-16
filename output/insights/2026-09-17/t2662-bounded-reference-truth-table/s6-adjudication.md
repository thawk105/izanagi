# 段 6 裁定 — レビュー A / B の所見と README の是正 ([T-2662])

レビューは read-only codex 2 本 (`s6-review-a.md` = レンズ A 候補集合と対照、`s6-review-b.md` = レンズ B
D248 解釈と向き)。両者とも「本番維持の向きは変えない」「P>H (本番だけ True) の反例は作れない」で一致し、
親の結論の**言い過ぎ**を 3 点倒した。所見ごとの裁定と対応を下に示す。

## 所見の裁定

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| B1 / (A の前提) | 「D248 の意味は本番側」「暫定を確定にする」は根拠を超える。D248 の逐語 (pattern の出現の左右・content 端・未知 byte の延長) は helper の読みとも整合し、D2104 項 25 自身が「内部の探索方式は未規定」と書く。本番側を規範にするのは D248 の解釈でなく**追加規則** | **real** | README 結論 2 を「D248 の逐語は内部探索方式を一意に定めない。本 wave は抑止を広げない条件 (D2104 項 25) に従い本番を維持する。D248 の唯一の解釈の証明とは扱わない」へ書き換え。decisions fragment は**実測の結果記録 + 運用判断 (本番維持)** に留め、追加規則としての明文化は worklog の裁定待ち項へ (closed) |
| A1 / B2 | 「境界 byte 入り path は landed 参照が構造的に成立せず必ず報告される」は不成立。D247 条件 5 は探索根より真に下位の**祖先 dir** の参照も認め、`_reference_patterns()` は祖先を全部生成する。境界 byte を含まない祖先 (例 `/offrepo/w`) が引用されれば抑止されうる | **real** | README 帰結を訂正。既存の表に測定済みの実例あり: R0098 (P1、祖先 `/offrepo/w` を引用 → 両方 True)、R0245 (P4、同)。実在 path 1 も `dev-wave-suite-floor-recheck` 等の境界なし祖先を pattern に持つ (closed、実測済み行を引用) |
| A2 | 単根の真偽表を本番の全根集合と同一視できない。本番の `encoded_roots` は全 match の root の集合で、入れ子の根 (例 `/offrepo` と `/offrepo/my dir`) や境界 byte を含む根では、長い根の走査が内部の境界 byte を跨ぎ、単根では False の file pattern が True になる | **real** | README 結論 1 に射程を明記。本番は根ごとの結果の和集合 (`matched.add`) なので、複数根の結果 = 各単根の結果の和集合。境界 byte を含む根の成分は **P9 で測定済み** (R0385: 根 `/off repo`、pattern `/off repo/w/a.py` → 両方 True)。よって入れ子の根があれば本番も True になりうるが、その行でも helper は True なので P>H は増えない (closed、測定済み成分 + コード上の和集合論証) |
| B3 | 本番コードのコメント (`_bounded_path_reference_matches` 内「token の set 一致は pattern の境界付き出現と同値」) は無条件では誤り。R0075 (引用符で囲んだ空白入り pattern、helper True・本番 False) が反例 | **real** | 実装面 (`tools/`) なので本 wave では触らない。次 wave の項 (同値テストの射程明記 + 負例 pin) に「コメントの同値主張を射程付きに直す」を含める (partial → 次 wave) |
| A3 / B (循環でない) | 未収録の型で P>H が生じる | **refuted** | 本番が `matched.add(token)` に到達する token は「非空の根に一致した左境界付きの位置から、境界 byte または content 末尾まで」の実部分列で、pattern と完全一致する。helper は全出現を `start = index + 1` で走査し、その出現で左右境界が成立するので True。chunk 分割 (`search_end = chunk_end + len(root) − 1`、`index >= chunk_end` の break、右境界探索は content 末尾まで) もこれを破らない。README にこの論証を「表の裏付け付きのコード論証」として載せる |
| A4 | `unmatched_patterns` の逐次縮小で最終 matched 集合が変わる | **refuted** | 根集合を固定すれば戻り値は `patterns ∩ T(content, roots)` で、既検出 pattern の削除は他 token の探索に影響しない |
| A5 | P11 (根の外の pattern) が本番経路から生成される | **refuted** | 根は resolve 済み、候補は根からの `os.walk` の `Path(directory) / filename` で同じ根を `_ExternalMatch` に保持、directory symlink は `followlinks=False`、file symlink は `lstat()` の regular 条件で除外。P11 の 4 行は入力領域外 (README は H>P 144 のうち P11 4 行を分けて書く) |
| A6 | 6 file の対照では実在 path での差の存在を示せない | **refuted** | 存在命題には足りる。467 file 全体の発火件数や実監査の抑止差には外挿しない (README に明記) |
| B4 | 本番維持は fail-safe の向きを取り違えている | **refuted** | 抑止を増やさず報告を残す向きは D248・D2104 項 25 と一致 |
| B5 | 真偽表には情報量がない (暫定が先にある) | **refuted** | P>H の有無、実在名での再現、chunk 跨ぎの不一致はいずれも反証可能だった (README「真偽表が否定しえたこと」節を追加) |
| B6 | helper は現在も本番から呼ばれる | **refuted** | 31b66034f の親で `_landed_reference_matches()` が helper を呼び、現在は定義と同値テストからの呼び出しだけ |
| B7 | 負例 pin は将来のユーザー裁定を妨げる | **refuted** | 「現行挙動と legacy との差の記録」として位置づければ、将来の裁定に合わせて期待値を変えられる。README の次の一手の文言を「意味を固定」から「現行挙動と legacy との差を記録」へ |
| A-nit | README の P0「全 74 行」は 72 行 | **real (nit)** | 訂正 (JSON 再計算 72)。H>P 144 のうち P11 4 行を除くと 140、実在 18 行は 6 file × 3 形であって 18 file ではない、hits 6 entry = 4 dir + 2 file、をすべて README に明記 |
| A / B 共通 | 今日、当該 file が到達不能 blob の一致候補になっているか、偽陽性・救出 triage の負担が実際に増えているか | **不明** | 本 wave は測っていないと README に明記。次 wave の候補にはしない (D2040 と同じく実害の観測を待つ) |

## 是正後の結論 (README に反映)

1. 真偽表 862 行で P>H は 0、H>P は 144 (入力領域外の P11 4 行を除くと 140)。差の条件は「探索根より下に
   境界 byte を含む path」で、境界 byte を含まない path は chunk 跨ぎを含め全 72 行一致。
   本番 ⇒ helper は表の裏付け付きのコード論証で全入力に成り立つ。**単根の表であり、複数根では本番の
   結果は各根の和集合になる** (境界 byte を含む根は P9 で測定済み)。
2. D248 の逐語は候補 path 内部の探索方式を一意に定めない (D2104 項 25 の理由の再確認)。本 wave は
   「抑止を広げない」条件に従い本番を維持し、これを D248 の唯一の解釈の証明とは扱わない。本番の方式を
   D248 の追加規則として明文化するかはユーザー裁定 (worklog の裁定待ち項、実害なしの P3)。
3. 向きは本番維持 (実装差分ゼロ)。helper は legacy の境界述語で本番の呼び手は無い。同値テストの候補は
   境界 byte を含まない同一 pattern 6 行なので、同値主張の射程はその範囲に限る。
4. 境界 byte 入りの file 自身への完全 path 参照は当該探索根の現行本番では認められないが、境界 byte を
   含まない祖先 dir の参照 (D247 条件 5 の祖先条項) や別候補・hardlink alias で抑止されうるので、
   「必ず報告される」とは言えない。

## 段 6 の形

実装面の差分ゼロなので fix 子・変異 matrix は無い (`DW-S04`)。レビュー所見の対応は docs (README) の
訂正だけで、親が行った。所見ごとの closed / partial 対応は上表のとおり。
