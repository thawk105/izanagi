## 総括

- 事実訂正は **3 件**：層3の protocol 軸は実装済み、軸1の文献取得は D2095 で部分再開済み、D2104 項13に「主経路完了まで」という期限はない。
- 改訂案は **既存文書 8 hunk＋spool fragment 2 件**。実装変更はゼロ。
- 準備 T は **5 本**。候補 (v) は T-2115 で実装済みなので新規起票しない。
- 準備 T の完了に superproject の pin 前進が必要なものは **0 本**。pin 前進自体は **T-167 の独立再承認**。
- P1 は部分異議、P2 は異議、P3・P4 は射程を限定して同意。
- 以下は裁定文の案であり、P1〜P4 を確定済みユーザー裁定として扱わない。書込み・テスト・check_docs の実走なし。
- 行番号は現 checkout 基準。パスは repo 相対で記す。

## 1. 事実の裏取り

| 対象 | 現物・結論 |
|---|---|
| (a) TicToc / Cicada genome | `orchestrator/campaign/genome.py:147` に `TICTOC_SPACE`、`:178` に `CICADA_SPACE`、`:209` の `SPACES` に両者を登録。記録は **T-2135**、`docs/archive/worklog-phase3-0902-1170.md:1`。設計判断は **D1418 / D1419**（`docs/decisions.md:44948`、`:44981`）。両者とも静的導出の有効24通りで、campaign 成立の証拠ではない。 |
| (b) floor baseline / 関門 | `orchestrator/campaign/between_run_floor.py:60` の鍵集合は **`{"silo", "mocc"}`**。既に protocol 別辞書であり、「汎用化を新設」ではなく **TicToc baseline の追加**が残件。D1373 述語は `:112`、3証拠の照合は `:131`、呼出しは `:304`。TicToc は先に `:285` の引数検査で拒否される。 |
| (c) mocc 編集面 | `orchestrator/campaign/source_digest.py:86` の EBS、`:99` の ALLOWLIST に `cc/mocc/transaction.cc`。`:81` が trace-hook 専用と明記。登録済みであることは変異探索の許可を意味しない。D579 は `docs/decisions.md:23370`。 |
| (d) 層3照合キー | **「protocol 軸が無い」は現況ではない。** `orchestrator/campaign/layer3_report.py:368` が campaign の protocol を解決、`:489` が floor 側を解決、`:609` が protocol・records・threads・workload を照合し、`:634` の criteria に protocol を出す。**T-2115** が追加済み（`docs/archive/worklog-phase3-0901-1140.md:46`）。 |
| (e) pin / hook branch | `git ls-tree HEAD external/ccbench` の gitlink は **`511c9538e4e8efa54b45cda62e72389ed3b706ec`**。submodule checkout も一致。`orchestrator/campaign/pin.py:28` の記号値は短縮7桁 `511c953`。hook branch は **`izanagi-t1943-mocc-g2-readfrom-witness`**、ローカルの remote-tracking ref は **`e9e477ca1b55348ab4530de0b1cf663ce4555290`**。この ref → 現 checkout の `merge-base --is-ancestor` は rc=1。ネットワーク照会はしていない。文書上の所在は `docs/decisions.md:64010`。 |

追加の訂正：

1. **D2104 項13は期限を「主経路完了まで」と定めていない。** `docs/decisions.md:64971` は保留と pin 再承認を規定し、`:64974` は現行 pin 設計を理由としている。新裁定は「完了待ちを解除した」ではなく、**準備を開始し、材料が揃った時点を再提示時点に定める**と書く。
2. **「D1760 / D1931 で文献調査が停止中」は一括では成立しない。** D2095（`docs/decisions.md:64478`）が軸1 OpenAlex の取得を同日部分再開済み。D1760 自身も通常の文献調査を許す（`:53442`）。D1931 の停止対象は軸3の登録済み検索（`:57963`）。近年 CC 候補の選定を、これら全体の再開に必須依存させない。

## 2. docs 改訂一覧

### 本文骨格

新節は `docs/phase3.md:193`、2026-08-01 改訂の直後、`## 読み方` の手前へ置く。

