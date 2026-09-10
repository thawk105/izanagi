## 所見

### L-1 台帳 key は座標の再利用を既知違反として誤認する
対象: plan「既知違反台帳の設計」、`tools/check_docs.py:211-215`
攻撃: file の移動・正規名への改名・byte 保存の分割／結合には耐える。一方、entry 74 が消失し、同じ番号・task ID・target を持つ別内容が 1 件置かれると、1 回の置換だけで同じ key と観測数になる。
そのとき何が起きるか: 黙って緑になる。全域番号一意性は同時重複しか検出せず、F58 型の ID／番号再利用を認証してしまう。
直し方: 既存 placeholder 台帳と同様、source H2 raw digest と carry 論理行 digestを key に含める。path と行番号は含めないため、通常のローテーションには耐え、archive 編集も不要である。
重大度: must-fix — 台帳が歴史的 occurrence ではなく、再利用可能な三つ組を許可している。

### L-2 母数下限は最初の fold 後から縮退を見逃す
対象: plan「既知違反台帳の設計」「残る危険」
攻撃: baseline 後に C 件の carry が追加された直後から、別の C 件までが消失または regex 対象外になっても `actual >= 404326` が成立する。少なくとも 1 件追加される最初の fold、早ければ同日から破綻する。
そのとき何が起きるか: 黙って緑になり、誰も止まらない。下限は時間とともに検出可能な損失割合を減らす。
直し方: 凍結 entry ごとの期待件数を固定し、現行 worklog は fold の before／after で非減少を検査する。watermark 更新は fold と原子的に行い、手作業の定数 ratchet に依存させない。
重大度: blocker — D837 が要求した空・部分母集合への防護が、コーパス成長そのもので腐る。

### L-3 台帳追加の無裁定迂回は三つの同時編集だけで成立する
対象: plan「変更プラン 1」「テストプラン 3-4」
攻撃: 担当者は新 key を足し、`EXPECTED_KNOWN_CARRY_ID_MISMATCHES` を 5 にし、同じ変更内の exact 比較テストを 5 件へ直せる。すべて編集許可された 2 file 内で完結する。
そのとき何が起きるか: 新規違反が黙って緑になる。「ユーザー裁定のみ」というコメントは機械的な障害ではない。
直し方: 台帳差分には、author が同じ patch で生成・変更できない承認 receipt または保護された review gate を要求する。現行テストは偶発変更検出としてのみ位置付ける。
重大度: blocker — brief の不変条件 6 を設計が実装していない。

### L-4 最悪の赤経路は 404,326 件の finding を常駐させる
対象: plan「変更プラン 4」手順 9
攻撃: target の ID 索引が広範囲に空になる、または照合 regex が壊れると、stream 自体は省メモリでも各 occurrence の finding を `findings` list に追加する。
そのとき何が起きるか: 最大 404,326 個の長い文字列でメモリ・ログが膨張し、必須 lint が診断を出す前に timeout／OOM しうる。全 wave の終了処理が止まる。
直し方: 全件を数えながら finding は分類別上限と数件の sample に制限し、抑制件数を表示する。台帳観測数の照合は最後まで継続する。
重大度: must-fix — 検査が最も必要な破損時だけ運用不能になる。

### L-5 不一致診断に参照先の所在がない
対象: plan「変更プラン 4」手順 7-10、「残る危険」
攻撃: 新規 mismatch の予定文言は source path／line、task ID、target 番号までで、target の path／lineを示さない。索引不能は target 単位に集約するが、代表 source の表示も契約化されていない。
そのとき何が起きるか: 赤にはなるが、担当者は別の索引や全域検索で target entry を探す。既知 key の `actual=0` も、復旧か裁定かを案内しない。
直し方: source entry と path／line、target path／heading line、期待 task ID、分類、総 occurrence 数と sample を必ず表示する。archive 本文を編集せず、復元または裁定へ返す旨も示す。
重大度: must-fix — 必須 lint の赤から安全な復旧操作へ到達できない。

