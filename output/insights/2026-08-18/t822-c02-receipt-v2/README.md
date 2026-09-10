# [T-822] 条件 2 の機械検査化と受領証 v2 (2026-08-18)

`authority: none` / `default_effect: no-state-change` — 本書は記録であり裁定ではない。
可変状態の正本は `docs/worklog.md` 末尾。一次資料 = 同 dir の `s1-brief.md` /
`s4-adjudication.md` / `s6-ruling.md` / `parent-measurements.md` / `mutation-spec.json` /
`mutation-out.json` / `verbatim/`。

## 1. 何が問題だったか

[T-1311] で arm は実行を変えるようになった (7 sink が同じ digest を消費し、変異 10/10 が KILLED)。
それでも受入 receipt は `certifying=false` かつ `c02-arm-binding-unproven` を必須理由として
保持し続けていた。証拠契約の条件 2 が `machine_checkable: false` で評価器 table にも無く、
受領証側にも「arm 束縛が証明された」と言える機械検査が無かったためである。

あわせて [T-822] 問 3 の実名不整合が残っていた。証拠契約と評価器が
`trial_registry` に **`accept_trial` という名の関数**を探していたが、その名前は実装に存在しない。
実名は `assert_trial_registry_acceptance` である。

## 2. 何をしたか

### 2.1 条件 2 を評価器 table へ載せた

- 契約の条件 2 を `machine_checkable: true` にし、`_evaluate_c02` を新設した。
- 機械検査対象は 6 条件 (1・4・9・10・11・12) から **7 条件** (2 を追加) になった。
- 判定器の版を `s8c-decider/v3` へ上げ、条件契約の**第 7 世代**を発行した。
- **充足を返す経路は 1 本も作っていない。** 終端は他の機械条件と同じ
  `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` である。

評価器は静的 AST だけを見る。段 6 レビューの指摘を受け、次の 2 点を強めた。

- `_called_names` は dead code と nested scope を数えるため、同 module に既存の `_live_nodes` を
  使う形へ変え、`if True: return` の後続も dead として打ち切る。
- namespace 構成子は「arm と digest を含む f-string が存在する」だけでは足りず、
  **その f-string が当該関数の return 値であること**を要求する
  (計算するが使わない実装を落とすため)。完全な alias 追跡は scope 外とした。

### 2.2 受領証 v2 — 理由落としの根拠を bytes からの再導出にした

v1 は `LEGACY_SCHEMA_VERSION` として残し、v2 を新設した。

- v2 の必須理由は `t468-approval-authority-absent` のみ。
- `c02-arm-binding-unproven` を落とせるのは、**受領証が名指して hash した bytes から
  digest を再導出できたときに限る。**
- `certifying` は両版とも構造的に `False`。**certified 選択の受理集合は 1 件も広がっていない。**

段 2 プランの当初案は receipt・report・run-start の 3 者一致を見る形だった。段 6 レビュー A が
「3 者はいずれも producer が書いた要約であり、相異なる 6 digest を捏造して binding digest を
正しく再計算した bundle が全部通る」と指摘し、親が採用した。最終形は、権威ある chain
(`autonomous_trial_completeness._check_arm_digest_chain`) と同じく **hash 済み report の
cell descriptor から canonical bytes を作って content digest を再計算**する。

検査は 4 段である。

1. descriptor bytes からの content digest 再導出
2. `SHA256(domain || holdout || arm || content_digest)` による binding digest 再計算
3. 同一 holdout の 3 arm の content digest が pairwise 非同一
4. report と attempt journal の run-start が receipt と exact 一致

descriptor を持たない partial report は C02 理由を**残す** fail-closed 形とした。

### 2.3 問 3 の実名整備 — 判定結果は 1 bit も変わらない

契約 JSON・評価器 literal・token-only fixture の 3 面で `accept_trial` を実名へ揃えた。

