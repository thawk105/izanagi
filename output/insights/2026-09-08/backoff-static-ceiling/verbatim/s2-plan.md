## 調査結果と結論

推奨は **(A)** です。

実測済みの 999 µs でも abort 抑制が飽和しておらず、(B) は測定不能域を固定するだけだからです。(A) は未使用の raw 値域 `V >= 3000` を高い定数値へ割り当てれば、既存の `0..2999` を数値的に一切変えず実現できます。

推奨する追加符号化は次です。

\[
E_{\text{constant}}(\mu)=
\begin{cases}
\mu & 0\le\mu\le999\\
\mu+2000 & \mu\ge1000
\end{cases}
\]

したがって静的 1000 µs は raw `BACKOFF_FIXED=3000`、静的 1500 µs は raw `3500` です。raw `1000..1999` と `2000..2999` は従来どおり乱択モードのため、直接の静的値として使いません。

## 現行符号化の逐語的な再導出

C++ の現物は [silo-backoff-fixed.patch:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:70) です。

```cpp
    double now_backoff = (static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 0ULL) ? static_cast<double>(BACKOFF_FIXED) : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 1ULL) ? static_cast<double>((static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + (((start * 0x9e3779b97f4a7c15ULL) >> 63) ? (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) - ((((start * 0x9e3779b97f4a7c15ULL) << 1) >> 1) % (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + 1ULL))) : ((((start * 0x9e3779b97f4a7c15ULL) << 1) >> 1) % (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + 1ULL)))) / 2.0 : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 2ULL) ? static_cast<double>((static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + (((start * 0x9e3779b97f4a7c15ULL) >> 63) * (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL)))) / 2.0 : static_cast<double>(static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL)));
```

Python の現物は [b10_backoff_shape_sweep.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:722) です。

```python
def exact_model(encoded: int, start: int):
    """Exact Fraction model for the one-line expression."""
    from fractions import Fraction

    if type(encoded) is not int or encoded < 0:
        raise ValueError("encoded must be a non-negative exact integer")
    if type(start) is not int or start < 0 or start > _MASK64:
        raise ValueError("start must be a uint64")
    code, mean_us = divmod(encoded, 1000)
    if code == 0:
        return Fraction(encoded)
    if code >= 3:
        return Fraction(mean_us)
    mixed = (start * MIXER) & _MASK64
    high = mixed >> 63
    if code == 2:
        return Fraction(mean_us + high * 2 * mean_us, 2)
    low = mixed & ((1 << 63) - 1)
    residue = low % (2 * mean_us + 1)
    offset = 2 * mean_us - residue if high else residue
    return Fraction(mean_us + offset, 2)
```

`V >= 0`、`q = V // 1000`、`r = V % 1000`、`u = (start × 0x9e3779b97f4a7c15) mod 2^64`、`H = u >> 63`、`L = u mod 2^63`、`a = L mod (2r+1)` とすると、両現物は同じ関数です。

| raw 値域 | 復号結果 |
|---|---|
| `q = 0`、`0 <= V <= 999` | 定数 `V` |
| `q = 1`、`1000 <= V <= 1999` | `(r + (2r-a if H else a)) / 2` |
| `q = 2`、`2000 <= V <= 2999` | `r/2` (`H=0`) または `3r/2` (`H=1`) |
| `q >= 3`、`V >= 3000` | 定数 `r = V % 1000` |

したがって `V=1000` は `q=1,r=0` なので常に 0、`V=2000` も常に 0、`V=3000` も現状は 0 です。`V>=3000` でも結果は剰余 `0..999` に戻るため、定数として表現できる上限は原理的に 999 µs です。

`BACKOFF_FIXED=-1` はこの式へ入りません。[patch:69-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:69) のプリプロセッサが stock の `Backoff_.load(...)` 枝を選びます。

## 案 A の file:line 変更計画

符号化の変更は、raw `V>=3000` の復号だけを `V % 1000` から `V - 2000` へ変えます。

\[
D_A(V,start)=
\begin{cases}
D_{\text{current}}(V,start) & 0\le V<3000\\
V-2000 & V\ge3000
\end{cases}
\]

このとき `D_A(E_constant(µ),s)=µ` です。