> **2026-09-17 改訂（本 wave の裁定）:**
> (1) 2026-07-27 改訂 (1) の Silo 固定という「当面」を終了し、mocc を第2例とする certified な protocol 横断比較と合成対象拡張の準備を進める。paper-story の C-1 は、拡張後のシステム主張に必要な未取得証拠として B 群相当へ位置づけ直す。性能比較・変異探索の成立を宣言するものではない。
> (2) 同改訂 (2) の selector 優先度引下げは変更しない。D1360 の trace-hook 経路、D1373 の関門、D579 の変異探索への独立実証、正しさ規律は維持する。
> (3) 段7のうち protocol 横断比較・合成基盤の準備は本裁定で着手可能とする。pin 前進は D1603 の材料3点を揃え、T-167 の再承認として別途提示する。D2104 項13の実測保留は、その再承認と実行条件の充足まで維持する。
> (4) 実装投資は A を先行し、その道具立てを B の近年手法追加へ使う。候補選定調査の扱いは別記する。b2 最適化移植への本格投資は従来のカード試作・前提検証に従う。
> roadmap 本体は改訂しない。本節は phase 内の準備着手順の変更であり、ロードマップの b1 主経路・b2 拡張予約を維持する。

C-1 の B 群化と A→B は、**親が段4で採否を確定してから**裁定文へ入れる。ユーザー逐語にこの分類・順序自体はない。

### 8 hunk

| # | 改訂位置 | 変更 |
|---|---|---|
| H1 | `docs/phase3.md:193` | 上記改訂節を挿入。旧7月27日節は履歴として保持。 |
| H2 | `docs/phase3.md:62` | 「段7全体が8b・層3後」を、**cross-protocol 基盤準備は9月17日改訂、b2 本格投資は従来条件**へ分ける。 |
| H3 | `docs/phase3.md:302` | S1 の「現状 non-blocking」を **「既存 silo 主経路では non-blocking、拡張先 protocol の certified 比較には必須」**へ限定。成立方法の再裁定はしない。 |
| H4 | `docs/phase3.md:470` | 見出しと `:472`〜`:476` の発火条件を二分。基盤準備は本裁定で着手、b2 移植・カタログへの本格投資は前提カードの結果で判断。 |
| H5 | `docs/phase3.md:480` | 「全項目未着手・T番号なし」は当時の記録と明記し、**A(b) の空間登録と層3 protocol 対応は T-2115 / T-2135 で進展済み**と現在地を追記。 |
| H6 | `docs/phase3.md:503` | 「段7全体の発火条件未成立」は8月21日時点の記録と限定し、現在の条件を新改訂節へ向ける。カードの No-Go 自体は変更しない。 |
| H7 | `docs/phase3.md:2595` | T-167 に **「pin 更新未承認・材料整備着手／材料3点取得後に再承認提示」**を追記。旧候補 `c9c1a9c` を今回の採用候補とみなさない。**worklog fragment の `見送り追記` で fold に所有させる。** |
| H8 | `docs/paper-story/README.md:70`〜`:87` | stale 項目数を1件へ更新し、C-1 の位置づけ変更を1項追加。「0件」の説明も過去時点の説明へ直す。移管済み3項の履歴は保持。 |

`docs/phase3.md:114` の旧順序文は日付付き改訂履歴として保持し、新節で supersede の対象を明記する。`:551` の非 silo 較正登録と `:1254` の T-023 発火記録は変更不要。

README の追記案：

> **C-1 の位置づけ変更（2026-09-17）** — 新裁定は Silo 固定の「当面」を終了し、mocc を第2例とする cross-protocol 比較を、拡張後のシステム主張に必要な未取得証拠へ移した。一次資料は phase3 の「2026-09-17 改訂」と本 wave の decisions 記録。凍結版 §1・§8 C-1 のスコープ説明は現在の方針ではない。性能比較0件、較正と性能選定の区別、pin 再承認と D579 の独立実証が必要という限界は維持する。

未 fold 時は新 D 番号を予測せず、**phase 節と実在する decisions fragment**を参照する。spool 外へ placeholder を置かない。

### `check_docs.py` との対応

| 対象 | 当たる検査・対処 |
|---|---|
| H1〜H7 | phase3 は living docs（`tools/check_docs.py:142`）。行番号参照検査 `:6721`、現行 pin literal 禁止 `:6738`、D参照実在性 `:6744`、パス実在性 `:6752`。**本文は節名参照・`pin.CURRENT_PIN` を使用**。この回答の file:line をそのまま docs へ貼らない。 |
| H7 | 台帳境界の一意性 `:2556`、先頭T形式・重複検査 `:2896`、worklog遷移閉包 `:2862`付近以降。T-167 を消去・取消線化・重複起票せず、既存行末への追記にする。 |
| H8 | paper-story は living docs 対象外（`:125`、列挙 `:128`）。**C-1 文言や「0件」を束縛する exact pin は見つからない。** 機械検査外なので一次資料への参照を目視確認する。 |
| fragment 2件 | `_check_spool_guard`（`:1259`）から `validate_spool_tree` による形式・参照検査。採番は placeholder、frontmatter とファイル名を一致させる。 |
| fold後 | D見出し重複 `:6665`、新Dへの参照、worklogの保存則・台帳閉包が対象。wave 中の `check_docs` だけでは `base:` 整合を保証しないため、親が fold dry-run も行う。 |