**この修正は受理集合を広げない。** 親が AST で実測したところ、実名関数
`assert_trial_registry_acceptance` は `assert_campaign_layer3_chain` も
`verify_s8c_cross_binding` も呼んでおらず、両名は `trial_registry.py` に **0 回**しか出現しない。
したがって条件 9 は同じ理由で不充足のままであり、条件 10 は verifier 側で先に落ちて
acceptance の名前検査へ到達すらしない。これは**将来 (i) を閉じたときに自動追随するための
潜在バグ修正**である。

非機械条件 C03 / C07 / C08 に残る同じ誤名は scope 外と裁定した (§5)。

### 2.4 恒真化の除去 — 2 件

- **充足可能集合が防壁でなかった。** `SATISFIABLE_CONDITION_IDS` は宣言されるだけで
  dispatch 後に照合されていなかった。実行時の関門にし、許可外の条件へ評価器が充足を返したら
  fail-closed で落とす。
- **負の対照が守るべき関数を monkeypatch していた。** 受領証側の対照は
  `_arm_execution_authorizes_reason_drop` を `False` へ差し替えて赤を作っており、
  **実装を `return True` へ変える変異を 1 件も殺せなかった。** 実データで実関数を通す形へ
  作り直した。変異 `t822.m14-reason-drop-always-true` がこの是正の直接の検定である。

### 2.5 契約の名前が実在することを検査するメタ検査

契約が名指す関数名の実在を検査する test は repo に **0 件**だった (親実測)。
新設し、chain 内の全 token を `checked` / `excluded` / `missing` の 3 集合へ分類して
**3 集合とも exact に pin** する。分類できない token が 1 つでも出たら赤にする。
先頭 hop だけを見て残りを黙って skip する形は段 6 レビューが見つけ、是正した。

## 3. 実測

- 焦点走: **976 passed / 0 failed** (11 test file、commit `e9846217`)
- 変異 matrix: **baseline PASSED、KILLED 13 / 13、SURVIVED 0、MISMATCH 0**
  (`mutation-out2.json`、commit `80669f6c`、dispatch runner、14 走行)。
  期待 node は全件 `matches_expectation = True`。
- `python3 tools/check_docs.py` rc=0、`check_ai_provenance.py --message-file` rc=0

期待 node は probe 走 (全件 SURVIVED 期待) で観測集合を集めてから完全集合として再登録した。
その probe で **1 件が生存**し、対照の欠落を実測で発見した (§2.4 の 2 点目とは別件、§6-5)。

**除外 1 件**: `test_repository_tip_binds_current_decider_version_without_activation` は
runner argv の `--deselect` で外した。この test は xdist の group marker を持ち、失敗行では
`@s8c-preregistration-candidate` 接尾辞が付くが pytest collection 側には現れない。harness は
両側を同じ正規化に通すため、この node は「collection に実在すること」と「観測 node と一致すること」を
同時に満たせない。xdist を切る案は実測 1 run 7 分 21 秒 (14 run で約 103 分) で採らなかった。
除外により `t822.m11` の killer は 5 → 4 になったが、他 12 変異の期待 node は不変である。

## 4. 敵対検証

段 3 (相談 2 本) と段 6 (レビュー 2 本) はいずれも **NO-GO** を返した。
親が採用した主な所見は §2 に織り込んだ。裁定の全体は `s4-adjudication.md` と `s6-ruling.md`。

親が **refuted / 格下げ**した所見:

- 「逆射影が report と run-start の不一致を隠す」→ 格下げ。production の chain が
  `dict(start_arm) != dict(report_arm)` で 3 者一致を既に強制しており、不一致 bundle は
  producer が作れない。射影に 3 者一致を足すのは安価なので nit として実装した。
- 「同名 `C02` の二義化」→ 部分採用。恒久的な必須理由を足すと理由落とし自体が無意味になるため、
  命名と文書で解いた。規範文書に「受領証の理由落ち = 受領証が自分の参照 bytes 上で arm 束縛を
  証明した、であって事前登録条件 2 の充足ではない」と明記した。

