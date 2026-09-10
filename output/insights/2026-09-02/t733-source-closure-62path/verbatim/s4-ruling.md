# 段 4 裁定 — [T-733] enforcement source closure の推移閉包化 (第 1 層)

親が段 2 プランと段 3 の 2 レンズを裁定し、実装するプラン v2 を確定する。

## 1. 閉包の寸法 — (P1) は反証、exact 62 path とする

- **親の (P1)「1 段目 30 path、合計 54」は refuted。** 親の測定 script が
  `from ..calibrator import runner` 形の 2 階層相対 import を解決し損ねて 6 本を落としていた。
  親が script を直して再測し 36 を確認済み。
- **段 2 の「明示 import 36、合計 60」も不十分。** レンズ A / B が独立に同じ 2 本を挙げた。
  Python は `orchestrator.critic.online_digest` を読む前に `orchestrator/critic/__init__.py` を、
  `orchestrator.qualification.artifacts` を読む前に `orchestrator/qualification/__init__.py` を
  実行する。両 file とも実際に再輸出を行うコードであり、差し替えれば挙動が変わる。
  既存 24 path に `orchestrator/verifier/__init__.py` が入っている先例とも整合する。
- **親の独立確認:** 最上位 `orchestrator/__init__.py` は存在しない (namespace package)。
  したがって package 初期化の追加はこの 2 本で閉じる。
- **確定: 新規 suffix は 38 path、合計 exact 62 path。未収載は 69 module。**
  first-party import 推移閉包 131 module は両レンズが独立に再導出して集合差ゼロ。

## 2. 並び順

既存 24 path は 1 本も並べ替えない。これは `artifact_admission.py` の epoch preimage が
tuple 順に path と digest を連結するためである。新規 38 path は末尾へ
**repo-relative path の辞書順**で追加する。

## 3. 保証の文言 — 段 2 の案は採らない

D1075 は「保証の文言は閉包が閉じるまで広げない」と命じている。次の文言を採る。

`CAMPAIGN_VERIFIER_EPOCH_SCOPE`:

> enforcement source closure (curated exact 62 path; 2026-09-01 の静的 import 発見集合 131 module のうち、
> 既存 24、明示 import 先 36、実行時 package 初期化 2 を収載; source-import 推移閉包ではない)

`CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE`:

> 同発見集合の未収載 69 module、orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、
> package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、外部 command/Git、
> toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり、完全性を主張しない

- 「推移閉包が閉じた」と読めてはならない。
- D1128 の限界 (判定器自身が閉包の内側にある) を隠す文言にしない。
- 非 import 委譲の列挙は**例示であって全件ではない**と扱う。段 2 とレンズ A が挙げた個別の
  data file / 外部 Git の一覧は、完全一覧として文言へ焼かない。

## 4. real と裁定した所見 (実装する)

1. **package 初期化 2 本の収載** — 上記 1 のとおり。
2. **`test_t671_source_binding.py:38` の開いた slice** —
   `_RECEIPT_IMPLEMENTATION_PATHS = _EXPECTED_ENFORCEMENT_SOURCE_PATHS[19:]` は終端が無いため、
   末尾追加すると新規 38 path が receipt 実装面へ紛れ込む。親が現物で確認済み。
   pre-T733 の 24 本 tuple から `[19:24]` 相当で作り直す。
3. **epoch oracle が独立 known-answer でない (レンズ B 所見 3)** —
   `test_artifact_admission.py:426-437` の期待 E1 は fixture literal から再導出しており、
   production tuple と test literal を同時に並べ替えると検査が追随して緑になる。
   **固定 known-answer を 1 つ足す。** 具体値は子が計算した数字を使わず、
   **親が実装後に自分で計算して pin する。**
4. **保証文言の縮小** — 上記 3 のとおり。

## 5. real だが本 wave では実装しない (裁定パッケージへ返す)

1. **旧 exact-24 map の lock が decode 不能になる。**
   - 親の再測 (2026-09-01): 外部永続 root の campaign lock は **11 件すべてが現行 exact-24 map**。
     内訳は B10 backoff grid 3 件、paper-story A2 certification 8 件。
     レンズ B が引用した「5 件」は古く、正しくは 11 件である。
   - ただし **これは本 wave が新たに作る回帰ではない。** 旧 grammar の拒否は
     `test_campaign_lock_codec.py` が `exact 2 path` と `exact 12 path` について
     すでに名前付きテストで固定している、過去の閉包拡張から一貫した意図的挙動である。
     どの大きさへ広げても同じ代償が出るので、段階の切り方の問題でもない。
   - **親の追加実測: repo 内の consumer とテストは、この 11 件を decode 経由では読んでいない。**
     `test_b10_extended_figure_provenance.py` は外部 source を file bytes の SHA-256 で束縛しており
     (`_sha256(MEASUREMENT_ROOT / relative) == expected`)、`campaign_lock` の decode を通さない。
     したがって受入全走は赤にならず、図の再生成も壊れない。失われるのは
     admission API 経由でこの 11 件を読み直す能力である。
   - **裁定: 実装しない。** 歴史 grammar registry (旧 8/12/14/25/27/24 を `HISTORICAL_RAW` だけで
     読む versioned decoder) は新しい機構であり、受理集合を変えるので、ユーザー裁定が要る。
   - **したがって、段 2 が提案した「pre-T733 exact-24 map を拒否するテストの新設」は採らない。**
     裁定待ちの方針を先に凍結してしまうためである (レンズ B の警告を採用)。
     既存の exact-2 / exact-12 拒否テストが、後述の変異 3 を十分に KILL する。
