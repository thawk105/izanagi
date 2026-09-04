# [T-2246]/[T-2247]/[T-2248] K2 の宣言範囲と投入知識源を端から端まで束縛する — 材料と実測 (2026-09-04)

wave branch `worktree-dev-wave-t2246-k2-knowledge-closure`。

commit 列: `47e55de8f` (実装統合)、`61b06ae28` (main 取り込み 1)、`ec86de471` (段 6 修正 1 巡目)、
`8dc62e4c5` (docs と裁定記録)、`6f44620dd` (段 6 修正 2 巡目)、`0ae3dd7bd` (main 移設への先回り適合)、
`20c0c126d` (main 取り込み 2)、`c60b91a0c` (変異の一次資料と逐語)。
変異本走と受入全走はいずれも `20c0c126d` に対して実行した。

## 一次資料

| file | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief の逐語 |
| `verbatim/s2-plan.md` | 段 2 プラン (Codex read-only) の逐語 |
| `verbatim/s3-lens-a.md` | 段 3 敵対相談レンズ A (正しさ境界・受理集合) の逐語 |
| `verbatim/s3-lens-b.md` | 段 3 敵対相談レンズ B (scope・実効性) の逐語 |
| `verbatim/s4-ruling.md` | 段 4 裁定とプラン v2、変異事前登録の逐語 |
| `verbatim/s5-author.md` | 段 5 実装子の報告の逐語 |
| `verbatim/s6-lens-c.md` | 段 6 敵対レビューレンズ C (実装・受理集合) の逐語 |
| `verbatim/s6-lens-d.md` | 段 6 敵対レビューレンズ D (テスト実効性・変異帰属) の逐語 |
| `verbatim/s6-ruling.md` | 段 6 裁定の逐語 |
| `verbatim/s6-fix1.md` | 段 6 fix 1 巡目 (must-fix 4 件) の報告の逐語 |
| `verbatim/s6-fix2.md` | 段 6 fix 2 巡目 (期待値ずれ 1 件) の報告の逐語 |
| `verbatim/s6-merge-adaptation.md` | main 移設への先回り適合の逐語 |
| `verbatim/s6-merge-audit.md` | main 取り込みの合成監査の逐語 |
| `verbatim/parent-executed.md` | 親が自分で実行した分の記録 |
| `mutation-spec.json` | 本走の変異 spec (sha256 `22ce10093001d5e9231fb92a3f422cbeb82aa5b338446ef8bba1b29dfca4a16c`) |
| `mutation-ledger.json` | 本走の結果台帳 |
| `mutation-probe-out.json` | probe の結果 (観測 node の採取) |

## 何が問題だったか

D1429 (ユーザー裁定) は「参照を許した範囲」と「実際に投入した知識源」を分けて記録することを求め、
**この閉包が閉じるまで K2 を条件とする certified な最終選択を主張しない**と定めた。
D1570 (ユーザー裁定) は K2 が宣言した範囲を指し投入件数を条件にしないと定め、
取得結果が正当に空である場合に限って通す形へ直すよう求めた。

着手時点の実装は次の状態だった。

1. `knowledge_manifest` は source 1 件以上を要求し、取得結果ゼロの K2 アームを入口で拒否していた。
   同じ非空要求が試行台帳と材料レポートの schema、および K2 role の入力 schema にもあり、
   **4 層**に散っていた。
2. `validate_output_semantics` の K2 分岐は実在するが、production の呼び手が 0 件だった。
3. 閉じた proposal schema が K2 role の宣言済み出力 (`knowledge_use` を含む) を拒否していた。
   **「未配線」は consumer 不在だけでなく、入口の受理形が塞いでいることも含んでいた。**

## 直前 wave が既に閉じていた範囲 (本 wave は作り直していない)

T-2183 が `layer3_schema.json` / `layer3_report.py` へ `knowledge_provenance`
(`declared_sources` / `injected_sources`) を着地させ、受領証 digest と参照一覧の束縛まで済ませていた。
本 wave の純増は、**宣言範囲という第 3 の値**と、**role 出力側の配線**である。

