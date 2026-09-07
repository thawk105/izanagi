---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2198-fetchcontent-wiring
seq: 1
---

## {{D:a2-trace0-grammar-blocks-offline-wiring}}. 認証経路のオフライン配線は閉じた trace0 文法に塞がれており、実装せずユーザー再裁定へ返す

**決定:** D1524 が定めた「共有 measurement pipeline へ FetchContent の source dir 引数を通す」
配線を、本 wave では実装しない。D1524 の理由節が根拠にした事実の 1 つが実コードで反証されたため、
`DW-S04` に従い新事実を添えてユーザー再裁定へ戻す。

**反証された前提:**

D1524 は「保管庫と helper は既に在り、他の 2 driver が使っている。足りないのは引数の
引き回しだけである」と書いている。引き回しだけでは A-6 の read-heavy は 1 件も測れない。
`indeterminate` の原因が network から argv 文法へ移るだけである。連鎖は次のとおりで、
いずれも現行 main で 1 行ずつ確認した。

- `pipeline.py` は perf build の configure argv を WAL の `build_done.perf_configure_cmd` へ
  そのまま記録する。この argv は `buildcache._v2_commands` が組むので、FetchContent の define を
  足せばそれが記録される。
- A-2 / A-6 の collector はその argv を `validate_trace0_evidence` へ渡す。
- `paper_story_a2_certification._exact_trace0_configure_argv` は
  `expected = fixed + prefix + ordered_define_tokens` を作り `list(argv) != expected` で
  `CertificationError` を投げる。**tail に許されるのは dependency prefix と統制 define だけで、
  FetchContent の token を置く場所が無い。**
- 例外は collector で `indeterminate` へ変換され、cells と effects が空になる。

**逃げ道が無いことも確認した:**

- source dir を渡さず既定位置 `<base>/masstree-src` へ staging して
  `-DFETCHCONTENT_BASE_DIR=` 1 本だけにする案も落ちる。文法は expected を完全に determine
  しており、token が 1 本増えるだけで不一致になる。
- 記録前に FetchContent token を argv から取り除く案は採らない。走らせた argv と記録した argv が
  食い違い、provenance の偽造になる (絶対規律 2・3)。

**なぜ親が独断で進めないか:**

文法は policy JSON の `trace0_cmake_argv` にあり `_protocol_preimage` に含まれる。広げると
A-2 / A-6 の `protocol_sha256` が動く。これは凍結された認証プロトコルの同一性であり、
`bytes_sha256` と併せて golden literal が `orchestrator/tests/test_paper_story_a2_certification.py`
に 4 値 (5 箇所) 焼き込まれている。D1524 は共有経路への引数の引き回しを許可したが、
**認証プロトコルの凍結同一性を動かすことまでは書いていない。** D1396 が同型 (床値 official が
seam 判定に塞がれた) で機構を変えずユーザーへ返した前例に従う。凍結物を動かすのは人間の手番である。

**ユーザーへ返す解消案 (親の推奨は 1):**

1. `trace0_cmake_argv.configure` へ FetchContent の枠を**厳密な期待値として**足し、
   golden 4 値を張り直して凍結物の所定手続きで払う。過去の認証値は取り直さない (絶対規律 7) が、
   過去の結果と現行 policy の protocol hash が一致しなくなる旨を成果物へ明記する。
2. 文法を触らず A-6 を未充足のまま残す。配線もしない (配線だけでは `indeterminate` が続くため)。
3. 文法の検査を緩めて余分 token を許す。**親は推奨しない** — 閉じた文法は「走った argv が
   protocol の定めたものと完全に一致する」ことを証明する装置であり、緩めると証明力が落ちる
   (絶対規律 2)。

**却下した選択肢:**

- 引数の引き回しだけ実装して文法は後続 wave へ送る — 発火経路の無い条件付き機能を main へ入れる
  ことになり `DW-G04` に反する。`indeterminate` が続くので成果物も 1 mm も動かない。
- 親の判断で文法と golden を張り直す — 凍結された認証プロトコルの同一性を無認可で動かす。

## {{D:fetchcontent-wiring-needs-five-arguments}}. FetchContent の共有経路配線は 4 引数でなく 5 引数である

**決定:** 将来 D1524 系の配線を実装するときに共有経路へ通す引数は、source dir 3 本と
`fetchcontent_base_dir` の 4 本ではなく、`fetchcontent_dependency_receipt` を含む 5 本とする。

**理由:**

- `buildcache._build_v2_impl` は
  `if bool(fetchcontent_base_dir) != (dependency_receipt is not None): raise` という
  **同値条件**を持つ。base だけでも receipt だけでも拒否される。
- `_v2_commands` は source dir 指定時に base の同時指定を要求するため、source dir を通すなら
  base が要り、base を通すなら receipt が要る。4 本案では build 前に必ず失敗する。

**却下した選択肢:**

- 4 引数で足りるとする — 同値条件により base を渡した瞬間に全 cell が build-error になる。

## {{D:fetchcontent-identity-does-not-bind-all-dependency-content}}. FetchContent の build identity は依存内容を完全には束縛しない

**決定:** 現行の v2 build identity は FetchContent 依存の内容を完全には束縛しないという事実を
記録し、本 wave では是正しない。是正は別件として扱う。

**理由:**

- `_v2_identity` の pre-image に入る FetchContent 由来の項は
  `fetchcontent_dependency_receipt` (masstree の HEAD と `config.h` の digest) と
  `fetchcontent_transport_mode` (source-dir か否かの 1 bit) だけである。
  base dir の path、source dir 3 本の path、mimalloc と googletest の内容はいずれも入らない。
  mimalloc は実際に link されるため、出力に無関係な依存ではない。
- したがって同じ masstree receipt のまま mimalloc の内容だけを変えた 2 つの要求は同じ digest に
  なり、原理的には別依存の binary から certified 値が出る余地がある。
- ただし A-2 / A-6 の cache root は job-local であり、同一 job 内で staged 依存の内容が変わることは
  ない。**実際の露出は無く、本 wave の blocker ではない。**

**却下した選択肢:**

- 本 wave で identity を強化する — 主目的の外であり、`DW-G05` の scope 規律に反する。
- 露出が無いことを理由に記録しない — 別 driver が共有 cache root で同じ経路を使えば露出する。
