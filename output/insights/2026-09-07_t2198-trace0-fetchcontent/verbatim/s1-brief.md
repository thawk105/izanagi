# 段 1 brief — [T-2198] A-2 / A-6 認証経路の測定 build をオフライン依存へ配線する

## 確定済みユーザー裁定 (覆さない)

- **D1693** (2026-09-07 /rulings 第 12 回、推奨どおり): D1688 の**案 1** を採る。
  `trace0_cmake_argv.configure` へ FetchContent の枠を**厳密な期待値として**足し、
  `orchestrator/tests/test_paper_story_a2_certification.py` の golden 4 値 (5 箇所) を張り直す。
  過去の認証値は取り直さない (絶対規律 7)。過去の結果と現行 policy の `protocol_sha256` が
  一致しなくなる旨を成果物へ明記する。**文法を緩めて余分 token を許す案 3 は採らない。**
- **D1524**: 認証経路の build は共有経路へ引数を通してオフライン依存へ配線する。
- **D1689**: 共有経路へ通す引数は 5 本 (source dir 3 + `fetchcontent_base_dir`
  + `fetchcontent_dependency_receipt`)。`buildcache._build_v2_impl` の同値条件により 4 本では必ず失敗する。
- **D1690**: v2 build identity が FetchContent 依存内容を完全束縛しない件は本 wave では是正しない。

## 引数の前提のうち、現行 main で反証されたもの (段 4 で再裁定する)

依頼文と F808 は「`run_campaign` は FetchContent の source dir を受け取る引数を持たない
(`buildcache` 側には既にある)」と書くが、**これは現行 main では偽である。**
`orchestrator/campaign/loop.py:240-251` の `run_campaign` は既に 5 引数すべてを持ち、
`:562-571` で `pipeline.evaluate` へ、`pipeline.py:1298-1307` で `buildcache` へ素通ししている
(commit `466528512` "feat(t2356): 段 4 loop の事前構築成果を driver が消費する seam を通す" で着地)。
**裁定 (D1524 / D1693) の効力は変わらない** — 残っているのは「認証経路の呼び手が 5 引数を渡していない」
ことと「閉じた trace0 文法が FetchContent token を拒否する」ことの 2 点であり、D1688 が
`indeterminate` の真因と名指ししたのは後者である。**共有 pipeline の横断改修は不要になり、scope は縮む。**
F808 の当該行と D1524 の理由節は段 7 で追記訂正する (絶対規律 7、追記のみ)。

## scope (成果物影響 = DW-G05)

放置すると A-6 read-heavy は `indeterminate` のまま、paper-story §8 は「未取得」で確定し、
read-heavy の正しさは機序論証の外挿のまま残る。本 wave は次の 5 点だけを実装する。

1. **文法拡張**: 両 policy JSON の `trace0_cmake_argv.configure` へ FetchContent の枠を厳密に追加し、
   `_TRACE0_CONFIGURE_ARGV_KEYS` と policy 読込の exact 検査、`_exact_trace0_configure_argv` の
   `expected` 組み立てを対応させる。
2. **認証経路の 5 引数配線**: `run_workload` が staged 依存を検証して `run_campaign` へ 5 引数を渡す。
3. **条件 gate の配線**: `_condition_gate_family_context` の `prepare_masstree_fetchcontent` と
   `condition_meaning_gate.capture_define_inputs` を staged source 経由にする (F808 が実際に落ちた地点)。
4. **golden 張り直し**: 4 値 (5 箇所)。
5. **成果物への明記**: 過去の認証結果と現行 policy の `protocol_sha256` が一致しなくなる旨。

**scope 外**: 共有 pipeline の新規引数追加 (既に在る)、build identity の強化 (D1690)、
仮想リスク向けの gate・検査・台帳・一般化の新設、`post_oracle_dependency_binding` 経路の導入。

## 不変条件

- **規律 2 を緩めない。** 文法は閉じたまま。`list(argv) != expected` の全一致判定を維持し、
  余分 token を許す緩和・部分一致・`startswith` による受理拡大を入れない。
- **走らせた argv と記録した argv を一致させる。** 記録前に token を除去しない (provenance 偽造)。
- 過去の認証値を取り直さない。旧結果は旧 hash に束縛したまま残す。
- `_protocol_preimage` の構成 key は変えない (`trace0_cmake_argv` の中身だけが動く)。
- policy JSON は 2 本 (A-2 / A-6) を同じ形に揃える。片方だけ変えない。

## 変更面 (実アンカー)

| # | file:anchor | 役割 |
|---|---|---|
| 1 | `orchestrator/campaign/paper_story_a2_certification.v2.json` `trace0_cmake_argv.configure` | 文法本体 (A-2) |
| 2 | `orchestrator/campaign/paper_story_a6_certification.v2.json` 同上 | 文法本体 (A-6) |
| 3 | `orchestrator/campaign/paper_story_a2_certification.py:123` `_TRACE0_CONFIGURE_ARGV_KEYS` | key 集合 |
| 4 | 同 `:418-460` policy 読込の exact 検査 | 新 key の型・非空・非空白・一意検査 |
| 5 | 同 `:2091-2142` `_exact_trace0_configure_argv` | `expected` 組み立て |
| 6 | 同 `:3467-3477` `run_campaign` 呼出し | 5 引数配線 |
| 7 | 同 `:585-625` `_condition_gate_family_context` | 条件 gate の offline 化 |
| 8 | `orchestrator/tests/test_paper_story_a2_certification.py:1768-1772, 1852-1855` | golden 4 値 5 箇所 |
| 9 | 参照 (読むだけ) `orchestrator/campaign/s8b_floor_campaign.py:2572-2640, 3404-3435` | staged 依存検証の既存手本 |
| 10 | 参照 (読むだけ) `orchestrator/campaign/buildcache.py:1922-2005` `_v2_commands` | 実際に出る argv の権威 |

