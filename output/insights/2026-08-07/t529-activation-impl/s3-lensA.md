## must-fix

### 1. R1 を未裁定のまま既決扱いし、未活性 g2 を historical authority に昇格させる

根拠: `s1-brief.md:31-33,40-46`、`s2-plan.md:9-14,160,272-282`、`orchestrator/campaign/env_contract.py:329-380`、`orchestrator/campaign/s8b_ratified_freeze.py:2783-2800,3244-3251`、`output/insights/2026-08-06_t574-world-expansion/README.md:48-62`。

T-529 の逐語裁定は「fuse 解除前に履歴解決を配線する」までであり、artifact の記録 hash を「作成時に active だった証明」として扱う裁定ではない。現行正本も R1 は未裁定と明記している。

技術的にも、プランは inactive g2 を `GENERATIONS` と全世代 index に追加できるようにし、historical resolver は activation record を参照せずその index だけから解決する。したがって、record が一度も選択していない g2 の hash を持つ artifact まで read-only 再検証で受理できる。これは受理集合表にない黙った拡大である。

historical authority を「activation chain 上で ever-active な hash」に限定するか、artifact のレビュー済み commit 自体を別 trust root とする明示的なユーザー裁定を得て、その拡大と正負例を記載する必要がある。

**成果物影響:** 未活性 g2 を記録した floor/freeze/oracle artifact が historical evidence として report の有効行・certified selection の proof 参照へ入り得る。

### 2. P2 は false の `DW-G04` を「既知だった」だけで通過させている

根拠: `s1-brief.md:23-28,43-46`、`s2-plan.md:357-360`、`docs/dev-wave/core.md:57-60`、`orchestrator/campaign/s8b_ratified_freeze.py:1253-1256,1315-1324`、`orchestrator/campaign/s8b_oracle_report.py:1749-1759`、`output/insights/2026-08-06_t574-world-expansion/README.md:55-62`。

実測3が駆動したのは、既に構築した `RatifiedFreeze` を `reverify_published_freeze()` へ直接渡す内部経路である。production report はその前に `load_ratified_freeze()` を通り、現状は active pointer 不在で `no-active` になる。したがって、historical resolver の局所的な配線は確認できても、committed floor protocol を読む production 正例にはなっていない。

また、`DW-G04` は「既知事実なら免除」とは定めていない。逐語裁定 `rulings-inbox/...5rulings.md:263-267` にも、この gate を上書きする指示はない。P1 の「配線済み」という狭い命題は支持できるが、「D196 の前提がすべて充足した」という一般化は成立しない。

T-607 相当の production 到達性と正例を先に得るか、`DW-G04` を今回に限り上書きする明示裁定が必要である。

**成果物影響:** g2 切替後も committed g1 proof chain を production report が再検証できず、oracle report／certified selection の参照集合が欠落したまま T-529 だけが完了扱いになる。

### 3. active g2 正例が production 初期化と六入口を迂回しており、永久 fuse と区別できない

根拠: `s2-plan.md:192-208,212-217,244,345-348`、`orchestrator/campaign/env_contract.py:342-352`、`orchestrator/tests/test_env_contract.py:618-632`。

正例の手順5は、module import 完了後に `_ACTIVATION_STATE`、`GENERATIONS`、index、`REGISTRY` をまとめて patch する。これは production の

`_build_registry → validate_generations → load_activation_state → REGISTRY`

という初期化そのものを駆動しない。したがって、次の実装でも予定試験を通り得る。

- public validator と loader は serial 2 を受理する。
- production module 初期化だけが複数世代を拒否する、または tail view を残す。
- テストはその後 `REGISTRY` を g2 に差し替えるため成功する。

同じ理由で、`REGISTRY=sequence[-1]` 変異を line 217 の負例が必ず検出するという主張も成立しない。さらに六入口の正常系は「既存成功期待」、すなわち g1 のみであり、入口固有に `activation_serial > 1` を拒否する fuse も生き残る。

module 初期化とテストが共有する単一 construction 関数、または g2 source・record・calibration を同一 temp commit に置いた実 import が必要である。加えて六入口それぞれで active g2 receipt が最初の write まで進む正例を置くべきである。

