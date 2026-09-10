# 段 4 裁定 — [T-2048] floor 予約予算 drift

## 1. 結論

- **実装する。** 正式測定の protocol / freeze / policy / 実行値は変えず、現行 authority を誤記する shell コメントと README §5 だけを直す。
- scheduler request は 36000 秒のまま。driver `required_s=30000`、finalize reserve 600、preflight minimum envelope 30600 を役割別に記す。
- `28200` は stale literal として消さない。12-cell subtotal として正しく残し、共有 dependency prebuild 1800 を足して 30000 になる関係を明示する。
- `capacity` は曖昧なので使わず、`required_s` / finalize reserve / preflight minimum envelope / raw headroom / estimated residual headroom を分ける。

## 2. real / refuted 裁定

| 所見 | 裁定 | 採否・scope | 理由と成果物影響 |
|---|---|---|---|
| policy / PBS directive / qstat の三層 authority | real | 採用・内 | policy は期待・receipt 値、directive は scheduler への要求宣言、qstat は driver が束縛する実効 limit。混同すると再現手順の参照が誤る。 |
| 30000 + 600 = 30600 | real | 採用・内 | 現行 calculator と exact journal fixture が固定する。実行値は変更しない。 |
| 28200 を対象全文から消す | real finding | plan を棄却・内 | 28200 は 12-cell subtotal として正しい。stale なのは全 `required_s` と呼ぶ旧説明。 |
| 4500 を固定 slack とする | real finding | plan を修正・内 | raw headroom は 5400。4500 は prologue 約900秒を仮定した estimated residual で、保証・実測ではない。 |
| shell コメント変更は proof-chain identity に影響 | real | 採用・内 | script blob hash と source commit は変わる。既存 receipt を再解釈せず、将来投入は新 hash / receipt / 測定世代になる。 |
| 正式凍結 pin に触れる | refuted | 実装継続 | R33 実物は oracle/n-pilot driver/job を pin。floor script は submit 時に commit/blobへ動的束縛される。protocol/freeze bytes は無変更。 |
| queued/in-flight 旧 floor job が同 checkout を読む危険 | real 条件付き | 事前確認済み・内 | `qstat -u tanab` と process table に floor campaign job/process は無い。`floor_sc` は別 job。編集を進める。 |
| D87 の歴史本文も 30600 へ改稿 | refuted | 不採用・外 | D87 は当時値の provenance。現行説明だけを更新し、歴史 bytes は触らない。 |
| 既存 runtime test が docs mutant を kill | real finding | 帰属を棄却・内 | runtime test は production 非回帰だけを証明する。説明 mutant は scoped static oracle へだけ帰属させる。 |
| raw mutation output を repo 内へ置く | real finding | 不採用・内 | T-1981 の clean-scan 事故に従い raw result は repo 外、repo 内は spec と要約だけにする。 |

scope 外の real 所見に、新たなユーザー裁定を要するものはない。

## 3. plan v2

1. D95 Codex author が `tools/pegasus/floor_campaign.sh` 冒頭コメントだけを編集する。PBS directive、変数、処理行は触らない。
2. 親が `tools/pegasus/README.md` §5 の 1 bullet を同じ役割分離へ直す。D87、policy、calculator、tests、protocol、freeze は無変更。
3. shell には 12-cell subtotal 28200、shared prebuild 1800、required_s 30000、finalize 600、minimum 30600、raw headroom 5400、prologue estimate 約900、estimated residual 約4500 を別ラベルで記す。
4. README は policy=期待値、PBS directive=要求宣言、qstat=実効 limit の三層と、現行 driver envelope 30600 を簡潔に記す。D87 の歴史値を現行値として引用しない。
5. 関連受入は exact journal 30000/600、generic formula、shared prebuild、PBS-policy equality、policy-over-envelope、qstat parser / match-mismatch。pytest は `tools/run_tests.py` 経由、shell syntax は同 runner の既存関連 test で担保する。
6. 実 scheduler 投入・floor 本走は行わない。説明差分の受入に性能測定は不要。

## 4. gate の禁止

- 禁止: scheduler request 36000 を driver minimum 30600 へ下げない。通る正例: policy/PBS/qstat が 36000 のまま、calculator が 30000 + 600 を要求する現行経路。
- 禁止: 28200 を全 `required_s` と記さない。通る正例: 28200 を 12-cell subtotal とし、共有 prebuild 1800 を一度だけ加えて required_s=30000 とする説明。
- 禁止: estimated 4500 を保証値・実測値と書かない。通る正例: raw 5400 から prologue estimate 約900 を引いた estimated residual と明記する説明。

## 5. 変異事前登録

| ID | 変異 | 単一 oracle | 期待 |
|---|---|---|---|
| M1 | shell コメントの shared prebuild 行を除き、28200 を再び全 required_s と呼ぶ | 対象コメント block のラベル付き算術を検査する scoped static oracle | KILLED |
| M2 | raw headroom 5400 と estimated residual 4500 のラベルを入れ替える | 同 block の exact relationship oracle | KILLED |
| M3 | README の current envelope を旧 `required 28200 + finalize 600 = 28800` へ戻す | README §5 bullet のラベル付き関係 oracle | KILLED |

- baseline が先に成功し、各変異は tracked file へ一意に注入し、oracle の非0が当該説明関係だけに帰属するときだけ kill と数える。
- runtime tests は上記 docs mutation の kill に数えず、production 非回帰として別記する。
- raw mutation result/probe は repo 外の wave job directory に置く。
