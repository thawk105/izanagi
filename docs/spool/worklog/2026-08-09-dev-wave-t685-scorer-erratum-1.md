---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t685-scorer-erratum
seq: 1
title: 採点器の曖昧さ検出が恒真だった — 相反する総括を 13/18 受理していた面ごと閉じ、[T-181] へ erratum を添えた (コード + docs、受入 7727 passed / 20 skipped、変異 11/11 検出・SURVIVED 0、branch worktree-dev-wave-t685-scorer-erratum)
---

## 本文

- **ユーザー裁定 (b) を実施した。**10 run は再走せず、`codex_reasoning_ab.score_text` の
  decision 抽出欠陥 (F176) を Codex `role=author` で是正し、[T-181] の認証済み台帳へ
  erratum を添えた。裁定の台帳側正本は main エントリ 347 の [T-685] 項。
- **段 1 の実測で、裁定が想定していなかった面が出た。**F176 は「正例 1 本を落とした」
  取りこぼし側だけを記録していたが、同じ lookahead は**受理側にも効いていた** —
  相反・否定を含む 18 種のうち **13 種を valid として受理**していた
  (`GO。しかしNO-GOでもある。` が `valid=True / decision=GO`)。曖昧さ検出は存在するのに
  発火しない恒真ゲートだった。{{F:scorer-conflict-guard-inert}} に記録した。
- **段 4 で採った設計を段 6 で撤回した。**段 4 は「決定語を広く抽出し、
  『条件・理由』の名詞修飾かつ同一文内に否定があるものだけ言及として除外する」案を採ったが、
  段 6 の敵対レビューが実装後のコードを直接叩いて 2 件を示した。
  (i) 無関係な否定を借りて相反決定を除外できる (`GO。NO-GOの理由は明白であり、これを採用しない選択肢はない。`)。
  (ii) 「反対語を検討して棄却する」自然な総括 20 文が HEAD では 20/20 受理なのに **0/20** になる。
  **両方が同じ根から出ている** — 主張か言及かは意味判定で、正規表現で分離しようとすると
  必ず両方向に外す。よって分離を試みる設計自体を捨てた。
- **代わりに採ったのは「抽出は据え置き、閉じた断定形と和集合を取る」案である。**
  受理集合の変化が両方向とも列挙できる — 従来拒否 → 新たに受理となるのは
  「抽出が空になる場合」(= F176 そのもの) と F176 が名指しした 4 表記だけで、
  それ以外はすべて拒否方向。親が production を触らない prototype で 41 項を実測してから
  実装子へ渡した。
- **焦点再レビューが親の設計の穴を 1 つ見つけた。**`{opening_decision}` を和集合へ足す処理は
  恒真で、変異させても生存する (冒頭 grammar が受理する形はすべて断定形の第 1 枝にも一致する)。
  fix 2 巡目で削除した。削除前後で 48 ケースの返却値が完全一致することを実装子と親の双方で確認した。
- **本 wave が閉じない面を 2 つ、正直に残す。**どちらも変更前と同挙動で回帰は無い。
  (i) 意味を伴う言及形の相反主張 (`GO。NO-GOの理由は明白であり…`) と英語の否定
  (`GO。GO is not the final decision.`) は通る。
  (ii) 他者・過去の判定を断定形で引用する総括 (`NO-GO。上流はGOと判断した。`) を過剰に拒否しうる。
  こちらは本 wave が新たに作った面だが、焦点再レビューが `output/insights/` 配下の
  `## 総括` を持つ実在 `.md` **1,065 件**を HEAD と新実装で全数比較し、
  **HEAD 受理 → 新実装拒否は 0 件**だった (差分 2 件はいずれも逆方向)。
  **2 つの誤りは対称でない**と裁定した — 誤受理は相反した総括を黙って台帳へ入れ、
  誤拒否は `failure_class="post-treatment"` として記録に残り人手裁定で回収できる
  (s03 が実際にそう回収された)。観測可能で回収可能な側へ倒した。{{T:scorer-decision-grammar-contract}}。
- **erratum は「decision 行だけ」ではないことを一次資料で確かめて書いた。**
  汚染は 8 field へ伝播している。とくに `adoption_eligibility` は max だけでなく
  **high も false** で、s03 が正常採点されていれば両 arm とも true になる —
  [T-184] が機械行を引用すると結論が反転する。
  human-derived の join (POS/high 3/3、POS/max 3/3、NEG 各 0/2、両読者一致 10/10) と、
  `neg_excluded_arms` が空である根拠 (両 verdict の findings 0 件。judgments だけでは足りない) を
  自分で計算して照合した。
- **是正後の装置で旧 manifest を `verify` すると rc=24 になる**ことを erratum に警告として書いた。
  `_replay_manifest` が凍結 score と canonical bytes 比較するためで、台帳の無効化ではなく
  装置が変わった事実の現れである (F61 の帰結)。
- **手順違反を 1 件自己申告する。**親が変異 spec を書く際、段 6 裁定の変異表を更新しないまま
  spec だけを書き換えた (1 件を落として番号を詰め、裁定に無い変異を 1 件足した)。
  焦点再レビューが指摘し、続く実走前検査でさらに 2 件の欠陥が出た。
  {{F:mutation-spec-diverged-from-preregistration}} に記録した。
