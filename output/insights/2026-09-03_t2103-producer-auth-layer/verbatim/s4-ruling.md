# [T-2103] 段 4 裁定 — 認証層の比較実験

base commit: `4ec3eba04354f9ba86117a2dd488c72d007045e6`。
段 4 直前に local main を再走査したところ `b20543ba40fde21e478cb3864154e2ef8ff8b873` へ進んでいた。
差分は `p3_b4_*` と重ならない (`.claude/agents/`、`orchestrator/codex_roles/`、docs)。
新規裁定 31 件のうち D1530・D1531 が本 wave を拘束する (§0 参照)。

## 0. wave 開始後に landed した裁定の取り込み

- **D1530** (段 8c の権威束縛は本番の呼び手を繋ぐ変更と同じ単位で行う): 本番の呼び手が存在しない
  防壁を単独で建てない、という先例。frozen consumer 候補の closure receipt は
  **production の呼び手が存在しない** (親実測 M3)。したがって同候補の変更閉包には
  「呼び手を新設する変更」が含まれる。これは比較の障害ではなく、**計上すべき費用**である。
- **D1531** (凍結束縛は hash 記録でなく内容の再導出で行う): 変異事前登録の凍結を、
  harness が自分で渡した hash との照合で済ませてはならない。**承認済み prereg file から
  内容を再導出して完全一致で比較する。**

## 1. 所見の裁定

### real・採用 (plan v2 に反映する)

| # | 出所 | 所見 | 成果物影響 |
|---|---|---|---|
| A1 | sol | D 系 (全候補 SURVIVED) を「全件 KILLED」採否規則の分母に入れており、「認証層なし」が事前確定する | 採否規則が無内容になり decision の結論が測定前に決まる |
| A2 | sol | raw guard を producer file 自身へ置くと producer bytes が変わり固定 SHA-256 と恒真に不一致 | 全入力で guard が偽、POS-1 も落ち、比較値が全て無効 |
| A3 | sol | 「producer member が存在する」は生成経路の候補集合に含意され恒真 | frozen の KILLED 数が水増しされる |
| A4 | sol / D1530 | frozen を直接 evaluator probe で測ると実運用経路を証明しない | frozen の 6/12 が本番経路の値でなくなる |
| A5 | sol | 同一 process では issuance 後の source 変更が import 済みコードに反映されない | C1 の SURVIVED 期待が観測できない |
| A6 | sol / luna | 変更閉包の数え方が experiment module を除外し、最小性の合成規則も未定 | 最小候補の選択が結果後に変えられる |
| A7 | sol / luna | R 系の raw KILLED は既存 rederivation に帰属し、新設 guard の増分能力でない | 候補の拒否能力を既存 gate の能力と取り違える |
| A8 | sol | 判定境界が未固定で、R 系は実経路だと他層に先に拒否され帰属が一意にならない | 変異の単一理由性 (DW-M01) が不成立 |
| A9 | sol / luna | 親 brief の「5-file pin = 固定期待 digest」は誤り。receipt は現在の bytes を hash 化するだけ | 親 brief の前提を訂正しないと候補の性質を誤って記述する |
| A10 | sol / luna | 親 brief の P2「raw assembly の拒否能力ゼロ」は過剰一般化 | baseline 列を持たないと誤った結論になる |
| A11 | luna | frozen 候補は現行 5-file consumer でなく一時的 6-member counterfactual | report の参照対象が誤る |
| A12 | luna | `finally` + `git checkout --` は SIGKILL・異常終了で復元しない | 親 brief の不変条件 1 が未充足のまま走る |
| A13 | luna | 候補が有効な状態での既存 29 node 非後退検査がない | 過剰拒否 (規律 2 と逆向きの破れ) を検出できない |
| A14 | luna | issuer 候補が commitment の key set を増やすと既存 v1 publication が loader から拒否される | issuer 候補の受理集合が縮む。計上しないと費用を過少評価 |
| A15 | luna | producer 認証不一致を `binding_domain_error` へ写すのは凍結文面と異なる拒否意味の追加 | 事前登録 §5.1.1 との束縛を壊す |
| A16 | luna | `observed_producer_sha256` を公開 dataclass へ足す任意案は不要な恒久 wire 拡張 | scope 外の恒久 API 拡張 |
| A17 | luna | 書くべき非保証 6 件 | 測定値の射程を超えた一般化を防ぐ |

