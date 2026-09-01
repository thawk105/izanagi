# [T-1712] 除外 2 field の対照実験 — launch contract の面で測った結果

- 日付: 2026-09-01
- base commit: 834efe61ff43ae81a12e313a5b087e0320aa4802
- 実装 commit: 41ff2e60813f1101f5b6ae56820221daaef30641
- 実測場所: Pegasus login node (焦点走) および計算ノード (変異行列の dispatch)
- 実 `claude` CLI の起動、LLM 呼出しはしていない

## 何を測ったか

`ClaudeProjectedRoleProvider` が比較から除外している 2 field を操作変数にした対照実験である。

- `argv.mcp_config_path` — `--mcp-config` の直後に置かれる argv 要素 (argv[17])
- `kwargs.cwd` — `subprocess.run` へ渡す cwd

3 つの capture を取った。

- control 2 本: `tempfile.mkdtemp` を決定化し、**同じ pathname を削除後に再作成**して 2 回採取する。
  provider の `close()` が neutral root を消すため、`_write_bytes_bound` の O_EXCL と
  「neutral cwd は invocation ごとの空 directory」という不変条件の両方を通る。
- treatment 1 本: 親 directory、basename prefix、path component 数、byte 長をすべて変える。
  D834 が既に除外している「乱数末尾要素だけの差」ではなく、path の形全体を変えている。

## 結果

焦点走は緑である (`1 passed`、後に関連 3 node と合わせて `4 passed`)。内訳は次のとおり。

- control 2 本の明示 call arguments は完全一致した。
- control と treatment の raw 差分は `{argv[17], kwargs.cwd}` のちょうど 2 件だった。
- 当該 2 field を sentinel へ置換した後の明示 call arguments は完全一致した。
- role 向け候補面 (`--agents` inline JSON、そこから復号した effective prompt、stdin payload) は
  完全一致した。
- 除外 2 field の実値と 6 本の canary は、role 向け候補面・env・除外以外の argv の
  いずれにも部分文字列として現れなかった。

## この結果で言ってよいこと

選んだ 3 つの pathname profile と固定 fixture において、supervisor から Claude CLI への
launch contract 上で、除外 2 field の値は他の観測 byte を動かさず、role 向け候補面・env・
除外以外の argv へ複製されていなかった。

## この結果で言ってはいけないこと

- **「除外 2 field は role から不可視である」とは言えない。** 実 CLI が cwd や mcp config path を
  system prompt・model 文脈・remote request・telemetry へ再投影するかは、この面から観測できない。
  D833 は「test double の runner 境界で見た同一性を『provider request の byte 同一性』と呼ぶ」ことを
  却下済みの選択肢として明記しており、D962 は argv / stdin を「送る依頼の本体」と再定義することを
  禁じている。本 insight はどちらの再定義も行わない。
- **事前登録 §4 領域 (iii) の 2 条件はどちらも測っていない。** 同項は「role からも provider の
  応答からも不可視」という連言を要求する。fake runner は provider 応答を持たないため後者も未測定である。
- **したがって D834 の「role からの不可視性は未証明である」は据え置く。** 除外集合と理由 mapping の
  文言は変更しない。`docs/phase3-8c-preregistration.md` の本文も変更しない。
- **B-6 は「変化なし」のままである。** B-6 は系全体の漏れ遮断とその状態での実走を要求しており、
  本 wave はそのどちらも満たさない。
- 単一 fixture provider・単一 role・固定 payload の結果である。holdout / arm / generation / role /
  transport の matrix と 6 cell の実走は測っていない。
- env は capture 間で一致したが、canonical ordering 自体は本 test の測定対象ではない
  (既存 oracle が担当する)。
- 観測したのは runner が受け取った**値**であり、positional / keyword の呼出し形までは固定していない。
  共有 fake runner (`_Runner`) が第 1 引数を positional でも `argv=` keyword でも同じ形で記録するためで、
  これは本 wave が持ち込んだ限界ではなく既存 helper の限界である。

