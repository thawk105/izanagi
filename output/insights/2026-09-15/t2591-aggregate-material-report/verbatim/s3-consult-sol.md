## 恒真性の所見

参照略号は次の絶対パスのファイルを指す。所見はすべて静的読解であり、テスト・変異は実走していない。

- `R`：[/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2591-aggregate-material-report/orchestrator/campaign/p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2591-aggregate-material-report/orchestrator/campaign/p3_b4_material_report.py)
- `I`：同 worktree の `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- `T`：同 worktree の `orchestrator/tests/test_p3_b4_material_report.py`
- `IT`：同 worktree の `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`
- `D`：同 worktree の `orchestrator/tests/test_floor_pair_driver.py`
- `F`：同 worktree の `orchestrator/campaign/floor_pair_driver.py`
- `P`：[/home/SFC/tanab/.claude/jobs/a0f6bd8d/tmp/wave-t2591/artifacts/t2591-aggregate-material-report/s2-plan.md](/home/SFC/tanab/.claude/jobs/a0f6bd8d/tmp/wave-t2591/artifacts/t2591-aggregate-material-report/s2-plan.md)
- `B`：[/home/SFC/tanab/.claude/jobs/a0f6bd8d/tmp/wave-t2591/brief.md](/home/SFC/tanab/.claude/jobs/a0f6bd8d/tmp/wave-t2591/brief.md)

### 1. §3 の assert は、単独では集約の実行を証明しない

- **所見：** 全項目の識別力は以下のとおり。「集約固有でない」と「無価値・恒真」は同義ではない。共通の投影 assert も、実 v2 bytes との結合に使えば必要な証拠になる。

  | §3 の assert | 集約以外でも真になる条件 |
  |---|---|
  | 3値が相異なる／第0値 < 第2値 < 第1値 | 入力 fixture の性質だけ。issuer が無視しても真 |
  | artifact schema が literal v2 | v1 は排除するが、v2 を名乗る手書き dict は通る |
  | operation が literal max | 演算を実行せず文字列だけ書いても真 |
  | expected_specs が3 pinsと一致 | 呼出し引数をコピーする stub でも真 |
  | sources 3件、path/hash/pin/floor/limitations 一致 | 入力情報をコピーする stub でも真 |
  | artifact・resolver・report が最大値と一致 | 最大 source の単一 authority でも、値だけなら真 |
  | report.floor 全体一致 | literal v2 を含めれば v1 は排除する。期待 dict を返す stub は排除しない |
  | artifact の実 hash 一致 | v1・手書き artifact にも実 bytes と hash はある |
  | 全 source・集約非保証の順序付き投影 | 手書き v2 stub でも真。実経路と組み合わせれば全 source の到達証拠になる |
  | 非最大 source 0・2 の limitation | 上記の部分集合。追加の独立証拠ではない |
  | evaluated／floor_argument／201 blocks／402 rows／raw UTF-8・hash | v1 でも真。件数と raw 結合は authority 不在でも成立し得る |
  | Markdown の床値・path・hash | v1 でも真。集約 artifact の正確な参照との結合が必要 |
  | Markdown の非保証 | 現行では成立しない。集約実行の証拠にもならない |

- **根拠：** `P:76–88`、`R:952–998`、`R:1214–1219`、`I:1194–1216`。
- **real か推測か：** assert の論理的限界は読解で確認。偽実装による通過は未実測。
- **成果物への影響：** 共通 assert の本数を「集約を検証した強さ」と数えると、単一 source の値だけを表示する実装の検出力を過大評価する。
- **推奨：** 正例の証拠を「実 issuer が発行した v2」「呼出し側で固定した3 spec と全 source」「独立した最大値」「同じ artifact の path/hash/schema が report bytes に届く」の連鎖として評価する。任意の stub を出力 assert だけで排除できるとは主張しない。

### 2. `analysis.floor_argument` は、実際の evaluator 引数を証明しない

- **所見：** ここがプランの具体的な穴。`analysis.status` は assembly 成功から設定され、`floor_argument` は evaluator 実行後に authority から上書きされる。実 evaluator に `None` を渡す変異でも、列挙された assert は解析結果の誤りを直接検査しない。
- **根拠：** 実引数は `R:267–278`。表示値の生成は `R:858–863` と `R:995–997`。内部検査も同じ authority との比較だけ（`R:1070–1075`）。実 evaluator は `p3_b4_analysis_path.py:349–353` で不正な floor を結果値として返す。
- **real か推測か：** 表示と実引数の独立性は読解で確認した real な検証欠落。変異時の新テスト緑は未実測。
- **成果物への影響：** report が「最大床値を渡した」と表示しながら、解析結果は別の床値で計算された状態を見逃す。
- **推奨：** 親が `floor=None` と非最大 floor への受渡し変異を測れ。正確な実引数まで主張するなら、既存 m9 のように実 evaluator へ委譲する観測を許すか、床値の違いを識別できる解析結果の独立期待値が必要。現在の3 patch 制限との整合も必要。

### 3. dict 到達と serialized bytes 到達が区別されていない

- **所見：** §3 は主に `document.json_value` の assert と読める。これだけでは「JSON成果物へ届く」を保証しない。また「3 spec」が本当に rr5／rr50／rr95 であることは helper 任せである。
- **根拠：** `P:74–88`、`R:1244–1255`。rratio の設定は `IT:1194–1197`。実 issuer は expected_specs が非空であることを検査し、3系列というこの正例の意図自体は固定しない（`I:1031–1060`）。
- **real か推測か：** プラン上の明示欠落は real。現行 serializer の不具合を発見したわけではない。
- **成果物への影響：** dict だけ正しく bytes が別内容でも、新正例の完了説明が過大になる。helper が変わって3系列の意味が失われても、pins の自己一致だけは残る。
- **推奨：** 実 `json_bytes` を decode した値で floor と非保証を確認する。3 pins に対応する spec の workload を literal rr5／rr50／rr95 と結ぶ。最大値は summary の binary64 値から独立に比較し、issuer の戻り値から逆算しない。

## 層の実体性の所見

### 4. 指定 cache の回避は成立する。上流の合成入力は残る

- **所見：** 実 issuer・resolver・builder が、指定されたテスト用 cache に落ちる経路は確認されない。builder 直接呼出しは有効。ただし「すべて実物」とは言えず、floor 入力 summary は手書き合成、calibration は返却値 stub、publication は共有 evidence fixture である。
- **根拠：** cache は `T:53–54`、アクセスは `T:248–264`。実経路は `I:1244–1248` → `I:1146–1169`、resolver は `I:1495–1515` → `I:1324–1325` → `I:1266–1271`、builder は `R:1230` → `R:215–278`。合成入力は `IT:1187–1321`。
- **real か推測か：** 読解で確認。全依存モジュールに cache が一切ないという主張ではない。
- **成果物への影響：** 既存 `_DOCUMENT_CACHE` の absent document を再利用する偽緑は、この設計では生じない。一方、実測 summary や calibration の真正性まで証明したとは言えない。
- **推奨：** 直接呼出しを維持する。証明範囲は「名指しした合成 source bytes を実 issuer が検証・集約し、実 resolver と builder が再読込する」と記す。helper の跨 file 配置自体を理由に共有 module 化する必要はない。

## seam と規律 2 の所見

### 5. Git seam は集約・投影を置換しないが、入力受理の一部を迂回する

- **所見：**
  - **環境 seam とする根拠：** Git patch は最大値計算、3 spec 閉包、source 再構成、report 投影を置換しない。外して増える検査は Git による入力の凍結・履歴 binding であり、集約 → report の結線そのものではない。
  - **迂回とする根拠：** その binding は実 issuer が呼ぶ入力受理ゲートの一部。`git show` が作業ファイルを返し、祖先判定が既定で成功するため、未追跡・HEAD と異なる bytes・実在しない祖先を実 Git 同様には拒否しない。
- **根拠：** `D:336–371`、`F:1212–1240`、`F:1285–1292`、`I:1054`。
- **real か推測か：** patch と検査の対応は読解で確認。
- **成果物への影響：** 既存 seam の緑から「実 Git に凍結された source を受理した」と言うと、成果物の出所保証を水増しする。ただし、それだけで集約・report 層が stub になったとは言えない。
- **推奨：** Git seam を結線試験の環境 seam と分類する判断には合理性がある。ただし現在の親制約では許可されていない。実 Git 案は制約を満たす手段として妥当だが、結線検証に不可欠という説明は修正する。

### 6. 実 Git 化だけでは受理境界の検証にならない。keyword 条件化自体は緩和ではない

- **所見：** 実 Git fixture でも、正しい入力だけなら Git 検査を削除した変異は通り得る。また、全 spec を生成後に pin する自己整合だけでは、意図した rr 系列の固定を証明しない。反対に、`_install_git` の設置だけを keyword で条件化し、既存既定値を維持する変更は、既存 issuer テストの受理集合を直ちに変えない。
- **根拠：** `P:46–49`、`IT:53–74`、`D:417–437`。実 Git は入力 commit と後続 spec commit を構成する。source の最大値・非保証は Git と別に `I:1194–1216` で構成される。
- **real か推測か：** 条件化は未実装なので「既存動作維持」は条件付き評価。正例だけでは拒否機能の削除を検出できない点は論理的限界。
- **成果物への影響：** 実 Git を使ったという理由で、不正入力を拒否する証拠まで増えたと扱う偽緑が生じる。Git 履歴を合わせる作業を集約の独立期待値と混同すると参照の意味も失う。
- **推奨：** 既定値・既存呼出し・calibration 設置を維持し、条件化は Git patch の設置だけに限定する。spec の変更に伴う hash 再計算は正当な fixture 構築であり、受理済み summary から expected_specs を作る変更は採らない。既存群の不変性は親が測れ。

## 親 brief への反証

### 7. stub を残すだけで新正例が恒真になる、という因果関係はない

- **所見：** P1-a の結論は支持する。ただし D1974 の「期待値を変えない」は「helper を変更できない」と同義ではない。残す理由は、既存 m9 が v1 の境界・投影を試し、新正例が別の v2 発行経路を試すためである。
- **根拠：** `B:61–64`、`T:98–132`、`T:842–955`。新正例の直接 builder 呼出しは `P:68–70`。
- **real か推測か：** 読解で確認。既存 m9 の緑が別 node の assert を成立させる経路は見つからない。
- **成果物への影響：** 問題は stub の存在ではなく、既存群の緑を新正例の検出力の証拠にすること。そうすれば未検証の v2 結線を検証済みと報告してしまう。
- **推奨：** m9 は維持する。新 node 自身について、v1 への置換、非最大値、非最大 source の非保証欠落を検出するか親が測れ。

### 8. patch 許可集合は、fixture 内部まで含めると狭すぎる

- **所見：** 「3つだけ」を fixture 構築にも適用すると、指定 fixture の再利用要求と矛盾する。さらに既存 fixture 内部には4箇所より多い patch がある。一方、calibration stub と fsync 無効化を認めたまま calibration 真正性・耐久性まで主張するなら、その主張に対しては広すぎる。
- **根拠：** `B:18–19,42–44`、`T:190–209`。追加の内部 patch は `orchestrator/tests/test_p3_b4_raw_record_producer.py:329–337,395–399`。同ファイル `108–115` の cache は writer authority であり、集約床値や report の cache ではない。
- **real か推測か：** 読解で確認した契約矛盾。
- **成果物への影響：** 内部 patch を隠すと evidence の生成条件を誤記する。3つだけを文字どおり強制すると指定 fixture を使えない。
- **推奨：** 許可集合の射程を「既存 evidence fixture の明示された生成条件」と「新正例が追加する差替え」に分けて明記する。前者を無制限に許可する説明にはしない。実引数観測が必要なら所見2の委譲 wrapper を別途明記する。

### 9. Markdown 非保証要求の撤回は正しい。ただし参照到達は撤回できない

- **所見：** 非保証の逐語 Markdown 出力は v1/v2 共通で存在せず、今回の集約結線に必須の既存契約ではない。撤回は妥当。残すべきなのは、**最大 source の単一 authority ではなく、集約 artifact 自身の path/hash と最大床値が表示されること**。
- **根拠：** `R:1097–1192`、`R:1214–1219`。JSON への参照は `R:1109`、完全投影を JSON とする説明は `R:1163`。
- **real か推測か：** 現物の描画内容は読解で確認。新たに schema・全 source 一覧を Markdown に出す既存要件は確認できない。
- **成果物への影響：** 非保証要求だけの撤回では出力は変わらない。path/hash の検査まで削れば、表示床値が同じ最大 source への誤参照を見逃す。
- **推奨：** `P:88` の非保証 Markdown assert は最新の撤回に合わせる。集約 artifact の実 hash/path、最大 ratio、および非保証を含む JSON bytes への Markdown の hash 結合は維持する。

### 10. document 到達で止めてよいが、「certified な公開成果物」とは言えない

- **所見：** builder は JSON/Markdown bytes を生成するので、今回の限定された投影到達には十分。ただし `write_material_report` は builder を呼ばず、生成処理を別に組み立てている。publish 成功を builder 正例から推論できない。また親の「certification 成果物」という説明は、現物の保証範囲と食い違う。
- **根拠：** `R:1222–1255` 対 `R:1551–1585`。publish では output 拒否条件、campaign 非交差、commit marker が加わる（`R:1559–1564,1581–1585,1479–1483`）。現物は `certifying=False`、`closed_world=False`（`R:884–886`）で、Markdown も selection を certify しない（`R:1141`）。親の説明は `B:78–80`。
- **real か推測か：** 読解で確認。
- **成果物への影響：** 床値・authority 参照の投影関数は共通だが、publish の受理集合は追加条件で狭い。明示 output_root では reproduction argv が変わり、JSON hash・Markdown hash も変わる。保存済みペアと commit marker の存在は builder では証明されない。
- **推奨：** 今回は document 生成まででよい。結論を「evidence-only report の生成 bytes に到達」と限定する。「公開済み」「certified」「保存まで実証」とは書かない。publish まで対象を広げる必要は、現在の投影目的からはない。

## 総括

**プランの最重要修正点は、`analysis.floor_argument` を実引数の証拠と扱わないことと、`json_value` の検査を生成 JSON bytes まで結ぶこと。**

実 v2 issuer → 実再解決 → 実 builder の経路は静的に接続されており、指定 cache の回避も成立する。production の変更を必要とする v2 拒否箇所は今回の読解では見つからなかった。

実 Git 化は入力の Git binding を実体化するが、それ自体が集約 → report の識別力を増やすわけではない。既存 m9 の stub 維持、Markdown 非保証要求の撤回、document 生成での停止は、上記の証明範囲なら妥当である。

**親が測れ：** 新 node 単独の実走、実 evaluator への床値受渡し変異、v1／非最大床値／非最大 source 非保証欠落の変異、helper 条件化後の既存群。ここではいずれも緑・変異検出済みとは報告しない。