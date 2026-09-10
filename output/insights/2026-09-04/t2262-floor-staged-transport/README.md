# [T-2262] 床値 staged transport を driver 内部の production 既定へ移す

- wave: t2262-floor-staged-transport
- branch: worktree-dev-wave-t2262-floor-staged-transport
- 着手時の local main: c7ed565892cd4aba52d7fa47a7d1da17b117c005
- 一次資料: D1396 (機構の確定)、D1562 (ユーザー裁定)、worklog carry [T-2262] (archive 1227)

## 何をしたか

床値 campaign の official 走行が起動できない状態 (D1396) のうち、**staged transport 側の関門を外した。**
payload の所在を caller の seam でなく driver 側で導出する形にし、18 名の不適格 seam 集合と
`_derive_refreeze_eligibility` の判定式は literal のまま変えていない (D1562)。

## 導出規則 (明示的に固定した形)

```
payload_root  = floor_submit_receipt.receipt_path(
                    repo_root, env_tag=contract.env_tag,
                    nonce=reservation_binding.nonce,
                ).parent / "masstree-payload"
staging_base  = <canonical TMPDIR> / "izanagi-floor-fetchcontent"
```

- nonce の authority は**検証済みの `reservation_binding`** であり、生の環境変数ではない。
  同 binding は submit receipt の `job_id` / `job_script_sha256` / `nonce` 一致検査を通っている。
- 検証済み束縛が無い環境では fail-closed で拒否する。環境変数にも外部取得にも落ちない。
- path 式は既存の canonical 関数を使い、自前で組み立て直していない。
- directory 走査、glob、候補探索、最新値選択、既定値 fallback はいずれも使っていない。

## 親が実測で確かめた要点 (子の主張をそのまま採らず自分で測った)

| # | 実測 |
|---|---|
| M1 | reservation binding の確定 (`s8b_floor_campaign.py:7253`) は `build_cells` 呼出し (`:7463` / `:7529`) より前。順序として導出に使える |
| M2 | 同 `:7265-7277` が receipt を `reservation_binding.nonce` で選び、3 field の一致を要求する |
| M3 | `floor_submit_receipt.receipt_path` が submission directory を作る canonical 関数として既在 |
| M4 | `pegasus` 契約は `single_process=True` なので production 床値経路では binding が必ず存在する |
| M5 | 床値側の `None` 分岐は `_build_cells_impl` の 1 箇所だけ |
| M6 | `s8b_oracle_n_pilot.py` が共有 helper の別 consumer として実在する |
| M7 | `measurement-generation-claims` は repo 内に**存在しない**。生きた部分 claim は 0 件 |
| M8 | 現 main の job script の sha256 は歴史 submit receipt の記録値と**既に不一致**で main は緑。現 bytes を照合する生きた検査は無い |
| M9 | 稼働中の別 wave が process 起動点台帳を編集中だった |
| M10 | `floor_liveness.py` は journal record を exact key 集合で検証する |

**設計の要の実測**: seam 分類は `:7262`、`repo_root` の正規化は `:7313`。分類が先なので、
driver が内部で導出した staging は非既定 seam として数えられない。18 名集合と判定式を
literal のまま保ったまま意図が成立している。

## 親 brief の誤りと訂正 (すべて記録に残す)

1. 「既存 env から payload 所在は導けない」→ **誤り。** 投入 nonce が PBS 経由で job 環境に入り、
   job 本体が 32 桁 hex を必須検証し、driver の import 先が既に読んでいる。親が段 2 投入後に自分で
   見つけ、誤った前提で走っていた起草子を停止して投げ直した (ABORTED-s2-plan-attempt1)。
2. 「official の関門は staged transport だけ」→ **誤り。** §8 の承認束縛方式が未裁定であることを
   理由とする無条件拒否が CLI と core の二重で存在する。親が段 2 投入後に実測し、段 3 の 2 レンズが
   独立に追認した。**本 wave 完了後も official は起動できない。**
3. 「`ATTEMPT_DIR` と `SUBMISSION_DIR` は互いに導出できない」→ path 式としては正しいが、
   runtime では submit receipt が両者を持つので相互導出できる。段 3 レンズ A が反証。
