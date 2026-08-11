# 段 3 敵対レビュー — sol

静的検査のみ実施した。pytest は実行していない。

## 受理集合の全数監査

厳密には「4 gate + 4 ruling」ではない。

| 面 | 変更点 | 新規の受理拡大 | 裁定根拠 |
|---|---:|---:|---|
| ruling profile | Q3 rollback | 1 | あり |
| ruling profile | Q3 revocation | 1。ただし `no fallback` literal のみ | あり。schema にはなし |
| ruling profile | Q3 X_f position | 1 | あり |
| ruling profile | U-A1 | 0 | 現行 validator は既に `activation-window` と却下案 `post-activation-lease` の両方を `resolved` として受理する。plan は singleton 化して狭める |
| required gate | Q3 3 件 | 3 | あり |
| required gate | U-A1 | 1 | あり |
| required gate | S8/S10 contradiction | 1 | 束 3(a) に根拠あり。ただし実装が空洞化している |
| gate shape | stage fixture gate の改名 | set 置換 | provisional のみ |
| gate shape | stage 6 gate の新設 | set 追加 | 5 点の裁定外 |

したがって新たに通る個別面は profile 3 点、gate status 5 点である。U-A1 は現行 `_SELECTION_ENUMS` が既に二案を受理するため拡大ではない。根拠は `calibration_freeze_authority_contract.py:73-84,445-508`、提案 gate 表は `s2-plan.md:165-180`。

## 所見

### SOL-01

- **ID:** SOL-01-STAGE0-UNREACHABLE
- **深刻度:** blocker
- **破れる具体構成:** plan どおり profile を更新し、`CFAB-S-SEAL`、`CFAB-S-GUARANTEE`、`CFAB-B-SIDE-EFFECT` を `unresolved/null` に固定する。その後の wave が正当に全 pending fixture を executable にし、stage 6・fixture assignment・下位 topology・conformance gate をすべて `resolved` にしても、`_applicable_unresolved_count()` は S と B の 2 件を数える。G だけが非 applicable である。`manifest.status="complete"` は拒否され、`"incomplete"` なら `require_stage0_complete()` が拒否する。S/B を resolve すれば plan の `_EXPECTED_RULING_STATES` に拒否される。
- **根拠の file:line:** `s1-brief.md:20-25` は先送り 3 件を incomplete 理由に残す。`s2-plan.md:152-161,235-240` はその状態を pin し、status 算出を変えない。ところが裁定は stage 5 を完了判定から除外するもの (`package.md:175-185`) であり、設計上 stage 0 は後続の前提である (`calibration-freeze-authority-bundle-design.md:628-639`)。実コードは profile の unresolved を一律に数える (`calibration_freeze_authority_contract.py:519-532,746-755,800-805`)。
- **放置した場合:** 先送りを守る全構成について `manifest.status=complete` の受理集合が空になる。上位 resolver、bundle-mode の certified 選択、材料レポート、`authority_admission` 台帳は永遠に段 0 関門を通れない。進むには、却下された束 3(c) 相当の「incomplete のまま進行」か、S/B の先行裁定のどちらかを密輸するしかない。
- **裁定:** stage 0 完了用の applicability と、将来の X 発効用 applicability を分離しない限り実装しない。

### SOL-02

- **ID:** SOL-02-REVOCATION-SCHEMA-USURPATION
- **深刻度:** blocker
- **破れる具体構成:** plan の `revocations/<bundle_digest>.json`、bundle 当たり 0/1 件、exact 7 key、`revoked_at` を UTC 秒 int とする案を、`revocations/<record_raw_sha256>.json`、承認 record 単位、RFC 3339 timestamp に置換する。live tip の有効な revocation を見たら authority 無しを返し、下位へ fallback しない点は同じである。設計文書の §7.5 だけをこの代案へ変更し、§7.2/§11 row ID と §8.1 ruling ID を維持すれば、現行・計画済みの contract 検査は通る。revocation record を読む validator/test は scope にない。
- **根拠の file:line:** 裁定パッケージは namespace/schema と fallback を併記する一方、推奨・選択内容として具体化しているのは「fallback しない」だけ (`package.md:168-171`)。brief はこれを根拠に schema まで解除する (`s1-brief.md:56-60`)。plan が新たに選んだ file naming、7 key、0/1、commit topology は `s2-plan.md:74-92`。現設計は明示的に schema を未定義としている (`calibration-freeze-authority-bundle-design.md:403,437-438,763-766`)。contract が設計から読むのは row ID と ruling ID だけ (`calibration_freeze_authority_contract.py:251-284`)。
- **放置した場合:** revocation 台帳で受理される path、target 粒度、時刻表現、重複数が、5 点の裁定にないまま固定される。意味上は同じ fail-closed revocation が schema 不一致で拒否され、certified 選択・レポート・台帳の受理集合が根拠なく狭まる。
- **裁定:** これは段 0 の責務の履行ではなく越権である。段 0 は裁定済み schema を exact 化する段であって、複数成立する schema から親が一つを選ぶ段ではない。namespace/schema/topology は裁定パッケージ候補として返す。