親自身の前提も 2 件反証された。

- 「additive schema なら凍結 golden を保てる」→ **誤り**。producer が v2 を出す以上 golden は割れる。
  既存の射影機構へ値付き消費を足すのが正規経路だった。
- 「第 7 世代の hash が受領証側の source bytes に依存する」→ **誤り**。protected preimage は
  証拠契約 hash と規範文書の 3 hash だけである。

## 5. 成果物影響

**certified 選択の値・proof 参照は 1 件も変わっていない。** 変わったのは 3 点である。

1. 受領証が掲げる非認証理由の集合 — v2 は arm 束縛を bytes で証明できたときだけ
   `c02-arm-binding-unproven` を落とす。`certifying` は依然 false で、
   `t468-approval-authority-absent` は必須のまま残る。
2. 判定器が条件 2 を評価器へ dispatch するようになった (機械検査対象 6 → 7 条件)。
3. 許可外の条件への充足申告が実行時に fail-closed で落ちるようになった。

## 6. 残る限界 (paper over しない)

1. **bundle 一式の捏造は受領証層では落ちない。** 受領証が束縛するのは「名指して hash した bytes」
   であり、その bytes 自体を全部作り替える攻撃は事前登録 commit 束縛と追記専用 registry の
   射程に残る。この 2 機構が機械検査対象外である現在地は変わっていない。
2. **条件 2 の評価器は静的 AST だけを見る。** 完全な束縛解決 (alias 追跡) は実装しておらず、
   「静的到達可能性は完了の証明ではない」という §6 の但し書きは条件 2 にもそのまま当たる。
3. **非機械条件 C03 / C07 / C08 に `accept_trial` の誤名が残る。** 現時点で判定結果は変わらないが、
   将来それらを機械化する wave が同じ穴を踏む。裁定パッケージ候補。
4. **条件 9 / 10 は不充足のまま。** `verify_s8c_cross_binding` は実装に存在せず、
   Layer-3 chain の acceptance 必須化は [T-822] 問 1 側 ([T-1310] 待ち) の射程である。
5. **受領証 verifier の拒否点 22 箇所のうち、直接の負の対照を持つのは 6 箇所である** (実測)。
   変異 probe で 1 件が生存し (report echo の一致検査)、その対照を足して 6 箇所になった。
   残る 15 箇所は構成可能な対照が未整備である (1 箇所は公開入力から到達しない防御分岐)。
   本 wave の scope は arm 束縛の証明であり、全拒否点への対照整備は
   `DW-G03` の族一般化 (独立 2 例) に当たるため実装していない。裁定パッケージ候補。
6. **変異 harness と xdist の node 名前空間が衝突する。** group marker を持つ test は
   失敗行と collection で異なる ID を持ち、期待 node として登録できない (§3 の除外 1 件)。
   本 wave は `--deselect` で回避したが、機構としては未解決である。裁定パッケージ候補。

## 7. 並行 wave との衝突とその解き方

本 wave の途中で、再凍結 wave (`dev-wave-t1336-t1337-t1347-refreeze`) が先に land し、
条件契約の**第 6 世代を取った**。本 wave の世代は第 7 世代になった。

**merge では解けない型だった。** 凍結の不変検査は `for item in graph.commits` で
全祖先を走査し、各点で契約と世代 record の一致を要求する。したがって
「契約を変えたが tip の世代 record は古いまま」の commit が祖先に残ると、
後から正しい世代を足しても永久に拒否される。合成監査の子がこれを見つけ、親が裏取りした。

解決は履歴の組み直しである。作業内容を main 基準の patch として退避し、branch を main tip へ
戻して再適用し、**契約変更・実装・規範文書・世代 record を単一 commit に入れた**。
