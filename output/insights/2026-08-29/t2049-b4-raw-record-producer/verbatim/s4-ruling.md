# [T-2049] 段 4 裁定 — plan v2 と変異事前登録

段 3 の 2 レーンは独立に同じ中核欠陥 4 件へ到達した (precursor 恒真 / 割当が append 順 /
事前発行 result path の無視 / arm ごとの pair 選び直し)。独立 2 例の一致をもって real と認定する。

## 0. 親 brief の訂正 (両レーンが指摘し、親が real と認めたもの)

- **(訂正 1) WAL と checkpoint の前後関係を逆に書いていた。** 観測されたのは
  「loop state が WAL より 1 世代先行」であり、事前登録 §7.2 が非保証に挙げる
  「進んだ WAL と一世代古い loop state」ではない。**向きが逆**である。
  producer への要求は変わらない (両者の対応を fail-closed にする) が、根拠の記述を訂正する。
- **(訂正 2) 実アンカー表を「実測済み」と一括で書いたのは過大である。** 1 本の legacy on campaign から
  実測できたのは lowercase stage、`fitness_tps` の十進 token、whiteboard `result`、`reflux` の 4 つだけ。
  receipt・sidecar・abort・missing・off・並行性・201 block の値域は**静的仕様であって実測ではない**。
  plan v2 ではこの区別を source artifact の記述にも持ち込む。
- **(訂正 3) 「欠けているのは producer だけ」は 49 passed から導けない。** 導けるのは
  「消費側は適合 raw 文書を受理する」までである。主張を弱める。
- **(訂正 4) 「402 campaign root」という前提は現 launcher の identity と一致しない。**
  campaign id は driver と arm の固定 config から決まり、proposal / block / attempt を含まない。
  したがって **1 arm 試行の単位は campaign root ではなく (campaign root, iteration)** であり、
  同一 root に複数 block の iteration が同居しうる。これは設計の土台なので plan v2 で作り直す。
- **(訂正 5) 既存 pre-run publication (`B4PrerunPublication`) を入力契約から落としていた。**
  同 publication は `attempt_id -> artifact_path` の完全な写像、封印済み registry、manifest、
  schedule receipt、seed receipt、完全性 receipt を既に持つ。これが再利用すべき既存機構である。

## 1. 所見の裁定

### real・採用 (plan v2 に反映する)

| # | 所見 | 裁定 |
|---|---|---|
| L1 / S1 | `precursor_hash` が registry からの転記だけで campaign と束縛されない | real・採用 (§2.1、§2.6) |
| L2 / S3 | 任意 `record_root` への slot 群は新しい一回性台帳の新設である | real・採用 (§2.2) |
| L3 / S2 | publish 順を実行 slot として記録している | real・採用 (§2.3) |
| L4 | 読み取り中不変を campaign 終了と取り違えている | real・採用 (§2.4) |
| L5 | post-link `durability_unknown` から再開できない | real・採用 (§2.2) |
| L7 | `contaminated` の証拠源が事前登録の汚染と一致しない | real・採用 (§2.5) |
| L8 / S5 | arm ごとに別の receipt pair を選べる | real・採用 (§2.5) |
| S4 | 同一の実試行を複数 block へ複製できる | real・採用 (§2.6) |
| S6 | crash と入口停止が artifact から識別不能 | real・採用 (§2.7) |
| S7 | `anomaly_class` が treatment 後の ABORT reason を指している | real・採用 (§2.7) |
| S8 | §7.1 が要求する model hash が schema にない | real・採用 (§2.7) |
| S9 | ledger が許す非有限十進 ratio を producer が新たに拒否する | real・採用 (§2.8) |
| L10 | test 設計に変異の一意帰属がない | real・採用 (§3) |
| L11 | `491796.5` は binary float で正確に表せるため負例が発火しない | real・採用 (§3) |
| L12 | 時点を狙う負例に発火位置の識別がない | real・採用 (§3) |
| S-nit1 | 「binary float を経由しない」は字義どおりには成立しない | real・採用 (§2.8) |
| S-nit2 | 統合正例が authority 分岐を一度も通らない | real・採用 (§3) |

