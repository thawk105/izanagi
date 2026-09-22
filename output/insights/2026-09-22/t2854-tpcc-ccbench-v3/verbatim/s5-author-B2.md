途中実装を監査し、完成させました。計算ノード部分は **実装済み・未実走** です。

1. **成果物**

   置き場はすべて [probe/](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/) 配下です。

   | ファイル | 行数 | 役割 |
   |---|---:|---|
   | `run_probe.py` | 746 | 必須引数、C0〜C6、証拠保存、変異 harness、失敗時の非0終了 |
   | `mutation-spec.template.json` | 73 | D1・M1〜M5 の逐語置換と期待判定 |
   | `v3check.py` | 276 | 既存の構造・witness・内容検査。変更なし |
   | `selftest.py` | 148 | 既存146件の自己試験。変更なし |

2. **自己確認の実走結果**

   ```text
   python3 output/runs/t2854-ccbench-v3/probe/v3check.py --selftest
   rc=0
   v3check selftest: 146/146 passed; failures=0

   python3 output/runs/t2854-ccbench-v3/probe/run_probe.py --help
   rc=0
   ```

   - Python 3ファイルを `compile()` で構文確認：rc=0。
   - JSON解析と anchor 一意性確認：rc=0。D1・M1〜M5すべて出現数1。M2はD1適用後に確認。
   - tracked／staged diff：ともに空。
   - build・benchmark・計算投入は実行していません。

3. **前巡から追加・修正した箇所**

   - 実行入口、C0〜C6の段階制御、途中失敗時のJSON保存、未実行段の記録を追加。
   - D1先行適用、置換diff、対象targetの再build、pristine復元・SHA-256照合、逐次flushを実装。
   - KILLEDを「判定失敗かつ最初の理由が期待コードと一致」に限定。build失敗はERROR。M5はbuildしません。
   - D1がk=1000に到達したことも要求。
   - include活性をflag 1／2の順序付きfile入退場列で比較する裁定を、コードと `compute.json` に明記。負例と空出力拒否も追加。
   - YCSB verifierの取引数参照を、誤っていた直下の `txns` から `stats.txns` へ修正。
   - 変異走の例外時にもdigestを保存して生traceを削除。変異結果から完全frame見本を除外。

   裁定§3・§4からの逸脱：**なし**。ただし、計算ノードでの受入成立は未確認です。

4. **親によるanchor確定時の注意**

   `anchor_status` は `checked-against-author-a-worktree` です。最終C2の実bytesで次を再照合してください。

   - D1：commit失敗block後のquit判定block。
   - M1：取引種別setter呼出し。
   - M2：**D1適用後**の `#if !TRACE` とquit判定。
   - M3：v3 W呼出しだけのtable引数。
   - M4：v3 C呼出しだけのtx_type引数。
   - M5：setter後の `#line 56`。

5. **所有外への依存**

   - repoからimportする `_resolve_toolchain`：compiler digestの照合契約に依存。
   - 同 `_normalize_objdump`：C3の逆アセンブル正規化に依存。
   - `fetch_third_party.py hydrate`：引数、固定依存policy、`source_root` JSONに依存。
   - `orchestrator/verify.py`：CLIと認定JSONの `stats.txns` 等に依存。
   - CCBench：CMake宣言、21 compile entry、target／flag名、trace schema、stdout counterに依存。
   - witness解析は確認したrepo関数相当のローカル実装です。

## 総括

- 既存検査器を変更せず、probe入口・段階制御・変異harness・specを完成。
- 自己試験146/146、構文、help、anchor一意性は実走確認済み。
- C0〜C6の計算ノード検証は実装済み・未実走。
- 親は最終C2でanchorを再照合し、レビュー・fix後に投入してください。