| アンカー | 変更 |
|---|---|
| [patch:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:70) | 最後の fallback だけを `static_cast<double>(static_cast<uint64_t>(BACKOFF_FIXED) - 2000ULL)` にする。 |
| [patch:69-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:69) | `#if`、`#else`、stock 行、`#endif`、マーカーは変更しない。 |
| [b10_backoff_shape_sweep.py:263-264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:263) | `EXPECTED_HOLE_LINE` を同じ 1 行へ更新。`FORMULA_SHA256` はその bytes から再導出。 |
| [b10_backoff_shape_sweep.py:730-742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:730) | `code >= 3` を `Fraction(encoded - 2000)` に変更。他の分岐は変更しない。 |
| [b10_backoff_shape_sweep.py:648-662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:648) | B-10 shape 用 `encode()` / `decode()` は変更しない。shape code 3 は引き続き B-10 grid 外。 |
| [b10_backoff_shape_sweep.py:1042-1062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:1042) | `grid.encoding == "BACKOFF_FIXED=shape_code*1000+mu"` と shape 閉集合は変更しない。 |
| [b10_backoff_shape_sweep.py:287-288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:287) | Options hash と hole を sentinel 化した frame hash は変更しない。 |
| [backoff_extended_sweep.py:55-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:55) | `EXTENDED_SWEEP_US` は物理座標なので末尾 1000 を維持。既存 module 内に小さい static encoder/decoder を置き、1000 を raw 3000 に変換する。 |
| [backoff_extended_sweep.py:367-395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:367) | `_ordered_points()` と `_t2266_points()` の `BACKOFF_FIXED` に物理値でなく encoder 結果を入れる。 |
| [backoff_extended_sweep.py:625-634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:625) | report label の `backoff_us` は raw 3000 でなく復号した物理 1000 を使う。 |
| [backoff_extended_sweep.py:66-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:66) | 新しい T-2266 系列では `REALIZED_US` を 1000 まで伸ばし、`UNREALIZED` を空にする。旧 999 系列と混同しないよう report schema/campaign identity を更新する。 |
| [backoff_extended_sweep_report.py:255-282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep_report.py:255) | `reference_genome` の raw 値は encoder 結果と比較し、出力 `backoff_us` は物理値を保持する。 |
| [backoff_extended_sweep_report.py:465-499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep_report.py:465) | WAL の raw `BACKOFF_FIXED=3000` を静的 1000 µs として復号する。raw `1000` は新系列では受理しない。 |
| [patches/README.md:174-191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/README.md:174) | 「raw 値 = µs」ではないこと、`1000..2999` は既存 mode、`µ>=1000` は `µ+2000` と明記する。 |
| [docs/decisions.md:52466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/decisions.md:52466) | 選択、符号化、旧系列非遡及を新決定として追記する。 |
| [docs/worklog.md:3368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/worklog.md:3368) | 静的検査、hash、実測引き渡しを追記する。 |

T-2266 の新しい 1000 µs 実測が得られた後に限り、[t2216_backoff_walk_model.py:53-54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/t2216_backoff_walk_model.py:53) の tail を `999→1000`、report schema を新系列へ更新します。[test_t2216_backoff_walk_model.py:256-258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_t2216_backoff_walk_model.py:256) も同時更新します。旧 999 の値を 1000 と読み替えてはいけません。

## 案 A のテスト変更

| アンカー | 変更 |
|---|---|
| [test_b10_backoff_shape_sweep.py:2564-2618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2564) | `0..999` に加え、raw `1000..1999` と `2000..2999` が旧閉形式と一致することを pin。`exact_model(3000,s)==1000` も追加する。 |
| [test_b10_backoff_shape_sweep.py:2818-2845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2818) | C++ hole と Python `exact_model` の比較対象へ 3000、3001、3999 などを追加する。 |
| [test_condition_meaning_gate.py:294-299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_condition_meaning_gate.py:294) | 999 の正例を維持する。 |
| [test_condition_meaning_gate.py:403-417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_condition_meaning_gate.py:403) | raw 1000 が静的 1000 ではなく 0 になる F718 負例を維持する。これは既存域不変の pin でもある。 |
| [condition fixture supplied:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/fixtures/condition_meaning_gate/supplied/include/backoff.hh:6) | 新 hole line へ更新。 |
| [condition fixture f707:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/fixtures/condition_meaning_gate/f707-missing-supply/include/backoff.hh:3) | 同じ新 hole line へ更新。供給欠落だけを変異させる fixture 間同一性を保つ。 |
| [test_backoff_extended_sweep.py:271-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:271) | 物理 grid 末尾は 1000 のまま、genome の raw 値だけ 3000、report の物理値は 1000、`UNREALIZED` は空であることを pin。 |
| [test_backoff_extended_sweep.py:829-830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:829) | gate へ渡る raw 集合の末尾を 3000 とする。 |
| [test_backoff_extended_sweep_report.py:66-84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep_report.py:66) | raw genome と物理 `backoff_us` を encoder/decoder 経由で対応させる。 |