### real だが本 wave の scope 外 — 非保証として明記し、裁定パッケージへ回す

| # | 所見 | 裁定 |
|---|---|---|
| L6 | `treatment_fired` は「その decision で次を合成した」を証明しない | real。事前登録 §7.2 が既に開いた経路として明記済み。producer は receipt 水準の意味に**限定して**書き、非保証へ列挙する。閉じるには critic 経路の変更が要り、D824 の明示除外と衝突する |
| L9 | producer が凍結 closure 外に残り、production verdict への接続が無い | real。本 wave の scope 定義そのもの。`p3_b4_analysis_path.py` の 5-file pin は動かさない。非保証へ列挙し、裁定パッケージ 3 として返す |
| L-pkg1 / L-pkg2 / L-pkg3 | 3 件の裁定パッケージ候補 | §4 でユーザーへ返す |

### refuted

- なし。両レーンの所見はいずれも実コードで裏が取れた。

## 2. plan v2 — 確定する設計

### 2.1 入力契約を pre-run publication に束縛する (L1/L2/S1/S3 の根治)

producer の公開 API は、caller 宣言の `block_id` と `record_root` を**受けない**。
既存 `B4PrerunPublication` を読み込み、そこから次を得る。

- `attempt_id -> artifact_path` の事前確定した写像 (`planned_result_artifacts`)
- 封印済み registry (`initial_proposal_sha256` を含む attempt 行)
- manifest (`block_id`、`assignment_schedule`、reference 3 値、canonical 順序)

**出力先は `planned_result_artifacts[attempt_id].artifact_path` ちょうど 1 か所である。**
caller が root を選べる経路を作らない。これは新しい台帳ではなく、既に封印された
issuer commitment の消費であり、ユーザー裁定「既存機構の再利用を優先し新しい一回性台帳を作らない」に従う。

### 2.2 一回性は「事前確定 path の排他 create」だけが担う (L2/L5)

- slot 番号や `arms/<ordinal>-slot-<n>.json` のような producer 固有の occupancy 状態機械を**作らない**。
- 排他 create が既存 target に当たったら、**既存 bytes を読み、同一なら成功 (冪等)、
  異なれば構造化拒否**とする。これで post-link 不明状態から再開できる。
- 「link 後の不確定」を不可逆な終端にしない。再実行が同じ入力から同じ canonical bytes を作る限り
  何度でも通る。canonical bytes は決定的でなければならない (timestamp・pid・乱数を含めない)。

### 2.3 実行 slot は durable な証拠から導く (L3/S2)

`assignment_observation` を publish 順から作ってはならない。
両 arm の **WAL 先頭 record の `ts`** (production writer が書いた durable な値) を比較して導く。

- 2 つの `ts` が同値、または一方が読めない場合は fail-closed とし、raw を組み立てない。
- 使った 2 つの `ts` と、その出所 (file path と record 位置) を source artifact に記録する。
  後から第三者が同じ判定を再現できなければ、権威を名乗る意味がない。

### 2.4 終端性は終端 record の実在で決める (L4)

「読み取り前後で bytes が変わらなかった」ことは終端性の証拠ではない。

- `execution_disposition = executed` は、当該 iteration の **終端 record (`commit` または `abort`) が
  WAL に実在する**ときだけ。
- 終端 record が無いときは、**まだ走っている**のか**終端 record を残さずに終わった**のかを
  区別しなければならない。区別せずに前者を `missing` として封印すると実走中の試行が欠測になり、
  後者を publish しないと crash した試行が報告から消える (file-drawer)。
  **どちらも事前登録 §7.1 違反である。**