## 実測した argv の形 (`_v2_commands`、`post_oracle_dependency_binding` 無しの v2 経路)

```
[cmake, -S, <src>, -B, <bdir>,
 -DCMAKE_BUILD_TYPE=Release, -DENABLE_SANITIZER=OFF,
 -DCMAKE_C_COMPILER=<cc>, -DCMAKE_CXX_COMPILER=<cxx>,
 -DCMAKE_PREFIX_PATH=<prefix>,
 -DFETCHCONTENT_BASE_DIR=<base>,
 -DFETCHCONTENT_SOURCE_DIR_MASSTREE=<m>, -DFETCHCONTENT_SOURCE_DIR_MIMALLOC=<i>,
 -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=<g>,
 <controlled defines ... -DCCBENCH_TRACE=0 最後>]
```

`-DFETCHCONTENT_FULLY_DISCONNECTED=ON` は `post_oracle_dependency_binding` を渡したときだけ出る。
`pipeline.evaluate` はこれを渡さないので、**本経路では出ない。文法へ入れない**
(出ない token を期待値に入れると全 cell が拒否される)。source dir 3 本の順序は
`buildcache._FETCHCONTENT_SOURCE_NAMES = ("masstree", "mimalloc", "googletest")` の固定順。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 文法の表現形。** 親案: `fetchcontent_base_dir_argument` (= `-DFETCHCONTENT_BASE_DIR=`) と
  `fetchcontent_source_dir_argument_prefix` (= `-DFETCHCONTENT_SOURCE_DIR_`) +
  `fetchcontent_source_dir_names` (= 順序付き 3 名) の 3 key を足し、`expected` は
  `fixed + prefix + [base] + [source 3 本] + ordered_define_tokens` とする。
  攻撃点: token を素の literal 配列で持つ方が「厳密」に近いか。名前を policy に持たせると
  buildcache 側の定数と二重管理になり、食い違ったとき文法が黙って通してしまわないか。
- **(P2) staged 依存の供給元。** 親案: `run_workload` へ `--third-party-source-root` を足し、
  `<root>/{masstree,mimalloc,googletest}-src` を検証して使う。永続 cache
  `/work/1/SFC/tanab/izanagi-thirdparty-cache` は `<name>` (末尾 `-src` 無し) 配置、
  `fetch_third_party.py hydrate` は `<staging>/<name>` 配置、`s8b_floor_campaign` は
  `<base>/<name>-src` 配置で **3 つの綴りが併存する**。どれを認証経路の契約にするかは
  実在 path で決める。qsub env key を増やすなら `_QSUB_ENV_KEYS` の exact 集合も動く。
- **(P3) `fetchcontent_dependency_receipt` の作り手。** `buildcache._observe_fetchcontent_dependency_receipt`
  は build 側の観測器である。認証経路が build 前に receipt を用意する正しい経路がどれか
  (`prepare_masstree_fetchcontent` の戻り値か、独立観測か) を実コードで確かめる。
- **(P4) 条件 gate の扱い。** `capture_define_inputs(configure_args=...)` は trace0 文法の対象外だが、
  ここが F808 の実際の落下点である。offline 化しないと read-heavy は依然 1 件も測れない。
  scope に含める前提でよいか。

## 成果物の形

コード + テスト (実装子)、policy JSON 2 本、golden 5 箇所、insight (逐語・変異台帳)、
spool fragment (worklog / decisions / failures)。変異 matrix と受入全走は免除しない。

## 分割方針

実装は 1 単位 (文法と配線が同じ argv 契約を共有するため分けると食い違う)。
段 2 プラン 1 本、段 3 敵対相談 2 本 (レンズ A = 文法の証明力と受理集合、
レンズ B = 実行経路の実在性と staged 依存の綴り)、段 5 実装子 1 本、段 6 レビュー 2 本。

## 条件 dispatch の成立

`DW-O08` (freeze / proof chain)、`DW-O09` (凍結 bytes の pin 閉包)、`DW-O10` (producer write-path)、
`DW-O13` (exact 述語の改訂 = 受理形の新設) が成立。`DW-O09` の pin 閉包実測: 4 hash を repo 全体で
検索した結果、live な pin は `orchestrator/tests/test_paper_story_a2_certification.py` の 5 箇所だけ。
`FROZEN_MANIFEST` 系台帳 (`test_frozen_artifacts.py`、`s1_expected_goldens.py`) は両 policy を
参照しない。`output/insights/` 側の過去 receipt は歴史記録であり張り直さない (絶対規律 7)。