4. 「凍結 bytes pin は不在」→ 言い方が不正確。歴史 submit receipt は job script の bytes を記録する。
   ただし M8 のとおり現 bytes を照合する生きた検査は無く、更新対象の凍結 pin は不在という
   結論自体は保つ。記録は当時の事実であり書き換えない (規律 7)。
5. 「pilot の `nondefault_seams` が結果から消える」→ public result schema にその field は無い。
   値は private な measurement-generation claim にある。

## 段 3 / 段 6 の所見のうち、機構を作らずに閉じたもの

- **部分 claim の resume が basis 混在で拒否される** (段 3 レンズ B、段 6 レビュー B が追認)。
  M7 のとおり生きた claim が 0 件で、直す対象が存在しない。回復機構は作らず、
  **「本変更をまたぐ resume はできない。新しい `campaign_run_id` で投入し直す」**を記録に残す。
- **staging 失敗の liveness 診断が generic へ退化する。** 変わるのは診断の粒度であり
  certified 値・受理集合・参照ではない。M10 のとおり journal へ event を足すと exact key 検証を
  割る危険があり、失う診断より持ち込む危険が大きいと裁定した。
- **driver 内 `cp -a` が process 起動点台帳を変える。** M9 の稼働 wave と衝突するため、
  subprocess を使わない in-process copy へ方針を変えて回避した。

## 変異検査

- spec: `mutation-spec.json` (sha256 = 72db2cab8c93b8fe3ebd6aa919991a422f596684987eeed0f89b127b2a31e46c)
- 結果: `mutation-result.json`。**baseline PASSED、6 変異すべて KILLED、期待 node と完全一致。**
- 観測 probe: `mutation-probe-observation.json` (全件 SURVIVED 期待で観測 node を集めた回)

| ID | 変異 | 期待 node 数 |
|---|---|---|
| MU1 | nonce の authority を検証済み束縛から生の環境変数へ戻す | 15 |
| MU2 | 固定 prefix の ancestor 非 symlink 検査を無効化 | 3 |
| MU3 | 束縛が無いとき環境変数へフォールバックする | 1 |
| MU4 | 既定経路の pin 検査呼出しを削除 | 3 |
| MU5 | 3 依存の source-dir を prebuild へ渡さない | 4 |
| MU6 | 導出した base を分類器へ渡す raw 引数へ再代入する | 1 |

### erratum (登録を外した変異と、観測の訂正)

- **MU7 (destination の事前不在検査の削除) は登録から外した。** 事前 `lexists` 検査と排他 `mkdir` の
  両方が同じ入力を拒否するため単一理由にできない。実装子と段 6 レビュー A が独立に同じ結論を出した。
  両方とも裁定の必須条件なので実装には残している。冗長 gate であり単独変異の証拠から外す。
- **初回 probe は親のミスで停止した。** MU1 の置換後文字列に、一意化のために付けた文脈行を
  残さなかったため構文が壊れ、テスト file 全体が収集エラーになり失敗 node を抽出できなかった。
  harness は fail-closed で停止し、作業ツリーを正しく復元した (親が `git status` 空を実測)。
- **MU3 は初回の形が弱すぎた。** `if False:` で検査を殺すだけでは、束縛が None のまま
  AttributeError で落ちるだけになり、対象テストが見ている「正しい環境変数と payload を用意しても
  staging が起きないこと」に噛み合わない。環境変数へフォールバックする忠実な形へ差し替え、
  単独 probe で狙った 1 node だけが赤になることを確認してから本走へ入れた。

### この変異検査が証明していないこと

- MU6 に対応する検査は、分類器呼出しより前に**同名の**束縛が現れないことを見る。
  別名の変数を経由して導出値を流し込む回帰は射程外である。
- 計算ノードの offline 条件で外部取得が実際に発生しないことは実測していない。
  静的には top-level の 3 依存で閉じるが、投入される upstream source 内部の nested FetchContent は
  射影から確定できない。発生しても preflight で fail-closed になる。

## 残る関門 (本 wave では外れない)

official は §8 の承認束縛方式が未裁定であることを理由に、CLI と core の二重で無条件拒否される。
job script も pilot 固定である。**したがって本 wave 完了後も床値 official は起動できない。**
D1396 は承認束縛の実装を明示的に見送っており、その解除は別の裁定に属する。
