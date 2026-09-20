## レンズ B

静的検査のみ実施しました。追加テストの主要な帰属は成立していますが、**probe と変異の事前登録には修正が必要**です。

### must-fix

**B1 — E-1 probe は新形の再利用判定を再導出しており、author の「plan v2 実装済み」は成立しません。**

- **根拠:** `s4-ruling.md` の E-1 は実装した判定関数の呼出しを要求しています。しかし [probe L78–88](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/probe/t2803_receipt_attr_cold_rate.py:78) は digest 比較と包含検査を自前で合成しています。実装側の包含検査は [checker L2508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2803-provenance-receipt/tools/check_ai_provenance.py:2508) です。
- **成果物への影響:** 実装の包含方向を逆転・削除しても probe の新形判定は変わらず、「実装した再利用条件の失効指標」という証拠能力を持ちません。
- **是正案:** attributes の一致・包含判定を小さい関数に局所抽出し、受領証検査と probe の双方から呼ぶ。probe 内の再導出を削除し、author 報告を訂正する。全 binding を持つ監査の再実装は不要です。

**B2 — M-1〜M-7 は意味上の変異表であり、置換 `old` の一意性を確認できる事前登録になっていません。特に M-6 の kill は置換範囲に依存します。**

- **根拠:** `s4-ruling.md` と `s5-author.md` の変異表には、正確な `old`／`new` 文字列がありません。[checker L2500–2509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2803-provenance-receipt/tools/check_ai_provenance.py:2500) では文字列検査、復号、列の検査、包含検査が分かれ、復号例外は L2557 で捕捉します。
- **成果物への影響:** M-6 を外側の例外処理だけで変更すると、空集合で prefix 検査を続行する変異にはなりません。base64 の検査だけを緩めても zlib が拒否します。別理由の赤を登録した kill と取り違えられます。
- **是正案:** matrix 実行前に正確な置換対を固定し、各 `old` の出現数を1と確認する。M-6 は候補 field の処理に限った復号失敗→`stored=[]`→後続 prefix 検査という差分を明示し、他の prefix 検査を変更しないこと。

現ファイルで確認した置換候補は次のとおりです。これは**既存の登録文字列の検証ではなく、登録に使える位置の確認**です。

| 対象 | 現ファイルの文字列 | 出現数・注意 |
|---|---|---|
| M-1 | `working = []` | 1。ただし既にある初期化なので、これへの置換だけでは変異にならない。L2342–2346 の構築ブロックを指定する必要あり |
| M-2／M-3 | `if source != {"kind": "absent"}:` | 1 |
| M-4／M-5 | `or not set(stored) <= set(candidates)` | 1 |
| M-6 | L2500–2509 の候補 field 処理 | 正確な複数行 `old` が未提示 |
| M-7 | `receipt["attribute_candidates"] = encoded_candidates` | 1 |
| EQ-1 | `sorted(attribute_paths)` | 1 |

表中の説明的な `kind == "unreadable"` は実装内に存在しません。これをそのまま `old` にしてはいけません。

### should

該当なし。判定・受理集合・変異の証拠能力に関わる修正は上記にまとめました。

### nit

**B3 — T-neg-4 の全破損形を、各形式検査への独立した帰属と解釈してはいけません。**

- **根拠:** [テスト L8378–8384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2803-provenance-receipt/orchestrator/tests/test_check_ai_provenance.py:8378)。`suffix` の `tools/invalid`、`empty-payload` の空要素、`empty-element` の空要素は、形式検査を外しても現在候補への包含検査で拒否されます。`missing` は先行する key 集合検査で拒否されます。
- **成果物への影響:** 現実装の判定は変わりませんが、これらの緑を個別 guard の変異検出力として数えると証拠を過大評価します。
- **是正案:** 統合的な fallback テストとして維持し、独立 kill の主張から除外する。author が M-6 に `[False-base64]` を選び、`missing` を除いた判断は妥当です。

**B4 — E-1 の実行条件と未測定範囲の記録を補うべきです。**

