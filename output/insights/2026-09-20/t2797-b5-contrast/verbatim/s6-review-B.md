# 検査範囲と結論

**現時点の受入は NO-GO。consumer が不整合な台帳を正常として受理する2点を must-fix とする。** job body の旧経路破壊、53枠の算術だけの検査、禁止された大規模実装の混入という疑いは反証できた。

対象 HEAD は `e574815582e0516fa9e3a0ed8d351525c162fdc2`。以下の動作評価は **未実走・静的読解**であり、親の 85／54／36／184 件の緑を独立再現したとは扱わない。レビュー中に親の README 編集と fix1 の registry・固定表更新が現れたため、それらは HEAD 外の変更として区別した。

略記：

- **G**：`orchestrator/campaign/b5_generator_contrast.py`
- **R**：`orchestrator/campaign/b5_generator_contrast_report.py`
- **L**：`orchestrator/campaign/p3_s4_loop.py`
- **SH**：`tools/pegasus/p3_s4_loop_pegasus.sh`
- **J**：`tools/pegasus/b5_contrast_launch.py`
- **TJ**：`orchestrator/tests/test_p3_s4_loop_job_contract.py`

# B01 — B=10 と評価1件の台帳が正常な登録比較に入る

**対象：R:236、`test_b5_generator_contrast_report.py:28`。判定：real。格：must-fix。**
**成果物影響：評価履歴を欠いた系列が正常な受理集合に入り、登録比較で優越を返せる。**

`_validate` が検査する A/B は範囲だけで、`evaluation-result` の件数・連番と B の一致を検査しない。

これは仮想的な改変例ではない。既存の `ledger()` fixture は、探索評価を **1件だけ**作り、各イベントと終端を `a=10, b=10` にする。`test_registered_twelve_pairs_three_blocks` はその台帳群について `invalid == []` と優越判定を期待する。pilot 正例も **B=10、logical_sessions=7** を固定している。

統計関数の縮約 fixture と、完全な producer 台帳を受理する consumer の正例が混ざっている。

**代案：** 完了系列では B と論理評価記録・連番を照合する。不完了系列は欠測として保持する。JSON consumer の正例は producer が生成できる10評価の形へ直し、1評価なのに B=10 の例を負例にする。新しい発効 gate は不要。

# B02 — score の fitness と bench 証拠の不一致を検出しない

**対象：R:238、R:360、`test_b5_generator_contrast_report.py:303`。判定：real。格：must-fix。**
**成果物影響：bench 証拠と異なる fitness から score・CV・比較結果を算出できる。**

`_validate` は `bench_payload` 内の品質整合を調べるが、イベントの `fitness_tps` と `bench_payload["median_tps"]` を照合しない。`_project` はイベント側の fitness を採る。

`test_fresh_median_not_search_max_and_slow_endpoint_not_replaced` は、この欠落を正例にしている。score の fitness を `[10,40,50,60,100]` に変更しながら、fixture の bench payload は元の値のまま据え置き、`invalid == []` を期待する。

G の `classify_slot` はこの一致を検査している。consumer の正例が producer の生成条件を満たしていない。

**代案：** 正例では fitness・bench median・rep 値を整合させる。不一致だけを残した負例を追加し、既存 `_validate` の数値照合に含める。

# B03 — LLM 待機費用が成功寄りに欠落する

**対象：G:626、G:701、R:315。判定：real。格：should。**
**成果物影響：拒否・timeout・継承不一致に費やした待機が費用分布から消える。**

`proposal_wait_wall_s` を返すのは `_handshake` の proposal 受理経路だけ。拒否・timeout・allocation 終了には経過時間がない。受理後に schema 不合格となる経路でも provenance を保存しない。

consumer はさらに `evaluation-result` の provenance だけから待機時間を集める。そのため、正常評価前の待機だけが `llm_turn_seconds` に入りやすい。**job の待機時間と親の LLM 実手番時間も同一ではない。**

また `_header` の job 情報は PBS_JOBID／host だけであり、R が読む `job.Elapse` は producer から供給されない。queue 待ちも別途採取が必要。

**代案：** 全 handshake 終了経路で実経過時間を既存イベントへ残す。consumer は opportunity 単位で重複なく集計する。親の手番、queue 待ち、job Elapse は外部証拠との対応を明記し、immutable header の後編集で埋めない。

# B04 — logical_sessions が A-only の試行も数える

**対象：R:313、R:329。判定：real。格：should。**
**成果物影響：認可上の53／60論理 session と、報告上の session 数が一致しない。**

`physical` は slot key のある全イベントを集め、`logical_sessions` はその logical slot 数を返す。投入前の `rejected-preprocess` や `pre-start-failure` も含む。

