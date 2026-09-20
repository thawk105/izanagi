## 所見 (CA-1 …)

**推すのは A-3＋必要な test 修正 B。** production の変更は、承認済み active v2 の実行時に限り、T-080 の zero-hit 判定を既存の full launch validation に置換する。receipt のその他の検査・epoch 束縛は維持する。

- **CA-1 — receipt の無条件拒否は意図的だが、v2 との接続には欠落がある。** `_t080_adapter_refusals` の `None` は「legacy verifier へ委譲」であり、「receipt が無効でも実行可」ではない。`_make_gate_decision` と `_campaign_t080_value` の拒否を削って解決してはいけない。
- **CA-2 — A-3 の「未知性層 2 だけ委譲」は、そのままでは広い。** `_verify_holdout_live_scan` は zero-hit のほか、候補集合・candidate ID・検索式・照合規約を凍結文書と比較する。この束縛を失わず、**期待 hit の判定だけ**を v2 に委譲する必要がある。
- **CA-3 — active v2 が無い木は引き続き拒否される。** X1'＋G、A／X 無しの状態は A-3 後も zero-hit を満たさない。これは実装未完ではなく、批准前を実行可能にしないための境界である。
- **CA-4 — 初回 receipt 解決だけ直しても足りない。** `run_block` は campaign-start 前に `_resolve_t080_receipt` を再実行する。ここを旧方式のまま残すと再び invalid になり、epoch 比較で拒否される。
- **CA-5 — B は補助として必要。** draft fixture と official preflight は active v2 oracle とは別の契約を検査している。A-3 が着地しても、実 checkout の成果物を無差別に複製する経路 (i)(ii) は直らない。
- **CA-6 — 「A を実装すれば oracle 実走可能」とは断言できない。** 本件の阻害は解消できるが、D2120 が別管理とした spec 承認等は残る。A／X 後の実測もまだ無い。

## receipt の役割と設計意図

`t080_freeze_migration.py` 冒頭は「一回限りの移行専用」としつつ、発効後の gate が receipt の bytes、closure、live pin、live unknownness scan を検証すると明記している。**一回限りなのは移行であって、発効後の検証を省く宣言ではない。**

現行 driver は receipt を v2 より先に解決し、その refusal を常に集約する。さらに campaign の耐久記録に `active-valid` または `never-issued` を要求する。したがって、実装上は v2 active 後も receipt の履歴・有効性を要求する設計である。ただし receipt 未発行の正当な履歴は許されるため、「receipt 文書の存在が常に必須」とは異なる。

一方、v2 の C2-4 は承認済み artifact から導いた hit 集合と全走査の完全一致を要求する。D2077 step 7 が意図する拒否は **official 床値の再起動**であり、批准後の oracle まで恒久拒否することではない。

以上から、**receipt の fail-closed と epoch 維持は意図、v2 の正当な closure hit にも v1 zero-hit を重ねる部分は統合設計の穴**と判断する。原作者の心理的意図まで確定するものではないが、現物と裁定の要求はこの解釈が整合する。

## 択の比較表

| 択 | 期待集合の authority | 除外・検出力への影響 | 判断 |
|---|---|---|---|
| A-1 | 正規に承認・発効し、検証された世代が束縛する artifact | 除外を増やさず完全一致なら維持可能。ただし C2-4 の二重実装が退行要因 | 次善 |
| A-2 | v2 の承認・検証系へ全面移管 | receipt 履歴、欠落・改変検出、epoch 記録まで失う危険 | 最小案ではない |
| A-3 | 同一実行文脈の full launch validation が検証した active 世代 | zero-hit のみ置換。他の束縛と検査を残せば検出力を維持可能 | **採用** |
| E | commit の bytes 一致だけでは不足。承認・発効・意味検証が必要 | official run artifact を scan 免除へ追加する。occurrence と消失検出を自動的には継承しない | 不採用 |
| B | test が明示する合成履歴・入力 | 正負例を保てば検出力維持。実 root 依存を取り除くだけでは production は直らない | A-3 の補助 |
| C | authority は変わらない | 45 node の検出機会を削除する | 不採用 |
| D | branch を変えても承認契約は同じ | chain を持つ oracle checkout では同じ receipt 拒否 | 本件の解決にならない |

A-1 は `_validate_axis_occurrences` を共有できるが、それだけでは十分でない。同関数の入力は、承認、artifact bytes、protocol、環境契約などを検証した結果でなければならない。安全な共有単位を広げると、既存 `launch_validate` を利用する A-3 に近づく。

A-2 を採るなら、置換対象を少なくとも「receipt 履歴・artifact／closure 検証・live 検査・campaign epoch・開始直前再照合」に分解し、それぞれの後継を定義する必要がある。そこまでの変更を本件で行う理由はない。

E は `_active_chain_exempt_exact` の単なる延長ではない。同関数は active chain の限定された記録を免除し、official result 等は現在 C2-4 の**検査対象**である。X1' は bytes の保存証拠、世代文書は束縛内容、承認 A と有効な pointer X は批准・発効の根拠であり、いずれか一つで scan 免除権限になるわけではない。

