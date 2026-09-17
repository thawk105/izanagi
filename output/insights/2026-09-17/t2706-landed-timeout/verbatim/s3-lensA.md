## 所見

以下、`実装`＝`tools/check_branch_landed.py`、`test`＝`orchestrator/tests/test_check_branch_landed.py`。JSONL は読取時点の774レコード・完了7件を確認した。静的検査のみで、変更・pytest実走はしていない。

- **A1 — real｜実装:225,1485,1732,1918,1939／s1-brief.md:33,39｜影響: verdict・受理集合**
  上限変更で**同じ repo・commit に返る verdict は変わり得る。しかも改善方向だけではない**。構成例として、60秒予算で決定的証拠の取得まで50秒、`cherry` が15秒、終端ref確認が1秒かかる場合、cap=5なら観測timeoutを捕捉して約56秒で確定できる。cap=20なら残余10秒を使い切り、ref確認で `indeterminate` になる。証拠に対する論理条件は不変でも、時間制約込みの入力受理集合は不変でない。
  **推奨: 採用** — 不変性の対象を「決定的証拠の受理条件」に限定する。D2104-item24.md:9も時間内に返せるverdict集合の変化を明記している。

- **A2 — real｜実装:1310,1485,1722,1732,1773,1788,1922,1939｜影響: verdict**
  観測層の分離は**値の依存関係についてだけ**成立し、予算は分離されていない。verbatimは各proof unit内で走り、後続unit・history scanの予算を消費する。ledger corpus/probeと`cherry`はhistory scanの**後**なので、そのscanを遡って妨げないが終端ref確認を妨げる。なお `_ledger_probe` 自身のdeadline例外は全体予算切れなので、その後のGitによるref確認も失敗する。
  **推奨: 採用** — 「観測はverdictに触らない」を「観測結果は判定根拠にしないが、実行時間は確定可能性に影響する」へ訂正する。

- **A3 — refuted｜実装:811,1341,1389,1734,1753／timing-lifted-2.json.jsonl:312,319｜影響: verdict・受理集合**
  「19.476秒のany-path探索が完走して初めて `not-landed` が出るから、上限そのものを負証拠にしている」という攻撃は成立しない。正常完了した探索の不一致、pure-add・同path候補ゼロ、完全history scan、終端ref一致が根拠である。D922項4の語では **closed-worldの負証拠による判定**。上限はその証拠の取得可否を左右する。`any_path` のJSON表示が `decisive=False`（実装:1470）でも、不一致は負例判定の必要条件なので、単なる任意観測とは扱えない。
  **推奨: 採用** — この区別を根拠説明に残す。timeoutを負証拠へ変換する欠陥としては不採用。

- **A4 — real｜実装:475,1310,1403,1425,1739,1773,1788,1922,1931,1987｜影響: verdict・test帰属**
  `AssessmentError`を捕捉する箇所は**10箇所**。briefの8箇所は誤りで、planの列挙は一致する。順に入力解決、verbatim、spool整合性、spool exact探索、history scan、ledger corpus、ledger probe、patch-id、task index、最上位。決定的探索のtimeoutを確定判定に変換する経路は見つからない。ただし「一度でもtimeoutなら最終indeterminate」は観測timeoutの捕捉・継続により成立しない。
  **推奨: 採用** — planの10箇所へ統一し、「決定的探索の不完全性」と「観測の不完全性」を区別する。

- **A5 — real｜実装:214,239,748,1144,1216,1243,1246,1535,1538,1541,1987｜影響: verdict・test帰属**
  timeoutの入口は `TimeoutExpired` だけではない。Git開始前、batch候補解析、ledger corpus/probe、task indexの残余予算検査も `assessment-timeout/truncated` を生成する。batchは全行検証完了前に肯定候補を公開しない。最上位は `UnicodeDecodeError` もindeterminate化する一方、Git起動時の `FileNotFoundError` / `PermissionError` 等の `OSError` は捕捉せず、JSONを返さず異常終了し得る。これは偽landed・偽not-landedの経路ではない。
  **推奨: 採用** — 例外監査へ追記する。OSError対応の実装追加は本waveから外す。

- **A6 — real｜s1-brief.md:13,14／timing-interim.txt:5,6,7／timing-lifted-2.json.jsonl:292,295,312｜影響: verdict・値選定**
  「重いのはpath logだけ」は反証済み。`cherry`は9.115秒、`--find-object`は19.476秒。途中集計のpath log中央値は3.692秒、今回読取の98本では3.867秒であり、「中央値に5秒が掛かる」を全体へ一般化できない。`1aa5…` はpath logが3.562秒で、5秒超なのは観測の`cherry`。また親の初期一覧にはreceipt取得の`show`、ledger corpusの`cat-file --batch`、Git以外のledger照合時間が十分反映されていない。
  **推奨: 採用** — 操作別・run別に整理し直す。「30/30失敗は決定的」という因果説明は撤回する。過去の30/30という観測自体は今回の資料だけでは否定しない。