たとえば random が stock 成立後に30回すべて投入前拒否となれば、探索 B=0 でも報告上は31論理 session となる。実際の追加測定を示す値ではない。

**代案：** 現在の値は「試行した論理 slot 数」と呼ぶ。予算に対応する session 数は、同 slot の全 attempt を見て投入済みを一度だけ数える。物理 attempt・A-only 拒否は別の既存集計として残す。

# B05 — dry-run の契約は「全 subprocess 禁止」では成立していない

**対象：J:70、J:250、`test_b5_contrast_launch.py:198`。判定：real。格：should。**
**成果物影響：CLI 全体の副作用保証を、検査した範囲より広く報告してしまう。**

`main(--dry-run)` は `validate_submit_tree` を通り、Git subprocess を呼ぶ。subprocess 禁止の test は、構築済み `SubmitTree` を渡す `launch()` の検査。main の test は tree 検証自体を stub にする。

一方、段4 §2.4 の逐語は **qsub と mkdir をしない**であり、これは現物と整合する。A3 の末尾も Git subprocess の使用を明記している。

**代案：** 契約を「Git による読取り検証は行う。qsub・mkdir は行わない」に統一する。Git 読取りを消すための独自 Git parser は増やさない。

# B06 — launcher と job の検査対象 PIN が異なり得る

**対象：J:99、SH:304。判定：real。格：should。**
**成果物影響：launcher の事前検証と、投入先 job の PIN 判定が食い違う。**

J は **launcher をロードした checkout** の `p3_s4_loop.PIN` を使う。SH は **投入対象 checkout** の module を読み直す。別 commit の launcher から投入できる CLI なので、両者の一致はコード上保証されない。

ほかの指定面はおおむね整合する：

- full lowercase HEAD、tracked clean／submodule 除外、CCBench clean、AI worktree container 拒否。
- launcher は追加で superproject／CCBench の checkout root を検査するため、完全に同じ受理集合ではない。
- 通常の `.git` 配置では common repository の導出も一致する。

**代案：** 投入対象 checkout の launcher を使う運用を使用例で固定するか、PIN を投入対象から読む。別 checkout の暗黙一致に依存しない。

# B07 — module CLI は LLM の部分 K2 指定を受理する

**対象：G:843、G:463、SH:107。判定：real。格：should。**
**成果物影響：job body では拒否する宣言欠落を、module CLI では既定値で実行できる。**

SH は LLM に K2 4 env を非空必須とする。G の CLI は manifest だけを必須にし、classification／de-novo は `None` のまま許す。`slot_argv` も欠落値を転送しない。

正規 launcher 経由の試走には値がそろうため、この経路を直ちに壊すものではない。しかし、段4の「LLM の固定 K2 束」と module CLI の受理集合には差がある。

**代案：** B-5 CLI でも3入力を一括必須にするか、module 直接起動では既定値を許すという契約を親が明示する。

# B08 — job body の旧経路破壊・fallthrough の疑いは反証

**対象：SH:54、SH:189、SH:652、SH:669、TJ:1972。判定：refuted。格：—。**
**成果物影響：検査した差分では、旧3経路の argv・rc 本文は維持されている。**

旧 blob `350cad87e` と新 blob `49327c966` の Git 差分では、`candidate_rc=0` 以降に変更がない。

- mode は未設定だけ off。空値・不正値・部分設定・旧 mode 併用・K2 条件は repository 解決より前。
- proposal 必須条件の例外は `series && arm=llm` に限定。
- ledger の `realpath -m` による repository 内拒否は repository 解決後、EXIT trap より前。
- B-5 起動は prebuild 後・旧分岐前の1箇所。`|| b5_rc=$?; exit "$b5_rc"` は trap の rc 捕捉と整合する。
- TJ は B5 pins、stage order、呼出し数に加え、実 shell で4 arm×rc 0／7、trap 転記、fallthrough 変異を検査する。
- 旧 K2 fragment 変異と、fixture を prebuild 前へ移す変異も保持されている。

ただし **scheduler の強制 kill 時まで compute-result 作成を保証するものではない**。

**代案：** 別 job body は作らず、この構造を維持する。

# B09 — launcher の4 job・53枠・qsub 形は実装に結び付いている

**対象：J:122、J:144、J:200、J:210。判定：refuted。格：—。**
**成果物影響：定数53の比較だけで、自由な schedule を許しているわけではない。**

`validate_pilot_cap` は4 job、arm 順、write-heavy、series=1、block=1、mode 対応、各予算定数を検査する。producer の test も実際の runner 呼出し列を stock 1＋search 10＋score 5、block-stock 5 と固定する。

qsub は共通10 env＋LLM 4 env を `-v` で列挙し、walltime と `-o/-e` を明示する。`-q/-A/-b` を script に任せ、対象 checkout を cwd にする形は既存 K2 投入と同型。空白・`,` を含む path も拒否する。