2. **qualification schema の live bytes が別 binding で閉じていない** (レンズ A 所見 5)。
3. **非 import 委譲一般 (外部 Git、toolchain、binary、data/schema) の包括的 binding。**
4. **同一 `campaign-verifier-epoch/v1` domain が複数の path grammar を指す意味互換問題。**

## 6. refuted と裁定した所見

- **凍結 3 点の再生成は不要。** F712 の恒久対応どおり現行 golden と凍結 golden が分離されており、
  fig2b / fig2c / fig4 の provenance JSON、PNG、PDF はいずれも据え置く。両レンズが独立に確認。
- **新規 38 path で capture が常に失敗する、という懸念。** 38 file すべて tracked、HEAD blob あり、
  regular file、readable。親も untracked 0 件を確認済み。
- **推移閉包 131 の測定自体の誤り。** 両レンズが独立に再導出して集合差ゼロ。
- **`autonomous_trial_completeness.py` は producer** という段 1 の分類は誤りで、比較器が正しい。

## 7. 親 brief 自身の誤り (訂正して記録する)

1. 1 段目フロンティア 30 は誤り。正しくは明示 36、実効 38、合計 62 path。
2. 「閉包の成長は受理集合を狭める方向だけ」は誤り。exact key 集合の検査は旧集合から
   新集合への**非互換な置換**であり、旧 map を拒否する一方、旧コードが拒否した新 map を受理する。
   規律 2 の意味での弱体化ではないが、「狭まるだけ」とは書けない。
3. 「authority = null」は wire 上不正確。正しくは「schema-less v1 で authority key が無く、
   decode 後に `authority is None` になる」。
4. 「失効する certified campaign は 0 件」は repo 内 tracked 32 件に限れば正しいが、
   既存成果物一般への一般化は誤り。外部に 11 件ある。
5. producer 一覧から `tools/plotting/plot_s1_9pair.py` と `tools/plotting/plot_backoff.py` が漏れ、
   `guided.py` が critic text の実 consumer である点も落ちていた。

## 8. 分割方針

Codex `role=author` 1 子。tuple、epoch preimage、scope golden が密結合しており、
production と test を分けると suffix 順序と count の不一致を作りやすい。

## 9. 変異事前登録 (DW-M01)

実装前に登録する。各変異は production だけを変異させ、test literal は同時に変えない。

| # | 変異 | KILL するテスト | 単一理由性 |
|---|---|---|---|
| M1 | production tuple から `orchestrator/calibrator/runner.py` を落とす | `test_t671_source_binding.py` の exact tuple 検査 (独立 literal 側は変えない) | 前後に同じ入力を拒否する層は無い |
| M2 | clean binding 取得後に `orchestrator/campaign/buildcache.py` へ 1 byte 足す | `test_t671_source_binding.py` の全 member live drift 検査 (`contract-loader-drift`) | literal 一致ではなく disk/commit blob 差を見る |
| M3 | `_validate_authority` の exact key 集合検査を subset 許容へ緩める | 既存 `test_v2_rejects_legacy_exact_two_source_blob_keys` と `test_v2_rejects_pre_wave_exact_twelve_source_blob_keys` | 新設テストを足さずに既存で KILL する |
| M4 | `verify_live_contract_loader_binding()` の loop を `CONTRACT_LOADER_RELATIVE_PATHS[:-1]` にする | 辞書順 suffix 末尾 path を dirty にする live drift case | loop の実効性を直接見る |
| M5 | production tuple の新規 38 path のうち 2 本を入れ替える (test literal は据え置き) | 上記 3 の固定 known-answer E1 と ordered-list SHA | key 集合が同じでも順序差を検出する |

**受理集合を縮小する wave なので、承認外の過剰拒否を検出する正例も登録する (DW-M01)。**

| # | 正例 | 通ることを要求するテスト |
|---|---|---|
| P1 | 新しい exact-62 map を持つ lock が decode でき、E1 epoch を発行する | `test_campaign_lock_codec.py` の v2 decode 正常系 / `test_artifact_admission.py` の E1 経路 |
| P2 | authority を持たない schema-less v1 lock が E0 として現行どおり扱われ、`HISTORICAL_RAW` で読める | `test_artifact_admission.py` の E0 / HISTORICAL_RAW 経路 |

## 10. 不変条件 (実装子への拘束)

- 規律 2 を緩めない。anomaly 検出時の即 reject を変えない。
- 凍結成果物 (fig2b / fig2c / fig4 の PNG / PDF / provenance JSON) の bytes を変えない。
- 既存 24 path の並び順を変えない。
- `_CAMPAIGN_VERIFIER_EPOCH_DOMAIN` (`campaign-verifier-epoch/v1`) を変えない。
- `_require_verifier_epoch_for_purpose` の D1163 挙動 (certified では current closure の
  可用性だけを要求し、記録 closure と現行 closure の bytes 差を拒否しない) を変えない。
- 閉包の正本を静的 AST 解析器にしない (D368)。curated exact tuple のままとする。
- 歴史 grammar decoder を作らない。pre-T733 exact-24 の拒否テストも新設しない。
- gate・検査・台帳・一般化を本題の外へ広げない (ユーザー明示の scope 外)。