[test_b10_backoff_shape_sweep.py:815-818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:815) の「shape code 3 は B-10 grid 外」は変更しません。runtime decoder が 3002 を静的 1002 と読めることと、B-10 shape driver が 3002 を登録 shape として受理しないことは両立します。

## 案 A で動く凍結束縛

静的な 1 箇所置換だけを行った場合、再導出した候補 hash は次です。

- patch SHA-256: `36cd974c...` → `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a`
- formula SHA-256: `5b3d8dee...` → `1205b1ffb4fa6740873f1aa1ecf50bfc484239fb74aa28464dcb2e3a19fbe8df`

分類は次のとおりです。

| 対象 | 分類 | 理由 |
|---|---|---|
| [patch bytes](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:70) | 再登録が要る | `artifacts.patch_sha256` が変わる。 |
| [formula pin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:263) | 再登録が要る | hole の逐語 bytes と `formula_sha256` が変わる。 |
| [prereg schema/artifacts](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:284) | 再登録が要る | v4 の artifact 束縛を上書きせず、canonical path 上の明示的な次版にする必要がある。 |
| [physical residual provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:489) | 再登録が要る | 旧 probe は旧 formula/source commit に束縛される。値が同じ見込みでも、新版への機械的流用は不可。 |
| [SPACE_VERSION/TRIAL](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:88) | 再登録が要る | D1304 が据え置きを認めた根拠は「式・patch・符号化空間が不変」だった。今回は式が変わる。 |
| `grid.encoding` | 値は動かない | `"BACKOFF_FIXED=shape_code*1000+mu"` は登録 shape 0/1 に対して依然正しい。静的高値の escape はこの shape grid の外。 |
| R1〜R5、means、shape、実行順、統計手続き | 値は動かない | raw `0xx` / `1xx` の復号は不変。 |
| Options/frame hash | 値は動かない | hole 以外の patch bytes、stock 枝、待機 loop は不変。 |

完了済み正式系列はすべて「値は無効化されない」に分類します。

- write-heavy `e3de15eb` 45 cell
- balanced `143a3f74` 45 cell
- read-heavy `acf840c8` 45 cell
- それらを集約した 135/135 cell の最終 report

これらは旧 v4 の prereg commit `77b33e37...`、blob `ea910de32...`、spec SHA `9c594114...`、patch/formula hash の下に残します。新版へ resume・追記・再ラベルしてはいけません。

また、旧拡張系列の F718 1000 行は新 decoder で遡及的に 1000 µs になりません。旧 binary は raw 1000 を実行しており、実体 0 のままです。[既存図の非遡及宣言](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/paper-story/figures/README.md:215) と [F718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/failures.md:19625) は変更しません。

`source_digest` については次の分類になります。

- `BACKOFF_FIXED=-1`: 変更行は preprocess で除去されるため、引き続き `stock`。identity は不変。
- 非負値: hole の preprocess bytes が変わるため、0..2999 も含め新しい `source_digest`、`src_token`、`variant_id`、cache key になる。数値意味が同じでも旧 WAL へ resume しない。
- 旧 `src_token` と既存成果物: 歴史 identity として有効なまま。無効化・書換えはしない。

identity の伝播点は [source_digest.py:2063-2072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/source_digest.py:2063)、[pipeline.py:124-130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/pipeline.py:124)、[buildcache.py:624-640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/buildcache.py:624) です。これらの実装自体は変更しません。

## 案 B の file:line 変更計画

(B) は decoder と B-10 凍結束縛を一切変えず、静的 driver の物理域だけを `0..999` に閉じます。

