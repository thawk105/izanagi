## 総括

最小案は、**既知の旧文書だけを既存の固定 root で識別し、歴史閲覧と現行意味互換性の検証を分ける**ことです。新規文書には現行の自己整合検証を残します。generator/source 比較の一律撤去、T-080 adapter への全面委譲は採りません。

実読・読取照合で、brief の前提を次のように修正します。

- 旧 bytes の SHA256 は指定の `354f4b…11f516` と一致。
- 不一致 source は **6種類**：`axis_trigger_gating.py`、`s8a_trigger_sweep.py`、`genome.py`、`backoff_sweep.py`、`s6_sort_sweep.py`、`p3_s4_loop_sort.py`。generator を加えて7ファイルです。「source 7件と generator」は今回の実物と一致しません。
- `frozen_at_head=2066ce6…` は commit として利用不能。`e5dfa84c6` の generator blob は記録 SHA と一致しますが、これを全 source の凍結 HEAD として扱う根拠はありません。
- generator/source SHA の比較を外しても、ancestor 検査と全文再構成比較で停止します。
- 「既存 consumer の意味照合だけで十分」という P1 は、そのままでは成立しません。校正には対象照合がありますが、measurement と holdout の射影照合は、現行コードとの意味一致を全面的に代替しません。

編集・pytest・commit は行っていません。以下は親が実装判断・実測するための計画です。

## 最小実装計画

以下の短縮パスは repo root 相対です。

1. **歴史閲覧を明示的な経路として追加する。**

   [s1_known_axes_freeze.py:864](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_known_axes_freeze.py:864) の `verify_document` と同ファイル `:941` の `verify` に、例えば `historical=False` の keyword を追加します。既存 Python consumer の既定は現行利用のまま保ち、CLI `verify`（`:960`）から歴史閲覧を指定します。

   旧文書の識別には `t080_freeze_migration.py:47` の既存 `KNOWN_AXES_RAW_SHA256` を再利用し、receipt verifier は呼びません。新しい root 値・台帳は作りません。

   `verify(path)` は読み取った同一 bytes、`verify_document(doc)` は既存 writer 形式の直列化により旧文書を識別できます。実物について `json.dumps(..., ensure_ascii=False, indent=2) + "\n"` が旧 bytes と完全一致することは読取確認済みです。辞書 API の対象は、この既知文書の復元形に限定します。

   **識別成功時だけ旧文書の扱いを適用**し、未知文書や改竄文書は従来の厳格検証に進めます。任意の recorded generator SHA を信用して歴史扱いする分岐は禁止です。

2. **旧文書の歴史閲覧では、出所の完全性と凍結入力束縛を検証する。**

   `s1_known_axes_freeze.py:877` の source 走査を利用し、記録された WAL・provenance・文書・ccbench 入力の存在と SHA 照合を維持します。`source_resolver` も引き続き有効にします。

   歴史識別済み文書に限り、上記6種類のコード source と generator の記録 SHA を live SHA に一致させません。除外対象は既存 `_module_source` 呼出しに対応する閉じた集合とし、`.py` 全般などへ広げません。記録識別子自体の変更は旧文書の識別を失うため受理しません。

   この経路では、旧 HEAD の存在・ancestor（`:895`）や現行 `build_document` との一致（`:914`）を歴史的事実の条件にしません。現行の述語・comparator 権威集合も閲覧条件から分離します。現在の `_validate_schema`（`:826`）は意味検査を含むため、そのまま歴史経路の先頭に置く案は不可です。

3. **現行利用には、既存再構成による意味照合を残す。**

   歴史識別済み文書を現行 consumer が使う場合は、既存 `_validate_schema`、`assert_s1b_pairing`、`build_document` を通します。

   再構成文書との比較では、**認証済み旧コード source の SHA だけ**を記録値へ合わせた比較用コピーを作ります。元文書は変更しません。generator は既存 `generator_sha` 引数（`:918`）で記録値を渡せます。

   path・key・source 配列の順序／件数・lines・flags・述語・comparator・選定結果・参考値・pairing などは比較対象に残します。これにより、コード編集だけの不一致を除き、既存の構成照合を維持できます。意味の異なる再構成や再構成失敗は現行利用を拒否します。

   この案は最小のため、現行利用には従来の全文比較に由来する保守的な拒否が残ります。散文変更まで意味互換とみなす一般化は今回行いません。