## 交絡について

3 capture は artifact root を分けている (`invoke` が `artifact_root/payload_{invocation_id}.json` を
O_EXCL で作るため、同一 root では 2 回目が失敗する)。invocation ID は 3 capture で共通にした。
artifact root は argv・env・cwd・stdin のどの観測面にも現れないため、観測差分の交絡源にならない。

## 変異行列

`tools/mutation_harness.py` を dispatch 経路で走らせた。固定 HEAD は
`41ff2e60813f1101f5b6ae56820221daaef30641`、spec sha256 は
`ce5703796991348ddf928cdad03c1185ac79c647d4085743599aa95a89286da2`。
baseline は PASSED。結果は 6/6 KILLED、MISMATCH 0、SURVIVED 0、TIMEOUT 0。

本 wave はテスト強化だけの wave なので、DW-M08 に従い新テストだけが検出する差分を示す必要がある。
差分は最後の 1 件である。**追加した差分は 589 行の純追加で削除がゼロ**のため、
同時に走らせた既存 2 テストは変更前 HEAD の版と byte 一致であり、
両者を同じ走行で観測することが新旧比較になっている。

| 変異 | 内容 | 落ちたテスト | 位置づけ |
|---|---|---|---|
| ROLE-AGENTS-JSON | `--agents` operand へ mcp path を連結 | 新テスト + 既存 matrix | 冗長 gate |
| ROLE-STDIN | stdin へ cwd を連結 | 新テスト + 既存 matrix | 冗長 gate |
| ENV-CWD | env へ cwd を値に持つ key を追加 | 新テスト + 既存 matrix | 冗長 gate |
| NONEXCLUDED-ARGV | 除外対象でない argv 要素へ mcp path を連結 | 新テスト + 既存 matrix | 冗長 gate |
| TEMP-PARENT-LEAK | env へ一時 directory の親を漏らす | 新テスト + 既存 matrix | 冗長 gate |
| PATH-LENGTH-LEAK | 除外対象でない argv 要素へ mcp path の**長さ**を漏らす | **新テストのみ** | 純増の実証 |

最後の 1 件が新テストだけに落ちる理由は次のとおりである。既存 matrix テストは全 provider が
実 `tempfile.mkdtemp` を使うため path 長が常に同じで、長さ由来の値は holdout 間で不変になり
検出できない。新テストは control と treatment の path 長を明示的に変えているため検出する。
これは D834 が「除外は候補列挙にとどめる」とした懸念の実例である — path から導いた値が、
既存の holdout 不変性検査をすり抜けたまま対象別ラベルになりうる。

`TEMP-PARENT-LEAK` は当初「新テストのみが殺す」と予測したが外れた。既存 matrix テストが
env の key 集合を厳密に固定しているため、新しい env key を足す変異はそこで落ちる。
予測を外した記録として残す。

## 冗長 gate の扱い

DW-M03 に従い、既存テストも同時に落ちる 5 件は冗長 gate として明記し、
新テスト単独の検出力の証拠から外す。新テストの検出力の証拠は `PATH-LENGTH-LEAK` 1 件と、
テスト内に置いた helper の面脱落を殺す合成 oracle (argv 全 19 index と kwargs 全 7 key を
1 面ずつ変え、それぞれちょうど 1 件だけ検出されることを要求する) である。

## 実走した検査

- 焦点走 (login node): 新テスト単独で `1 passed`。
- 焦点走 (login node): 新テスト + 既存 T-1354 の 2 件 + tracked Python の AST 走査メタテストで `4 passed`。
- 焦点走 (login node): 本 test module を import する `test_reflux_originless_compatibility.py` で `2 passed`。
- 変異行列 (計算ノード dispatch): baseline PASSED、6/6 KILLED、MISMATCH 0。