- **変異は実走前検査で 2 件を潰してから本走した。**M05 は fix 2 巡目で消えた行を anchor に
  しており harness が `anchor count=0` で fail-closed に中断した (実装は無傷)。
  M12 は期待 node を反転させず生存すると判明したので登録から外した。
  残る 11 件を memory 上で変異させ、全数で判定が反転することを確認してから投入した。
  **本走は 11/11 検出・SURVIVED 0・期待 node は 11/11 で発火** (完全一致 6、
  同じ正規表現の枝を突く姉妹 param による過剰決定 5)。harness の rc=1 は MISMATCH の
  厳格判定によるもので、生存ではない。M10 (抽出を widen する変異) では歴史 control
  `test_m10_historical_controls` も落ち、段 1 の実測が独立に再現した。
- **段 5 / 段 6 の実装子・fix 子はいずれも pytest を実走できなかった**
  (`qstat -Q` preflight rc=1、runner rc=16)。3 子とも「実装済み・未実走」と正直に申告した。
  テスト実測はすべて親が行った (対象テスト 139 passed / rc=0、受入全走 tip 64315fb9、request 898047.nqsv、1406.80 秒、7727 passed / 20 skipped / rc=0)。
- **記録機構の穴を 1 つ見つけた。**`docs/spool/failures/` の fragment は「新規」と「再発」しか
  扱えず、**既存 F の恒久対応欄を「実施済み」へ更新する経路が無い** (現在 10 件が「未実施」のまま)。
  F176 も同じで、canonical 台帳を wave が直接編集するのは禁じられているため迂回しなかった。
  新規 F の本文から F176 の恒久対応の実体を指す形にした。{{T:spool-failures-update-path}}。
- 軽量版の判断: ユーザー指示の「軽量」は 10 run 再走の回避と 9 段フル儀式の回避と解し、
  `DW-C00` が「正しさ防壁に触る / 受理集合が変わる」段で敵対検証子を禁じていない以上
  省略できないため、段 2・3・6 を最小構成 (プラン 1、レンズ 2、レビュー 2、焦点再レビュー 1) で実施した。
  **結果としてレビュー 3 本すべてが実効のある所見を返し、設計を 2 度組み直した。**

## 次の一手差分

### 完了

- [T-685] 採点器の是正と control 追加を実施し、[T-181] へ erratum を添えた。
  10 run の再走はしていない。残るのは {{T:scorer-decision-grammar-contract}} の裁定。
  remaining: none
  base: 7cc5581e0504eb88ea590e8bf581671a61c923830bcfca564bca9bd1b8e7451f

### 更新

- [T-181] **P1・完了 → [T-184] へ引き渡し可**: 認証済み台帳
  (`output/insights/2026-08-09_t181-certified-rerun/`) に erratum
  (`erratum-f176.md`) を添えた。汚染 8 field の列挙、[T-184] が使ってよい human-derived の
  join (POS/high 3/3、POS/max 3/3、NEG 各 0/2)、是正後装置での replay mismatch 警告、
  retention 宣言を含む。**機械 `decision` 行・`primary_judgment_ledger`・両 eligibility の
  実質的引用を禁じる。** 2026-07-30 の旧成果物は再検証不能のため引用しない。
  base: bf8aa7eb93a7b8b739c85ab28f4855a2028544c8b17924bd6b1df2e920d2d159

- [T-184] **P1・入力が揃った**: [T-181] 依存は erratum 付き台帳で充足した。
  読むべき正本は `output/insights/2026-08-09_t181-certified-rerun/erratum-f176.md`。
  [T-184] 全体の開始可否は [T-180]〜[T-183] の状態による。
  base: e197e21f2bee014e2ef1baaa824a055e01feda1d2e0aedb8179991e85a987088

### 新規

- {{T:scorer-decision-grammar-contract}} **P2・新規**:
  `codex_reasoning_ab` の決定 grammar が正規表現である限り、「主張」と「言及」を分離できず
  両方向に外す。残る面は 3 つ — (i) 意味を伴う言及形の相反主張が通る、
  (ii) 英語の否定・相反が通る (`decision_disclaimed` も抽出も日本語前提)、
  (iii) 他者・過去の判定を断定形で引用する総括を過剰に拒否しうる。
  (i)(ii) は変更前と同挙動、(iii) は本 wave が作った面だが実在 1,065 件では未発火。
  選択肢は (a) 出力言語と総括の書式を prompt 側の契約で狭める、
  (b) 二読者の人手裁定を機械 decision の上位に置くことを明文化する、
  (c) 現状を「観測可能な側へ倒す heuristic」と明文化して受容する。
  実害の実測が無いので (c) から始めるのが安いが、(a) は再発を構造的に減らす。

- {{T:spool-failures-update-path}} **P2・新規**:
  `docs/spool/failures/` の fragment は「新規」「再発」しか持たず、**既存 F の恒久対応欄を
  更新する経路が無い**。現在 `docs/failures.md` の 10 件が「恒久対応: 未実施」のままで、
  そのうち F176 は本 wave で実装済みだが台帳上は未実施に見える。
  wave が canonical を直接編集するのは禁止されているため迂回できない。
  選択肢は (a) fragment に「更新」節を足す (対象 F と差し替える行を base digest 付きで書く)、
  (b) 恒久対応の状態を F 本文でなく別の索引に持つ、(c) fold 後に人手で直す運用を明文化する。

- {{T:conflict-failure-reason-diagnostic}} **P3・新規**:
  相反決定で落ちても failure reason が `summary does not start with one GO/NO-GO decision` のままで、
  冒頭 grammar 不良と区別できない。受理集合は変わらないので診断の質の問題。
  規律 3 (なぜ壊れたかを構造化して返す) の観点では直す価値がある。