**これらの本文に対する exact prose pin、phase3 全体の byte 上限は `tools/check_docs.py` では見つからなかった。checker の pin 更新は不要。** byte 制限の集成 `:5940` は command / tools / provenance 等の別集合である。

## 3. spool fragment の骨格

**T/D番号は暫定名だけを使い、実番号は fold が振る。** 規約は `docs/spool/README.md:49`、`docs/spool/decisions/README.md:5`、`docs/spool/worklog/README.md:5`。

### decisions 1件

成果物：

`docs/spool/decisions/2026-09-17-dev-wave-cross-protocol-scope-release-1.md`

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-cross-protocol-scope-release
seq: 1
---

## {{D:cross-protocol-scope-release}}. Silo 固定の当面を終了し、protocol 横断比較の準備と pin 再承認を分離する

**決定:** 親が採択した第2節の裁定本文。
2026-07-27 改訂 (1) の変更範囲、(2) の据置き、
D2104 項13との関係、T-167 の再提示条件を明記する。

**理由:**
- 本 wave のユーザー発話3件を逐語で保存する。
- 論文価値を強めるため、第2 protocol で検証できる条件を整える。
- 空間登録・較正・性能比較・変異合成を区別する。
- 層3 protocol 軸と文献取得の現況訂正を記録する。

**却下した選択肢:**
- stock 専用経路や D1373 の緩和で比較を成立させる。
- 編集面登録だけで mocc の変異探索を許可する。
- 材料なしで pin を進める、旧成果物を新 identity に張り替える。
- 完了済み T-2115 と同じ protocol 軸追加を再起票する。
```

同日裁定の関係は、「D2104 全39項を撤回」ではなく**項13の準備着手・再提示時点に限る変更**とする。

### worklog 1件

成果物：

`docs/spool/worklog/2026-09-17-dev-wave-cross-protocol-scope-release-1.md`

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-cross-protocol-scope-release
seq: 1
title: Silo 固定スコープを解除し、cross-protocol 準備と pin 再承認を分けた
---

## 本文

- ユーザー発話3件と、親が採択・棄却した P1〜P4。
- 決定 = {{D:cross-protocol-scope-release}}。
- 事実訂正3件、未実測事項、実装変更ゼロ。
- 子の静的調査と親の実測を区別した受入記録。
- エージェント工数・異常など、git 差分から復元できない情報。

## 次の一手差分

### 新規

- {{T:cross-protocol-pin-evidence}} **P1・新規**: D1603 の材料3点を揃える。
- {{T:tictoc-trace-hook}} **P2・新規**: submodule branch 上で TicToc hook と positive control を用意する。
- {{T:tictoc-floor-baseline}} **P2・新規**: 既存 floor driver に TicToc baseline を追加する。
- {{T:mocc-mutation-proof-design}} **P1・新規**: mocc 変異探索の独立機械実証を設計する。
- {{T:recent-cc-candidate-selection}} **P2・新規**: 近年 CC 手法の候補選定調査を行う。

### 見送り追記

- [T-167] 2026-09-17、{{D:cross-protocol-scope-release}} により材料整備へ着手。pin 更新は未承認。{{T:cross-protocol-pin-evidence}} で材料3点が揃った時点で本項の再承認として提示する。旧候補 c9c1a9c の採用を意味しない。
```

各T本文には次節の完了判定・依存を入れる。既存active項との重複は親の起票時に確認し、同一主題なら新規を増やさず既存項を更新する。T-167 自体を `完了` にしない。

## 4. pin 非依存で進める準備 T 鎖

ここで「pin前進不要」は、**superproject の gitlink を動かさず準備成果物を完成できる**という意味である。

