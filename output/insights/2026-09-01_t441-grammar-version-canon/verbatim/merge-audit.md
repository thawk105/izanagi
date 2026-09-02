## 両側の効果の生存

**R-01 — 条件 gate と文法版束縛はともに生存している**

根拠: `orchestrator/campaign/p3_s4_loop.py:1289` で campaign 由来の版を確定し、reject 記録へ `:1325`、`:1346`、`:1357`、build 経路へ `:1368-1373` で渡している。条件 gate は検疫通過後の `:1364` で実行され、duplicate／certified／aborted の各結果へ `:1375-1389` で載る。WAL 側も `orchestrator/campaign/wal.py:647-662` と `:1523-1525` で版を強制する。

**成果物影響:** certified 選択は条件 gate 合格済みかつ版束縛済みの source/cache identity を使い、reject 試行台帳にも版が残り、材料レポート相当の戻り値には条件 gate 証拠が残る。

深刻度: nit（適合確認、修正不要）

## 早期 return と経路

**R-02 — reject・dry-run・duplicate の経路順序は両側の意図を保存している**

根拠: 文法版は全経路の分岐前 `orchestrator/campaign/p3_s4_loop.py:1289` に束縛される。preflight reject は `:1324-1338`、dry-run は `:1340-1352`、build 時 quarantine reject は `:1354-1363` で版付き記録を残して終了し、条件 gate には到達しない。duplicate は条件 gate と `run_campaign` の後にのみ `:1374-1378` へ到達する。これは相手側の配置 `theirs-p3-s4-loop.py:1264-1310` と一致する。

**成果物影響:** reject の受理集合は変わらず、試行台帳だけが版付きになる。dry-pass は条件 admission を偽装せず、duplicate は現在の条件 gate 証拠と既存 WAL 証拠の両方を返す。

深刻度: nit（適合確認、修正不要）

## 例外の順序

**R-03 — 新しい先行例外は文法版不一致だけで、裁定どおりの fail-closed 順序である**

根拠: 合成後は文法版検査 `orchestrator/campaign/p3_s4_loop.py:1289` →候補検疫 `:1290-1363` →条件 gate `:1364` →campaign 実行 `:1368` の順である。版不一致時に候補 reject や条件 gate より先に `ValueError` となる観測差はあるが、`s4-ruling.md:28-31` が build／WAL 前の exact 強制を要求している。条件 gate が build 直前に発火する相手側の順序は維持されている。

正準化された source が条件 gate に渡るため、その source digest は raw literal 版から変わり得るが、実際に build・certified 選択される材料と証拠が一致する方向の差である。

**成果物影響:** 不正な版の候補は reject 台帳さえ作る前に停止し、正しい版では条件 gate が canonical source を検査するため、certified 選択と参照 source の食い違いは生じない。

深刻度: nit（適合確認、修正不要）

## 変数の束縛

**R-04 — `condition_gate` と `backoff_grammar_version` の未束縛参照はない**

根拠: `backoff_grammar_version` は `orchestrator/campaign/p3_s4_loop.py:1289` で、最初の参照 `:1327` より前に必ず束縛される。`condition_gate` は `:1364` で束縛され、その後に正常復帰した `run_campaign` の結果処理 `:1374-1389` だけから参照される。束縛前の reject／dry-run は当該変数を参照しない。

**成果物影響:** どの正常 return でも台帳値や材料レポートが未定義変数で失われる経路はなく、例外終了を誤って aborted／duplicate と記録することもない。

深刻度: nit（適合確認、修正不要）

## 戻り値の形

**R-05 — 各 return の key 集合は両側の契約を保っている**

根拠: reject は `orchestrator/campaign/p3_s4_loop.py:1335-1338`、`:1351`、`:1363` で `{outcome, variant, digest}`、dry-pass は `:1352` で `{outcome, variant}` のまま。duplicate は `_resolve_duplicate` の既存形へ `condition_gate` を追加して `:1375-1378`、certified／aborted は `:1383-1389` で既存 key に `condition_gate` を追加している。文法版は戻り値 key ではなく variant identity・WAL・source/cache へ載せる自分側の設計どおりである。

**成果物影響:** reject／dry-run は存在しない条件証拠を材料レポートへ載せず、build 到達後の certified／aborted／duplicate だけが条件証拠を持つ。試行台帳の版情報も欠落しない。

深刻度: nit（適合確認、修正不要）

## 識別子の二義化

**R-06 — 同名識別子に意味の衝突はない**

根拠: `condition_meaning_gate` は module、`condition_gate` はその admission 証拠 dict として `orchestrator/campaign/p3_s4_loop.py:129-162` と `:1364` で一貫している。`backoff_grammar_version` は campaign 由来の exact integer として `:1113-1123`、`:1289`、`:1327-1373` で一義的に使われる。条件 gate 内の `value` は同じ `genome.flags["BACKOFF_FIXED"]` を参照する。

**成果物影響:** grammar version、条件 admission、BACKOFF_FIXED 値が別の意味へ取り違えられず、variant identity・台帳・材料レポート・受理集合の参照関係は維持される。

深刻度: nit（適合確認、修正不要）

## 総括

静的合成監査では must-fix／should-fix はなく、この merge はこのまま commit してよい。