**成果物影響:** テスト成功後も production g2 が import または各 writer で拒否され、certified 成果物・report・試行台帳の contract hash は永久に g1 のままになる。

### 4. activation record 間の世代遷移規則がなく、skip と downgrade が黙って受理される

根拠: `s2-plan.md:77-89,95-101,272-282`、`orchestrator/campaign/env_contract.py:202-228,278-313`。

候補世代列には隣接 successor 制約があるが、record chain の検査は「指定 generation が存在する」ことしか要求しない。よって次が valid chain になる。

- serial 1 の g1 から serial 2 で直接 g3 を選ぶ。
- serial 2 の g2 から serial 3 で g1 へ戻す。
- active contract を一つも変えない no-op record を任意に積む。

predecessor/state hash は順序を束縛するだけで、遷移の意味を制約しない。古い commit への checkout 非検出を明記した `s2-plan.md:113` も、新しい serial による明示 downgrade の説明にはならない。少なくとも non-decreasing、必要なら「各 env は据置または +1」の規則を置くか、rollback／skip を意図した受理拡大として列挙して正例を付ける必要がある。

**成果物影響:** activation serial が増えているのに新規 run の contract hash が旧較正へ戻る、または未審査の中間世代を飛ばす結果が受理され、certified 選択・report・台帳の環境参照が意図しない世代へ変わる。

## should-fix

### 5. 「成果物 bytes は1 byteも変わらない」は既存 committed file に限定すべき

根拠: `s1-brief.md:49-51`、`s2-plan.md:248-259`、`orchestrator/qualification/t126_driver.py:346-425`、`orchestrator/qualification/contract.py:454-509`、`orchestrator/campaign/silo_ladder_rung1.py:254-288`。

既存 `output/` を編集せず contract hash も維持する点は支持できる。一方、activation module／record を identity 閉包へ追加すると、新規 T-126 の `code_identity`・series identity と新規 silo の `runtime_modules_sha256` は必ず変わる。brief の P4 は「既存 committed bytes を書き換えない」と「今後生成する artifact の値も不変」を混同している。後者は false なので、変わる identity 値を明示する必要がある。

### 6. import-time activation failure は入口の例外翻訳で捕捉できない

根拠: `s2-plan.md:133-142,175-182`。

`load_activation_state()` は `env_contract` の module 初期化時に走るため、malformed record や calibration 不一致は各入口関数へ到達する前に発生する。入口内で `EnvContractError` を既存境界例外へ翻訳しても、import 失敗の CLI 契約は保持できない。

入口 API を monkeypatch して拒否する試験だけでなく、壊れた HEAD record を持つ subprocess import／CLI 正例・負例で、実際の rc と診断境界を固定すべきである。

### 7. 末尾空白 g2 は activation mechanics の正例であって production 較正の正例ではない

根拠: `s2-plan.md:194-208`、`orchestrator/tests/test_env_contract.py:840-870`。

現在の Pegasus g1 calibration は effective-clock の既知 self-inconsistent 例である。末尾空白だけを足した g2 は既存 loader 上は合法で、serial 2 の機械経路を発火させる用途には使えるが、新しい較正取得や production evidence の成立は示さない。テストの保証名を activation mechanics に限定し、`DW-G04` の production 正例へ数えないことを明記すべきである。

## nit

なし。

## 総括

現状は land 不可で、must-fix は4件である。最大の問題は、未裁定の historical authority、production では発火しない正例、module patch による永久 fuse の見逃し、activation record の無制約な世代遷移である。

前 wave の指摘のうち、非偽造性を主張しない trust-root 文言、g1 exact-hash grandfather、read-only historical と live current のコード上の分離は改善されている。初期 state hash と既存 calibration SHA も静的再計算では一致した。六入口の列挙された再照合点は、現行コード上の明示的な最初の永続 write より前に置ける。

親実測1・2・4は狭い命題として破れを見つけなかった。実測3は内部 historical 経路まで、実測5は現行正本と矛盾、実測6は patch seam の存在までであり production liveness へ一般化できない。pytest その他のテストは実行していない。