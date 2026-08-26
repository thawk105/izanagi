## 総括

最重要 must-fix は、両腕の `test-only` receipt を整合的に `certified` へ書き換えると正式関門を通過できる点です。  
Git 検証も `LD_PRELOAD` などを継承しており、固定 executable が実効的な trust root になっていません。  
§5 は Markdown 上で隠された表や不可視文字で偽装した placeholder を誤受理します。  
model mismatch は停止しますが、failure receipt と CLI から固定署名が失われます。  
親が実測した `N/?A` の過剰拒否は既知として除外しました。

## must-fix

### 1. 両腕を整合的に昇格すると `test-only` pair が certified 関門を通る

- `根拠` `orchestrator/campaign/p3_b4_closed_critic.py:1063`, `:1090`, `:1104`, `:1193`, `:1263`, `:1504`。関門は可変 JSON 内の `evidence_class` しか見ず、verified admission や production factory の所有証拠を受け取りません。テストも片腕だけの昇格で止まっています (`orchestrator/tests/test_p3_b4_closed_critic.py:1658`)。
- `具体的な破り方` — injected runner を使う test-only pair を両腕とも実行する。各 start receipt の `evidence_class` を `certified` に変更し、各 terminal receipt も同様に変更して `start_receipt_sha256` を再計算する。他の artifact は変更不要です。両腕の class が一致するため `assert_b4_arm_pair` が通り、再読後の `assert_b4_certified_arm_pair` も通ります。
- `成果物影響` — fake runner の envelope、model、decision が certified 選択集合へ入り、正式レポートと台帳が test-only 標本を certified と参照します。
- `修正案` — `assert_b4_certified_arm_pair(pair, on_path, off_path, *, admission_record_path)` のように live pair と record を必須にし、production factory だけが付与する別 seal と `VerifiedB4AdmissionRecord` を確認してから、receipt の model/prompt/projection を record と再照合する。receipt `/v2` の field は変更不要です。正例は、有効な record を渡して `create_b4_closed_critic_pair` が返した live pair と、その両 terminal path の組です。

### 2. 固定 Git executable が動的 loader 環境で差し替え可能

- `根拠` `orchestrator/campaign/p3_b4_admission_record.py:209`, `:221`, `:238`。`_git_environment()` は `GIT_*` だけを除き、`LD_PRELOAD`、`LD_LIBRARY_PATH`、`HOME`、`XDG_CONFIG_HOME` をそのまま子 Git へ渡します。
- `具体的な破り方` — Python 起動後に `os.environ["LD_PRELOAD"]` を攻撃用共有ライブラリへ設定する。固定された `/usr/bin/git` 自体は起動しますが、ライブラリが `open`、`read` などを横取りし、`rev-parse`、`ls-tree`、`cat-file`、`merge-base` に偽の HEAD、record、文書 blob、祖先関係を返せます。既存テストは `GIT_*` と `PATH` だけを攻撃しています (`orchestrator/tests/test_p3_b4_admission_record.py:294`)。
- `成果物影響` — HEAD に存在しない record や外部 object graph の事前登録文書が受理され、その偽の model/prompt/projection で生成した標本が certified 集合へ入ります。
- `修正案` — `_git_environment() -> dict[str, str]` を継承型から固定 allowlist 型へ変え、動的 loader、locale、home/config 系を遮断する。必要なら system/global config も固定無効化する。正例は、実 repository の HEAD に canonical record と同一 §5 blobがある通常呼び出しです。

### 3. Markdown 上に存在しない §5 表と、表示上の placeholder が受理される

- `根拠` `orchestrator/campaign/p3_b4_admission_record.py:443`, `:456`, `:461`, `:474`。parser は Markdown 構造を解釈せず、raw line と raw cell textだけを検査します。
- `具体的な破り方` — §5 heading より前で fenced code block を開き、`### 5.1` より後で閉じる。範囲内の raw lines は現行 parser を通りますが、Markdown 上では heading も表も単なるコードです。別経路として値を `T<U+200B>BD` にすると、表示上は `TBD` でも regex と whole-value 検査を通ります。これは既知の `N/?A` 過剰拒否とは逆方向の欠陥です。
- `成果物影響` — 実際には §5 が記入されていない文書 hash が正式な preregistration 参照として台帳に入り、その record による実走が certified と受理されます。
- `修正案` — 公開署名は維持し、内部で Markdown AST 上の実在する level-2 §5 heading、table node、level-3 §5.1 heading を検査する。cell の可視文字列は NFKC 正規化し、default-ignorable 文字を拒否してから placeholder を検査する。正例は fenced block 外の通常の 10 行表で、各値が具体値、期待値行が record と一致する文書です。

