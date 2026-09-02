---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2102-b4-reference-tps-domain
seq: 2
---

## {{D:b4-finite-decimal-registry-only}}. reference_tps の有限十進述語は registry admission だけに置き、狭まる面を過小に書かない

**決定:** D1424 決定 4 が示した配置の択一のうち、**registry admission 限定 (択 A)** を採る。
述語は `p3_b4_analysis_ledgers._validate_attempt` の既存 exact-rational / 正値検査の直後に
1 つだけ置き、`_ratio_payload` / `_ratio_from_payload` / `_manifest_row_payload` の
manifest codec には置かない。判定は「既約分母から 2 を割り切れるだけ割り、次に 5 を
割り切れるだけ割り、残りが 1」で、`p3_b4_raw_record_producer._fraction_token` と同じ手順を
**独立に**書く。共有 helper へ切り出さない。

`reference_tps` は schema 上 optional であり、非 `SCHEDULED` row では `None` が正当な値である。
述語は値が `None` でないときだけ評価する。

**択 A が実際に狭める面を、説明で過小にしない。** `_validate_attempt` は 3 箇所から呼ばれるため、
in-memory batch の hash、封印、外部 registry JSONL の読取、完全性検査、manifest 生成、
registry violation の追記と計数、contract binding の構築がすべて狭まる。
意図的に狭めないのは `load_analysis_manifest` 単独と `assert_manifest_unchanged_before_run` で、
非有限十進を含む単独 manifest は引き続き読める。完全な registry/manifest 組は registry を
先に読むため成立しない。

**述語の射程は「有限十進性の判定が一致する」までとし、「受理集合が完全に一致する」とは
主張しない。** `_fraction_token` は十進 token 化の最終段で整数から文字列への変換を行うため、
処理系の桁数上限という操作上の制約を追加で持つ。有限十進でも桁数上限を超える比は registry を
通り、publication で `EVIDENCE_SCHEMA` として落ちる。この残差は本決定では埋めない。

**理由:**

- `_ratio_payload` と `_ratio_from_payload` は registry と manifest の共用である。狭めると
  manifest 単独の reader/writer の wire 受理集合まで縮む。事前登録 §5.1.1 の純関数契約は
  `reference_tps` を「有限の正の exact rational」としており、三分の一はその条件を満たす。
  manifest transport がそれを運べなくなると、§5.1.1 が述べる入力値域と transport の能力がずれる。
- 狭まる面を過小に書かないのは、D1424 決定 4 が「registry only と説明しながら 4 境界を実装するな」
  と縛った禁止の対称である。説明と実装の食い違いは、どちらの向きでも同じ害を持つ。
- 独立実装を選ぶのは、producer 側防壁との故障独立性を保ち、producer を source closure の外に
  保ち、変更 scope を増やさないためである。共有 helper が必然的に adapter/contract の単一変換
  権威と結合するわけではない。
- 桁数上限を足さないのは、D1424 決定 4 が述語を名指しで指定しており、該当する比を生む producer が
  存在しないためである。名指しされていない第 2 の述語を実測なしに足すことになる。

**却下した選択肢:**

- **manifest codec も含めて 4 境界すべてを狭める** — manifest 単独 transport の受理集合が縮み、
  事前登録が述べる入力値域と transport の能力がずれる。
- **丸めて受理する** — 受理集合を広げ、凍結側が受け取る値を元の値と別物にする。D1344 が却下済み。
- **凍結された消費側を改訂して非有限十進を exact に運ぶ** — 支持する production 証拠が 0 件。
- **述語を adapter と contract が共有する単一変換権威へ置く** — 分析入力の値域の意味までずれる。
- **桁数上限の検査を同じ wave で足す** — 裁定が名指ししていない第 2 の述語であり、該当値を生む
  producer が存在しない仮想リスクである。

## {{D:m12-producer-side-redefinition}}. 受理集合を縮めた層より下の防壁は、縮小と同じ変更で下層の直接検査へ作り直す

**決定:** 上流の層で受理集合を縮めた結果、下流の防壁を検査していた既存テストがその防壁へ
到達しなくなる場合、**そのテストを上流の拒否期待へ移設してはならない。** 下層の実体を名指しする
直接検査へ作り直す。B-4 の M12 では次の二段にする。

1. 下層の実体 (`p3_b4_raw_record_producer._fraction_token`) を直接呼び、非有限十進に対して
   専用の例外を送出することを検査する。
2. 上流を通る正常な入力で下層の実体を差し替え、その例外が下層の拒否 code へ写ることを、
   artifact・field・code・detail の全項目で検査する。**差し替えが実際に呼ばれたことを
   assertion で固定する。**差し替えなしで成功する正例対照を同じテストに置く。

差し替え (monkeypatch) を使ってよいのは、正規の注入 seam が無く、かつ実体へ当該入力を届ける
経路が上流の検査で閉じていることを、呼出し元まで読んで確かめた場合に限る。

**理由:**

- 上流の拒否期待へ移すと、下層の分岐は一度も実行されなくなる。テストは緑のままだが、
  その緑は何も保証しない恒真な保証になる。これは絶対規律 2 に直接触れる。
- 差し替えの実効発火を固定しないと、下層の呼出しそのものを例外送出へ置き換える変異が
  検査を素通りする。差し替えが呼ばれたことの assertion は、上流が実際に下層を通ることの証拠でもある。
- 正例対照が無いと、差し替え以外の理由で拒否された場合と区別できない。

**却下した選択肢:**

- **上流の拒否期待へ移設する** — 下層の分岐が無検査になる。
- **下層の実体を再実装したものを検査する** — 実体を名指ししないため、両層を stub にしても緑になる。
- **上流の検査を緩めて実体へ入力を届ける** — 受理集合を広げることになる。
