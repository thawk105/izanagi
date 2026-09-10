# 段 6 レビュー所見の親裁定 (fix 子への指示の正本)

対象 commit `4d573b038`。レビュー 2 本 (`s6-reviewA.md` = 整合レンズ、`s6-reviewB.md` = 実効性レンズ)
の所見を real / refuted に裁定した。

## must-fix (全部直すこと)

### F1. production 封印が受理記録の検証を通さずに鋳造できる

**両レンズが独立に指摘。最重要。**

`VerifiedB4AdmissionRecord` (`orchestrator/campaign/p3_b4_admission_record.py:115`) は
任意の値で直接構築できる。`_create_b4_production_context`
(`orchestrator/campaign/p3_b4_launcher.py:248`) は型だけを見て production 封印を発行し、
その値が実 `verify_b4_admission_record` 由来かを検査しない。
`_bind_b4_campaign` (`:268`)、`_write_b4_launch_sidecar` (`:312`)、
`_activate_b4_launch_context` (`:344`) もすべて module 属性として直接呼べる。

レビュー B が実際の到達経路を書いている。架空の受理記録を作る →
production context を得る → 実 `default_cfg` → campaign 束縛 → 起動記録の書込 →
context の有効化 → 公開 `p3_s4_loop.main(..., _b4_launch_context=context)` → bootstrap →
`run_campaign` → `pipeline.evaluate` → `wal.append`。
**この経路は起動器も実 `verify_b4_admission_record` も一度も通らない。差し替えも属性書換えも不要である。**

**これでは起動器が支配点になっていない。本 wave の目的が達成されていない。**

**直し方:** production 封印の発行者を closure の中へ閉じる。発行者自身が
受理記録の path を受け取り、実 `verify_b4_admission_record` を走らせてから封印を出す。
module 属性として公開するのは validator だけにする。
`_create_b4_production_context(VerifiedB4AdmissionRecord, ...)` の形を module 属性に残さない。

**テストの扱い:** production context を要る検査は、実際に commit された受理記録の fixture を
通すこと。`orchestrator/tests/test_p3_b4_closed_critic.py` に既に実 fixture の先例がある
(`create_b4_closed_critic_pair` を実 `admission_record_path` で呼ぶ検査)。それを再利用せよ。
**架空の `VerifiedB4AdmissionRecord` を作って production context を得る検査は全部書き換えること。**

### F2. G4 の driver 種別の照合が自分自身を期待値にしていて恒真である

`orchestrator/campaign/p3_b4_launcher.py:394-400` が
`expected_driver_kind=context.driver_kind` を渡している。context を context 自身と比べているので
この検査は必ず成立する。

**直し方:** 期待値を context の外から取る。起動記録または decode した lock の値と exact 比較する。

### F3. campaign 束縛が「`None` でないこと」しか見ていない

`orchestrator/campaign/p3_b4_launcher.py:225-228` の `require_campaign_binding=True` は
`campaign_id is None` だけを見る。現在の cfg / lock の campaign id、arm、driver 種別との
一致を見ない。

**直し方:** 各 formal 境界へ `expected_campaign_id` と `expected_arm` を渡し、
中央の helper で exact 一致を検査する。値は呼び手の申告でなく cfg または decode した lock から取る。

### F4. certified sink の分類が素通りに倒れ、識別語を複製している

`orchestrator/campaign/wal.py:411-424`。

1. `OSError` と `CampaignLockCodecError` を `False` に変換している。
   **lock が実在するのに読めない・decode できない場合は素通りではなく拒否にすること。**
   lock が存在しない場合だけ「B-4 でない」とすること。
2. `UnicodeDecodeError` を捕捉していないため、通常の COMMIT に新しい失敗経路が増えている。
   これも lock 実在時の拒否側へ寄せること。
3. 識別語 `"b4_protocol"` / `"p3-b4-reflux-ablation/v1"` を文字列で複製している。
   正本は `orchestrator/campaign/p3_s4_loop.py:116-117` である。
   **識別語を依存の低い module へ移し、3 driver と `wal.py` が同じ定数を import すること。**
   複製したままでは、正本が変わったときに関門が黙って発火しなくなる。
   これは本 repository が繰り返し踏んできた「謳うだけで発火しない保証」そのものである。

