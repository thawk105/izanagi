# [T-1092] acceptance-receipt 段の失敗理由診断 — 材料

wave = `worktree-dev-wave-t1092-receipt-diagnostics` / base = main `849d3d59` → `22c13a04` 取り込み。
裁定 = 2026-08-13 第 12 回 /rulings 確定内容 #1 (authority: user、23:44 JST)。

## 事故の一次資料

`/work/1/SFC/tanab/dev-wave-jobs/2026-08-13_t1053-t1066/` (repo 外、job dir)。

| 事実 | 実測 |
|---|---|
| waiter log 全文 | 4 行。末尾が `error: stage=acceptance-receipt rc=70` |
| 同走行の pytest | `acceptance-child-3.log:22` = `10750 passed, 65 skipped in 123.89s` |
| detail / source_rc | いずれも**無し**。約 14 の raise site のどれかを判別できない |
| 走行時の実装 | `59b8beb6` (branch worktree-dev-wave-t1053-t1066)。`detail` の出現 **0 件**、`acceptance-receipt` の出現 20 件 |

## 親が反証した仮説 (最有力 2 説がいずれも成立しない)

| 仮説 | 判定 | 反証の実測 |
|---|---|---|
| 受入 lease の TTL 切れ | **反証** | 許容 age は 2100 秒 (`_LEASE_TTL_SECONDS=2400` − `_RECEIPT_PUBLISH_MIN_TTL_SECONDS=300`)。waiter-3 は 19:16:45 起動 / 19:20:31 終了 = 226 秒 |
| 走行中に main が追い越した | **反証** | `git reflog show main` は 08-02 の clone まで 825 entry で欠落なし。**08-13 の 15:00〜20:00 に main ref の更新は 1 件も無い** (次の更新は 20:48:17) |

**commit の author 日時では ref の移動を証明できない** (既存 commit への移動・巻き戻し・過去日時
commit の取り込みを見落とす)。段 3 の敵対レビューがこの穴を指摘し、根拠を reflog へ差し替えた。

**帰結。** git 履歴・全 log・source を持つ親が特定できなかった。これが本 wave の純増検出力である。
真因の最有力仮説は `receipt-lease-check` の `state="acquired"` 経路 (先行 owner 解放後に
最終 claim が `acquired` を返す) だが、事故世代に診断が無い以上**証明はできない**。
本 wave はこの仮説に依存せず全 site へ一律に診断を付ける。

## 変更の骨格

判定条件・分岐・rc・stage 名・受理集合は不変。失敗時の `raise` へ引数を足すだけ。

- 既存 `_Outcome.detail` / `_attestation_detail` / `_print_outcome` を再利用し、新機構を作らない
- stderr の既存 `error:` 行は形も stream も残したまま `detail=` を足す
- **加えて** stdout へ別接頭辞 (`diagnostic:`) の 1 行を出す (裁定の文言どおり)
- publish は sigblock 失敗と rename 失敗を別 reason へ分ける
- detail 生成は signal mask 区間の外で行う
- mask 復元失敗は receipt が**未 publish のときだけ** fail-closed。publish 済みの成功は覆さない
- reclaim の下位条件は `failure_kind` で 14 種に分ける
- 短絡で未評価だった条件は `null` で明示する (判定に使っていない値を観測値と偽らない)
- cleanup が一次 outcome を置換するときも一次 stage/detail を入れ子で保存する
  (**返す outcome の選択は変更しない**)
- 自由文字列 256 bytes / serialized detail 2048 bytes で切り詰め
- 例外は型名と整数 errno のみ。メッセージ・`repr`・path・環境値・stdout 原像 hash は出さない

## 変異検査 (DW-M08 の「構造化シグナルだけを pin する型」)

`mutation-spec.json` / `mutation-ledger.json` (最終走)、`mutation-ledger-probe.json` (初回 probe)。

最終走 = **9/9 KILLED、MISMATCH 0、SURVIVED 0、harness rc=0**。

- **A1〜A5 = diagnostic sensitivity pin** (reason すり替え、観測値の削除、publish 分割の差し戻し、
  stdout 行の削除、cleanup 入れ子の削除)。DW-M08 に従い kill でなく別枠の診断感度固定として扱う。
- **B1〜B3 = 受理集合が鈍っていないことの確認** (TTL `>=`→`>`、main 再照合 `!=`→`==`、
  child-green の rc 検査除去)。既存テストが従来どおり kill することを示す。
- **C1 = fail-open 防壁** (診断 normalizer が必ず例外を出す)。rc/stage が `unexpected-error` へ
  倒れないことを固定する。

### probe で 1 件が生存し、base からの穴を露出させた

初回 probe で **B1 が SURVIVED** した。`>=`→`>` は残り時間がちょうど 300 秒のときだけ
受理→拒否に変わる境界変化であり、等価変異ではない。既存テストは 299 秒 (`age_seconds=2101`)
しか試しておらず、**境界が固定されていなかった (base からの穴)**。
DW-M02 の再照準として、300 秒ちょうど (`age_seconds=2100`) で publish・rc=0 になることを
固定するテストを足した (production は 1 行も変えない)。同型の未固定境界として
detail の 256 / 2048 bytes 上限ちょうども固定した。再走で B1 は KILLED。

### 期待 node の確定手順 (DW-M08)

初回 probe → 実測 `failed_nodes` を完全集合として再登録 → 再走。
再走でも 3 件が MISMATCH したが、差は signal / handler 復元系の 3 node
(`test_public_main_failure_restores_handler_without_release`、
`test_public_main_real_signal_after_success_uses_restored_handler`、
`test_signal_after_core_success_uses_restored_real_handler`) の出現揺れだけで、
いずれの変異でも決定的な killer ではなかった。2 走の観測の積を安定核とし、
この 3 node を `--deselect` した確認走で 9/9 KILLED を得た。

## 測定値 (すべて計算ノード、`--force-dispatch`、rc はパイプに通さず `.done` から取得)

| 時点 | 結果 |
|---|---|
| 変更前 baseline | 199 passed |
| 実装 + fix 1 巡 | 238 passed |
| fix 2 巡 | 4 failed / 247 passed (**既存テスト 1 件の回帰**) |
| fix 3 巡 | 251 passed |
| 変異再照準 (境界テスト) | 254 passed |
| main (`22c13a04`) 取り込み直後 | 276 passed |
| マージ統合監査の修正後 | **277 passed** |

## 並行 wave との合流で見つけた漏洩

main 側に [T-1076] (稼働中 waiter の実行 bytes 照合契約、実装 `70ae5bf2`) が着地し、
同じ 2 ファイルを変更していた。git の自動マージは競合なしで通り、テストも 276 passed で緑だった。
しかし Codex `role=author` による合成監査で欠陥 1 件を検出した。

- **T-1076 が新設した waiter bytes gate の失敗経路が、共通の attestation 形式を使わず
  手組み JSON で detail を作っており、初期束縛失敗時に例外メッセージ (`str(exc)`) を
  運用 log へ出しうる状態だった。**
- テストが緑なので、実行して初めて見える型である。共通形式へ統合し、型名と整数 errno だけに絞り、
  不正 SHA も原文でなく型・byte 数・分類だけにした。非漏洩の回帰テストを追加した。

**教訓。** 新しい失敗経路を足す wave は、既存の「診断に何を載せてよいか」の規律の外側に
出やすい。合流時に監査しないと、診断可能性を上げる wave の隣で漏洩が増える。
