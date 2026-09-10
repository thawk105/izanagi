静的検査のみで、テスト・probe は実走していない。

### A1 — freeze producer / validator は NUL path を含む契約を凍結でき、brief の「存在しえない」は誤り

- file:line: `brief.md:50-51`、`s8c_preregistration.py:340-347,1408-1415,1722-1725`、`s8c_preregistration_evidence.py:689-695`
- `evidence_contract_sha256()` は任意の妥当な JSON を canonical hash するだけで、`load_contract_bytes()` を通さない。JSON blob 内の path は `"\u0000"` で表現でき、tree entry 名が NUL-free でも freeze record の `evidence_contract_sha256` / `protected_sha256` に束縛できる。
- 成果物影響: `validate_condition_freeze_at()` はその契約を valid freeze として受理しうる一方、activation registry は後段で `evidence-contract-invalid` に倒れる。certified 選択は現状 fail-closed だが、凍結台帳・proof chain の受理集合には NUL path を含む契約が残り、訂正には新 generation が必要になる。
- 現 tracked contract とその Git 履歴を静的検索した範囲では `\u0000` はなく、直ちに g1 再発行が必要という証拠はない。ただし根拠は直接内容検査であって tree 形式ではない。
- 深刻度: **must-fix**
- 推奨: **裁定へ**。freeze 発行・検証にも NUL-only 検査を広げるか、「invalid contract も凍結可能だが発効不能」という既存境界を維持して brief の保証を狭めるかを段 4 で決める。`load_contract_bytes()` 全体の流用は NUL 以外も拒否して受理集合を変えるため、無裁定では採用不可。
- 証拠種別: 実コードで静的に成立。実走なし。

### A2 — H1 は `str` サブクラスの `__contains__` で上層 NUL guard を迂回できる

- file:line: `s2_out.md:14-21`、`orchestrator/campaign/s8c_preregistration_evidence.py:183-190`
- `"\x00" in value` は元のサブクラス上で評価されるため、基底文字列に NUL を持ちながら membership を偽装する値は `_nonempty_string` と `PurePosixPath` を通り、元オブジェクトのまま返りうる。
- 成果物影響: 現 production の JSON decoder は通常 exact `str` を生成し、さらに H2 が Git 手前で止めるため、現在の certified 経路が突破される証拠はない。ただし「2 層が独立に fail-closed」という受理集合の主張は偽になる。
- 深刻度: **should-fix**
- 推奨: **採用**。上層でも一度 exact `str` を作ってその値を検査し、membership を偽装する NUL 入り `str` サブクラスの direct regression test を追加する。
- 証拠種別: 実コードに基づく静的反例。実走なし。

### A3 — 変異表の「必須 node 1 件」は harness の失敗 node 完全集合契約を満たすとは限らない

- file:line: `s2_out.md:251-260`、`tools/mutation_harness.py:1177-1193`
- harness は赤 node の集合が `expected_nodes` と完全一致した場合だけ `KILLED` とする。プランは mutation runner の exact nodeid 集合を指定せず、「他 node も赤になるが必須 detector は一つ」でよいとしている。
- 全追加 node を runner に含めるなら、M-NUL-SAFE は `[required-nul]`・`[consumer-nul]`・`[trailing-nul]`、M-NUL-BLOB は `[trailing-nul]`・`[embedded-nul]` が赤になる。表の一件だけでは `MISMATCH` になる。
- 成果物影響: `MISMATCH` を kill と扱えば、防壁の変異帰属を示す mutation ledger／proof chain が成立しない。
- 深刻度: **must-fix**
- 推奨: **採用**。段 4 で、(a) runner を `required-nul`・`embedded-nul`・TAB 正例の exact nodeid だけに限定するか、(b) runner に含める全赤 node を `expected_nodes` に登録するかを固定する。M-C0-SAFE/BLOB は単独変異なら同じ TAB node でも前後層に mask されない。
- 証拠種別: harness 実装で裏付け済み。変異実走なし。

### A4 — `probe_nul.py` 単体からは記載された実測結論を機械的に導けない

- file:line: `probe_nul.py:29-47,57-67`、`brief.md:14-19`
- `plain.split()[0] == nul.split()[0]` は両応答が `blob` であることを検査しないため、両方 missing でも true になりうる。`read_blob_at` 部も例外を捕捉して表示するだけで、sha256 は先頭 16 桁のみ、比較 assertion もない。
- job directory の静的列挙では probe stdout の保存物がなく、brief がいう「出力が一次資料」を本レビューから再照合できない。
- 成果物影響: 受理集合縮小の前提証拠が checkout・Git 応答へ機械束縛されず、誤った実測でも wave が進行できる。なお、両応答が成功した blob record だと確認した上での完全 OID 一致は、同じ Git object を読んだことを示す。ただし NUL tree entry の実在や他 Git command の挙動までは示さない。
- `TAB は alias しない` も、この probe が直接示すのは `CLAUDE.md` の末尾 TAB 一例だけである。H6 を実走すれば、実在する埋め込み TAB path の対照が追加される。
- 深刻度: **should-fix**
- 推奨: **採用**。blob 型・サイズ・完全 OID を parse/assertし、plain/NUL の full digest を比較する。stdout、HEAD、Git version を保存するか、既存 T-714 の記録を一次資料として明示する。
- 証拠種別: probe ロジックと artifact inventory の静的検査。probe 再実走なし。

