# [T-337] / [T-479] / [T-318] — 種別宣言 `declared_use_class` の実装 (2026-08-18)

wave: `dev-wave-t337-t479-t318-use-class` / branch: `worktree-dev-wave-t337-t479-t318-use-class`
起点 main: 38f173cb / 取り込み main: 0482dc39

## 何をしたか

campaign producer に利用意図の種別 `declared_use_class` を**宣言必須**で持たせ、
族の外延をファイル名列挙から宣言由来の閉包検査へ移した。設計判断は decisions 台帳の新 D が正本。

## 起動命令の前提が覆った 2 件

1. **field 名は既に pin 済みだった。** `declared_use_class` は D282 pin 済み受領証 schema
   (`output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1248`) に
   enum `["official","exploration","qualification","dry"]` として実在し、D500 決定 (4) が
   本文で同じ意味に用いていた。新 D の役目は候補選択ではなく条文化と supersede になった。
2. **RF 受領証 producer は前日に閉じていた。** D500 (2026-08-17) が閂を投入 gate と同定し、
   残余の land を名指しで禁じている。実装可能な残余は D123 決定 (2) 軸だけだった。

## 一次資料が決めた読み

段 3 レンズ B は「T-318 を campaign namespace 軸と読むのは非同値なすり替え」として NO-GO を
出した。親が一次資料を逐語で開いて反証した。

`docs/archive/worklog-phase3-0802-113-116.md` の (116):

> **[T-318] は (a)** — producer ごとに `artifact_role` を宣言させ閉表で管理する。ファイル名列挙は
> **D123 決定 (2) 自身が弱点と自認しており**、新規 producer の更新漏れで静かに崩れる。

T-337 は同じ枠への適用先である。`docs/archive/worklog-phase3-0802-117-121.md` の (121):

> **[T-337] は (a)** — 正例 artifact の適格性は新 D で権威境界を定義し `artifact_role=qualification`
> を **[T-318] 準拠で置く**。

したがって本 wave = T-318 の機構 + T-479 の名前確定であり、T-337 の適用は D500 が保留している。

## wave 前の実コードが、禁じられた形そのものだった

`orchestrator/campaign/loop.py` の `campaign_namespace: str = "official"` により、
種別を宣言しない producer は黙って official namespace へ書けた。ユーザーが scope 外として
名指しで禁じた「宣言なしを既定で official 扱い」が、実コードに入っていた。

この vector を突くテストは wave 前 0 件で、既存の
`test_run_campaign_default_namespace_remains_official` はむしろ**省略時 official を正例として
固定**していた。本 wave の検査は純増の検出力である。

## 敵対レビューが是正した親の誤り

- `artifact_role` の production は 3 file でなく **2 file**。親がテストを数えていた。
- 「探索由来 campaign が official 受理集合へ入る経路を閉じる」は**過大**。実際に防げるのは
  宣言の省略であって、`official` と誤って申告する事故ではない。caller の自己申告が意味 gate に
  ならないことは D162 決定 (1) が既に条文化しており、producer identity 束縛は本 wave の射程外。

## 段 6 の must-fix 3 件 (親が実測で全件 real と確認)

1. **閉包 meta-test の負例が恒真だった。** 負例テストがローカル関数で判定規則を書き直しており、
   本物の閉包検査を固定リストへ戻す変異を落とせる node が 1 つも無かった。
   fix 後は fixture も実検査も同じ `_campaign_driver_is_closed` を通る。
2. **走査が `ast.Name` 形限定で素通り経路があった。** `layout.exploration_campaign_layout(...)` の
   ような module 修飾の呼び出しは campaign root を作るのに検出されなかった。
   fix 後は attribute 形も検出し、負例 fixture 自身が module 修飾形を使う。
3. **個数 assertion が差分で削除されていた。** `assert len(layout_calls) == layout_count` と
   `assert len(run_calls) == run_count` が消え、余分な root / run が緑になる状態だった。
   fix で宣言由来の形へ復活させた。

加えて移行漏れの consumer 1 件 (`test_trigger_gate_binding.py` の signature 検査)。

## 実測

- 焦点走 (計算ノード、request 921866.nqsv): **1006 passed / 1 failed / 9 skipped**、49.99 秒。
  唯一の赤は `test_p3_s4_loop.py::test_checkpoint_direction_and_magnitude_domains_match_role_policy`
  の `ModuleNotFoundError: No module named 'codex_roles'` で、file 選択走の import path 未確立に
  よる**偽赤**。当該 module は `orchestrator/codex_roles` に実在し、`orchestrator/` を sys.path へ
  載せれば import できる。差分は当該 file に触れていない。
- 変異 matrix: **baseline PASSED・11/11 KILLED・SURVIVED 0・MISMATCH 0** (HEAD 9867082a)。
  第 1 変異は wave 前の実コードの形 (必須引数へ `= "official"` 既定値を戻す) である。
- 全史 provenance 監査: 4099 件、新規違反なし。`check_docs.py`: 違反なし。
- 凍結 source pin の不一致は wave 前から存在する (記録 `9b64f34bac37…67dbf4` /
  現物 `9a27a97ac271…89e3c`)。検証は計測 checkout の resolver 経由で live tree に束縛されない。

## 塞げていないもの (塞いだと書いてはならない)

- **`official` の誤申告は検出できない。** 宣言は利用意図であって権威ではない。
- **`run_campaign` を通らない producer の runtime gate は無い。** 8c は
  `exploration_campaign_layout` を直接呼ぶため、宣言と閉包検査の対象ではあるが必須引数の
  gate は通らない。trial-local layout の型分離は D123 決定 (4) が別裁定へ送済み。
- **閉包検査は静的走査である。** 動的に layout を構築する producer は AST 走査を回避しうる。
- **RF 9 層は 0/9 のまま。** 所在の実測表は `nine-layer-map.md`。

## 収録物

- `nine-layer-map.md` — RF 9 層の所在実測と被覆計画。
- `verbatim/` — 段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 6 敵対 2 レビュー、fix 報告、
  取り込み監査報告の逐語。
- `mutation-spec-final.json` / `mutation-final2-ledger.json` — 変異事前登録と結果台帳。