4. **新規生成物の厳格経路を変更しない。**

   歴史識別に一致しない文書は、generator SHA、全 source SHA、ancestor、既存 pin hold、全文再構成比較を維持します。`build_document:734` の出力変更は不要です。

   `generate:925` の既存ファイル上書き拒否も維持します。新規生成物の自己整合性を「旧文書の歴史的真正性」で代替しません。

## 変更path・consumer区分

| path・行 | 区分／最小変更 |
|---|---|
| `orchestrator/campaign/s1_known_axes_freeze.py:826,864,941,960` | 本体変更。歴史識別・検証経路分離・比較用コピー・CLI 指定 |
| `orchestrator/campaign/s1_measurement_freeze.py:160,253,414` | 現行利用。既定の現行意味検証を維持。`:170` の cells 射影だけでは代替不可 |
| `orchestrator/campaign/s1_verify_extime_calibration.py:230` | 現行利用。`:249` の name/flags/predicate 完全一致と`:255`の正準検査を維持 |
| `orchestrator/campaign/s8b_oracle_driver.py:509` | 現行利用。`:518` の `verify` が歴史閲覧へ落ちないことをテストで固定 |
| `orchestrator/campaign/s1_direct_comparison.py:375` | 間接 consumer。measurement verifier を経由するので、その意味検証を維持 |
| `orchestrator/campaign/s8b_holdout_freeze.py:775,1015,1124` | 原則変更なし。入力束縛、既存 hold、variant binding 再照合を維持 |
| `orchestrator/campaign/t080_freeze_migration.py:47,1301,1677,2163,2430` | 原則変更なし。既存定数だけ参照。12/51 closure・履歴・receipt 再構成を新経路に置換しない |

consumer 本体は既定を維持すれば原則編集不要です。特に measurement と校正が T-080 adapter を呼ばない既存契約（各テスト `:286`、`:243`）を維持できます。

## 受理／拒否集合

| 入力・状況 | 歴史閲覧 | 現行利用 |
|---|---|---|
| 既知旧文書、入力束縛正常、コード SHA のみ変化 | 受理 | 意味再構成一致なら受理 |
| 同じ旧文書、live flags／述語／comparator が非互換 | 受理 | 拒否 |
| 既知旧文書の dangling HEAD | 閲覧拒否理由にしない | 旧文書識別を条件に ancestor を要求しない |
| 旧 generator/source 識別子、内容、source path/key の改竄 | 拒否 | 拒否 |
| WAL・provenance 等の入力コピーを改竄 | 拒否 | 拒否 |
| 新規文書が現行生成と自己整合 | 従来の厳格経路で受理 | 受理 |
| 新規文書の generator/source SHA 改竄、非 ancestor、再構成不一致 | 拒否 | 拒否 |

「受理」は既存 hold が解消した、または旧判定が certified になったことを意味しません。

## 不変条件

- 旧 artifact・campaign・WAL・判定・trust root の bytes／値を変更しない。
- `freeze_verification_hold.py:14` の `HELD=True`、21件の check ID、既存 marker 伝搬を変更しない。
- T-080 の historical/static artifact root 検査は実際に hold 中です（`test_t080_freeze_migration.py:1293,1313`）。これを復活させたり、新規歴史経路の成功根拠として数えたりしない。
- 旧 root の再利用は、今回要求された**既知旧文書の識別**に限定する。既存 held gate へ新検査を差し込まない。
- golden の独立値、既存拒否テストの期待理由、hold 対象 node を変更しない。
- 正しさの保証範囲は既存の構成・述語・flags 等の検査範囲。任意のコード変更の意味同値性を証明したとは主張しない。

## テスト／変異