### A5 — H2 が拒否するのは文字列化後の NULであり、元の `bytes` / PathLike の NULではない

- file:line: `s2_out.md:33-45,242-247`、`orchestrator/campaign/s8c_preregistration.py:960-970`
- `bytes` の NUL は `str(bytes)` で `\\x00` へ可視化されるため guard に掛からない。これは actual NUL を Git へ送る迂回ではないが、同じ repr を名前に持つ tree entry があれば、元の bytes path の filesystem 意味とは異なる blob を読む。任意 `os.PathLike` も `__fspath__` ではなく `__str__` が契約になる。
- `Path` / `PurePosixPath` の文字列表現に actual NUL があれば H2 で拒否され、そこに再文字列化穴はない。
- 成果物影響: 現 production caller は契約由来の `str` なので現在の certified 値への到達は確認できないが、公開 primitive の直接利用では path/hash 束縛の意味が入力型により変わる。
- 深刻度: **should-fix**
- 推奨: **裁定へ**。D267 どおり「単一文字列化後の text が API 上の path」と定義するなら保証文をその範囲へ狭め、本件は不採用でよい。元の bytes/pathlike 意味まで守るなら非文字列拒否または `os.fspath` 契約が必要で、既存受理集合を変えるため無裁定では足さない。
- 証拠種別: 静的な型・変換経路。実走なし。

### A6 — `read_blob_at` 以外にも line-framed path sink はあるが、現 caller から hostile contract path は届かない

- file:line: `orchestrator/campaign/s8c_preregistration.py:1128-1155,1311-1316,1336-1353`
- `_batch_oids()` も `f"{commit}:{path}\n"` を `cat-file --batch-check` へ渡し、NUL guard はない。ただし現 production caller は `docs/decisions.md`、`SOURCE_PATH`、`EVIDENCE_CONTRACT_PATH`、整数から生成した generation path だけである。`log` / `ls-tree` の pathspec も `FREEZE_DIR` 定数だった。
- 成果物影響: 現 caller 閉包では受理集合・certified 値は変わらない。将来ここへ契約由来 path を接続すれば同じ alias が再発する。
- 深刻度: **nit**
- 推奨: **不採用**（今 wave の実装範囲）。保証は「契約由来の hostile evidence path の現行 sink を閉じる」と限定する。全 Git path primitive の一般 hardening を望むなら別途裁定へ送る。
- 証拠種別: grep と実 caller の静的追跡。実走なし。

反証できなかった点もある。

- H2 は検査済み exact `text` そのものを f-string と stdin に使っており、`__format__`、再文字列化、Unicode 正規化の入れ替わりは見つからなかった。
- H3 は恒真ではない。`_legacy_unframed_blob` が prefix blob を返すことを先に固定し、その後 production guard の例外を要求するため、H2 を旧条件へ戻すと赤になる。NUL filename を作らない fixture 方針は正しい。
- P1 の reason code 再利用と検査順は、NUL-free 入力の受理・拒否や既存 CR/LF reason を変えない。NUL と別の不正条件を併せ持つ入力だけ reason precedence が変わる。
- H6 は M-C0-SAFE と M-C0-BLOB を単独変異すれば、それぞれ上層 load と下層 read で独立に赤くなり、前後層の mask はない。
- T-732 の `HEAD..main != 0` 時だけ mergeし、merge 後に再検査する補正にはレンズ A の blocker を認めない。ただし lease が land までを覆わない以上、再検査後に main が進む residual race は残るため、「再走をなくす」ではなく「待機中に land 済みの差分を吸収する」と表現すべきである。

## 総括

- **NO-GO**
- must-fix: **2 件**（A1、A3）
- 親が段 4 で裁定すべき点:

  - freeze producer / validator まで NUL-only gate を広げるか、凍結層は invalid contract を許す既存境界として保証を狭めるか。
  - mutation runner の exact node 集合と `expected_nodes` 完全集合を確定すること。
  - `_safe_path` を exact `str` 上で検査する A2 は採用推奨。
  - 非文字列入力の契約を「文字列化後 text」に限定するか、bytes / PathLike 自体も検査対象にするか。
  - probe の結論を blob success record と保存済み出力へ束縛すること。
  - P1、H2、H3、H6、および T-732 の条件付き merge 補正は採用可能。