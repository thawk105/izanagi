## 所見

### 1. 事前登録された失敗 node 集合が M1・M3・M6 で不正確

- 所見: DW-M08 の完全一致に使う期待 node 集合を、そのまま採用できない。
- 根拠: gate は manifest の行数だけ反復するため、空 manifest の P2 では判定式を反転・恒真化しても実行されない (`tools/codex_reasoning_ab.py:1693`, `orchestrator/tests/test_codex_reasoning_ab.py:2241`)。また N3 も closure=False なので、M3 では N1 に加えて N3 も落ちる (`orchestrator/tests/test_codex_reasoning_ab.py:2185`)。
- 成立条件: `ruling.md` の設計上の対応を、再導出せず mutation harness の完全期待集合へ転記した場合。
- 成果物への影響: 正しく検出された変異が node 集合不一致で KILLED と認定されず、段 6 の検査証跡と acceptance 判定が成立しない。
- must-fix か nit か: **must-fix**。実装ではなく、変異 matrix の期待集合を本走前に訂正する必要がある。
- 確信度: **高**。

### 2. M5 は具体的な注入形が未確定で、現状の記述だけでは正当な kill を主張できない

- 所見: `reasons.append` の「oracle key への置換」を字義どおり同じ位置で行うと、`oracle` はまだ定義されておらず、意図した fail-open ではなく実装エラーになる。
- 根拠: 書込位置は `tools/codex_reasoning_ab.py:1695`、oracle の生成は同 `:1706` 以降。P1 の exact key pin は `orchestrator/tests/test_codex_reasoning_ab.py:2220`。
- 成立条件: mutation harness が一行置換で未定義の `oracle` を参照する場合、または key を未初期化時だけ追加して P1 でも落ちると期待する場合。
- 成果物への影響: クラッシュを「fail-open 変異の kill」と誤認し、実際には受理集合の防護を検証していない証跡が残る。
- must-fix か nit か: **must-fix**。append を除去して未初期化 snapshot を受理させ、oracle の新 key を成功経路へ追加する具体的な複数箇所変異として固定すべき。
- 確信度: **高**。

## 変異 M1〜M6 の帰属判定

- **M1: 殺せる。** 実際の失敗集合は N1、N2、N3、N4、P1。P2 は空 manifest なので落ちない。N1・N2・N4 は拒否から受理へ、P1 は受理から拒否へ変わるため帰属は成立する。N3 は initialized 側の誤 reason で拒否されたままなので、そこだけは診断感度であり kill の根拠にしない。
- **M2: 殺せる。** N1〜N4 は共通 helper が path を含む新 reason の存在を検査する (`orchestrator/tests/test_codex_reasoning_ab.py:2131`)。別 reason だけで `pytest.raises` が通っても helper が落ちるため、mask されない。
- **M3: 殺せる。** closure=False の N1 と N3 が受理へ変わる。期待集合は「N1 のみ」ではなく **N1、N3**。
- **M4: 殺せる。** N3 は manifest 順を明示検査し、先頭を initialized、後段を uninitialized に固定している (`orchestrator/tests/test_codex_reasoning_ab.py:2176`)。先頭行だけなら N3 が受理される。
- **M5: 判定不能。** 意図された複数箇所の fail-open 変異なら N1〜N4 が受理され、さらに key を成功 oracle に常設すれば P1 も落ちるため検出力はある。しかし具体的な注入差分なしでは、未定義変数クラッシュとの区別がつかない。
- **M6: 殺せる。** P1 は initialized 行を実際に通過するため拒否される。P2 は loop 0 回なので落ちない。実際の失敗集合は **P1 のみ**。

## 恒真判定

負例 N1〜N4 は空回りしていない。spec helper は実 HEAD、改名済み branch、空の dirty・untracked・numstat、実 bytes の hashes、対応する modes、空 forbidden を設定している (`orchestrator/tests/test_codex_reasoning_ab.py:2104`)。N1・N3 は closure を切り、N2・N4 は事前に object closure を seal している (`:2100`)。さらに exact reason を要求するため、新 gate 削除時に別理由の赤が残ってもテストは通らない。

N4 の monkeypatch も有効である。`TOOL` は module object としてロードされ (`orchestrator/tests/test_codex_reasoning_ab.py:59`)、`verify_snapshot` は呼出時に module global `_snapshot_spec` を参照する (`tools/codex_reasoning_ab.py:1610`)。差替え後に `spec` なしで呼ぶため、既定 spec 選択経路を実際に通る。

P1 は manifest に initialized 行を一つ持ち、gate loop を実際に一回通過するので恒真ではない。P2 は意図どおり空 manifest で通るが、行単位の判定式に対しては完全に恒真であり、M1・M6 の検出力はゼロである。

P1 の oracle key 集合は実装の `:1706-1726` と一致しており、top-level key の追加を確実に検出する。ただし未初期化時だけ出現する条件付き key は P1 では検出できず、その場合は N1〜N4 の受理変化が検出根拠になる。

## 総括

production gate と N1〜N4 の reason 帰属には、静的に見て重大な mask はない。  
P1 は非恒真だが、P2 は空 loop のため M1・M6 を殺さない。  
M1・M3・M6 の完全期待 node 集合を再導出し、M5 の具体的な意味保存変異を固定するまで段 6 は **NO-GO**。  
DW-M03・DW-M08 に基づく静的判定であり、pytest は実走していない。