### F5. 既存テストの期待値を戻す

`orchestrator/tests/test_p3_s4_loop.py::test_b4_fixture_main_rejects_run_one_iteration_bypass_m13`
の期待値を、変更前の
`pytest.raises(L.B4ProtocolError, match="fixture run_one_iteration")` へ**戻すこと**。
実装の順序を変えて G1 へ到達させる必要はない。既存の関門が先に発火するのが正しい挙動である。

`orchestrator/tests/test_p3_b4_closed_critic.py` で旧 CLI 関連の 3 件を置換したこと自体は
裁定 R13 (旧 CLI を hard-fail 化) の結果なので**受理する**。ただし完了報告に、
置換後の各検査が何を固定しているかを 1 行ずつ書くこと。

### F6. M08 / M09 / M10 の副作用の観測が恒真である

**両レンズが指摘。変異事前登録の根幹に関わる。**

M08 / M09 は cfg 由来でない tmp layout を渡すため、G3 を外しても既存の layout 関門
(`orchestrator/campaign/p3_s4_loop.py:1241-1243`) が先に拒否し、campaign root も state file も
作られない。M10 は `T.exploration_campaign_layout` だけを差し替えており、
共有関門が参照する `L.exploration_campaign_layout` は差し替えていないので同じである。

**直し方 (レビュー B の案を採る):**
- M08 / M09 は共有の `L.exploration_campaign_layout` を対象 tmp layout へ差し替える。
- M10 は `T` と `L` の両方を同じ layout へ差し替える。
- 実 `run_one_iteration` を包む spy を置き、G3 を外したときに渡される state の
  `iteration == 1` を観測する。
- **永続化された state file の不在を「state が進んでいない」の証拠に使わないこと。**
  state の保存は G2 の例外より後でしか起きないため、その不在は恒真である。

### F7. 正例が差し替えすぎで、実体の証明になっていない

`orchestrator/tests/test_p3_b4_closed_critic.py:2442-2467` の正例は
`REPOSITORY_ROOT`、`ROLE_FILE`、`shutil.which`、controller の初期化、各 layout resolver、
snapshot / 受理記録 / digest、`ensure_resumable_attempts`、pin / 単独性検査、
`L.run_one_iteration` を差し替えている。

**直し方:** 実 `create_b4_closed_critic_pair`、実 driver `main`、実 `wal.append` は
差し替えないまま残すこと。そのうえで、**差し替えた対象を 1 つ残らず docstring に列挙し**、
「この正例が示すのは経路であって、科学処理本体の実体ではない」と明記すること。
完了報告でも同じことを書くこと。**「実 factory と実 driver を通って certified を確認した」とは書かないこと。**

## 受理する (直さない) — 理由を記録する

### A1. G1 が試験用の封印も受理していること

裁定 §3 は G1 に production context を要求すると書いたが、実装は試験用の封印も受理している。
**これは受理する。** 理由は次のとおり。

- 標本を生む境界 (G2 / G3 / G4 / G5) はすべて production context を要求する。試験用の封印で
  作った marker 付き cfg は、certified な標本を 1 つも作れない。**標本の受理集合は変わらない。**
- G1 を production 必須にすると、golden identity の検査すべてが実 commit 済みの受理記録を
  用意する必要があり、検査の費用が跳ね上がる割に受理集合が変わらない。
- レビュー B 自身が「意図的なら §5 の書き方をそう改めればよい」と代案を出している。

**したがって親は事前登録 §5 の文言を「封印されていない marker 作成を閉じた」へ改める。**
「起動器だけが鋳造できる」とは書かない。**この文言の変更は親が行う。fix 子は docs を触らないこと。**

### A2. COMMIT 後に lock を書き換えて B-4 へ再分類できること

**scope 外。裁定 §4 の 2 番目 (報告時の後付けの名乗り) と同じ形である。**
G4 は COMMIT の時点で marker があった経路だけを閉じる。
事前登録の文言は「COMMIT 時に exact marker が存在した経路だけ閉じた」と限定する。
**この文言も親が書く。fix 子は docs を触らないこと。**