| T候補 | 目的・完了判定 | 依存 | 実アンカー／予定成果物 | pin前進 |
|---|---|---|---|---|
| (i) `cross-protocol-pin-evidence` | 候補 full OID、D297 検査結果、承認済み定数・事前登録・identityへの波及表を揃える。検査が拒否した場合も理由を記録するが、**前進可能とは判定しない**。 | 対象候補の固定。TicTocも同じ候補へ載せるなら(ii)後に検査を取り直す。 | `tools/check_trace0_preprocess_identity.py:651`、CLI `:728`。予定 `output/insights/<実施日>_cross-protocol-pin-evidence/` | 不要 |
| (ii) `tictoc-trace-hook` | `TsWord` 版IDの設計、branch上の実装、positive/negative control、TRACE分離の証拠を保存。stock経路で代替しない。 | 正式な編集面契約・D16 の適用整理。mocc専用 D579 を流用しない。 | `docs/phase3.md:489`、`external/ccbench/cc/tictoc/transaction.cc`、予定 `output/insights/<実施日>_tictoc-trace-hook/` | 不要 |
| (iii) `tictoc-floor-baseline` | 既存辞書へ根拠付き TicToc baseline を追加。CLI選択と protocol別出力、hook不在時の拒否を確認。完了条件に実測を入れない。 | genome登録は充足済み。コード実装は(ii)と独立、実測開通には(ii)とpin再承認が必要。 | `between_run_floor.py:60`、`:285`、`:304`、`genome.py:147` | 不要 |
| (iv) `mocc-mutation-proof-design` | 変異hole、auditor契約、X/P/I・hot/cold lock被覆、陽性/陰性例と期待拒否を事前に定義。既存証明の充足分と未閉鎖分を表にし、後続実装の受入条件を確定。**設計完了で変異探索を解禁しない。** | D579、既存mocc計装の証拠。 | `docs/decisions.md:23370`、`source_digest.py:81`、`orchestrator/campaign/s3_mocc_lock_coverage.py`。予定 `output/insights/<実施日>_mocc-mutation-proof-design/` | 不要 |
| (v) 層3 protocol 軸 | **起票しない。T-2115 で実装済み。** 将来の非 silo成果物接続では、契約世代・活性化・対応campaignを別途確認する。 | D2083 項3の接続条件。 | `layer3_report.py:530` の直下glob、`:538` の契約pin、`:609` のprotocol照合 | 不要 |
| (vi) `recent-cc-candidate-selection` | 近年手法の一次資料・実装可用性・ライセンス・対象workload・trace移植費用・既存CCとの差を候補表にし、追加対象と棄却理由を提示。 | Bの実装着手はAの共通基盤後。**候補調査は独立可能**。D2095との重複取得を避ける。 | `docs/decisions.md:53442`、`:57963`、`:64478`。予定 `output/insights/<実施日>_recent-cc-candidate-selection/` | 不要 |

(i) の既存 checker は無条件に protocol 汎用ではない。`tools/check_trace0_preprocess_identity.py:678` は `SILO_SPACE` の context を列挙し、`:186` は追加・削除・renameを、`:195` はheader変更を拒否する。**候補全体を検査できたか、どの context の保証か**を材料に含める。

依存の中心は次のとおり。

```text
(i) 材料3点 ─→ T-167 の独立再承認 ─→ pin前進 ─→ 非silo実測の条件確認
(ii) TicToc hook ─┘                           ↑
(iii) TicToc baseline ────────────────────────┘

(iv) mocc変異実証設計 → 別waveの実装・機械実証 → mocc合成対象の開放
(vi) 候補調査 → Aの共通基盤を使うB実装の選定
```

材料3点だけで verifier 通過や正式測定の認可まで充足した扱いにしない。

## 5. P1〜P4 への異議

### P1 — 部分異議

**Aの実装投資を先行することには同意。Bの候補調査までA完了に従属させる点には異議。**

通常の関連研究調査は D1760 が許している（`docs/decisions.md:53442`）。軸1の登録済み取得も D2095 で部分再開済み（`:64478`）。軸3の停止は説明可能性の登録検索に限る（`:57963`）。

したがって、**「A→B実装、候補調査は独立」**が適切。新手法の要求を早期に知ることは、共通基盤の要件確認にも使える。「全停止中の文献調査を再開しないと候補選定できない」という前提は採らない。

### P2 — 異議

**SHA束縛は実在する。D297 合格から内容ハッシュへの置換を導くことはできない。**

grepで確認した主な束縛：

| 層 | ファイル・行 | 束縛 |
|---|---|---|
| A-1事前登録 | `orchestrator/campaign/paper_story_a1_paired.v3-sized.json:17`、`...v3-pilot.json:17` | `canonical_pin` に現行 full SHA |
| A-1 source契約 | `paper_story_a1_source.v1.json:5`、`...v2.json:4` | `canonical_head` |
| A-1 consumer | `paper_story_a1_paired.py:205`、`:1076`、`:5228` | 固定OIDとsource evidenceの照合 |
| 性能事前登録 | `docs/backoff-policy-performance-preregistration.md:129`、`docs/backoff-counterfactual-preregistration.md:140`、`docs/dynamic-backoff-preregistration.md:82` | 現行full SHA＋patch stack |
| balanced別事前登録 | `docs/t1998-balanced-stock-inline-preregistration.md:83`、`:144` | gitlink full SHA |
| campaign identity | `orchestrator/campaign/ident.py:214`、`:226` | `ccbench_commit` をpreimageに含めSHA化 |
| campaign.lock | `campaign_lock.py:19`、`ident.py:378` | exact key集合と保存preimage照合 |
| source evidence | `source_digest.py:192`、`:253` | `ccbench_commit` を保持 |
| A-2実行 | `paper_story_a2_certification.py:1352`、`:3310`、`:3693` | evidence・identity・現行pinとの一致 |
| H1/H2関連の駆動 | `p3_autonomous_workload_trial.py:828`、`:1279` | baseのcommitを継承してidentityを生成 |

