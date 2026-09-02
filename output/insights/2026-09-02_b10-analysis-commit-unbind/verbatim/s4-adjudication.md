# 段 4 裁定 — B-10 事前登録束縛から analysis_commit による再開拒否を外す

段 2 プラン 1 本、段 3 独立検査 2 本 (レンズ A = 正しさ境界、レンズ B = 整合と実効性) を裁定する。
裁定 inbox (`docs/spool/`) は wave 開始後も空であり、取り込む更新はない。

## 所見 A-1 — 「analysis_commit の除去が解析・検証コードの閉包束縛を失わせる」

**判定: 大部分 refuted。残余は real だが scope 外。**

レンズ A は「`analysis_code_sha256` が覆うのは 1 file だけなので、除去後は別の parser・
安定性判定・verifier の結果が同じ campaign / report に混ざる」と主張した。親が現物で確認した。

- 再開時に `ident.verify_against_lock` (`orchestrator/campaign/ident.py:385-396`) が、
  campaign.lock に記録された contract-loader 束縛を**現在の disk bytes と内容ハッシュで再検証**する
  (`orchestrator/campaign/contract_loader_binding.py:363-382`)。
- その閉包 `CONTRACT_LOADER_RELATIVE_PATHS` (`orchestrator/campaign/campaign_lock.py:49-74`) は
  24 path で、`pipeline.py`、`loop.py`、`wal.py`、`ident.py`、`artifact_admission.py` と
  `orchestrator/verifier/` 一式 (`core.py`/`dsg.py`/`model.py`/`parse.py`/`__init__.py`/
  `report.py`/`commit_receipt.py`) を含む。
- B-10 はこの経路を通る。`loop.py:406` が `ident.ensure_resumable_wal` を呼び、
  同関数は `ensure_campaign_identity` (`ident.py:482-486`) 経由で上記検証に到達する。
  `require_environment_contract` の既定は `True` で (`ident.py:353`)、無効化するのは
  `guided.py:196,222` だけであり B-10 は該当しない。

よって「verifier の受理集合が違う結果が混ざる」経路は**既存の内容ハッシュ機構が既に塞いでいる**。
`analysis_commit` はその役目を担っていない。

**残余 (real):** 閉包外にあるのは `orchestrator/calibrator/benchparse.py` と
`orchestrator/calibrator/analyze.py` の 2 file である。これらは correctness certification ではなく
throughput の読み取りと安定性判定に効く。

**scope 外とする理由:**

1. 塞ぐには閉包の拡張という**新しい gate** が要る。ユーザー引数が
   「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示している。
2. `analysis_commit` を残すことは代替にならない。それは「現行コードとの差だけを単独の拒否理由に
   する」ことそのものであり、絶対規律 7 と D1163 が禁じる形である。しかも repo 全体の任意の
   commit を拒否するので、防ぎたい 2 file の変更に対して過剰であり、かつ無関係な commit を
   全部巻き込む。D1163 は「現行 closure との一致は verifier が有効であることを証明しない。
   変わったことしか示さず弱くなったことを示さない」と明記している。
3. 事前登録文書 §1 が要求する束縛に analysis_commit は含まれない。除去は事前登録に反しない。

**扱い:** 段 7 で裁定パッケージとしてユーザーへ返す。本 wave では実装しない。

## 所見 A-2 — 「テスト計画が上記の正しさ境界を検査しない」

**判定: 採用しない (must-fix でない)。**

A-1 が scope 外になったため、その境界の検査も本 wave の scope 外である。加えて、
その境界を守っているのは本 wave が一切触れない既存機構 (contract-loader 束縛) であり、
本 wave の変更で受理集合が変わらない。`DW-G05` に従い、成果物の値・受理集合・参照が
どう変わるかを示せないため must-fix にせず、追加 review も起動しない。

レンズ A が「予定 negative predicate は恒真ではない」と確認した点は採る。

## 所見 B-1 — 行番号を固定した台帳テストの取り残し

**判定: real、採用、scope 内 must-fix。**