- **根拠:** probe L53–61 は渡された HEAD と checker ファイルを使用し、旧 checker が `f94b61fc8` の main blob であること自体は確認しません。L99 は cold 率・wall の非測定を明記していますが、他 binding・partition・受領証探索は列挙していません。
- **成果物への影響:** 指定どおりの入力なら判定・集計は変わりません。probe 単体から main blob との比較を証明することはできません。
- **是正案:** 親の実行記録に旧 blob の抽出元と一致確認を残し、報告へ「他 binding・partition・受領証探索は未測定」を追加する。一般的な入力検証基盤の追加は不要です。

### テスト・変異の帰属確認

| テスト／変異 | 静的な評価 |
|---|---|
| T-pos-1／M-2 | absent 再包含なら L8272 の digest 同一 assertion で最初に赤。author の「delta のみの監査」まで到達しません |
| T-pos-1／M-5 | digest は同じまま逆包含で cold となり、L8276 の delta 観測で赤 |
| T-pos-2 | tracked child により候補入りし、属性自体は untracked。working を落とす変異は L8287 で赤。index が肩代わりしません |
| T-neg-1／M-4 | digest 同一・候補減少を固定。包含を外すと merge を省略し、L8311 の rc=1 期待で赤になる構成 |
| T-neg-2 | 属性だけを削除し候補集合を維持。working を落とすと L8330 の digest 差で赤 |
| T-neg-3／M-3 | absent→lstat EACCES を注入。unreadable を除外すると L8351 で赤。候補集合は同じ |
| T-neg-4／M-6 | `[False-base64]` は適切な候補。ただし B2 の正確な変異差分が前提 |
| T-neg-5 | sorted・正しい suffix の候補を一つ追加。他の field を保つため包含違反への帰属が成立 |
| M-1 | 既存 `[untracked]` は実属性による merge path 変化を確認してから rc=1 を要求。working 全削除への帰属が成立 |
| M-7 | T-neg-5 は L8400 の zlib 復号で先に失敗。T-pos-1 は L8276 の warm 観測で失敗。単一の主 node を選ぶなら後者が明瞭 |
| EQ-1 | `attribute_paths` は set として生成され、`add` のみで更新。同じ bytes 列を同じ順序で返すため等価 |

`_receipt_run` の monkeypatch は実関数を呼ぶ観測 wrapper です。両層 stub、揮発 payload の焼き込み、fixture への現行 checker hash 差し込みは、追加差分にありません。保存済み digest を読む assertion は値の注入ではありません。oracle 比較は rc と `CaptureResult` の双方を比較し、stdout・stderr を含みます。

既存 assertion の変更は `[0]` による digest 比較の維持です。期待値変更はありません。ただし `independent_of_tip` 等が absent 候補差への感度を失う点は、裁定・author 報告どおり残ります。

### probe・過剰実装・consumer

- probe は既定値で **61 snapshot／60遷移**を古い順に扱い、初回を別計上します。追加・削除の候補 directory 数も数えます。同じ checkout で両 fingerprint 関数を呼ぶ点は満たします。
- checker・出力を checkout 外に限定し、bytecode を抑止し、`finally` で元の detached HEAD に戻します。作業木の clean 確認はあります。ただし Git メタデータまで一切変更しない保証ではありません。
- 本体に一般化・台帳・互換層の追加はありません。保存直前の候補再照合は、digest から候補差を外した後も監査中の変更を検出するための局所的な補完です。削除対象とは判断しません。
- `focus-1.log` は **2738 passed／5 skipped、child rc=0、最終 rc=0**。赤は記録されていません。末尾の `recording-unavailable:series-invalid` は記録不能の診断で、テスト失敗ではありません。
- consumer の内部契約や author の「233 matches／68ファイル」という検索集計は、指定された資料だけでは独立再確認できません。ログも nodeid 一覧を含まないため、この集計だけで個々の consumer 実走を証明することはできません。

## 総括

**NO-GO — must-fix 2件。**

追加テストの主要な帰属は成立しています。E-1 の実装判定呼出しへの修正と、変異の正確な置換対・主 kill node の固定を済ませてから、変異 matrix と実測へ進めるべきです。