### refuted

| # | 所見 | 反証 |
|---|---|---|
| R1 | sol・luna とも「brief の 18/18 KILLED は M13 が正例である一次資料と矛盾する」 | 一次資料 `mutation-registered-spec.json` の M13 は `category: "positive"` かつ `expected_status: "KILLED"` である。整数 `reference_tps` を過剰拒否させる変異を正例 test が殺す形であり、report の `summary` (`KILLED: 18`, `SURVIVED: 0`, `MISMATCH: 0`, `registered: 18`) と矛盾しない。両レーンは射影された散文表だけを見て spec 本体を見ていない。**ただし表現は精密化する**: 「17 負例 + 1 正例 (過剰拒否検出) の計 18 件がすべて期待どおり KILLED」と書く |

### real だが scope 外 — 裁定パッケージへ回す

| # | 所見 | 扱い |
|---|---|---|
| X1 | frozen 候補を本採用するには `p3_b4_material_report.py:224` の production callsite から receipt を渡す変更が必須 | 本 wave では実装しない。変更閉包として計上し、D1530 の先例 (本番の呼び手を繋ぐ変更と同じ単位で行う) を添えて裁定パッケージへ |
| X2 | D 系 (post-assembly 改変) を拒否するには raw judgment と source object judgment を照合する下流 payload-binding 層が要る | 候補外。共通穴として報告し、別 task 候補として返す |
| X3 | 固定 trust anchor の本採用時の所有者・更新条件・正規 producer 更新との同時変更規則 | 未定。本採用を裁定するときの前提として返す |

## 2. plan v2 — 確定する設計

### 2.1 測定は主 worktree を一切変異させない (A12 / 親 brief 不変条件 1 の根治)

`git checkout --` による復元に依存しない。各 case は **base commit の内容を repo 外の scratch へ
展開した使い捨て tree** で実行する。主 worktree の bytes は測定中も一度も変わらない。
復元失敗という状態が構造的に存在しなくなり、5-file pin の恒久変更も起こり得ない。

- scratch root は repo 外 (`/work/1/SFC/tanab/t2103-scratch/`)。全 registered worktree の外。
- 各 case 終了時に scratch tree を破棄する。破棄失敗は `ABORTED` として記録し、
  その case の KILLED / SURVIVED を比較表へ昇格させない。
- 主 worktree の `git status --porcelain` が測定の前後で不変であることを harness が確認する。

### 2.2 候補 guard は producer file の外に置く (A2)

3 候補の guard 実装は新規 module `orchestrator/campaign/p3_b4_producer_auth_experiment.py` に置く。
各候補の一時差分は「その層の実 callsite から guard を 1 回呼ぶ」だけとする。

**trust anchor の定義 (循環回避):** anchor は「候補 prototype を適用した後・rogue 変異を適用する前の
producer file bytes の SHA-256」とする。候補ごとに 1 つ、**rogue 変異を 1 件も走らせる前に**測って
prereg へ凍結する。結果を見てから更新しない。raw assembly 候補で guard 呼び出し行が producer file に
入る場合も、この定義なら POS-1 が恒真に落ちない。

### 2.3 判定境界を固定し、baseline 列を必須にする (A7 / A8)

各 (mutation, candidate) について **2 回**測る。

- **baseline**: 候補 prototype なし。既存 gate だけ。
- **prototype**: 候補 guard あり。

比較値は **増分** (`prototype で KILLED かつ baseline で SURVIVED` の件数) とする。
既存 gate が拒否した case は `BASELINE_REJECTED` として別カテゴリに記録し、候補の拒否能力に数えない。
これで R 系の raw KILLED が既存 `source_rederivation` に帰属することが表に出る。