### 4. model mismatch の固定署名が failure 成果物から消える

- `根拠` `orchestrator/campaign/p3_b4_closed_critic.py:780`, `:869`, `:883`, `:892`, `:1553`。発生時の例外文字列は固定署名ですが、failure terminal は `error_type` だけ、CLI も型名だけを保存・表示します。テストも型名だけを確認しています (`orchestrator/tests/test_p3_b4_closed_critic.py:965`)。
- `具体的な破り方` — envelope の唯一の opus slug を record と異なる値にする。呼び出しは停止しますが、terminal には `B4AdmissionRecordError` しか残らず、`[admission-mismatch] expected_claude_model_snapshot` は失われます。
- `成果物影響` — failure receipt、レポート、台帳の失敗理由が model mismatch を特定できず、別の admission error と同じ値になります。
- `修正案` — failure terminal に閉じた列挙の `error_signature` を追加し、admission error では固定署名を保存する。CLI も同じ署名を出す。正例は record と envelope が同じ `claude-opus-5` で、従来どおり success receipt `/v2` になる呼び出しです。

## nit / backlog

- projection mismatch は artifact root 作成後です (`p3_b4_closed_critic.py:960-975`)。query/provider より前なので fail-closed ですが、空 root が残り同じ出力先での再試行を妨げます。
- `_RECORD_NOT_AT_HEAD` は Git executable 不在、layout 異常、HEAD 異常も一括変換します (`p3_b4_admission_record.py:520-531`)。拒否は維持されますが、固定署名の条件が名称どおり一意ではありません。
- `assert_b4_certified_arm_pair` は同じ receipt を二度読みます (`p3_b4_closed_critic.py:1509-1515`)。2 回の読取間で pair を交換できる TOCTOU もあります。

§5 の併走 wave 依存は次のとおりです。

- `## 5.` と `### 5.1` は各 1 行必須。level、番号、重複を変えると拒否、fail-closed。
- 両 heading 間は空行を除いて正確に 12 行。説明、caption、comment、追加行、折返しを入れると拒否、fail-closed。
- header と separator は `|欄|値|`、`|---|---|` 固定。空白や alignment marker の変更は拒否、fail-closed。
- 各行は raw `|` 分割で正確に 2 cell。追加列や値中の escaped pipe も拒否、fail-closed。
- label は exact 10 個の集合。追加、削除、言い換え、句読点や backtick の変更は拒否、fail-closed。行順変更だけは受理されます。
- 期待値行は key 順、空白、lowercase hex、model prefix まで固定。書式変更は拒否、fail-closed。
- fenced block、HTML context、不可視文字による見かけ上の変更は誤受理であり、must-fix 3 の pass-direction です。

テストの追認箇所があります。

- §5 fixture が実装の `_SECTION5_LABELS` と `_EXPECTATION_ROW_LABEL` から生成されています (`test_p3_b4_admission_record.py:49-69`)。label の欠落や変更をテストも追随して緑になります。
- schema version と固定文書 path も実装定数から生成しています (`:83-85`)。
- receipt の exact key 集合を `fields(C.B4ClosedCriticReceipt)` から導出しています (`test_p3_b4_closed_critic.py:846`)。field 増減を検出できません。
- certified fixture 自身が production validator を呼んで正例化しています (`:544`)。
- projection manifest の digest 検査が実装の `_canonical_json_bytes` を使っています (`:1373`)。

## 恒真監査の結果

無し。

## 攻撃できなかった面

- record 検証は executable 探索、artifact root、provider 作成より前です (`p3_b4_closed_critic.py:1004-1019`)。
- prompt は provider 作成直後かつ query 前、model は envelope 保存・provider 検証後かつ decision parse 前に照合されています。
- success receipt は `/v2` のままで field 増減はなく、既存 `_read_verified_terminal_receipt` と `assert_b4_arm_pair` の検査削除もありません。
- `create_b4_closed_critic_pair_for_test` の公開引数は増えていません。
- projection closure には validator Python file だけが追加され、record JSON は入っていません。