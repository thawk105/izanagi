# 段 6 fix (2 巡目) 裁定 — [T-2288]

1 巡目で must-fix 1 と nit 1 は実装された (未実走)。**残るのは must-fix 2 だけ**である。
1 巡目の報告が挙げた 2 つの障害について、親が現物を読んで裁定した。

## 裁定 1 — 「期待 spec 列と summary を同時に 1 組落とす」負例は撤回する

**1 巡目の指摘は正しい。** 追補 (f) は「期待列が結果を見る前に選ばれたことは証明しない」と
明記しており、両方を落として閉包が一致する入力を拒否する根拠は契約に無い。
**この負例は要求から取り下げる。実装しないこと。** 代わりに何も足さない
(この境界は追補 (f) が人手の採用責任として既に書いている)。

## 裁定 2 — 既存 helper の monkeypatch は「迂回」ではない。使ってよい

**1 巡目の「較正 payload が `{}` なので正例にならない」という判断は採らない。**

`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` の `_synthetic_source` は、
`driver_tests._install_git` と `floor_pair_driver.calibration_verify.load_verified_calibration` を
monkeypatch する。**これは既存の issuer テストがすべて使っている定型の seam であり、
本 wave が検査する機構ではない。** 禁止した「stub や monkeypatch で本体を迂回する」とは、
**集約そのもの** (期待 spec 列の照合、窓・層・セル・標本の閉包検査、Fraction 最大の合成、
v2 の再構成比較、create-only 発行) を差し替えることを指す。

したがって **`_synthetic_source` と同じ seam を使って正例を組んでよい。**
較正と Git の seam は差し替えてよい。集約の関数は 1 つも差し替えてはならない。

## 残る作業 (must-fix 2)

`orchestrator/campaign/p3_b4_floor_artifact_issuer.py` と
`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` の 2 file だけを編集する。
docs・duration ledger・他 file は 1 文字も編集しない。commit も `git add` もしない。

### (A) 公開経路の正例を 1 つ作る — これが最優先

`_synthetic_source` を土台に、次を満たす合成入力を作れ。

- **3 つの spec。** workload が互いに異なる (例: `ycsb_rratio` が 5 / 50 / 95)。
  `env_tag`・protocol・threads は 3 つとも同じにする。
- **各 spec がちょうど 2 窓。** `driver_tests._valid_document` が返す document の `windows` は
  1 件なので、2 件目を足す。`statistics.closed_strata` と `pairs` / `cells` も、
  2 窓すべてを覆うように整合させる。
- **全セル被覆**と、**許容内の欠測**を含む。
- 3 つの summary を書き、`floor` の値は 3 つとも異なるようにする (最大がどれか一意に決まる)。

そのうえで、**公開 API を順に通す 1 本のテスト**を書け。

1. `issue_aggregate_authoritative_floor` で発行する。
2. `load_authoritative_floor` で読み戻す。
3. `resolve_preregistered_authoritative_floor` で §5 pin 経由の解決を通す。

assert すること — 返る `floor_exact` が **3 入力の最大**と exact に一致すること、
`schema_version` が v2 であること、3 入力すべての出所 (summary と spec の path・sha256) と
非保証欄が成果物に残っていること、成果物の path と sha256 が pin と一致すること。

**材料レポートまで届ける経路**は、既存 test が使う組立経路でそのまま届くなら加えよ。
合成 repo では届かせられないと判断したら、**理由を報告に書いて、そこで止めよ。**
届かない部分を「届いた」と書かない。

### (B) その正例を土台にした公開 API の負例を 4 つ作る

いずれも (A) の入力から 1 点だけ変え、無関係な hash・schema・自己整合は正しく更新して、
**狙った検査まで到達させよ。各テストで停止した error code を assert** せよ。

1. 期待 spec 列を固定したまま、対応する summary を 1 件落とす。
2. 発行済み成果物の `floor_exact` を非最大値へ替え、`source_float_hex` と外側 hash も整合させる。
3. 発行済み成果物から**非最大入力**の出所または非保証を 1 件落とし、外側 hash も整合させる。
4. 単体としては有効な入力のうち 1 件だけ identity (`env_tag` / protocol / threads のいずれか) を
   変え、**公開 API が集約全体を拒否する**ことを示す。

### (C) 既存を壊さない

既存テスト関数・fixture・decorator・期待値を変更・反転・緩和・skip・削除しない。
`issue_authoritative_floor` / `load_floor_pair_summary` / `_authority_value` / publisher の本文、
v1 定数、v1 成果物の bytes と命名、CLI の旧省略形を変えない。
n = 62 と 24 時間分離を機械検査しない (追補 (f))。
実文書 `docs/phase3-b4-reflux-ablation-preregistration.md` を読むテストを新設しない。

### (D) 実走

`PYTHONPATH=. python3 -m pytest orchestrator/tests/test_p3_b4_floor_artifact_issuer.py -q` が
hook に拒否されるなら、**それは想定内である。** exact command と拒否理由を書き「未実走」と
正直に書け。親が実走する。実走できないことを理由に (A)(B) を作らないのは不可である。
**作ることと走らせることは別である。**