## 段 4 の裁定が段 6 で 2 度覆された — いずれも「裁定は正しいが実装が目的を壊した」型

本 wave で最も再利用価値のある観測である。

### 1. 受理集合を守るための機構が、その受理集合を壊した

段 3 のレンズ B が「知識入力の有無で K2 の出力契約を選ぶと、実績のある呼び方が後から拒否される」
ことを指摘した。段 4 はこれを採用し、**呼び手が role 契約を明示したときだけ K2 経路へ入る**と裁定した。

実装は `load_proposal_file` の関数契約としてはそのとおりに作られた。ところが呼び出し側の `main()` は、
知識 manifest が与えられていれば role 契約の有無にかかわらず知識射影を渡していた。結果として
**知識 manifest だけを渡す従来の呼び方が「片側指定」として拒否されるようになった。**
これは唯一実績のある K2 走行 (T-2182) の呼び方である。

裁定の文言は満たされていた。壊れていたのは裁定の目的である。段 6 のレンズ C が見つけた。

### 2. 新設した停止分岐が、JSON の重複キーで迂回できた

段 4 は絶対規律 6 に従い「role が指示めいた内容を申告したら fail-closed で停止する」と裁定した。
実装はその分岐を正しく置いた。しかし proposal file を通常の JSON 読み込みで読むため、
同じ object 内に `instruction_like_content_detected` を `true`、続けて `false` と書くと
**後勝ちで前者が消え、schema・停止分岐・参照整合性のすべてを通った。**

repo には既に重複キーを拒否する parser が 2 つある。使っていなかっただけである。

## 中心的な主張が段 6 まで一度も証明されていなかった

「旧 manifest の digest を 1 byte も変えない」は本 wave の設計目的そのもので、
既存 K2 campaign の識別子を保つための制約である。ところが段 5 が書いたテストは、
戻り値を**同じ module の定数**と突き合わせるだけだった。定数と生成側を同時に変える実装でも緑になる。

段 6 のレンズ D がこれを指摘し、実在 campaign `p3-s4-loop-s4-autonomous-b6dde2ef` の
**受領証 canonical bytes 全体**を literal golden として固定した。digest
`6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406` も literal で入っている。

同じレンズが、`main()` の知識射影テストが**検査対象を差し替えたうえ期待値も同じ生成器を呼び直して
作っている**ことも見つけた。生成器が欄を落としても緑になる恒真テストである。

## 変異の期待 node は推測でなく probe で採った

段 6 のレンズ D が「事前登録した 9 件のうち 6 件で期待 node が完全集合でない」と指摘した。
`DW-M07` に従い、**全件 SURVIVED 期待の probe を先に走らせて観測 node を採取**し、その実測値を
期待値にして本走した。レンズ D は候補集合も提示したが、実測とは一部食い違った
(例: `t2246.m01` はレンズ D の推測 6 件に対し実測 9 件)。**推測で埋めなかったことが正しかった。**

## 変異結果 (本走、HEAD `20c0c126d`、baseline 緑・失敗 node 0)

| id | 位置 | 期待 | 実際 | 殺した node 数 |
|---|---|---|---|---|
| `t2246.m01` | 拡張形の空許可を外し、空 source を常に拒否する | KILLED | KILLED | 9 |
| `t2246.m02` | canonical value から宣言範囲欄を落とす | KILLED | KILLED | 6 |
| `t2246.m03` | 受領証 v2 の canonical manifest から宣言範囲と取得実績を落とす | KILLED | KILLED | 4 |
| `t2246.m04` | 閉じた proposal schema の K2 分岐を legacy 分岐へ差し替える | KILLED | KILLED | 6 |
| `t2246.m05` | 参照整合性検査の呼出しを除去する | KILLED | KILLED | **1** |
| `t2246.m06` | 材料レポート schema の拡張形へ非空要求を戻す | KILLED | KILLED | 7 |
| `t2246.m07` | 論理 output schema 検証の呼出しを除去する | KILLED | KILLED | **1** |
| `t2246.m08` | 指示めいた内容の申告での停止分岐を除去する | KILLED | KILLED | **1** |
| `t2246.m09` | 同分岐の条件を反転し正常な申告まで拒否する (過剰拒否の正例) | KILLED | KILLED | 6 |

