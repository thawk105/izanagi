# 段 4 裁定 追補 1 (erratum-1) — 段 5 の停止を受けた列挙の更新

**正本の関係:** `stage4-ruling.md` は凍結し、本書が追記で訂正する。衝突したら**本書が優先**する。

**発生:** 単位 A の実装子が fail-closed で停止した (差分ゼロ)。停止理由は 2 件で、
**いずれも親の裁定の欠陥である。実装子の判断は正しい。**

1. 裁定 §2.1 は `verify-deps` の廃止を命じたが、§6 の「既存テストの期待値を反転・緩和・skip・
   削除しない」と衝突した。単位 A が所有する
   `orchestrator/tests/test_pegasus_thirdparty_fetch.py` に `verify-deps` の成功と shallow 受理を
   要求する node が 4 つある (`:749`, `:814`, `:841`, `:848`)。
2. **裁定 §2.3 の consumer 列挙が 134 commit 分古かった。**
   列挙後に main が進み、`orchestrator/campaign/b4_binary_record.py:68-83` が
   `verify-deps` を実際に呼ぶ consumer として着地していた。同 file は
   `prepare_dependencies()` で gflags / glog を旧 locator から解決して build し、
   3 依存だけを `hydrate` している。

---

## (1) `verify-deps` は予定どおり廃止する。その test の削除を明示的に許可する。

**命令そのものを消す以上、その命令の test を残せない。これは「生き残る挙動の期待値を緩めること」
ではないので、§6 の禁止には当たらない。**

- 削ってよいのは `test_pegasus_thirdparty_fetch.py` の **`verify-deps` を呼ぶ node だけ**
  (`:749`, `:814`, `:841`, `:848` とその fixture 専用 helper)。
- **同 file の他の node は 1 つも削らない。** 既存 3 依存の `fetch` / `hydrate` / `verify` の検査は
  全部残す。
- `allow_shallow=True` を許す経路が消えることは**受理集合の縮小**であり、意図した変更である。
  報告にそう書く。

**採らない案:** 「`verify-deps` を hydrate 済み source の検証へ再定義する」。
`verify` が cache の 5 本を既に見るので重複であり、旧名を残すと経路が 2 本あるように読める。

## (2) consumer 列挙を現行 main (`d97c423bd`) で採り直した。追加は 3 file。

| file | 単位 | 理由 |
|---|---|---|
| `orchestrator/campaign/b4_binary_record.py` | **C** | `verify-deps` を呼び、旧 locator から gflags / glog を build する |
| `orchestrator/tests/test_b4_binary_record.py` | **C** | 上の契約テスト |
| `orchestrator/tests/test_hooks.py` | **A** | `_FETCH_THIRD_PARTY_SANCTIONED_SPELLINGS` (`:3024-3029`) に `verify-deps` の字面がある。命令を消す単位が同時に消す |

`hooks/` 配下と `.claude/settings*.json` に `verify-deps` の字面は**無い** (親が実測)。
機械防壁の配線は触らない。

## (3) `b4_binary_record.prepare_dependencies()` の付け替え方 (単位 C)

`verify-deps` → build → `hydrate`(3 本) の順を、**`hydrate`(5 本) → build** へ変える。
gflags / glog の source は `<staging-root>/gflags` / `<staging-root>/glog` になる。

**変えないもの:** `cache_root` 必須の検査、`_helper_failure` の診断文、
`_install_dependency` の argv、`prefix` の作り方、`compilers_for_current_site()` の呼び。

## (4) 期待赤の更新

単位 A 実装後、B / C 着地までに赤になる test file に
**`orchestrator/tests/test_b4_binary_record.py`** を加える (計 6 file)。
`test_hooks.py` は単位 A が同時に直すので**赤にしない**。

## (5) 変異事前登録への影響

**無い。** M1〜M7 はいずれも成立したままである。M3 の単一理由性の根拠
「旧 `verify-deps` を廃止済みなので shallow を許す層は他に無い」は (1) によって維持される。
golden (§2.2) も変わらない — `policy.json` の変更は 2 行のままである。

## (6) 親の手順の誤りとして記録する (段 8 候補)

**consumer 列挙を段 1 で採ったまま段 5 まで持ち越してはならない。**
本 wave では段 1 から段 5 の間に main が 134 commit 進み、その中に新しい consumer
(`b4_binary_record.py`) が着地していた。段 5 の投入直前に列挙を採り直すべきだった。
