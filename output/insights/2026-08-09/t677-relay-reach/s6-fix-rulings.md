# 段 6 fix 裁定 — 実装する所見と裁定内容

親裁定。レンズ C (must-fix 7 + nit 1) とレンズ D (must-fix 7 + nit 2) を突き合わせ、
実装する所見を F1〜F10 に確定する。ここが fix の最終正本である。

## F1 — E2E oracle を実 `longreprtext` へ厳密化する (C#1, D#1)

**裁定: 実装の会計が正しく、テスト oracle が誤り。** レンズ C の算術で確定した。

- E2E の case 数は 24 (`test_pytest_failure_digest.py:419`)
- oracle: `"Failed: "` 8 bytes + payload 16,384 = 16,392 bytes/件 → 393,408
- 実 report: worker banner 46 bytes + 改行 1 byte + payload 16,384 = 16,431 bytes/件 → 394,344
- 差: `(46 + 1 - 8) × 24 = 936`

oracle 側を直す。**assertion を削る・緩める・近似にすることは禁止**。各 case を処理した
`gwN` をテスト側の独立 sidecar へ記録し、既知の banner 形式・改行・payload から実
`longreprtext` を完全再構成して、byte 数・SHA-256・`omitted_manifest_sha256` を厳密計算せよ。
worker id や Python 表記を固定できない部分は、**形式を検証したうえで実値を会計へ取り込む**。

## F2 — excerpt の行構造を保つ (C#2, C#6, D#6)

現行は全改行を `\x0a` へ escape して最大 4 KiB の 1 行へ潰している。これは裁定 A1 の
「代表 failure の**本体**が人間へ届く」を部分的にしか満たさない。

**裁定: source の論理改行を物理改行として復元し、各物理行の先頭へ必ず `> ` を付ける。**

- 各行内部の非 ASCII・C0・DEL・backslash の escape は維持する (改行だけを行区切りへ戻す)
- `> ` は `tools/mutation_harness.py:791-795` の `_strip_relay_prefix` が剥がさないので
  consumer 防護は保たれる。**先頭行だけに付ける実装は禁止** (2 行目以降が
  `FAILED path::name` だと偽 node になる)
- byte 会計は行単位で行い、excerpt 全体の rendered bytes 上限 4,096 は維持する

## F3 — 選択ループを incremental にする (D#2)

`_build_failure_digest` は `selected_count=1..N` ごとに全 block を再描画しており、
110 件で 6,105 block 描画、1,000 件で 500,500 block 描画になる。失敗した全走の終了処理に
秒〜分級が乗る。

**裁定: block を一度だけ描画し、累積 bytes が予算を超えた時点で停止する。**
`rendered_blocks`・`retained_bytes`・rank を保持し、候補ごとに全 block を再描画しない。
会計行の桁数変動による収束処理は現行どおり維持してよい。

## F4 — 例外の優先順位を確定する (C#3)

inner hook の例外が飛んでいる最中に digest emitter が `BaseException` を投げると、
元の inner 例外が置換されて失われる。

**裁定: 元の例外を最優先で保存する。**

- inner 例外が飛んでいない場合: 現行どおり。通常例外は一行 ERROR、`BaseException` は伝播
- **inner 例外が飛んでいる場合: digest 出力は試みるが、emitter が投げた例外は種別を問わず
  抑止し、元の inner 例外をそのまま伝播させる**

pluggy 経由 (`yield` へ sentinel を throw し、かつ stash が非空) のテストで固定せよ。

## F5 — `ImportError` の fail-open を対象 module 不在に限定する (C#7, D#4)

現行は `_load_failure_digest_budget()` の任意の `ImportError` を無言 return している。
`dispatch_compute` 内部の依存破損まで握り潰し、診断が無言で消える。

**裁定: `ModuleNotFoundError` かつ `exc.name` が対象トップレベル module (`tools`) の場合だけ
無言 fail-open。それ以外の `ImportError` は既存の一行 ERROR 経路へ送る。**
exit code は変えない。

## F6 — 実 pytest 終了形で緑無出力を固定する (C#5)

現行 (b) は synthetic `SimpleNamespace` だけで、実 `TestReport` の終了形を固定していない。
`report.failed or hasattr(report, "wasxfail")` と壊しても 9 テストすべて緑になる。

**裁定: 小さい subprocess pytest で pass / skip / xfail / 非 strict xpass / 0 collected /
成功 `--collect-only` を実行し、最終 stdout に digest marker が 1 byte も無いことを固定する。**
strict xpass と collection error 付き `--collect-only` は digest が出ることも固定する。