**9/9 KILLED、期待と完全一致 (matching=9)。**

`m05` / `m07` / `m08` はちょうど 1 node で、単一理由性を実測で確認した。
`m05` (参照整合性) と `m07` (論理 output schema) が互いに遮蔽しないという段 4 の親判断と
段 6 レンズ D の独立判定は、実測でも一致した。前者の入力は `use` 欄を持つ範囲外 index、
後者は範囲内 index で `use` 欄を欠く入力で、拒否できる層が排他である。

`m09` は承認外の過剰拒否の正例であり、`m08` と対で
**「必要なときだけ止まる」ことの両側の証拠**になっている。

## 冗長 gate として単独変異の証拠から外したもの (DW-M03)

段 6 のレンズ C が名指しした恒真述語のうち、変異登録に影響するもの。

- `wal.py` の宣言範囲・取得実績の再検査 2 箇所 (前段の digest 検査と受領証検査が同じ値を先に見る)。
- 拡張 schema の内側 `required` (外側で既に required)。
- output schema の wrapper 2 階層の required / additionalProperties
  (閉じた proposal schema の exact key 検査が先に走る)。
  **ただし schema の型・enum・`knowledge_use` item 検査は恒真ではない**ので、
  `t2246.m07` は帰属可能なまま (実測でも 1 node で KILLED)。

## 却下した設計 (一次資料は verbatim/ の各逐語)

- **外部取得を実行し結果が空だったことを独立に証明する retrieval receipt。**
  D1570 自身が救済を「宣言 + 記録」と定めており、D1429 は許可リストや機械的 leak 判定の
  初手新設を絶対規律 5 違反として却下している。機構は足さず、受領証の `declaration_status` へ
  「呼び手の宣言であって取得行為の証明ではない」と明記した。
- **宣言範囲と投入 source の包含判定。** 同上。
- **受領証分類の閉集合を試行台帳の読み出し側でも強制する。** 本 wave が持ち込んだ欠陥ではなく、
  生成側は既に強制している。次タスクへ繰り越した。
- **role の分類申告が親の受領証と矛盾したときの拒否。** role の自己申告は親の受領証を
  上書きしない (D1494) という境界を、逆向きにも守る。
- **取得件数と投入件数の等値要求と `completed_nonempty` の一般機構。**
  3 件取得して 1 件だけ投入する正当な状態を表現できなくなる。空の場合だけに閉じた。
- **`m07-control` の等価変異。** T-2183 が同じ等価性を既に実測している。

## 主張の境界 (これを超えて書かない)

- **言える:** 宣言した取得・投入の範囲、取得実績、取得結果が空であるという事実が、
  manifest → 受領証 → campaign identity → 試行台帳 → 材料レポートへ束縛された形で記録される。
- **言える:** 旧 2-key manifest の canonical bytes と digest は 1 byte も変わらない。
  既存 K2 campaign の識別子は保たれる。受領証 bytes 全体の literal golden で固定した。
- **言える:** K2 role の出力に対する参照整合性検査が、production の proposal 経路から
  呼ばれるようになった。論理 output schema 検証と、指示めいた内容の申告での停止も同じ経路にある。
- **言わない:** 取得結果が空であることが実際に外部取得を行った結果であること。
  これは呼び手の宣言である。
- **言わない:** 投入 source が宣言範囲の内側にあること。selector は強制機構ではない。
- **言わない:** 参照整合性が照合したのが role の実際に読んだ入力であること。
  照合対象は campaign が束縛した知識射影である。