**H1/H2事前登録本文に現行 full SHA を直接固定する箇所は、`docs/phase3-8c-preregistration.md` と関連s8c群の検索では見つからない。** この限定を付け、A-1と同じ固定方式だと断定しない。

結論は二つを分ける。

- **過去成果物の無効化ではない。** 旧pinと旧identityを保持する。`pin.py:11`〜`:18` も歴史的driverのpin保持を明記している。
- **新pinで旧登録・旧lockをそのまま使えるとは限らない。** A-1の別checkout維持、新系列・追補の要否、環境契約への波及を(i)で調べる。

D297 は限定contextの観測者効果検査であり、identity schema変更の承認ではない。

### P3 — 同意、ただし主張を二段に分ける

実測と独立実証が揃った後に言える文面：

> 「Silo と MOCC の対象 workload に対し、同じ正しさ検証・性能判定の契約で variant を評価し、比較結果と選択根拠を返した。」

**mocc側で実際に変異を生成・検証した後**には、さらに：

> 「この合成・選択手順を Silo 以外の第2実装でも実証した。」

| 主張階層 | 効果 |
|---|---|
| 評価器 | 異なるCC実装で正しさ・identity・性能判定を適用した証拠が増える。ただしhookだけでは不足。 |
| システム | 第2例で合成・比較・選択まで成立すれば、Silo専用という適用範囲を広げる。stock対比較だけなら評価経路の拡張まで。 |
| LLM固有 | 2 protocol化だけでは因果的寄与・優越を示さない。別の対照が必要。 |
| 無人自律 | protocol数の追加では証明しない。セッション非依存駆動・正式系列の証拠が別途必要。 |

根拠は `docs/phase3.md:11`、`:48`、`docs/paper-story/2026-09-17.md:300`、`:1699`、`:2476`。10 protocol選択、descriptor駆動の因果、一般的なCC合成の成立へ広げない。

### P4 — 同意、ただし b2 全体の前倒しは含めない

本案は roadmap 本体を編集せず、phase内の準備着手条件を記録する。`docs/roadmap-history/README.md:26` は協議済み改訂についても版上げ等を不要としている。

ただし `docs/roadmap.md:478` の E を実質的に全面撤回しながら「本体は触らない」とするのは不整合。**cross-protocol準備の前倒しと、b2本格投資の順序を分ける**。b2まで前倒しする場合は、本パッケージの射程を拡張した判断として親が扱う必要がある。

## 6. リスク

- **文書サイズと検査範囲。** phase3 は現状 **547,784 bytes / 3,122行**。`check_docs.py` に全体byte上限は見つからないが、詳細を新節へ大量複製せず、裁定の射程と参照だけにする。本文の exact pin 更新は不要という静的所見であり、親の実測合格を代替しない。
- **同日裁定の記録。** D2104 の「推奨通り」一括承認と、本 wave の直接発話3件を別々に保存する。採択する場合は「直接発話を受け、項13の準備着手・再提示時点を変更した」と明記する。**ユーザーが明示していないA→B・B群化・pin承認を逐語の内容として記録しない。**
- **T-167 の旧候補。** `c9c1a9c` は古い項目名に残る候補である。今回観測したhook refの先端を自動採用せず、候補full OIDと検査対象を(i)で固定する。
- **凍結版の保持。** `docs/paper-story/2026-09-17.md` は変更しない。README stale節に方針変更と一次資料を追加し、性能比較0件など未解消の限界は残す。
- **foldとの衝突。** T-167 の行末追記はspoolだけが所有し、同じ文を直接編集でも足さない。新D/T番号を先取りしない。親が `spool_fold.py --dry-run --show-diff` で採番・参照・台帳遷移を確認し、foldはland経路に任せる。
- **射程の混同。** scope解除、hook移植、pin更新、floor取得、変異探索解禁、性能比較、論文主張成立は別々の到達点。今回のdocs-only裁定で完了扱いにできるのは、方針変更の記録と準備項目の起票までである。
