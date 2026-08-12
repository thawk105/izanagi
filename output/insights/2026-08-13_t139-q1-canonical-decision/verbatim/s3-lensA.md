### 1. 読んだ資料と、読めなかった資料

指定された必読資料 12 件はすべて読めた。読めなかった資料はない。

- `s2-plan.md`
- `s1-brief.md`
- `s1-brief-appendix-pins.md`
- `s1-brief-appendix-b1b4.md`
- `src-Q1-Q2-package.md`
- `src-worklog-516-t139.md`
- `src-rulings7.md`
- `src-D234.md`
- `src-D282.md`
- `src-D291.md`
- `src-D292.md`
- `src-D320.md`

追加で、凍結済み `receipt-schema-v1.json`、`record-items-v2.md` の関連節、承認 parser、追補 A の a10/a11、`src-land2q4-package.md` を限定読取した。Web 取得、編集、テスト実行は行っていない。

### 2. 判定 (GO / NO-GO / 条件付き GO)

**NO-GO。**

D320 との衝突が未裁定であることに加え、B1 の旧契約矛盾、B2/B3 の authority、B4 の transcript 閉包、conformance vectors の trust root に実質的な穴が残る。現状のまま canonical decision にすると、実装者ごとに受理集合が変わる。

### 3. 所見一覧

正例の独立照合結果は次のとおり。

| 契約 | 判定 | 根拠 |
|---|---|---|
| D234 継承 | 条件付き | core/addendum の具体物はあるが、条件 (iii) の fold root 表記が二義的 |
| B1 | 未実証 | v3 要件、v2 schema、writer、validator、正例 vector は未存在 |
| B2 | 未実証 | `O_EXCL` writer の部品例はあるが、T-139 の authority・seal・discovery は未存在 |
| B3 | 未実証 | terminal index、固定された系列 authority、write-once publication が未存在 |
| B4 | 構成不能 | `q_derivation`、`certificates`、`result` の grammar が閉じていない |
| Q2 manifest | 未実証 | `F_r*` と manifest/vector index が未発行で、vector digest の外部 anchor もない |

#### A-1-1

| 項目 | 内容 |
|---|---|
| ID | A-1-1 |
| 攻撃面 | A-1 |
| 主張 | D234 (iii) の祖先基準を「承認 decision の fold」と書き換えたため、D234 の fold と将来の `F_r*` のどちらか一意でなく、後者を選ぶと受理集合が空になる。 |
| 証拠 | `s2-plan.md:53,157`; `src-D234.md:81-94` は「本決定を fold した commit」と規定。追補 A の `addendum-a-reissue.md:40-46` は core commit を過去の `88d68f...` に固定している。 |
| 成果物影響 | `F_r*` を祖先 root にすると固定 core ref が条件を満たせず、pilot/main の全 receipt が恒久拒否される。 |

#### A-1-2

| 項目 | 内容 |
|---|---|
| ID | A-1-2 |
| 攻撃面 | A-1 |
| 主張 | 各正例は「writer、validator、正例 vector が land した後」という未存在物への循環条件で、現時点の到達可能性を独立に証明していない。 |
| 証拠 | `s2-plan.md:70,107,126,141,149,261-264`。特に正例 vector が land すれば正例がある、という説明は非空性の証明にならない。 |
| 成果物影響 | 常時 deny の実装と正しい実装を区別できず、空の certified 選択・レポート・台帳を「実装済み」と誤記できる。 |

#### A-2-1

| 項目 | 内容 |
|---|---|
| ID | A-2-1 |
| 攻撃面 | A-2 |
| 主張 | B1 は旧 §6.3 と §8 の矛盾を解消せず、「受理入力に使わない」を「単独では使わない」へ弱めている。 |
| 証拠 | `s2-plan.md:64,66,121,136`; `record-items-v2.md:604-608` は `cmake_cache` 照合を要求する一方、同 `:784-799` は `cmake_cache`、`exclusivity`、`fixed_inputs` などを受理入力に使う実装を拒否する。 |
| 成果物影響 | 最弱実装は自己申告値を他入力と組み合わせて利用でき、別実装は完全無視できるため、同じ receipt の受理・拒否が engine ごとに分岐する。 |

#### A-2-2