D2077 の却下は特に official clean scan の拡大を対象とするため、「あらゆる exact exemption を一律禁止」と広げて読む必要はない。それでも E は本件の「走査除外を広げない」に反し、既存 full validation を使う A-3 より余分な正当化が必要になる。

## 推す択と根拠

**A-3＋B を、一つの整合修正として採る。** 次の境界を固定する。

1. **active v2 無し：従来どおり。** 正当な未発行履歴は `never-issued`。発行済み receipt は従来検査を通った場合だけ `active-valid`。X1' の hit は invalid のまま。
2. **active v2 有り：full launch validation 成功時だけ置換。** 承認不正・走査不能・closure 不一致の場合は拒否し、legacy 成功へフォールバックしない。
3. **receipt の他の失敗は残す。** 発行後削除、receipt 改変、closure 破損等を v2 成功で帳消しにしない。既存 hold を拡大しない。
4. **発行状態の意味は変えない。** active v2 があるから `never-issued` を `active-valid` に変換しない。`active-valid` の検証条件のうち、live unknownness の世代別判定だけを新 D で明文化する。

実装の最小単位は以下になる。

| file:function | 必要な変更 |
|---|---|
| `t080_freeze_migration.py:verify_receipt` | receipt 検証と未知性判定の接続を分離。単なる `skip_scan=True` を公開しない |
| 同：`_verify_holdout_live_scan` | 候補・検索式・照合規約の束縛を保持し、zero-hit と v2 完全一致の判定を明確に分ける |
| 同：`static_gate_adapter` | 二重に旧 zero-hit を呼ぶ経路にも同じ条件を適用。v1 単独利用は維持 |
| `s8b_oracle_driver.py:_resolve_t080_receipt`, `gate_check`, `run_block` | 同一 root・HEAD・active 世代に束縛された検証結果を接続。campaign-start 前の再解決も統一 |
| `s8b_ratified_freeze.py:_launch_validate` 周辺 | 必要なら検索規約を含む検証証拠を内部共有。C2-4 の判定実装は複製しない |

`_make_gate_decision` の refusal 集約と `_campaign_t080_value` の invalid 拒否は維持する。検証済み型の exact type 確認だけで安全とせず、別 root・別 HEAD・旧 active 世代の結果を流用できない束縛が要る。開始直前の再検査でも、保存済み token の存在だけで live 検査を省略しない。

B では、経路 (i)(ii) に clean な合成 tree／履歴を用意する一方、**official 成果物が存在すれば clean scan は拒否する負例**を残す。(iii)(iv) も実 root の状態から切り離し、receipt 不正時の拒否を別の統合 test で固定する。45 本すべてが production 修正だけで緑になるとは扱わない。

境界 test・変異 matrix の骨格：

- **発効境界：** 未発効＋hit は拒否、正当な active v2＋期待 hit 完全一致だけ受理。
- **receipt 境界：** 未発行、正常発行済み、発行後削除、改変、closure 不正をそれぞれ検査。
- **走査境界：** closure 外 hit 追加、期待 hit 消失、不許可位置の occurrence、検索式・candidate 対応の改変、陽性対照不成立を拒否。
- **束縛境界：** artifact 差替え、列挙集合変化、別 root／HEAD の検証結果、開始前の receipt・active 世代変更を拒否。
- **経路境界：** 公開 `gate_check`、`run_block`、adapter、campaign-start 再検査で同じ条件が効くことを確認。
- **変異：** 完全一致を包含へ変更、receipt refusal 無視、承認前委譲、検索規約照合削除、開始前再検査削除を、それぞれ負例が捕まえること。

C は、既知の失敗を通す目的で有効な検査を hold に送る案なので却下してよい。ただし「test の hold は常に規律 2 違反」という一般論にはしない。

D は official 床値を継続する clean branch の用途では正当だが、oracle の解決にはならない。D2077 が分けるのは走行フェーズであり、oracle 用 branch に必要な chain を置けば本件の hit は再発する。

規律 7 は X1' の測定事実を無効にする根拠ではない。同時に、過去の採用決定が現在の実行 gate を省略する根拠にもならない。A は D2120 項 2(a) の撤回ではなく、**未認識だった実行上の前提を満たしてから取り込む順序の補足**として記録できる。

新 D の決定文案：

> D2120 項 2(a) の chain 取り込みを維持し、先に T-080 と active v2 の未知性検証の整合修正および境界検査を完了する。
> receipt の履歴・静的検証・既存 live 束縛・epoch を維持し、承認済み active v2 では zero-hit 判定のみ既存 full launch validation の完全一致検証へ委譲する。未発効時と official clean scan は従来どおりとする。
> 理由は批准後 closure と v1 zero-hit の衝突解消であり、receipt 全廃、走査免除拡大、hold 追加、test-only／branch-only 解決は採らない。

## 総括

**A-3＋B が最小。** 親の「production を先に整合させる」推奨には賛成する。ただし、検索規約の束縛、adapter の再検査、campaign-start 前の再解決までを実装範囲に含める必要がある。

本回答は指定資料とコードの読解による相談結果であり、編集・追加実測・テスト実行は行っていない。