追加先は既存の `test_s1_known_axes_freeze.py`、`test_s1_measurement_freeze.py`、`test_s1_verify_extime_calibration.py`、`test_s8b_oracle_driver.py` を基本とします。

| 正負対／変異候補 | 検出すべきこと・単一理由性 |
|---|---|
| 旧実物＋live コード SHA 差／歴史経路へ live SHA gate を戻す | 正例がその gate だけで落ちる。入力・旧 bytes は固定 |
| 旧 generator SHA 一箇所変更 | 歴史識別を失い generator 不一致で拒否。全文再構成に依存しない |
| 旧6種類の source SHA を一箇所ずつ変更 | 旧識別子を無条件に除外する弱体化を検出 |
| resolver が返す WAL または provenance コピーを一箇所変更 | generator/旧文書認証は正常のまま、該当 source SHA 理由だけで拒否 |
| 認証済み旧文書を固定し、再構成側の flags／comparator／pairing を一項目変更 | 歴史閲覧は成功し、現行意味照合だけが拒否 |
| 比較用コピーで source path/key/lines まで除去する変異 | SHA 以外の内容不一致を検出。入力 hash の前段拒否で代用しない |
| 新規文書の全文比較を無効化 | `what` 一項目改竄が受理される弱体化を検出 |
| measurement／oracle の呼出しを歴史閲覧へ変更 | 正常な旧文書＋非互換な現行構成で consumer が拒否することを確認 |
| hold の迂回・解除 | 既存 held/released 正負対と marker 集合をそのまま維持 |

変異ごとに正常対照を先に通し、対象以外の失敗がない状態を作ります。特に、旧文書の改竄が generator 不一致で先に止まる試験を「source 検査を kill した」と数えてはいけません。source 検査の変異は正常な旧文書＋resolver 入力改竄で独立させます。

既存検査との関係は次のとおりです。

- `test_s1_known_axes_freeze.py:650,673,702,718,728` の自己整合・内容改竄・source 改竄・generator 改竄・ancestor 拒否を維持。
- `s1_expected_goldens.py:624,657,679` の意味値、source layout、campaign SHA、CMake lines を維持。同ファイル`:10`は編集可能 source SHA を元から literal 固定していません。golden を変更する必要はありません。
- `test_s1_measurement_freeze.py:44` の **module shared fixture `real_known_axes_doc` は実 `build_document` → golden → `verify_document`** を実行します。新規経路の不具合は、その fixture を使う全 consumer に波及します。mock 成功や旧文書への置換は禁止です。
- 新テストが同 fixture を利用するなら、`conftest.py:260,520` の実 repo node／親・ccbench reader 分類と、`test_real_repo_serialization.py:132,1413` の独立期待・共有 fixture 閉包へ登録します。既存 hold 台帳には追加しません。
- 歴史閲覧の小テストは専用コピーで隔離し、実 Git／ccbench に触れるものだけ実アクセスどおり分類します。所要時間台帳は親の実測値で扱い、架空値を入れません。
- oracle の共有 fixture は receipt の historical basis と current runtime source を分けています（`test_s8b_oracle_driver.py:1008,1037,1048`）。今回の live bytes を historical closure に上書きして緑にしてはいけません。

親の実行対象は上記関連群に加え、T-080 履歴／hold、real-repo serialization、plain runner coverage、hold inventory/contract。`tools/run_tests.py` 経由の実測後に全走と指定 checker を行います。

## 未確定事項

- **固定 root を歴史識別に再利用する実装境界**は相談段で明示して確定する必要があります。これは識別子改竄拒否を成立させる本題の変更ですが、held artifact gate の再導入と混同しないレビューが必要です。
- 再構成の実走はしていません。現行利用が source SHA 以外でも不一致になるかは親が差分を取得してください。不一致を発見しても旧 golden や比較範囲を緑目的で緩めません。
- 本計画が閲覧可能にするのは known-axes 記録です。旧 measurement artifact 自身の generator/implementation hash 検査（`s1_measurement_freeze.py:400`）まで解除する計画ではありません。brief の「旧結果の利用可能性」はこの範囲に限定して記述すべきです。
