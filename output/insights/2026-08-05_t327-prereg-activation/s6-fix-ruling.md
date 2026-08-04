# [T-327] 段 6 fix 裁定 — 2026-08-05

敵対レビュー 2 本はいずれも **NO-GO** (rev1: blocker 7 / must-fix 4 / should 2、
rev2: blocker 4 / must-fix 5 / should 1)。親が real/refuted を裁定し、fix の範囲を確定する。

**fix は一枚岩の 1 子で行う** — 所見が module 横断 (core / evaluator / 契約 JSON / 3 テスト) で
相互依存しており、所有を素集合に割れないため (`DW-S06-B`)。

## 0. 本 wave の看板をさらに正確にする (rev1-8 / rev1-2 / rev1-10 の帰結)

レビューは「machine-checkable と称する 6 述語は、対象機構でなく no-op と文字列の存在を証明して
いる」「残り 6 述語は機構が完成しても永久に undefined」と実証した。**両方 real。**

**裁定**: 12 述語すべてを**本 land では SATISFIED にできない形へ揃える**
(`machine_checkable: false`)。本 wave が land するのは次の 2 つに限る。

- **(i) 条件契約の凍結機構** — これは実効である (無記録変更・空改訂・履歴改竄・改訂の裁定参照)。
- **(ii) 発効判定の枠組み** — fail-closed で、現状は常に**未発効**を返す。

述語の green 化 (production consumer を実証する completion-sensitive evaluator) は後続タスク
**U-8** として返す。文書・worklog にこの射程を明記し、「発効を強制した」とは主張しない。

## 1. real 採用 — fix する (F1〜F14)

