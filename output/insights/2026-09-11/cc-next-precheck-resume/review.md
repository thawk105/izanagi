## 総括

**blocking所見なし。** `HEAD 76928e91e` と `main d85bbb211` の差分は指定docs 3ファイルのみ。

1. **refuted：今回のdocsが前回の赤を起こす処理変更を含む。**
   `fabc967473` は文書追加のみ。workerの失敗境界はmanifest待ち3秒（`orchestrator/tests/test_codex_worker_launch.py:7005`）と終了待ち10秒（同`:1159`）。変更文書の本文を判定入力にする経路は確認されず、親の非帰属判断を反証しない。
   ただしT1259は実repo全体を走査する（`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:163`）。**走査負荷への間接影響まで「到達不能」と断定するのは強すぎる**。F945/F273も今回の遅延原因を直接証明するものではない。

2. **real：mainのT1259修正は前回の失敗箇所を変えている。refuted：テスト削除・緑の偽装。**
   `e28a62d26` は各ケースの実走査をmodule snapshot＋ケース別deepcopyへ変更し、既存real-repo群へ登録。setupを含む排他は `orchestrator/tests/conftest.py:2179`。assertion削除・skip追加・timeout緩和はない。初回走査と30秒制限は残り、再発解消は未実証。

3. **refuted：指定されたrun-cardの説明が現mainと矛盾する。**
   - 値探索：単一リテラル・単一文の検疫（`backoff_hole_grammar.py:702`）、整数値域の検査（同`:745`）。
   - role休眠：native 0／static 14／runtime blocked（`.codex/agents/README.md:1`、`tools/check_codex_agents.py:249`）。
   - critic bool：カウンタ更新と停止判定（`p3_s4_loop.py:2213`、`:1280`）。次生成のwhiteboard・測定入力とは別経路（同`:1198`、`:1222`）。rich反例の自動入力とは扱っていない。

**非実走範囲：** 読取り・静的差分照合のみ。テスト、checker、実験、変更、commit、landは未実施。受入の緑は報告しない。
