# [T-663] / F57 launcher フレークの診断計装 — 一次資料

wave `dev-wave-t663-flaky-truth-table` (2026-08-09) の逐語と台帳。

## 何をしたか

`test_codex_worker_launch.py` の受入全走限定フレーク (F57) について、
**次の再発時にどの受理 conjunct が落ちたかを観測できるようにした**。
原因そのものは確定していない。フレークが直ったとも主張しない。

## 段 1 の実測 (親)

| 観測 | 値 |
|---|---|
| 成功期待テストの launcher 実所要 (login node、receipt 84 件) | min 0.254 / median 0.428 / p90 0.671 秒 |
| 既定 wall 予算 | 3.0 秒 |
| evidence grace / termination grace / poll | 1.0 / 0.05 / 0.01 秒 |
| 単独 file を計算ノード 32 並列で走らせた結果 | 64 passed (再現しない) |
| 既定 wall を 0.30 秒へ縮めた probe | 19 failed / 45 passed、署名が F57 台帳と完全一致 |

失敗署名 `assert 1 == 0` / stdout・stderr 空は、production `accepted` の
**7 条件のどれが欠けても**出る。区別する receipt は pytest tmp とともに失われる。
これが F57 の「未確定」の正体である。

## 撤回した主張 (段 3 が倒した)

- 「evidence grace の余裕が薄い」は比較対象の取り違え。evidence deadline は
  session/rollout の発見までの期限で、親は完了後の総 `wall_clock_s` と比べていた。
- 「0.30 秒 probe が機序を確認した」は**正の対照にすぎない**。実障害の原因が予算超過であることは
  示さない。

## 段 4 の核心裁定

**時間予算を一切広げない。** 段 2 プランの wall 3→6 / evidence 1.0→2.0 /
termination 0.05→0.2 / harness timeout 10→20 は全面不採用。レンズ A が 4 拡大すべてに
「拡大後だけ通る具体的回帰」を構成した。計装が先、値の変更は実 artifact の後。

## 診断の実効 (probe で実演)

従来 `assert 1 == 0` としか出なかった場所に、次が出るようになった。

```
truth_summary: outcome='not_accepted' stop_reason='max_wall_clock_s' launcher_rc=1;
attempt[1] accepted=False failed_predicates=["limit_trigger"]
```

## 計装自体の負荷依存 (F9) — 発見と修正

fix 1 巡目の wiring meta-test は実 launcher が rc=0 を返す前提で `pytest.raises` を書いていた。
**観測したいフレークが発火した瞬間に `DID NOT RAISE` で落ちる**設計だった。
親が 0.30 秒 probe で決定的に再現し (23 failed / 56 passed)、
実 launcher を走らせる meta-test 7 呼び出しを「起こりえない期待 rc」へ統一して解消した
(同 probe で `DID NOT RAISE` 0 件、診断 meta-test の赤 0 件、16 failed / 58 passed)。

## 変異 matrix

事前登録 3 本すべて KILLED、観測 node は事前登録と完全一致、baseline 緑。

| ID | 変異 | 赤くなった node | 種別 |
|---|---|---|---|
| M1 | `codex_exit_code` を常に 0 | 新 meta-test 1 本のみ | diagnostic sensitivity pin |
| M2 | `validator_rc` を常に 0 | 新 meta-test 1 本のみ | diagnostic sensitivity pin |
| M3 | `_evidence_status` の missing 判定を殺す | 新 1 本 + 既存 2 本 | 実効 kill |

**DW-M08 の新旧両走はこの 1 走で満たしている。** M1 / M2 の走行では既存テストが全て同席して
緑のままであり、赤くなったのは新 meta-test だけである = 変更前の検出面はこの 2 変異を
検出しない。M3 は新旧どちらの面でも検出する実効 gate である。

## ファイル

- `brief.md` — 段 1 brief (一部は段 4 で撤回済み)
- `s2-plan.md` / `s2-prompt.txt` — 段 2 プラン起草
- `s3-lensA*.{md,txt}` / `s3-lensB*.{md,txt}` — 段 3 敵対相談 (正しさ境界 / 実効性)
- `s4-adjudication.md` — 段 4 裁定 (**正本**)
- `s5-impl*.{md,txt}` — 段 5 実装
- `s6-R1*` / `s6-R2*` — 段 6 敵対レビュー (どちらも NO-GO)
- `s6fix*` — 段 6 fix (1 巡目は親の手順ミスで消失、2 巡目が採用版)
- `mutation-spec.json` / `mutation-ledger.json` — 変異 matrix