- 区別には**既存の advisory campaign lock (`orchestrator/campaign/lock.py` の `campaign_lock`) を使う。**
  非 blocking で取得できれば所有 process は生きていない = その走行は終わっている。
  `CampaignBusy` なら実行中である。新しい liveness 機構を作らない。
  - 終端 record あり → `executed`。stage / reason を写像する。
  - 終端 record なし + lock 取得可 → 終端記録を残さず終了した → `terminal-record-absent` を publish する。
  - 終端 record なし + `CampaignBusy` → **まだ publish しない。** 後で再実行する。
- 観測した 2 条件 (終端 record の有無、lock の取得可否) を source artifact に記録する。
- **非保証:** flock は advisory であり、所有しない process が保持することも、
  一度終わった campaign が後から再開されることも排除しない。逐語で列挙する。
- 「読み取り前後で bytes が変わらなかった」ことは、上のどの判定の代用にもならない。

### 2.5 pair は block 単位で 1 つに固定する (L7/L8/S5)

- 最終組立てで、同一 block の on/off 2 artifact が **同じ `pair_id`** を宣言していることを要求する。
  異なれば拒否する。arm ごとの local 検査だけで通してはならない。
- `contaminated` は事前登録の意味 (off アームが赤詳細を受けてしまったこと) に合わせる。
  証拠源は receipt の off digest に赤詳細が載っていないことの検証であり、
  `admitted_view_sha256` の不一致は **`protocol_ok=false`** 側へ寄せる。
  両者を取り違えると、protocol violation を contamination として弱く報告してしまう。

### 2.6 attempt の一意性を publication 内で閉じる (S4/L1)

- 同一 publication 内で、`(campaign_id, iteration, arm)` の 3 つ組が 2 つ以上の `attempt_id` に
  現れたら拒否する。同じ実試行を複数 block へ複製する経路を塞ぐ。
- **閉じられないもの:** registry の `initial_proposal_sha256` が、その campaign の当該 iteration を
  実際に生んだ precursor であること。実測の結果、
  **`initial_proposal_sha256` を計算・記録する経路は repo のどこにも存在しない**
  (registry の field としてしか現れない)。したがって producer は転記の権威に留まる。
  **これを閉じたと書いてはならない。** source artifact の非保証へ逐語で列挙する。

### 2.7 報告 field を実体に合わせる (S6/S7/S8)

- **disposition を推測しない。** crash と入口停止を識別する証拠が artifact に無いなら、
  その 2 値を使わない。証拠が決める値だけを書き、決まらなければ artifact を publish しない (§2.4)。
- `anomaly_class` という名前を使わない。実体は終端 ABORT の `reason` なので `terminal_reason` と呼ぶ。
  treatment precursor の anomaly class を表す field は現状の証拠から作れない。非保証へ列挙する。
- §7.1 の `model/prompt/projection hash` のうち、receipt に実在するのは
  `role_file_sha256`、`effective_prompt_sha256`、`projection_sha256` である。
  **model は `model_snapshot` という非 hash の識別子しか無い。** 実在するものを正確な名前で持ち、
  model hash が無いことを非保証へ書く。無い物を hash と名乗らせない。

### 2.8 数値の扱いを実態に合わせる (S9/S-nit1)

- 「binary float を一切経由しない」とは書かない。実際には WAL の schema gate が一度 float へ decode する。
  producer が保証するのは **出力 token が入力 lexeme と同一であること**である。
  そのため WAL bytes を 2 度読み、2 度目で lexeme を保存する経路を明示する。
- `reference_tps` が有限十進で表せない既約有理数のとき、raw JSON では exact に表現できない
  (`as_b4_exact_fraction` は list を受けない)。これは**凍結された消費側の制約**であって
  producer が作る制約ではない。producer は丸めず、**この理由だけを名指しした構造化拒否**を返す。
  裁定パッケージ 2 として返す。

### 2.85 D162 の適用 (段 4 直前の既裁定再照合で発見。主題照合で引いた)