| 項目 | 内容 |
|---|---|
| ID | A-2-2 |
| 攻撃面 | A-2 |
| 主張 | B3 は peer path の直接指定だけを除き、caller が `study_id` と `series_id` を選べるうえ、`receipt-set.json` の write-once authority を定めていない。 |
| 証拠 | `s2-plan.md:111-122`; `record-items-v2.md:134-143` では両 ID は receipt field にすぎない。B3 API は `PreregBinding` や B2 の sealed set を受けず、index の `O_EXCL`、履歴検査、terminal transition も規定しない。 |
| 成果物影響 | caller が結果を見て有利な series/index を選ぶか index を差し替え、別系列を隠した paired verdict を certified 選択へ渡せる。 |

#### A-2-3

| 項目 | 内容 |
|---|---|
| ID | A-2-3 |
| 攻撃面 | A-2 |
| 主張 | B4 は top-level と `j_derivation.input` だけを閉じ、`q_derivation.input`、`certificates`、`result`、kind ごとの null/参照関係を未定義のまま残している。 |
| 証拠 | `s2-plan.md:128-137`。承認済み数値契約は `addendum-a-reissue.md:724-750` で区間、選択、終端を定めるが、それらを transcript のどの exact field に写すかがない。 |
| 成果物影響 | validator ごとに異なる transcript を受理でき、再導出 `J`、`design_not_feasible`、main slot 数、最終レポートが分岐する。 |

D234 の 7 条件は個別に次のように照合した。

| 条件 | 判定 | plan |
|---|---|---|
| (i) canonical core path | 維持 | `s2-plan.md:51` |
| (ii) blob 実在・申告 digest・承認 digest | 維持 | `s2-plan.md:52` |
| (iii) D234 fold の子孫 | **二義的** | `s2-plan.md:53`。A-1-1 |
| (iv) addendum A の同型解決・従属三つ組 | 維持 | `s2-plan.md:54` |
| (v) exact-key、欠落・余剰拒否 | 維持 | `s2-plan.md:55` |
| (vi) checkout 由来 head の祖先 | 維持 | `s2-plan.md:56` |
| (vii) pilot の全追補、main の B 追加 | 維持 | `s2-plan.md:57` |

#### A-3-1

| 項目 | 内容 |
|---|---|
| ID | A-3-1 |
| 攻撃面 | A-3 |
| 主張 | `conformance_vectors` は manifest 自身にしか pin されず、D282/D291 または新 `F_r*` payload から期待 digest を与える trust edge がない。 |
| 証拠 | `s2-plan.md:192-214` の root mapping に `conformance_vectors` がない。D282 の exact 6 role は `src-D282.md:27-51`、D291 の exact 2 role は `src-D291.md:60-68`。 |
| 成果物影響 | manifest と弱い vector index を同時に差し替えて自己整合でき、必要な負例を欠く validator が conformance 済みとして certified 経路へ入る。 |

#### A-4-1

| 項目 | 内容 |
|---|---|
| ID | A-4-1 |
| 攻撃面 | A-4 |
| 主張 | B2 の最終 snapshot と `O_EXCL` writer 契約だけでは、seal 前の delete-and-recreate、内容差替え、実際の qsub 前存在を validator が証明できない。 |
| 証拠 | `s2-plan.md:101-103` は syscall 契約と最終双射だけを定める。承認要件は `record-items-v2.md:470-476,777` で create-only 性の検証を要求する。全履歴検査や外部 event authority はない。 |
| 成果物影響 | 最終 bytes だけ整合する改変済み intent が通り、試行台帳の attempt 母集合と投入順序が実際と異なっても受理される。 |

#### A-5-1

| 項目 | 内容 |
|---|---|
| ID | A-5-1 |
| 攻撃面 | A-5 |
| 主張 | decision 題と見出しの「受理述語欠落 4 件を閉じる」は単独引用すると gate 完成と読め、後段の禁止文に依存して初めて contract-only と分かる。 |
| 証拠 | `s2-plan.md:24,28` 対 `s2-plan.md:245-249`。D292 は canonical decision だけが解除権限を持つため、canonical 見出しの曖昧さ自体が危険である (`src-D292.md:3-8`)。 |
| 成果物影響 | 見出しだけを索引・handoff・状態判定が読むと `pilot_submission` を解除済みと誤認し、未完成 gate で投入できる。 |

#### A-6-1

