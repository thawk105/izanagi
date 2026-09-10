# [T-419] (iii) — 着手前に見送り済みだった。実装せず記録を訂正する

dev-wave (2026-08-07)。branch `worktree-dev-wave-t419-iii`、起点 main `29ae9975`。
起動引数 = `/dev-wave [T-419] (iii)`。**実装差分なし (docs のみ)。**

## 結論

[T-419] の着手条件 (iii)「別 process の完全独立検証」は、**着手する前から見送り裁定済み**だった。

> **[T-560] P2・裁定済み (2026-08-06 /rulings) → 見送り**: publish 済み bytes の別 process
> verifier + 最終 receipt 束縛の完全形は作らない。同一 process 内再読で足りる (プロトタイプ基準)

これは 2026-08-06 の委任一括裁定 (worklog エントリ 270、大前提 = アカデミアのプロトタイプ基準)
で「再考して反転したもの」として明示的に見送りへ倒された項である。本 wave の scope はこの逐語と
完全に一致する。よって段 4 で **実装しない** と裁定し、`4→7→8→9` で閉じた。

**検出は段 3 の敵対レンズ B** が台帳の一次資料に当たって行った。それまでに codex 子 3 本
(段 2 プラン 1 + 段 3 敵対 2) を消費している。

## 収録物

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief と前提実測。**誤り 3 件は `s4-adjudication.md` を参照** |
| `s2-plan.md` | 段 2 codex プラン (read-only, reasoning=max)。実装しないが、再裁定時の材料として保存 |
| `s3-lensA.md` | 段 3 敵対レンズ A (恒真性・自己成就・純増検出力)。NO-GO、所見 10 件 |
| `s3-lensB.md` | 段 3 敵対レンズ B (独立性の名乗り過剰・効く層の網羅)。NO-GO、所見 10 件 |
| `s4-adjudication.md` | 段 4 親裁定 (real/refuted、親 brief の訂正、裁定パッケージ) |
| `prompts/` | 各段の prompt 全文 |

段 1 前提実測に使った使い捨て probe は実装面 (実行可能資材) にあたるため repo へは入れず、
repo 外の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s1-premise-probe.py` に置いた。
測った値は本 README と `s1-brief.md` の表が正本である。

## 前提実測 (2026-08-07、login node、worktree `dev-wave-t419-iii`)

| 対象 | 実測 |
|---|---|
| `registered/calibration-94a4b79fa31bba3c.json` | 別 process から canonical 帯述語 **pass**、content-address **一致**、schema v2 **ok**、48 samples、method = 方式 α (`k5/interval-ns50000000`)、`tolerance_pct=2.0` |
| `registered/calibration-753f535a8d024727.json` | 同経路で帯述語 **fail** (既知の自己不整合)、content-address 一致、schema v2 ok |
| job 892707 | `calibrate_rc=0`。`calibrator.cli → execution_guard → env_contract` の import 連鎖は計算ノードで実際に通っている |
| `output/s8b-freeze/floor_protocol.json` | `FROZEN_MANIFEST` で凍結。bytes は `contract_sha256 = e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` を pin |

## 段 3 の 2 レンズが独立に出した結論 (T-560 の見送りを補強する)

- **「完全独立」ではない。** 別 PID・別 interpreter になるので calibrator 内の monkeypatch・
  module global・policy 再束縛からは分離されるが、同一 checkout・同一 predicate/schema/policy・
  同一 host/filesystem/UID・同一親 shell を共有する。実現するのは process-local state からの
  分離であって、独立実装でも別 trust domain でもない (レンズ B 所見 2)。
- **land しても (iii) は閉じない。** 新 wiring を通った実 job も final receipt も無く、
  post-hoc 判定では代替しない (レンズ B 所見 5)。
- **効く層は future certify wrapper だけ。** published 集合、registry / loader の受理集合、
  現行 certified 選択結果・レポート参照は 1 つも変わらない (レンズ B 所見 4)。
- **被検証者が検証者を選ばない、は成立しない。** verifier の subject は calibrator が書く
  `publish.json.target` であり、静的に確認できる迂回が 9 系統ある (レンズ B 所見 3)。
- **判定 artifact に生 bytes を内包する設計は自己成就。** receipt の複製 bytes と checks を
  一緒に作り直せば常に自己整合し、実ファイルだけを差し替えても赤くならない (レンズ A 所見 2)。
- **Python 3.9 互換テストは 3.10 の interpreter 上では恒真に近い** (レンズ A 所見 5)。
- **変異事前登録 11 件のうち 4 件は kill の帰属が成立しない** (レンズ A 所見 6)。

## 親 brief の誤り 3 件 (訂正)

1. **「`registered/` を列挙する test は 1 件も無い」は誤り。**
   `orchestrator/tests/test_pegasus_tools.py:632` の `_acquisition_probe_document` が
   `next(...glob("calibration-*.json"))` で列挙している。正しい主張は
   「94a4 の verdict を固定する意味的 assertion が無い」。
2. **「in-process の判定は certify job を再走しない限り再現不能」は過大。**
   publish 済み artifact は content-addressed で残るので job を再走せず再評価できる
   (本 wave の前提実測がそれを実行した)。正しい主張は「判定そのものが artifact として残らない」。
3. **`docs/phase3.md` の T-272 記述への親の訂正も過大。**
   job 892707 の `calibrate_rc=0` は import 連鎖が当時の計算ノードで通ったことを示すが、
   artifact は python 版数を記録しておらず、1 job・1 node の成功は shell 3 本の版数 gate 不在を
   解消しない。

## 実装差分ゼロの射程

実装差分が無いため、**変異 matrix と受入全走は対象外**である。変異事前登録も行っていない
(登録すべき変異面が存在しない)。段 1 の前提実測は repo 外の使い捨て probe で行い、
repo へは 1 byte も書いていない。

## 裁定パッケージ (ユーザーへ返す、優先度順)

1. **94a4 の活性化と凍結 floor protocol の衝突。** 凍結済み `floor_protocol.json` は旧 contract
   hash を pin し、`validate_protocol` は現在の `lookup(env_tag)` と比較する。新世代を活性化すると
   凍結済み protocol が拒否されうる。凍結 bytes の書換えは禁止なので、歴史的世代の解決
   (`resolve_by_contract_sha256`) か新 protocol 世代の発行かを先に決める必要がある。
   これは着手条件 (iv) と活性化権限の**手前**に効く。
2. **[T-560] の見送りを維持するか、覆して (iii) を実装するか。** 覆す場合の材料
   (段 2 プランと段 3 の 20 所見) は本 insights に揃っている。ただしレンズ 2 本は
   「実装しても『完全独立』は名乗れず、成果物のどの値も変わらない」と結論している。
3. **見送り裁定が依存タスクの着手条件へ反映されない事故の制度化。** 独立 2 例が揃った。
4. **`test_pegasus_tools.py:632` の `next(glob(...))`** が registered/ 2 件で非決定になった。