`--submit` は qsub 前に evidence directory を作るだけで、allocation-qstat／reservation／receipt を置かない。部分投入失敗後に自動再投入もしない。

**代案：** 現行の固定 schedule を維持する。53は正常な最大論理測定数であり、物理 retry／品質 round／完走保証とは区別する。

# B10 — CLI 配線・WAL fixture・変異 test の有効範囲

**対象：G:470、G:499、G:520、`test_b5_generator_contrast.py:128`、TJ:1280。判定：refuted／根拠不足（下記）。格：—。**
**成果物影響：単位契約の検出力はあるが、実機統合まで緑とは言えない。**

**refuted：**

- 較正・verify の配線欠落。最終 slot argv に固定され、L の B-5 限定 kwargs で rounds=3 になる。
- 新 coder entrypoint の必要性。既存 L CLI を subprocess で使っている。
- fake runner が WAL classifier を迂回する疑い。sidecar／lock／JSONL を書き、実 `classify_slot`／WAL reader を通す。
- M13／M14／M16／M17／M18 が別単位の偶然の赤だけに依存する疑い。対応する shell／統計／launcher test を変異側に適用している。

`default_runner` は `sys.executable -B -m ...`、cwd=repo_root、継承 env＋`PYTHONDONTWRITEBYTECODE=1`。**timeout 引数はない。** TimeoutExpired test の1800秒は注入値であり、production timeout の証拠ではない。

`_header` は Git metadata をファイルから読み、subprocess を増やさない。G 自身に LLM API 等の network 呼出しはない。

WAL fixture の成功系列は、実 pipeline の build／verify／bench／commit 順、attempt ID、workload tag と整合する。ただし admission receipt 等を省いた縮約 fixture であり、実 build の代替証拠ではない。

**根拠不足：**

- TJ の Python stub は reservation を10800秒として返す。8時間 qstat の実解析・束縛は未証明。
- fake runner による履歴継続は G のループを検査するが、実 subprocess と fresh layout を通した停止不適用の統合実走ではない。
- 新3 test の `__main__` は `pytest.main` へ到達する形。launcher test の import には repo root を通す実行環境が必要で、harness の存在だけでは独立起動環境まで保証しない。

**代案：** 単位の緑を保持し、最初の実台帳を consumer まで通して確認する。未実走の範囲を実走済みに繰り上げない。

# B11 — pin 閉包と fix1 の状態

**対象：各 inventory test、`admission_registry.json:34`。判定：refuted／根拠不足（下表）。格：—。**
**成果物影響：不要な pin 更新を避けられるが、統合後の受入緑は別途必要。**

| 面 | 現物からの判断 |
|---|---|
| official perf inventory | 新3 module は述語に該当しない。`current_perf` 等の文字列 key は Name／Attribute 判定対象外で、discovery call もない。 |
| exploration namespace | L の layout 呼出し11、run_campaign 2を現物で確認。runtime 1は未実走。 |
| wiring import 閉包49 | L に新 module への逆 import はない。差分による閉包増分はないが、49の再列挙は未実施。 |
| campaign caller inventory | 新 module に直接 run_campaign 呼出しはない。L は2を維持。 |
| campaign CLI shape | G／R は正規 `DIRECT_BOOTSTRAP` と相対 sibling import を使用。 |
| authority issuer | 新 module に issuer import／呼出しなし。既存 L の登録 site を利用。 |
| plain runner | 新3 file に実行 signal を持つ main harness あり。 |
| SH third-party pin | 対象の逐語・出現数を変える差分なし。 |
| hooks | module 実行の一般的分類 test は、campaign 全 module の網羅的 admission inventory ではない。 |

author が挙げた主要な既存 nodeid、CLI bootstrap／relative import の2件も実在する。A3 の0件選択は本人が rc=5 と報告しており、通過扱いにはしていない。

**registry は途中で状態が変わった。** 当初は launcher 未登録だったが、最終再読時には `local-ok` と固定表3箇所が追加済みだった。したがって「未登録のまま」は最終 working tree について refuted。HEAD にはまだ含まれない。

guard のコード上は、登録前の launcher は未登録 Pegasus 実行体として拒否対象、登録後はこの拒否条件を通過する。ただし **登録後の exact dry-run と inventory test は未実走**。

**代案：** fix1 を統合した状態で該当受入を確認する。registry 同期を資源実測や実起動経路全体の保証とは呼ばない。

# B12 — 意味を保って削れる箇所は小さい

**対象：G:342、G:369、R:117、J:214。判定：real。格：nit。**
**成果物影響：重複処理・未使用引数を減らせるが、試走の成立条件は変わらない。**

削除・縮約できるもの：

