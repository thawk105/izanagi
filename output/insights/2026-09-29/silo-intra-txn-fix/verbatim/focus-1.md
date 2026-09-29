## 対応表

| 所見 ID | 判定 | 根拠 file:line | 1 行 |
|---|---|---|---|
| R01 | closed | `fix1-out/scripts/run_ci_then_judge.sh:14-22` | 子 script を `bash` で起動し、両方の rc を記録している。 |
| R02 | closed | `fix1-out/scripts/launch_gate_liveness_v2.py:35-50` | 対照は発生した条項の違反合計 ≥1、両条項とも発生 0 なら判定不能。修正側の違反 0、両条項の発生、certified、取引数照合、rc 0 も維持している。 |
| R03 | closed | `format-ci.sh:27-35`、`inv-run.sh:36-45` | 検査 rc を最終 rc と `.done` に反映する。 |
| R04 | closed | `format-ci.sh:17-25`、`format-ci.log:5-27` | 既存 checkout を拒否し、各 checkout の clean 状態を必須にした。実走ログでも四つの format 検査が rc 0。 |
| R05 | closed | `fix1-out/scripts/inventory_silo_patches.py:44-50` | trigger の前提は README の重ね順と driver の実適用行を出典にした。 |
| R06 | closed | `fix1-out/scripts/inventory_silo_patches.py:102-115,160-173` | base の `_head_defines` と適用後の `_worktree_defines` を照合し、得た**同一の define 集合**で適用前後を比較する。 |

R06 では、patch が追加した軸マクロの CMake 既定値を `_worktree_defines` から取得する。既存 define の変更は拒否し、新しい値も適用前後の**両方**へ渡すため、patch 後だけに define を足す照合ではない。これは D297 と同じ define 取得系を使った stock 文脈の比較である。自己走の `inventory.md:1` は A=39、C=2、D=3、E=0。以前 E だった軸 patch は、既定値を供給した状態で前処理が成功し、前後の出力が一致した結果として A になっている（`inventory_silo_patches.py:168-173,220-231`）。

## 新しい所見

- **N01・should・`mk-fix.sh:58`** — commit 後の F branch 表示は実走で `git rev-parse` が失敗した（`mk-fix.log:83-86`）のに、script は rc 0 で進んだ。放置すると branch 照合のログを成功した証拠と誤読しうる。**推奨:** この表示の失敗を検出して停止するか、commit 前に使った F ref の取得方法で再照合する。

## 総括

**GO**。R01〜R06 の焦点修正は閉じた。N01 は証拠ログの修正事項。計算ノードの CI・D297・trace の結果は、この静的再レビューでは判定していない。