### L-6 fold の現行出力は適合するが、その契約を固定するテストがない
対象: `tools/spool_fold.py:1572-1626,1839-1894,2227-2269`、plan「テストプラン」
攻撃: 現在は同じ ID を再帰解決し、`- [T-NNN] (prior_ordinal)` を生成し、rotation は entry bytes を移すため適合する。しかし checker 単体 fixture しかなく、compact 文法・source 選別・rotation 境界の将来変更を検出しない。
そのとき何が起きるか: 次の文法または rotation 変更で fold 自体は成功し、land 前の必須 lint が全 wave を赤にする。
直し方: spool で投影した entry を新 checker に渡す統合テストを、非 rotation と強制 rotation の両方で追加する。
重大度: must-fix — canonical writer と reader の互換性が静的な偶然に留まる。

### L-7 path 非依存 key でも archive の非番号名への改名には耐えない
対象: plan「変更プラン 6」、`tools/check_docs.py:2683-2736`
攻撃: carry source 登録は `filename_claim.classification == "numbered"` に限定される。既知 4 件の file を byte 保存のまま非番号 archive 名へ改名すると、三つ組は不変でも観測対象から消える。
そのとき何が起きるか: 最初の改名で台帳 `expected=1, actual=0` が赤になり、以後すべての必須 lintが止まる。通常の `spool_fold` rotation では発生しないが、将来の archive 再編で発生する。
直し方: rename 耐性を要件とするなら、carry 照合の corpus 選択を filename 分類から分離する。分離しないなら番号形式を永続契約として明記し、専用診断を出す。
重大度: must-fix — plan の「path を外せばローテーション耐性がある」という根拠が不完全である。

### L-8 1.69 秒の probe は提案実装の費用上限にならない
対象: `parent_measurements.md`「コスト」、plan「残る危険」
攻撃: 提案経路は各 occurrence で二つの regex、line 計算、dataclass 生成、target set lookup、台帳 lookup を行う。射影資料には probe の同一処理性を示すコードがなく、赤経路の finding 常駐費用も測られていない。
そのとき何が起きるか: green 増分も現時点では未確定であり、破損時は baseline 10.52 秒／157MB との比較が無意味になる可能性がある。
直し方: 実装後に green 実 repo と、全件 mismatch を集約する worst-case fixture の wall／maxrss を別々に測る。倍化条件は green だけでなく診断可能な赤にも置く。
重大度: must-fix — 親の実測値自体ではなく、提案実装へそのまま外挿した点が未証明である。

## 親 brief への反証

- P1 は破れた。三つ組は通常の file rotation には耐えるが、歴史的 occurrence の置換と非番号名への改名には耐えない。
- P3 は破れた。単調増加量への固定下限は腐らないのではなく、最初の増加から損失許容量を作る。
- 不変条件 6 は満たされない。台帳、固定総数、exact テストを同じ author patch で更新できる。
- 「traversal 1 回 = 1.69 秒」を実装増分とする推定は成立が未証明で、赤経路の費用を含まない。
- 凍結 archive 非接触そのものは壊せなかった。digest を用いる修正も archive bytes の変更を必要としない。

## scope 外だが real な所見

- L-2 の自動 ratchet と L-3 の承認境界を実効化するには、現在の 2 file scope 外で `spool_fold` または独立 gate／receipt を変更する必要がある。段 4 の裁定へ返すべきである。
- F58 型の「同じ ID だが別内容」は本検査を黙って通る。target に同じ ID の偽項目を置くだけで成立するため、将来は substantive digest を carry 鎖へ持たせるかを別裁定にすべきである。

## 総括

最も危険なのは L-2 で、404,326 の固定下限は最初の fold 後から部分消失を黙認する。  
次点は L-3 で、「ユーザー裁定のみ」が同一 patch 内の三変更に対する防護になっていない。  
したがって現プランはそのまま採用すべきでない。  
段 4 では、台帳 key の digest 化、fold と原子的な母数 ratchet、外部承認境界への scope 拡張を裁定すべきである。  
現行 spool 出力との静的整合は確認できたが、テストは実走しておらず、緑は主張しない。