`orchestrator/tests/test_ccbench_spawn_sites.py` の `_DEFERRED_GATE_MEMBERS` (`:817-833`) が
`orchestrator/campaign/b10_backoff_shape_sweep.py` の **2518 行 (`_build_binary`)** と
**2914 行 (`run_formal`)** を整数で固定し、`test_deferred_gate_ledger_is_exact_and_every_entry_
names_a_live_sink` (`:1961-2021`) が exact 集合として突き合わせる。3 行削除すると 3 行ずれて赤になる。

**成果物影響:** 全体検査が変更を受理せず、その revision からレポート・台帳を確定できない。

**裁定:** 編集面に `orchestrator/tests/test_ccbench_spawn_sites.py` を**加える**。
行位置を人工的に保つ (空行・ダミーコメントで埋める) 方法は採らない — 削除の意図が読めなくなり、
次の編集で同じ罠を再生産する。台帳の 2 整数を実際の行位置へ更新する。
これは scope 拡大ではなく、同一変更の consumer 側である。

## 所見 B-2 — 過去 row の commit provenance をどこまで認証するか

**判定: 選択肢 A (単純除去) を採用。選択肢 B は scope 外で裁定パッケージへ。**

除去後、validator は row の `source_commit` / `analysis_commit` を receipt や歴史 blob へ
結び直さない。ただし現行の比較も row の値を receipt と照合しておらず、単に現行 HEAD と
比べているだけなので、**現行実装も provenance の真正性を高めていない**。
receipt bytes の hash 一致検査 (`b10_backoff_shape_sweep.py:2414-2425`) はそのまま残る。
選択肢 B (歴史 row の commit 値を保存 receipt へ束縛) は新しい検査とテストを伴う scope 拡張である。

## プラン v2 (確定)

段 2 プランの 3 除去をそのまま採用し、次を加える。

1. `orchestrator/campaign/b10_backoff_shape_sweep.py:213-222` — `core()` から
   `"analysis_commit"` の 1 行を削除。dataclass field・形式検査 (`:191-211`)・
   現行 HEAD の記録 (`:1387-1395`) は残す。
2. 同 `:2386` — `row.get("analysis_commit") != prereg.binding.analysis_commit` の 1 行を削除。
3. 同 `:2388` — `row.get("source_commit") != prereg.binding.analysis_commit` の 1 行を削除。
4. **(追加)** `orchestrator/tests/test_ccbench_spawn_sites.py` の `_DEFERRED_GATE_MEMBERS`
   (`:817-833`) と exact 台帳 assert (`:1970-1976` 付近) の行番号 2518 / 2914 を、
   削除後の実際の行位置へ更新する。両方に同じ値を書く。
5. テストは段 2 のテスト計画どおり `orchestrator/tests/test_b10_backoff_shape_sweep.py` へ
   追加する。digest literal をテストへ焼き込まず、等値 / 不等値で検査する。
   受理後の row に旧 `analysis_commit` と旧 `source_commit` が残ることも assert する。

**維持する不変条件 (子への禁止事項として個別に列挙する):**

- `analysis_code_sha256`、`spec_sha256`、`patch_sha256`、`formula_sha256`、`prereg_commit`、
  `prereg_blob_sha` を `core()` から外さない。
- 解析 bytes と現行 HEAD blob の照合 (`:1378-1385`) を消さない・緩めない。
- `prereg_commit` の祖先検査 (`:1348-1354`) を消さない・緩めない。
- submission receipt の `source_commit` と現行 HEAD の照合 (`:466-472`) を消さない。
  これは投入 receipt と実行 checkout の対応づけであり、過去 WAL の無効化ではない。
- correctness gate、`docs/b10-backoff-shape-preregistration.md`、
  `tools/pegasus/` 配下、`contract_loader_binding.py`、`campaign_lock.py` を変更しない。
- 上記 3 file 以外を編集しない。互換層・移行機構・新しい gate・台帳を足さない。

## 変異事前登録

`s4-mutation-preregistration.md` に分けて記す。

## 実装しないと裁定したもの

- A-1 の残余 (`benchparse.py` / `analyze.py` を内容束縛の閉包へ入れるか) — 裁定パッケージ。
- B-2 の選択肢 B (歴史 row の commit provenance 認証) — 裁定パッケージ。
