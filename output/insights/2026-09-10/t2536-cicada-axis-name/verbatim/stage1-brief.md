# 段 1 brief — [T-2536] cicada 軸名を CCBench の実体 cache 変数へ合わせる

## 研究前進
認定 (certification) 系列で cicada を受理集合へ入れるための土台。genome 軸 `INLINE_VERSION_OPT` に対する
CMake cache 変数は cicada では `CCBENCH_INLINE_VERSION_OPT_CICADA` であり、汎用写像 `-DCCBENCH_<軸名>` では
CMake が未使用と報告して値がコンパイラへ届かない。よって cicada の genome は build の忠実な写像にならず、
cicada の認定較正 record は 1 件も作れない。完了判定は (a) cicada の genome から出る configure 引数が
CCBench 実体の cache 変数名と一致する、(b) 対応が崩れたら CCBench 実体側の記述を読んで落ちる検査がある。

## 確定済みユーザー裁定 (command 引数、逐語)
「名前の対応は CCBench の実体側から取り、対応が崩れたら落ちる検査を同じ変更単位で置く。Codex author = D95。
規律 2 は緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。」

## 実測した前提 (main 7f17e1c63、親が実行)
- 実体: `external/ccbench/cc/cicada/CMakeLists.txt` の `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_CICADA}`。
  `external/ccbench/cmake/Options.cmake:53-54` に `_CICADA` / `_OZE` の 2 本。cicada の他 4 軸、
  silo / mocc / tictoc の全軸は恒等写像 (`CCBENCH_<軸名>`)。
- 汎用写像の実体は依頼が挙げた launcher ではなく `orchestrator/campaign/model.py:63` `Genome.cmake_defines()`。
  build 本経路の `buildcache.py:1936,3189` と `screening_driver.py:131,166` が使う。
  `tools/pegasus/certify_calibration.sh:546-575` の case は silo/mocc/tictoc だけで cicada の枝を持たない。
- 受け手は `orchestrator/calibrator/cli.py:429-459` (`-DCCBENCH_` 剥がし → `missing_axes` で照合)。
- cicada の live build 経路は現存しない (`"cicada"` を持つ driver は `genome.py` のみ)。
- 凍結: `-DCCBENCH_INLINE_VERSION_OPT` を記録した tracked 成果物は 0 件。変更面に whole-file sha256 pin なし。
  `campaign_lock.py:88` が `genome.py` を contract loader 源に持つ (未 commit だと焦点走が drift 赤)。

## scope
- (in) 軸名 → CMake cache 変数名の対応表を izanagi 側に 1 本静的に宣言し、producer (`cmake_defines()`) と
  受け手 (`calibrator/cli.py` の逆写像) の両方が使う。CCBench 実体の `cc/<protocol>/CMakeLists.txt` を読んで
  drift で落ちる検査を同じ変更単位に置く。
- (out) cicada を `certify_calibration.sh` / `submit_certify.sh` の受理集合へ入れること (別 wave。
  `INLINE_VERSION_OPT=1` が上流の死にコードでビルド不能という別問題を含む)。oze。上流 insight。新台帳。

## 不変条件
- silo / mocc / tictoc の configure 引数は 1 byte も変わらない。`Genome.canonical()` の文字列も変えない。
- 軸名は C++ マクロ名のままとする (build の忠実な写像であること自体が規律 2 の対象)。
- 受け手は cicada について汎用名 `-DCCBENCH_INLINE_VERSION_OPT` を受理しない (D1864 の却下 alias にしない)。
- 既存テストの期待値を変えない。certify の protocol 白名 (受理集合) を変えない。

## (P1〜P4) 割れうる前提 — 親の provisional 裁定・攻撃対象
- (P1) 受け手側の逆写像は D1864 却下欄「受け手側に protocol 別の alias 正規化を足す」に当たらない。双射で、
  旧汎用名は拒否のままだから。
- (P2) 対応表は izanagi 側に静的に持ち、実行時に submodule を parse しない (D1863 の 2 実体照合を保つ)。
- (P3) cicada を launcher へ入れないことで依頼の「認定の対象にできる」を満たす (土台の除去で足りる)。
- (P4) 置き場所は import 循環 (`genome.py` → `model.py`) を作らない module とする。

## 成果物の形と分割
実装 3 file 程度 + 検査。docs は段 7 の spool fragment。編集面が小さいので段 5 実装は 1 単位。
段 2 plan 1 本、段 3 敵対 2 レンズ、段 6 レビュー 2 レンズ (受理集合と正しさ防壁に触るため軽量版にしない)。