| アンカー | 変更 |
|---|---|
| [backoff_extended_sweep.py:55-58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:55) | endpoint `1000` を `999` に置換する。可能なら同じ module の単一 `STATIC_MAX_US=999` を grid と T-2266 realized tail から参照する。 |
| [backoff_extended_sweep.py:64-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:64) | `T2266_REQUESTED_US`、`REALIZED_US=(...,999)`、F718 `UNREALIZED` は歴史的分離として維持する。 |
| [test_backoff_extended_sweep.py:271-285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:271) | upper endpoint を 999 に変更し、1000 が静的 grid に無いことを pin。既定 adaptive の 1000 状態を完全被覆する主張は削除する。 |
| [test_backoff_extended_sweep_report.py:137-147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep_report.py:137) | right-censored endpoint と bracket を `900,999` に更新。 |
| [patches/README.md:174-186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/README.md:174) | 直接の静的値域は `0..999`、raw `1000..2999` は shape mode、`>=3000` は静的 API として未サポート、と明記する。 |
| [docs/decisions.md:52466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/decisions.md:52466) | 999 で right-censored のまま閉じる設計判断を追記する。 |

(B) では次を変更しません。

- [patch hole と stock 枝](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-fixed.patch:69)
- [EXPECTED_HOLE_LINE、FORMULA_SHA256、exact_model](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:263)
- [B-10 prereg の patch/formula hash と grid.encoding](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:284)
- [T2216 tail 999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/t2216_backoff_walk_model.py:53)
- [p3_s4_red.py の synthetic 999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/p3_s4_red.py:171)
- F718、旧図、旧 provenance、完了済み測定値

ただし `EXTENDED_SWEEP_US` が search config に入るため、[backoff_extended_sweep.py:452-469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:452) から導かれる新 campaign ID は変わります。旧 1000 汚染系列へ resume してはいけません。

## 正例と負例

既存 runtime witness はこの検証に利用できます。[condition_meaning_gate.py:1382-1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:1382) が hole を評価 TU に埋め込み、[condition_meaning_gate.py:4220-4305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4220) が 2 文脈の binary64 bit を比較します。新しい gate は不要です。

**(A) の正方向**

- request: raw `BACKOFF_FIXED=3000`
- declaration: `MeaningCase(3000, bits(1000.0), bits(1000.0))`
- 期待: `declared-meaning-observed` / green
- これにより新 decoder、Python model、送信側 encoder の代表点を結ぶ。

**(A) の負方向**

- raw `1000` を静的 1000 と宣言すると、既存 [test_f718_1000_decodes_to_zero](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_condition_meaning_gate.py:403) と同じく expected 1000 / observed 0 で red。encoder bypass を捕捉する。
- 新 hole の最終項を旧 `%1000` へ戻した fixture に raw 3000 / expected 1000 を与えると observed 0 で必ず red。`-2000` を `-1999` に壊した場合も observed 1001 で red。この二つで過小・過大方向を分けて検査できる。

**(B) の正方向**

- raw `999` / expected `999.0` は既存 endpoint witness で通る。

**(B) の負方向**

- raw `1000` / expected `1000.0` は observed 0 で red。
- runtime witness が証明できるのは decoder の意味までで、driver の「受理上限 999」そのものは証明しない。上限は `EXTENDED_SWEEP_US[-1] == 999` と全静的 genome が `<=999` である既存 driver テストで固定する。追加機構は不要。

## 推奨と反対案を採る条件

(A) を推します。理由は次の三点です。

- 999 µs でも飽和していないという受領済み実測に対し、(B) は right-censoring を恒久化する。
- raw `V>=3000` を `V-2000` とするだけで、要求された `0..2999` の全意味を保てる。
- 変更は大きく見えるものの、複雑なのは数式ではなく凍結束縛の版分離であり、旧値を無効化せず処理できる。

反対案 (B) を採るべきなのは、研究上の問いを「静的 backoff は 999 µs まで」と明示的に狭め、999 で未飽和の right-censored 結果を最終結論として受け入れる場合です。または、新しい B-10 artifact 登録・probe・新 campaign identity の費用を負担しないという明示的な裁定がある場合です。

## 検証状態

ファイルは変更しておらず、worktree は clean です。pytest・build・実測は実行していません。

実施した静的確認は、必読資料全件の読了、指定 worktree 内の `git grep` による閉包確認、現行 hash の再確認、および提案する単一行置換後の formula/patch hash のストリーム再計算です。

## 総括

(A) の最小互換符号化は「静的 `µ>=1000` を raw `µ+2000`、raw `V>=3000` を `V-2000` へ復号」です。これなら stock inert、0..999 の定数、1000..1999 の symmetric-modulo、2000..2999 の binary をすべて維持できます。

代償として patch/formula/prereg/source identity は明示的に版を分ける必要がありますが、完了済み 135 cell、旧 28 点、旧 999 tail の測定値は無効化されません。旧成果物を新符号化へ遡及的に読み替えないことが実装上の最重要条件です。