## F7 — consumer テストへ 2 行目 decoy を足す (C#6, D#7)

現行 fixture は単一行の `FAILED ...` だけで、F2 の複数行化に対して非合成的である。

**裁定: fixture を `"header\nFAILED decoy.py::test_fake"` 相当にし、raw / `| ` 1 段 /
`| | ` 2 段の三形すべてで `tools/mutation_harness._failed_nodes` の抽出集合に
偽 node が現れないことを固定する。** 検査は literal 文字列一致ではなく、実際に
`_failed_nodes` を通した抽出集合で行う。

## F8 — relay 結合の境界ケースを足す (D#5)

現行 (h) は実 `_relay_scheduler_logs` を通しているが、digest が末尾に丸ごと入るケースだけ。

**裁定: (1) `size == 65536` ちょうど、(2) digest 開始位置が tail 境界の前後、
(3) digest の後にさらに child 出力がある、の 3 ケースを追加する。**
(3) では digest が中継から欠落することを**そのまま固定する** (これは現行仕様であり、
本 wave の保証が「digest が stdout 最末尾にある場合」に限ることの機械的な証拠になる)。

## F9 — テスト単独の検出力を上げる (C#8, D#7)

レンズが挙げた「単独で緑のまま」の具体例を潰す。最低限:

- (a): `sha256` を固定値に壊したら赤になるよう、hash をテスト側の独立計算と照合する
- (b): `sys.stdout.write` を `sys.stderr.write` に変えたら赤になるよう、stderr も検査する
- (d)/E2E: excerpt 本文を別内容へ置換したら赤になるよう、各 entry の excerpt tail と
  対応する期待 source の対応を hash または独立計算で検証する
- (f): 通常経路で wrapper が実際に writer を呼ぶことを固定する
  (`_emit_failure_digest` 呼び出しを削除したら赤)
- (e): `_load_failure_digest_budget` を定数 `49152` に壊したら赤になるよう、
  relay 定数を実際に import して導出関係を検査する

## F10 — `pytest.main()` 再入の扱いを確定する (C#4, D#3)

module global の stash は、同一 process 内の入れ子 session で外側の report を破壊する。
canonical acceptance でこの経路が実際に呼ばれるかは**未確認**である。

**裁定: 実害の実在が未確認なので、機構の全面書き換え (session 束縛の collector 化) は
本 wave では行わない。** 代わりに次の 2 点だけ行う。

1. `conftest.py` の「`pytest.main()` の再入でも前 session の report を持ち越さない」という
   **全称コメントは偽なので訂正する** (逐次再入に限る旨へ狭める)
2. 入れ子 session で外側 stash が失われることを**現行仕様として固定する回帰テスト**を置く

session 束縛への移行は裁定パッケージ候補 U4 としてユーザーへ返す。

## 変異事前登録の訂正 (C#8, D#8 を受けて)

段 4 の M1〜M7 を次へ差し替える。すべて diagnostic sensitivity pin で kill には数えない。

| ID | 変異位置 (`orchestrator/tests/conftest.py`) | 1 行変異 | 新テストの期待赤 |
|---|---|---|---|
| M1 | digest 予算の導出 | `* 3 // 4` を relay 全量へ | (e) |
| M2 | excerpt 抜粋 helper | tail slice を head slice へ | (a), E2E |
| M3 | excerpt 行頭 prefix | 全物理行への `> ` 付与を先頭行だけに変える | (g) |
| M4 | 会計行 | `omitted_bytes` を常に `0` | (c) |
| M5 | worker guard | guard を反転し controller で return | E2E, (b) |
| M6 | `_emit_failure_digest` の builder 例外 catch | `except Exception` を `except OSError` へ | (f) |
| M7 | 失敗収集条件 | `if report.failed:` を `if False:` へ | (b) の実終了形テスト, E2E |

M1 の期待赤は段 4 の「(c), (e)」から **(e) のみ**へ訂正する ((c) は固定予算を直接渡すため緑)。
M6 は変異位置を `_emit_failure_digest` の **builder 呼び出しを包む catch** に一意化する。
M7 は段 4 の登録 (stats 参照への置換) が現コードへ適用不能なので、上記へ差し替える。

## 裁定パッケージへ追加する候補

- **U4**: digest の failure stash を module global から session/plugin instance 束縛へ移すか。
  同一 process の入れ子 `pytest.main()` で外側 report が失われる。canonical acceptance に
  この経路が実在するかは未確認。