### SOL-03

- **ID:** SOL-03-STAGE-SCOPE-SELF-ATTESTATION
- **深刻度:** blocker
- **破れる具体構成:** plan の 9-entry gate 表と hash を入れるが、10 件の case と `row_coverage` は一切変更しない。これは plan 自身の構成である。各 case には stage field がなく、`CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` という文字列だけが「段 5 を除外した」と自己申告する。さらに設計 §10 の段 4 条件へ「旧 prediction bytes を再利用する」と S1 前提を書き足しても、§7.2/§11 row ID を変えなければ contract 検査を通り抜ける。
- **根拠の file:line:** plan は段集合を gate ID だけで表し (`s2-plan.md:117-127,165-181`)、cases と execution を無変更にする (`s2-plan.md:183-188`)。負例も旧 gate ID への戻ししか検査しない (`s2-plan.md:226-231`)。case schema は stage を持たない (`calibration_freeze_authority_contract.py:541-555`)。coverage は fixture ID と design row ID の対応しか持たない (`calibration_freeze_authority_contract.py:699-725`)。gate の owner は非空文字列として読むだけで、status 算出にも段番号にも使われない (`calibration_freeze_authority_contract.py:397-420,746-755`)。
- **放置した場合:** 段 5 を本当に除外した証拠も、段 1〜4・6〜8を本当に閉じた証拠もなく、gate 名だけで `resolved` にできる。将来 `manifest.status=complete`、certified 選択、レポート、台帳が、stage 6 の陽性・陰性 fixture 不在や S1/S2 の密輸を含む構成まで受理する。
- **裁定:** gate ID は証拠ではない。stage→fixture の実体対応から除外集合を導出できる機械表現が scope に入らないなら、実装せず裁定パッケージ候補へ返す。

### SOL-04

- **ID:** SOL-04-STAGE6-PSEUDO-RULING
- **深刻度:** must-fix
- **破れる具体構成:** proposed manifest で `CFAB-S8-S10-CONTRADICTION` を `resolved` にし、同時に `CFAB-STAGE6-COMPLETION-PREDICATE` を `owner=user,status=unresolved` とする。検査はこれを受理するが、predicate 本体・選択値・fixture・evidence はどこにもない。そのままなら永久 blocker、後日 status と module pin だけ `resolved` にすれば predicate 無しで閉じる。
- **根拠の file:line:** brief 自身が段 6 は裁定外の新 gate と認める (`s1-brief.md:61-65`)。plan は旧矛盾を resolved にしつつ新 user gate を追加する (`s2-plan.md:127-138,168-176`)。設計正本が言うのは「段 6 の判定式は段 0 と段 5 の裁定後に書く」であり、新しいユーザー択一が存在するとは書いていない (`calibration-freeze-authority-bundle-design.md:638-639`)。3-key gate schema には predicate 値も証拠もない (`calibration_freeze_authority_contract.py:387-428`)。
- **放置した場合:** 台帳上は §8/§10 矛盾が解決済みになる一方、実体は名前を変えて未解決のまま残る。逆に status だけ閉じれば、policy 未実装の X を stage 6 完了として扱い、bundle-mode の certified 選択・レポートを受理できる。
- **裁定:** 「段 6 も除外するか」「構造部分と policy 依存部分へ分割するか」は新しい裁定パッケージ候補。現 wave で user-owned gate として既成事実化しない。

## 親 brief の実測再検証

- `FROZEN_MANIFEST` は実際に 23 path で、全 key が `output/` 配下である (`test_frozen_artifacts.py:38-85,139-153`)。計画変更面との交差は 0 件だった。
- design、manifest、profile、contract/test の現 raw SHA-256 と Git blob OIDを検索したが、live tree に別 pin はなかった。case bytes の独立 pin は contract module 内にだけ存在する (`calibration_freeze_authority_contract.py:86-116`)。cases は plan 上無変更である。
- `orchestrator/campaign/**` と `tools/**` に対し、CFAB 名、hyphen/underscore 名、全 schema literal、gate ID、owner role、全 fixture ID、`authority_bundle`、`ruling_profile` を検索し、直接参照は 0 件だった。したがって「現 runtime production 配線なし」と FROZEN 交差 0 は反証しない。
- ただし設計正本の変更は将来の production 受理集合を変える。コード参照 0 は SOL-02 の schema 越権を無害化しない。

## 弱い懸念

- revocation 後、既に取得済みの authority object を保持する process を失効させるかは B の裁定境界に触れる。plan の「live tip」だけでは、既存 object の扱いが未確定である。resolver 未実装のため、現時点では検査を抜ける runtime 構成まで確定できず所見には数えない。

## 総括

NO-GO。  
最大の破れは、S/B を blocking unresolved のまま数えるため、束 3(a) を採っても stage 0 完了の受理集合が空になること。  
revocation exact schema と stage 6 の扱いは、5 点の裁定から導出できず裁定パッケージ候補である。  
FROZEN_MANIFEST 交差 0 と現 production 直接参照 0 は確認できた。