判定は **その候補層の guard が拒否したか**だけを見る。他層の拒否は KILLED に数えない。

### 2.4 採否規則を測定前に固定する (A1 / A6)

- **分子 (識別力):** C1 系 3 件 + R 系 3 件 = 6 件。層を分離しうる負例だけ。
- **対照 (分母外):** C0 系 3 件 (source-hash 比較が動くことの対照)、D 系 3 件 (3 候補共通の残存穴)、
  POS-1 (過剰拒否の検出)。**採否規則には使わない。**
- **採否:** 6 件の増分 KILLED 数が最大の候補を第 1 候補とする。同数なら変更閉包が小さい方。
  合成規則は結果前に固定する — 第 1 キー **本採用時の production file 数**、第 2 キー **pin site 数**、
  第 3 キー **test 波及 file 数**。3 キーすべて同点なら「最小と断定せず両論併記」とする。
- 6 件すべてを増分 KILLED できる候補が無いなら、**そう書いて閉じる**。
  「どの候補も単独では完全でない」は正当な結論であり、無理に勝者を作らない。

### 2.5 各候補の実 callsite (A4 / A15)

| 候補 | guard を呼ぶ実 callsite | 拒否の表し方 |
|---|---|---|
| issuer | `p3_b4_prerun_issuer.py` の `issue_b4_prerun_publication` (`:707`) 冒頭 | issuer の既存拒否経路。schema version は bump しない (A14) |
| raw assembly | `p3_b4_raw_record_producer.py` の `assemble_b4_raw_analysis` (`:1894`) 入口 | `B4RawRecordRejection`。既存 issue code を流用せず experiment 専用 code |
| frozen consumer | **実 production 経路**を通す。`p3_b4_material_report.py` の入力構築 (`:196`) → `evaluate_b4_artifacts` (`:224`)。receipt を渡す配線も一時差分に含める | **凍結 enum を変えない。** 認証不一致は experiment harness の独立した `producer_auth_rejection` として `evaluate_b4_artifacts` 呼出し**前**に記録する (A15) |

frozen 候補は closure tuple 2 箇所 (`_SOURCE_CLOSURE_PATHS` / `_CLOSURE_PATHS`) を同時に 6 member へ広げる。
report と decision では候補名を **「一時的 6-member expanded-closure prototype」** と書き、
「現行 frozen consumer の性質」と書かない (A11)。

### 2.6 frozen guard の述語から恒真部分を外す (A3)

述語は「member が存在する」ではなく **「producer member の sha256 が prereg に凍結した固定値と一致する」**
だけとする。存在は候補集合に含意されるので条件に書かない。

### 2.7 C1 系は 2 process 構成にする (A5)

issuance を行う process と assembly を行う process を分け、その間に scratch tree の producer bytes を
差し替える。同一 process 内の reload に頼らない。この 2 process 構成を prereg に書く。

### 2.8 非後退検査 (A13 / A14)

各候補が**有効な状態で**、既存 producer test の 29 node を走らせて緑を要求する。
期待値は 1 つも変えない。赤なら候補の過剰拒否として比較表へ記録し、隠さない。
issuer 候補については、既存 v1 publication が loader から拒否されないことを個別に確認する。

### 2.9 削除する案 (A16)

`B4RawAnalysisAssembly` への `observed_producer_sha256` 追加は plan から削除する。

### 2.10 prereg の凍結方法 (D1531)

harness は自分が渡した hash と照合する形を採らない。**承認済み `mutation-prereg.md` から
変異内容 (exact old bytes / new bytes / 適用位置 / 期待値) を再導出し、完全一致で比較する。**

### 2.11 変異の exact 固定 (sol の帰属所見)

P / T / C は意味ではなく **exact old bytes と new bytes** で登録する。対象 arm と適用順も固定する。
各置換の対象 file 内出現数が 1 であることを、走行前に harness が機械確認する (`bad=0`)。