- **言わない:** 既存 K2 campaign が replay / resume できること。digest と識別子は保つが、
  WAL は存在せず contract-loader 閉包の記録値は現 HEAD と既に異なる。
- **言わない:** この配線が発火した実績があること。**K2 role の wrapper が proposal 経路を
  通った実成果物は 0 件である。**

## 親が実走した検査

| 検査 | 結果 |
|---|---|
| 焦点走 1 回目 (参照関係で引いた 43 file、修正前) | 1 failed (非帰属、下記) |
| 焦点走 2 回目 (同 43 file、修正 1 巡目の後) | 3760 passed / 2 failed (非帰属 1 + 新テストの期待値ずれ 1) |
| 変異 probe (4 file、10 走) | baseline 緑、9 件すべてで観測 node を採取 |
| 変異本走 (4 file、10 走) | **9/9 KILLED、matching=9、baseline 緑** |
| `check_codex_agents.py` | rc=0 (0 native active / 14 static dormant) |
| `check_docs.py` | rc=0 |
| AI provenance 全史監査 | rc=0 (8062 件、新規違反なし) |
| **受入全走** | **`child-green`、20469 passed / 68 skipped / 0 failed** |

実装子と fix 子はいずれも投入 infra の `rc=16` で pytest を実走できず、実測はすべて親が行った。
**子の非実走を緑として数えていない。**

## 非帰属赤 1 件 — 受入全走で偽赤と確定した

焦点走で
`orchestrator/tests/test_profiler_directive.py::test_derived_directive_is_accepted_by_the_role_policy_check`
が `ModuleNotFoundError: No module named 'codex_roles'` で失敗した。
本 wave の `orchestrator/codex_roles/policy.py` への差分はコメント 2 行だけで、
この例外を生む経路がない。当該テストは接頭辞なし import を使い、`orchestrator/` が `sys.path` に
載っていることを前提にする。`DW-O18` の「file 選択走は `from tests import` 確立後に限り
未確立赤も偽赤」の型である。

**受入全走 (20469 passed / 0 failed) で同 node が通り、偽赤であることが実測で確定した。**

## 親の誤り (訂正)

merge commit `20c0c126d` の本文に「この merge は両親を超える実装面の内容を導入していない」と
書いたが、**これは誤りである。** `git diff-tree --cc 20c0c126d` は `p3_s4_loop.py` の 1 hunk を出す。
解消した行そのものは wave 側の親の逐語と同一だが、その周囲で自動 merge が main 側の変更
(`if a.b4_reflux_ablation:` 分岐と `default_cfg` 呼出しの削除) を適用したため、結果の領域が
両親のいずれとも異なる組合せになった。**この merge は真の合成を含む。**
同 commit の Codex `role=author` trailer は正しく、合成監査
(`verbatim/s6-merge-audit.md`) も別途行って must-fix ゼロを確認した。
履歴は書き換えず、この訂正を記録として残す。

## 運用上の実測 (次の wave が踏まないために)

- **merge 進行中の作業ツリーでは Codex 子を一切起動できない。**
  main 取り込みが `docs/dev-wave/operations.md` を変更していると、merge が staged の間は
  working tree が authority commit と異なるため、子が段によらず rc=2 で止まる。
  `DW-O17` の「非 ff は競合解消してから commit」と `D95` の「実装面の解消は Codex author」は、
  merge が dev-wave 文書を持ち込む場合に同時に満たせない。
  本 wave は「merge を一度戻し、clean な別ツリーで Codex author に先回りの適合を書かせ、
  それを commit してから merge し直す」で回避した。
- **変異 harness は login node での `--runner-mode local` を拒否する。** 計算ノードへの投入のみ。
  キュー混雑時は D612 の待ち上限上書き (900→3600 秒) を使う。
- **中断した投入の hold は手動 qdel しない。** 記録が「手動 qdel は別の防壁を発動させ、
  その解除もユーザー手番になる」と明示している。自然終了を待ってから hold の 2 file を消す。