|ID|所見|裁定|fix 内容|
|---|---|---|---|
|F1|rev1-1 / rev2-1: 公開 API の `registry=` 注入で発効 capability を偽造できる。core module 自身も C と照合されない|**real・blocker**|production entrypoint から registry 注入を除去し、テスト注入は明確に分離した private 経路にする。実行中の core / evaluator module bytes が `C` の blob と一致しないときは fail-closed (未発効) にし、両 hash を report に載せる|
|F2|rev1-2 / rev1-10 / rev2-2: AST の名前・文字列の存在だけで SATISFIED になる。no-op fixture を「正解の green」として固定している|**real・blocker**|12 述語すべて `machine_checkable: false` へ揃え、**SATISFIED を返す経路を持たせない**。no-op green fixture を削除し、「no-op / token だけでは充足しない」ことを検査するテストへ置換する。将来の green 追加時に negative control を要求する meta-test は残す|
|F3|rev1-3: 凍結 namespace が証拠契約自身の必須 artifact (manifest / schedule / sample plan / cap-lift) を拒否し、正しく実装するほど発効不能になる|**real・blocker**|世代台帳を専用 subdirectory (`output/s8c-preregistration/condition-freeze/`) へ分離し、閉じた namespace はその subdirectory だけにする。運用 artifact の置き場と混同しない。親が文書と g1 を追随|
|F4|rev1-4 / rev2-3: gN の「人間裁定必須」が任意 archive 中の字面一致で通る|**real・blocker**|裁定参照を**構造検査**にする — `docs/decisions.md` の `## D<N>.` 見出しとして、その改訂 commit 時点に実在することを要求する。自由文検索・任意 path を authority にしない。g1 は `null` 可|
|F5|rev1-5: `EffectivePreregistration` を `_construct_effective` / `object.__new__` / `dataclasses.replace` で偽造できる。証拠 list が mutable|**real・blocker**|frozen dataclass + tuple 化 + factory の private guard で難度を上げる。**同時に「Python 型を信頼境界にしない」を docstring と文書へ明記**し、consumer は `C` と report digest を毎回再検証する契約にする (完全な防止は Python では不可能であることを正直に書く)|
|F6|rev1-6 / rev2-7: §5 が `null` / `""` / `"未記入"` の JSON でも FILLED になる|**real・blocker**|null・空文字列・空 container・placeholder 等価文字列を拒否する。欄ごとの型 schema は引き続き scope 外 ([T-295])|
|F7|rev1-7: 正規化が H2 見出し文言と fenced code / prose の区別を落とすため、規範節を「非規範」へ改名したり code block 化しても hash が不変|**real・blocker**|canonical form に節見出しの文言と node kind (見出し / 段落 / list / code) を保持する。layout-only の正例テストと node-kind の負例テストを分ける|
|F8|rev1-9 / rev2-6: 事前登録変異 m01 (`all`→`any`) と m14 (merge 遷移) をテストが kill しない|**real・must-fix**|m01 は 11 SATISFIED + 1 非 SATISFIED の混合 fixture を全 12 位置で回す。m14 は merge 遷移だけを単独で撃つ fixture (先行 guard に当たらない) と exact reason で検査する|
|F9|rev2-4: invariant test が `HEAD` を見るため、commit 前の段 6 受入と構造的にデッドロックする|**real・blocker**|index / worktree から候補 commit を合成して検査する経路を持たせ、**未 commit 差分でも同じ性質を検査できる**ようにする。検査を弱めて回避しない|
|F10|rev2-10: 現 HEAD の reason code 12 件を丸ごと snapshot 期待値に焼き込み、他 wave の land で赤くなる|**real・should→採用**|「SATISFIED 0 件」の安全 invariant と、個別 reason の対象テストを分離する。個別 reason を固定するテストには更新契約をテスト名か docstring に書く|
|F11|rev1-12: git subprocess に timeout がなく、巨大履歴・世代番号で明示拒否へ到達しない|**real・should→採用**|git 呼び出しの timeout、世代番号・commit 数・blob bytes の上限、超過時の閉じた reason code を足す|
|F12|rev2-8: 「祖先であることではない」という新規文が §1・D116・C08 の ancestry 要件と矛盾する|**real・must-fix**|**親が文書を修正** — 「`C` において発効していること**かつ** `C` が測定 HEAD / 結果 commit の祖先であること」の**両方**を要求する。ancestry は必要条件であって十分条件ではない、と書く|
|F13|rev2-9: D116 は「8c へ凍結機構を導入しない」と決めており、それを supersede せずに hash 世代台帳を D116 の名で導入している|**real・must-fix**|**親が decisions fragment を起票** — [T-327] が D116 決定 (1) を「条件契約の hash 世代台帳を持つ」範囲でのみ supersede し、git ancestry を先後の主機構とすること・8b freeze 非変更・承認 record / active pointer / 失効 record を導入しないことを境界として固定する|
|F14|rev1-11: brief の (P3) 理由と `DW-O09` 記録が裁定どおり更新されていない|**real・should→採用**|**親が brief を更新** (query・key/role 側検索結果・分類を記録し、(P3) の理由を「compact canonical contract」に限定)|

## 2. 裁定パッケージへ追加 (U-8)

- **U-8**: 12 述語を「production consumer を実証する completion-sensitive evaluator」へ引き上げる
  設計と実装 (rev1-2 / rev1-8 が要求する end-to-end control)。本 wave では意図的に行わない。

既存 U-1〜U-7 は据え置き。U-1 (launch / acceptance 結線) は本 fix 後も未結線のままである。

## 3. refuted / 降格

- rev1-5 の「完全な偽造不能化」= **不可能**と裁定 (Python の型は信頼境界にならない)。
  F5 は難度向上 + 正直な限界記述に留める。
- rev1-8 の「6 述語が永久 undefined」= F2 の全面降格により**全 12 述語が同じ扱い**になるため、
  個別の欠陥ではなく本 wave の射程として文書化する。

## 4. fix 後に親が行う実測

1. 3 テストファイルの実走 (計算ノード dispatch)。
2. g1 の再生成 (F3 の path 変更と F7 の正規化変更で hash が変わるため) と統合 commit。
3. `check_docs.py`、`check_codex_agents.py`、変異 matrix (m01〜m17)、受入全走。
4. 焦点再レビュー (`DW-O16`、closed / partial / regressed 表)。