| 項目 | 内容 |
|---|---|
| ID | A-6-1 |
| 攻撃面 | A-6 |
| 主張 | P2 は誤りであり、後発 Q1/Q2 を D320 の暗黙 supersession と推論するだけでは、明示的に残された K1 の裁定を代替できない。 |
| 証拠 | `src-D320.md:7-10` は凍結 pin、commit 束縛、bytes 同一性機構の新設・維持を既定で見送る。plan は新 exact-byte payload、fold root、vector digest pin を要求する (`s2-plan.md:63-65,145-149,197-214`)。`src-land2q4-package.md:92-114` はこの衝突を K1 として明示的に残す一方、`src-rulings7.md:16-20` は K1/D320 を名指ししない。 |
| 成果物影響 | 新 manifest/pin を authority とする resolver と、D320 に従いそれを非 authority とする consumer が併存し、certified 選択・レポートの proof root が分岐する。 |

#### A-7-1

| 項目 | 内容 |
|---|---|
| ID | A-7-1 |
| 攻撃面 | A-7 |
| 主張 | 後続 scope の「consumer」一語では、certified selector、材料 report、試行台帳 sink の各配線と独立再検査を完成条件として固定できない。 |
| 証拠 | `s2-plan.md:243-247`。承認要件は resolver、validator、材料 report がそれぞれ独立に α 台帳履歴を再走すると定める (`record-items-v2.md:654-667`)。 |
| 成果物影響 | validator 単体だけを完成させ、report または certified sink が producer 申告を直接読む経路が残り、選択値・報告値・台帳値が不一致になる。 |

nit はない。上記はいずれも受理集合または成果物参照へ影響する。

### 4. 反証を試みて refuted になったもの

- **既存承認 blob の in-place 書換え:** refuted。plan は `record-items-v3.md` / `receipt-schema-v2.json` と後続 supersession を要求し、v1/v2 の既存 bytes を変更しない (`s2-plan.md:63-65,236`)。
- **D291 の exact 2 role・document relations・historical rejects が落ちる:** refuted。plan は D291 projection の全 field と exact 2 role を維持する (`s2-plan.md:175-190,198`)。
- **`alpha_reservation` が完全に未検査になる:** refuted。manifest では余剰として拒否し、固定 `F_r` の D282 payload を resolver が直接読む義務がある (`s2-plan.md:216`)。既存 seam も `approval_payload.py:166-171` に実在する。
- **plan 本文が明示的に D292 を解除する:** refuted。本文は解除案を却下し、投入禁止を明記する (`s2-plan.md:241,245-249,265`)。ただし見出しの独立曖昧性は A-5-1 として残る。
- **B5 の「実際に他作業がなかった」保証を復活させる:** refuted。記録値の整合までという上限を維持している (`s2-plan.md:226-227,266-267`)。
- **P1 の一 decision 化それ自体が不成立:** refuted。B1〜B4 を独立節・独立 failure reason に保つ限り、同一 decision に束ねること自体は禁止されていない。
- **P3 の実装境界がない:** refuted。contract-only、実装・配線・投入解除ではないことを明記している (`s2-plan.md:243-249`)。
- **P5 の field 数 6 件を踏襲した:** refuted。plan は実 payload の 9 field へ訂正している (`s2-plan.md:216,257`)。

### 5. scope 外だが real な所見 (裁定パッケージ候補)

- D320 の既定を T-139 のどの範囲で上書きするかを、`F_r*`、manifest fold root、vector digest pin ごとにユーザーへ明示択一で返す。
- create-only の意味を「trusted API の実行契約」に限定するか、Git 全履歴・外部 event log など検証可能な履歴性まで要求するかを裁定する。
- `series_id` の authority、B2 sealed set との結線、`receipt-set.json` の create-only publication と terminal transition を決める。
- B4 の `q_derivation`、`certificates`、`result`、failure reason、reference vector を含む完全 grammar を別成果物として凍結する。
- 新 approval payload に conformance-vector index の期待三つ組を置き、manifest の自己 pin でない trust edge を作る。
- producer、resolver、semantic validator、selector、材料 report、試行台帳 sink、full-path positive/negative test を別々の完了対象として登録する。

## 総括

NO-GO。既存の承認済み bytes を書き換える案ではない点と、D292 の本文上の禁止維持は確認できた。  
一方、B1 の旧契約矛盾、B2/B3 の authority、B4 の未閉包、vector の自己 pin が残る。  
D234 (iii) の fold root は D234 の fold と literal に固定しなければならない。  
D320 との衝突は暗黙 supersession で処理せず、実装差分ゼロのままユーザー裁定へ返すべきである。  
修正と完全正例の public-path 実証までは `contract-only`、`pilot_submission = forbidden` を維持する。