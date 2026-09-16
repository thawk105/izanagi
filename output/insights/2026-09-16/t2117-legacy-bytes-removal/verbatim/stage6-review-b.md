## 判定

静的読解では blocker / must-fix は見つかりませんでした。射影 `impl.diff` と現在の HEAD 差分は一致し、変更はテスト 1 ファイルだけです。pytest・lint・変異走は実行していません。

以下、`T` は `orchestrator/tests/test_codex_reasoning_ab.py`、`P` は `tools/codex_reasoning_ab.py` を指します。

## 1. helper の実在・署名

呼び出しと定義は整合しています。

| 対象 | 根拠・確認結果 |
|---|---|
| `TOOL._run` | `P:506` — `argv`, keyword-only `cwd` を受け取る |
| `TOOL._git` | `P:530` — `repo, *args` を受け取り `bytes` を返す |
| `_write_synthetic_benchmark_rollout` | `T:836` — 位置引数 3 個、戻り値は `tuple[Path, str]` |
| `_synthetic_task_manifest` | `T:6712` — 引数省略可能、deepcopy した辞書を返す |
| `TOOL.RC_SNAPSHOT` | `P:428` — 値は `20` |
| `ValidationError.rc / .reasons` | `P:441` — `.rc` を保持し、`.reasons` は **tuple** に変換する |

負例の tuple 完全一致 assert（`T:3710`）にも型の食い違いはありません。

## 2. rollout の bytes と patch envelope

指定された破綻仮説はいずれも成立しません。

- `_canonical_bytes` は末尾に `b"\n"` を付けます（`P:453`）。追記 JSON は前行と連結しません。
- `_json_lines` は `json.loads(line)` で読み、canonical 表現との一致を要求しません（`P:462`）。
- `_write_rollout` はディレクトリ作成と `write_bytes` のみで、読み取り専用化しません（`T:8050`）。
- SHA は追記後のファイルから計算します（`T:3628`）。
- 両 parser は裸の `@@` を anchor `None` として受理します（`P:708`、`P:868`）。
- `-base\n+authored\n` の追加行には改行があり、次の更新ヘッダーや `*** End Patch` と分離されます（`T:3608`）。
- envelope 末尾の改行は route A の `splitlines()`、route B の末尾空要素除去で処理されます（`P:688`、`P:845`）。

## 3. manifest と比較到達

auxiliary 3 件の差し替えで、この呼び出し経路には十分です。

`_validate_materialized_task_manifest` は `_validate_task_manifest` へ委譲します（`P:2767`）。要求は schema・kind、非空 tasks、必須フィールド・識別子・Mapping 型・finding IDs、auxiliary 3 件の session/SHA フィールドです（`P:2568`、`P:2669`）。task 内の歴史 pin に対応する実ファイルは検証しません。

`derive_independent_golden` が rollout を解決する対象は auxiliary の `author/fix1/fix2` だけです（`P:932`）。明示 SHA は `_find_rollout` でも利用され、歴史 `SESSION_IDS` との一致を要求する分岐には入りません（`P:579`）。

負例は fix1 の追加側だけを変えます（`T:3606`）。したがって静的読解では、route B は `authored` を正常に置換して比較へ到達し、期待した mismatch を返します。wrapper も消費した generator の代わりに `recorded` を実関数へ渡しています（`T:3653`、`T:3692`）。

## 4. 裁定との照合

| 裁定 | 照合結果 |
|---|---|
| D1367 | guard 本体（`T:794`）と自己検査 3 node（`T:963`、`T:972`、`T:985`）は無変更。 |
| D1382 | 歴史 anchor を復元せず、既存 helper による合成入力へ移行。terminal 対象は無変更。 |
| D1615 | `test_real_rollout_collector_golden_is_source_bound`（`T:9283`）は無変更。常時 assert と条件付き source 照合が残る。 |
| [T-2117] | 既存 M2 関数を残し、歴史 SHA assert と availability guard 呼び出しを撤去。比較の正例・負例を常時実行する構成。 |

`P` は HEAD 比で無変更です。歴史 patch との統合保証を失う点は、`adjudication-plan-v2.md:12` の受容済み代償と一致します。

## 5. 既存テスト・登録簿への波及

AST 比較では、削除された関数は **0 件**、変更された既存関数は M2 正例だけです。追加は helper と mismatch 負例の 2 関数です。

guard は自己検査から 3 回参照され続けるため、未使用にはなりません。新しい名前の衝突も確認できませんでした。

共有 fixture 閉包の対象は session/module scope です（`orchestrator/tests/test_real_repo_serialization.py:1437`）。今回の追加依存は function scope の `tmp_path` / `monkeypatch` で、`benchmark_snapshots` を使いません。所要台帳の未登録 node も unknown として処理されます（`orchestrator/tests/conftest.py:1675`、同 `:1740`）。

静的読解では、今回の変更によって登録簿・所要台帳が必然的に失敗する根拠はありません。lint の実行結果は未確認です。

## 所見 B-1：SHA 拒否能力の証明は射程外

- **主張:** 新しい正負例は、SHA 不一致を拒否する能力までは証明しません。
- **根拠:** `T:3628` は毎回正しい SHA を設定し、負例の変更対象も patch 内容です。拒否処理は `P:640`、呼び出しは `P:944`。この限界は `adjudication-plan-v2.md:22` で裁定済みです。
- **壊れる具体例:** `_verify_rollout_sha` を無処理にする変異＋今回の入力 → 新 2 node では検出できず、誤った SHA の拒否保証を実績から推論できてしまいます（静的読解）。
- **重大度:** scope 外。既裁定のパッケージ候補であり、本差分への修正要求ではありません。
- **成果物影響:** 本差分を放置しても認証済み選択・材料レポート・試行台帳の値・受理集合・参照は変わりませんが、新 2 node の実績を SHA 拒否保証へ拡張して解釈できません。

## 総括

最も重い残存事項は B-1 の既知の被覆限界で、scope 外です。  
指定された破綻仮説から blocker / must-fix は確認できませんでした。  
レンズ B の静的レビューとして、この実装は受け入れてよいと判断します。  
親の焦点走結果は再検証しておらず、変異走の成立も本レビューでは認定していません。