### 2.12 書くべき非保証 (A17)

report に次を書く。

1. KILLED / SURVIVED は C0 / C1 / R / D の 4 投入位置と P / T / C の 3 判断値、POS-1 にだけ適用され、
   他の判断値・任意のコード変異・coordinated rewrite・path race へ一般化できない。
2. `(path, SHA-256)` の一致は各層が検査した時点の repository bytes しか示さず、その bytes が
   対象 artifact を実際に生成したという因果的 provenance を証明しない。
3. frozen の測定値は一時的に拡張した 6-member closure と追加 gate の値であり、
   現行 5-file consumer の拒否能力や本採用可否を示さない。
4. R 系の raw KILL は既存 source rederivation gate によるもので、追加 guard の増分能力ではない。
5. D 系が全候補 SURVIVED であるため、どの候補も post-assembly 改変を含む end-to-end authenticity を
   保証しない。
6. issuer は issuance 後の producer 交代を観測できない。
7. 親 brief の「5-file pin」は固定期待 digest 照合ではない。receipt は現在の bytes を hash 化する。

## 3. test の確定要求

- 12 負例 + POS-1 の期待 matrix を持つ test。
- 各候補が有効な状態での producer 既存 29 node の非後退走。
- 主 worktree 不変を確認する meta 検査。
- prereg 内容の再導出一致を確認する検査 (D1531)。
- rogue producer は実体である。stub で代用しない。別 path から実際に attempt artifact と
  raw/source bytes を生成する。

## 4. 変異事前登録 (DW-M01) — 本 wave 自身のコードに対するもの

**これは実験の比較 matrix とは別物である。** 新規実装が壊れたときに test が殺すかを見る。

| ID | 変異位置 | 期待 kill 理由 |
|---|---|---|
| W01 | trust anchor の照合を `!=` から `==` へ反転する | 正規 producer が拒否され rogue が通る |
| W02 | baseline 走を省き prototype 結果だけを比較値にする | 既存 gate の拒否を候補の能力として数える (A7 の再発) |
| W03 | 判定境界を広げ、他層の拒否も KILLED に数える | 帰属が一意でなくなる (A8 の再発) |
| W04 | 主 worktree 不変の確認を外す | 測定が主 worktree を汚しても検出されない (A12 の再発) |
| W05 | frozen 述語を「member が存在する」に戻す | 恒真な保証が拒否能力として数えられる (A3 の再発) |
| W06 | D 系を採否規則の分母へ戻す | 結論が測定前に確定する (A1 の再発) |
| W07 | 置換 anchor の出現数 1 の機械確認を外す | 複数箇所置換で単一理由性が壊れる |
| W08 | prereg 内容の再導出を hash 照合へ置き換える | D1531 に反し、自分の値と自分の値を比べる |
| W09 (正例) | 正規 producer・正規経路・POS-1 | 追加条件で過剰拒否されないこと。この正例が緑であり続けることを確認する |

各変異は登録前に、対象 file 内で anchor が厳密に 1 回だけ出現し `old != new` であることを
親が機械確認する。落ちる node がちょうど 1 つに定まらない変異は登録せず再照準する。

## 5. 段 5 の分割

Codex `role=author` 1 本。編集面は新規 3 file (experiment module、rogue support、test) と
harness で所有が割れない。実装子には次を個別に明記する。

- **commit しない。** docs を編集しない。コードとテストだけを書く。
- 既存 file を恒久変更しない。既存テストの期待値を 1 つも変えない。
- 5-file pin の恒久拡張を成果物に含めない。
- 実体を名指しした負例を使う。両層 stub で機構を通らず緑になる形を作らない。
- 期待値へ揮発 payload (working tree hash 等) を焼き込まない。
- 実走できた node id と範囲を報告に併記する。実走不能なら「実装済み・未実走」と書く。
- 所有外 caller・共有 fixture・consumer test への波及可能性を静的列挙する。