D162「正例 artifact の適格性は producer が宣言せず、独立 validator の再計算だけを権威とする」は
本 wave に直接効く。凍結された adapter が `treatment_fired` / `contaminated` / `protocol_ok` を
raw 文書に**要求する**以上、producer はこれらを出力せざるをえない。しかし D162 決定 1 は
「producer が宣言できるのは閉集合の種別と raw な実行事実・証拠 pointer だけ」と定める。
両立させるため次を必須とする。

- **(a) 入力を閉じる。** producer の公開 API は `treatment_fired`、`contaminated`、`protocol_ok`、
  `execution_disposition`、`precursor_hash`、`assignment_observation`、`throughput` を
  **caller から受け取らない。** これらを含む入力は未知 field として拒否する (D162 決定 2)。
  すべて producer が証拠 bytes から自ら導く。
- **(b) 読み方を固定する。** 各証拠は**単一 fd / 単一 snapshot** で読み、hash と parse を
  **同一 byte buffer** に対して行う (D162 決定 5)。検査前後で hash を取り直す方式は
  ABA (検査中だけ適合 bytes へ差し替える) を防がないため採らない。**symlink は拒否する。**
  これは luna #4 (読み取り中不変を終端性と取り違える) への正しい答えでもある —
  単一 snapshot は「同じ bytes を見た」ことの担保であって終端性の担保ではなく、
  終端性は §2.4 が別に決める。
- **(c) 名乗りの限界。** producer は「適格である」と宣言しない。書けるのは観測事実と証拠 pointer、
  および凍結 adapter が要求する 3 boolean の**導出結果**までである。導出に使った証拠 pointer を
  source artifact に必ず残し、第三者が同じ bytes から再導出できるようにする。

### 2.9 変更面 (据え置き)

- 新規: `orchestrator/campaign/p3_b4_raw_record_producer.py`
- 新規: `orchestrator/tests/test_p3_b4_raw_record_producer.py`
  (末尾に `if __name__ == "__main__": raise SystemExit(pytest.main([__file__, "-q"]))` を置く)
- 既存 file の編集は行わない。`_SOURCE_CLOSURE_PATHS` に新 module を足さない。

### 2.10 名乗ってよい範囲

成果物・docstring・worklog で **`authoritative` / file-drawer closed / verdict-ready と名乗らない。**
名乗ってよいのは「事前確定した path へ、事前封印された registry / manifest に束縛した raw 記録を
書く生成者」までである。閉じていない点は非保証へ逐語で列挙する。

## 3. test の確定要求

- **通る正例を 2 本置く。** (a) 全件欠測の 201 block、(b) **certified を通る 201 block**。
  (b) は throughput の十進 token 保存、treatment・protocol・pair 束縛の全分岐を実際に通る。
  (a) だけでは authority 分岐を一度も通らずに E2E 成功できてしまう (S-nit2)。
- **十進の負例には binary float で表せない値を使う。** `491796.5` は表せるので発火しない (L11)。
- **時点を狙う負例は発火位置を固定する。** 呼出番号または同期点を test 内で明示する (L12)。
- **変異と test の対応表を作る。** 各変異点に対し、落ちる node id をちょうど 1 つ書く。
  複数落ちる / どれも落ちない箇所は登録前に再照準する (L10、DW-M01)。
- 検査は性質だけでなく**実体を名指し**する。両層 stub で機構を通らず緑になる形を作らない。

## 4. ユーザーへ返す裁定パッケージ (scope 外・実装しない)

1. **precursor と campaign の束縛を誰が閉じるか。** `initial_proposal_sha256` を実際に計算・記録する
   経路が repo に無い。閉じるには loop 側か issuer 側の変更が要る (T-2050 / T-2051 の領域)。
   閉じないまま B-4 を実走すると、raw 記録は「事前固定した 201 試行」ではなく
   「registry のラベルを付けた 201 の選択可能な証拠」に留まる。
2. **非有限十進の `reference_tps` を許すか。** 凍結された消費側は raw JSON 経由で exact に受け取れない。
   registry 側を整数・有限十進に制限するか、消費側 (凍結 closure) を変えるかの択一。