- **A7 — real｜timing-interim.txt:27／s2-plan.md:162,169／timing-lifted-2.json.jsonl:292,295,299｜影響: test帰属・値選定**
  全commandの最大時間と壁時計から作る表は**実測完走率ではない**。上記`1aa5…`の記録時間を固定した反実仮想では、cap=5で`cherry`を打ち切っても後続ref確認まで進めるため、「全commandがcap未満」を完走条件にすると完走を過小計上する。返るverdictは依然として証拠不足のindeterminateになり得る。
  **推奨: 採用** — planの「trace再現見積り」という留保を採用し、途中表の見出しを訂正する。完走率と確定判定率を別に実測する。

- **A8 — real｜s2-plan.md:59,79,96,122,127／test:414,703,1006｜影響: test帰属・受理集合**
  提案3本が示すのは、定数の範囲・既定値との値一致、実timeoutの変換、通常proof logからの伝播である。**定数変更前後の入力受理集合不変は示さない**。負例は明示timeoutなので定数の実効動作を直接検査しない。signature比較は同値リテラルへの切離しを殺せず、極小の正数も範囲検査を通る。planはこの限界を正しく認めている。any-path・history scanの負証拠境界、観測timeoutと確定判定の共存は新規testの対象外。
  **推奨: 採用** — testの保証を限定して記載する。補強するなら負証拠経路のtimeoutと観測後の残余予算境界を優先し、「受理集合不変を証明」とは呼ばない。

- **A9 — refuted｜実装:63,217,229／s2-plan.md:76,94,95／test:1693｜影響: test帰属**
  env固定によって偽gitが選ばれなくなる、という懸念は成立しない。PATHは引き継がれ、`GIT_CONFIG_GLOBAL=/dev/null`は実行ファイル探索を妨げない。先頭の `-c VALUE` 群を解析し、元の全引数を保持して本物gitへ委譲するplanなら整合する。ただしselector誤実装によるproof log未到達はあり得るため、到達回数・実`TimeoutExpired`・phase検査が必要。
  **推奨: 採用** — planの方式を維持する。偽gitだけで再現できないenv変数を制御信号に使わない。

- **A10 — refuted｜s1-brief.md:25,29,41／s2-plan.md:7,10,11,181,182｜影響: scope**
  gate・運用台帳の判定ロジック・CLI・retry・timeout基盤・探索方式の変更は計画に含まれていない。全体予算変更もcarryのみ。一方「変更は定数1行＋test追加のみ」というbriefの字義は、根拠コメント・insight・worklog/decisions fragment追加と不一致。
  **推奨: 採用** — 「製品の動作変更は定数1行」と書き直す。文書追加を仕様拡張と扱う必要はない。

## 親 brief への反証

| 主張 | 判定 | 理由 |
|---|---|---|
| **P1** 最大完了時間×余裕2〜3 | **条件付き** | 候補生成則としては可能。初期の最大10.1秒は更新が必要。最大値だけでは共有予算への悪影響や完走率を決められない。 |
| **P2** 上限の役割は早期indeterminateだけ | **反証** | 証拠取得と観測の予算消費を変え、確定→indeterminateも起こり得る。ただし偽確定を新設する判定分岐は見つからない。 |
| **P3** 全体予算超過はcapだけで解消しない | **条件付き** | 必須の決定的探索だけで予算を超える場合は支持。持上げrunの総時間超過だけでは、打切り可能な観測を含むため断定できない。 |
| **P4** 変異matrix | **条件付き** | 同値リテラル切離しをsignatureで殺せるという期待は反証。極小値は提案testでは保証できないが、「単体test一般で検出不能」は言い過ぎ。planの限定が妥当。 |
| **P5** author1本・小差分 | **支持** | 動作変更を定数に限定する範囲では妥当。test・根拠文書の保証範囲を訂正する必要はある。 |
| **不変条件: 受理述語・確定経路** | **条件付き** | 決定的証拠への論理条件は維持できる。時間制約込みの入力受理集合・実際に通る経路・返るverdictは不変でない。 |
| **不変条件: min構造・CLI・schema** | **支持** | planに変更なし。ただしschema不変は `issues` / `phase_outcomes` の内容不変を意味しない。 |
| **不変条件: 定数1行＋testのみ** | **反証（字義）** | コメント・結果文書・fragmentも予定されている。「動作変更」の限定として修正可能。 |

## 総括

決定的探索のtimeoutを肯定・否定の証拠へ変換する経路は見つからない。
一方、上限変更で同一入力へのverdictは変わり、共有予算により確定率が悪化する経路もある。
「受理述語不変」は証拠の受理条件に限定すべきで、入力受理集合不変とは言えない。
planの捕捉数・変異・推計の訂正は採用できるが、観測による予算消費を説明へ追加する必要がある。
現時点の少数・途中計測から新定数を確定する根拠は不足している。