- `classify_slot` の同一 records に対する2回目の `wal_timing` 計算。
- R の `decide_comparison(..., baseline=...)` の未使用引数と、その新規内部 caller／test の対応引数。
- `launch()` が env を作った直後に `qsub_argv()` 内で再構築する重複。公開 helper の意味を保ち、組立だけ共有できる。

指定された hash8 事前網羅、純 verifier adapter、新 coder entrypoint、alias 群、汎用復活／再配置、108系列 launcher、発効 gate は見当たらない。

**解析 consumer、WAL 計時、限定 retry、継承検査、複数 workload の生成関数を削る根拠はない。** 行数だけを理由に864／511／262行を大幅削減する案は refuted。

**代案：** 上記の局所的縮約だけを任意で行う。

# B13 — README の修正文と例の追加方針

**対象：README旧:358、旧:387、TJ:1825。判定：real。格：should。**
**成果物影響：旧 K2 の説明を B-5 に適用すると、正しい env 束を組めない。**

親の並行差分では「較正・verify は未配線」の文は既に修正されていた。残る案は次のとおり。

1. 「K2 は proposal-path 必須」「classification／de-novo は任意」を **旧 proposal／pair 経路の規則**と限定し、B-5 LLM の例外・4 env 必須へ接続する。
2. B-5 env 表を mode／arm／workload／series／block／ledger に分け、未設定と空値、先頭ゼロ禁止、旧 mode との排他を明記する。
3. stock slot には coder role／allow-coder-derived-build／machine-generated-proposal を渡さないことを明記する。並行差分の arm 別括弧だけでは LLM stock にも付くように読める。
4. launcher 使用例は投入対象 checkout から起動する形にする。
5. qsub 例は共通10＋LLM4 env、8h／3h、`-o/-e` を示す。dry-run の最終 argv を利用できる。
6. `SESSION_BUDGET_S`、失敗待機の記録限界、純 verifier 秒ではないことを追記する。

TJ は SH を含む **bash fence がちょうど1個**と固定する。親が追加した launcher の `text` fence はこの数を増やさない。B-5 qsub の bash fence を追加するなら、旧 K2 正例を残したうえで、test を mode 別の具体的契約へ更新する。単に件数条件を緩めない。

# B14 — 8h／3h／1800秒の根拠と限界

**対象：brief「β」、G:49、G:513、J:203。判定：根拠不足。格：—。**
**成果物影響：外挿値を実測上限として扱うと、試走完走・本走費用の根拠を過大評価する。**

- **53**＝3 arm×〔stock 1＋探索10＋score 5〕＋block stock 5。認可形に対応する。
- **8h／3h**は module docstring と親の並行 README で暫定管理値と明示されている。
- **1800秒**は12〜14分外挿のおよそ2.1〜2.5倍だが、この倍率を選ぶ独立した実測根拠は指定資料にない。
- 1800秒は **新規 session／待機の開始判定**であり、session timeout ではない。LLM は待機中も残時間を確認するが、個々の session の完了までは保証しない。

**代案：** 暫定の開始余裕として記録し、正常・失敗・打切りを分けた試走の実測から本走値を裁定する。

## 総括

**must-fix**

- **B01** — Bと評価履歴の不一致を正常受理する。`b5_generator_contrast_report.py:236`
- **B02** — fitnessとbench証拠の不一致を正常受理する。`b5_generator_contrast_report.py:238`

**should**

- **B03** — 失敗待機時間を保存・集計し、親手番／job Elapse／queue待ちと区別する。
- **B04** — 論理slot試行数と認可上の論理session数を分ける。
- **B05** — dry-runはGit読取りあり、qsub／mkdirなしと契約を統一する。
- **B06** — launcherと投入対象のPIN参照元をそろえる。
- **B07** — module CLIの部分K2指定の扱いを統一する。
- **B13** — READMEの旧K2規則とB-5例外、stock argv、例の検査を整合させる。

**削除候補**

- 重複する `wal_timing` 計算。
- consumer の未使用 `baseline` 引数。
- launcher の env 再構築の重複。

**判定：NO-GO（αの受入）。** must-fix 解消と fix1 統合後の確認が必要。実機 qsub／build／bench／handshake の成立は未判定。

**親裁定が要る未確定事項**

- 1800秒を暫定開始余裕として採る根拠の記録。
- B-5 module直接起動でK2宣言の省略を許すか。
- 親手番・queue待ち・job Elapseをどの外部証拠から報告へ結ぶか。

自動実行前審査 `guard_bash` は、読取り専用のAST・bytes照合コマンドを `admission_registry.json` が「未登録 Pegasus 実行体」との理由で拒否した。この機械照合は未実施であり、pytest緑や登録後の実効確認として報告していない。