3. **凍結 closure 外の producer をどの層が認証するか。** 5-file pin を動かさない限り、
   source bytes の hash が一致しても「どの producer 意味論で作られたか」を verdict が識別できない。

## 5. 変異事前登録 (DW-M01)

実装後に harness で走らせる。各変異は単一理由性を実装時にコードで確認し、
確認できなければ登録せず実効 gate へ再照準する。

| ID | 変異位置 | 期待 kill 理由 (受理集合または fail-closed 挙動の変化) |
|---|---|---|
| M01 | `precursor_hash` を registry lookup でなく caller/receipt 宣言値から取る | 事前封印 registry と異なる precursor が通る |
| M02 | 出力 path の事前確定 (`planned_result_artifacts`) 照合を外す | 任意 root へ raw 集合を作れる |
| M03 | `assignment_observation` を publish 順から作る | 実行順と逆の遵守判定が通る |
| M04 | 最終組立ての `pair_id` 一致検査を外す | 別 pair の on/off を 1 block として通せる |
| M05 | lock snapshot を分類用と検証用に 2 度読む | D1240 の二重読取 bypass が復活する |
| M06 | WAL stage の写像を素通しにする (lowercase をそのまま出す) | adapter の closed enum を回避する vocabulary が通る |
| M07 | 十進 token を float 経由で再出力する | 非有限十進の入力 lexeme が変化して通る |
| M08 | `(campaign_id, iteration, arm)` の一意性検査を外す | 同一試行を複数 block へ複製できる |
| M09 | 終端 record の実在検査を「読み取り中不変」に置き換える | 未終端 iteration が executed として通る |
| M14 | 終端 record 不在時の campaign lock 検査を外し、常に publish する | 実行中の試行が欠測として封印される |
| M15 | 終端 record 不在時の campaign lock 検査を外し、常に publish を見送る | 終端記録を残さず終わった試行が報告から消える (file-drawer) |
| M16 | 入力 schema を開き、caller 宣言の `treatment_fired` 等を受理する | D162 決定 2 に反し、producer が適格性を宣言できる |
| M17 | 証拠を 2 度開いて読み直す (hash と parse を別 buffer にする) | ABA 差し替えが通る (D162 決定 5) |
| M18 | symlink 拒否を外す | 証拠 path の差し替えが通る |
| M10 | off の `treatment_fired` を一律 false にする | 全 block が treatment shortage になる |
| M11 | 証拠が決めない disposition を既定値 (crash 等) で埋める | 根拠のない disposition が報告に載る |
| M12 | 非有限十進の `reference_tps` を丸めて通す | 消費側の exact 照合を欺く値が通る |
| M13 (正例) | 過剰拒否の検出。整数 `reference_tps` と全証拠が揃った正当な publication | producer 固有の追加条件で拒否されないこと。**SURVIVED が期待値ではなく、この正例が緑であり続けること**を確認する |

M13 は DW-M01 の「受理集合を縮小する wave では承認外の過剰拒否を検出する正例も登録する」に対応する。
S9 が示したとおり、この producer は正当な母集合を新たに拒否する risk を持つ。

## 6. 段 5 の分割

Codex `role=author` 1 本。編集面は新規 2 file のみで所有が割れない。
実装子には次を個別に明記する (契約文書に書いてあるだけでは破られる)。

- docs を編集しない。commit しない。
- 既存 file を 1 byte も編集しない。特に `_SOURCE_CLOSURE_PATHS` と closure 5 file。
- 新しい署名・nonce・一回性台帳・認証 seal を作らない。
- `authoritative` / file-drawer closed / verdict-ready と名乗らない。
- 閉じられない点は非保証として逐語で列挙する。
- 判断 field を caller から受け取らない (§2.85 (a))。証拠は単一 fd / 単一 buffer で読む (§2.85 (b))。
- 新規 test file の末尾に自走 harness
  `if __name__ == "__main__": raise SystemExit(pytest.main([__file__, "-q"]))` を置く。
