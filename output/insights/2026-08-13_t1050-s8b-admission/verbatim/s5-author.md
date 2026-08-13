## 現行挙動

変更前は portable binary record に admission receipt がなく、次の状態でした。

- receipt 欠落や別 cell 由来 receipt という状態を表現、検査できず、hash-only record が受理されていました。
- build admission の検証結果は build 後の store、resume、floor 測定、oracle 実走へ搬送されていませんでした。
- store、resume、測定直前、oracle 実走直前では、実 bytes と record の SHA 不一致だけを拒否していました。
- floor artifact と ratified freeze は binary hash と binding を検査していましたが、発行時 admission との連続束縛はありませんでした。

## 実装した変更

Production:

- [s8b_binary_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_binary_admission.py:1)
  - root 非依存の `s8b-binary-admission/v1` schema、発行器、canonical outer SHA、exact validator、portable key 正本を新設。
  - 元の sealed `BuildAdmission` を完全検証し、`source_root` だけを除外。
  - source digest、tracked diff、paths、pin、policy、review input、cell、binding、binary SHA、contract、trace を束縛。
- [build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/build_admission.py:449)
  - artifact 非依存の公開 policy resolver を additive に追加。既存発行、検証ロジックは未変更。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:1333)
  - `build_cells` 発行、portable projection、resolve、store 全件事前検査、resume、floor 測定直前を接続。
  - store は全 record と全 bytes を検査し終わるまでディレクトリも作成しません。
- [s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_stats.py:593)
  - 必須引数を追加せず、receipt の exact key、outer SHA、subject、artifact 内 cell 対応を無条件検査。
- [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_holdout_freeze.py:1275)
  - official result を current policy、protocol pin、contract、V1 freeze entry と照合。
- [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_ratified_freeze.py:1641)
  - live launch は current policy を要求し、historical reverify は current policy を要求しない経路分離を実装。
- [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:846)
  - 全 schedule receipt を store 読込前に検証し、実 bytes を record SHA と receipt subject SHAへ個別に照合。
- 保証名は「発行時に検証した admission の、保存から oracle 実走直前までの連続束縛」に限定しました。

Test:

- [test_s8b_binary_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_binary_admission.py:1)
  - 発行、root 非依存、None／空／malformed、subject 不一致、同一 binary の別 cell swap、live／historical policy 分離を追加。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_floor_campaign.py:5238)
  - fresh issuer → store → projection → resolve → resume 正例、receipt key 欠落、全件 preflight を追加。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_oracle_driver.py:4484)
  - binary、source、entry、binding が同一の別 cell receipt swap と、M5 receipt subject gate の隔離テストを追加。
- [s8b_v2_freeze_fixture.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/s8b_v2_freeze_fixture.py:109)
  - hash-only record を production issuer 由来の receipt と実 binary bytes に置換。
- [test_s8b_materialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_materialization.py:453)
  - manifest literal SHA を `4860905ed2c9bf994886564bad0b3185f3d6e512230e85db43e57503f261fbc8` へ更新。
- 既存の異なる root 間 deterministic test 本体は変更していません。

## 実走結果

指定 runner を4回起動しましたが、すべて pytest collection 前に終了しました。

- `test_s8b_binary_admission.py` 単体: rc=16
- 上記と `test_plain_runner_coverage.py`: rc=16
- 変更対象9 test file: rc=16
- 正負例、golden、root deterministic、meta-test の個別 nodeid 集合: rc=16

共通原因:

`Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`

したがって、pytest nodeid は一件も実走されておらず、緑とは申告しません。

静的検査は以下が rc=0 です。

- `git diff --check`
- 変更15ファイルの AST parse、NFC、U+0300〜U+036F 不在
- production 8 module の import
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 禁止領域と非接触ファイルの差分なし

## 期待赤

他単位の未 land に起因すると事前に特定できる期待赤はありません。

ただし pytest 自体が未到達のため、collection error、fixture 波及、実行時失敗の有無は未確認です。

## 波及

- receipt を持たない repo 外の旧 manifest、result、resume artifact は意図どおり拒否されます。互換 loader は実装していません。
- live artifact は `CURRENT_PIN` 更新後に拒否され得ます。published freeze の historical reverify は current policy 非依存です。
- portable binary fixture を手書きしている所有外 test は、新しい必須 exact key に追随が必要になる可能性があります。
- manifest bytes と共有 fixture の binary identity が変わるため、所有外の literal SHA があれば更新対象です。
- tracked `output/s8b-freeze`、V1 trust root、docs、非接触3ファイルは変更していません。
- commit、add は実行せず、差分は working tree に残しています。

## 変異への対応

- M1: portable exact-key 集合から receipt を外すと、key 欠落拒否テストが赤になります。
- M2: key を保持した None／空 receipt は validator の専用 missing gate で拒否します。
- M3: `subject.binary_sha256 == record.binary_sha256` は独立条件で、record 側だけ揃えた負例が検出します。
- M4: cell、holdout、configuration、entry、binding の tuple gateを独立配置し、同一 binary／source／entry／binding の receipt swap で検出します。
- M5:既存 record SHA 対応を残したまま、store bytes と receipt subject の比較を独立条件と隔離テストで検出します。

## 未了・未確認

- 指定 nodeid と波及 test は実装済みですが、Pegasus dispatch 障害により未実走です。
- 親段6の5本の mutation harness は未実施です。
- 親による受入全走、provenance 監査、commit は未実施です。

## 総括

実装対象の production code と test は working tree に反映済みです。  
root 非依存 receipt と current policy の独立権威を導入しました。  
store は全件 preflight 後にのみ書込みを開始します。  
live と historical reverify の policy 要件を分離しました。  
5型の負例と fresh 経路の正例を配置しました。  
禁止領域、非接触ファイル、tracked output は変更していません。  
静的検査は通過しましたが、pytest は基盤障害により未実走です。