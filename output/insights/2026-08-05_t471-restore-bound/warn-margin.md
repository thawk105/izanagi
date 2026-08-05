# [T-471] warn margin (`elapstim_req` の warn 値) の設計メモ — 候補、未 certify (2026-08-05)

- `authority: none` / `default_effect: no-state-change`
- **本文書は設計メモであり、値を certify しない。** `DW-G04` に従い、発火条件を満たす
  既存 artifact path も計測 ID も揃っていない項があるため、実装せず設計に留める。
- [T-360] は着手前 (D131 前提 6 点 + D105 supersede を伴う次 wave のユーザー裁定待ち) である。

## 1. 予算の分解

`elapstim_req="<max>,<warn>"` の warn 値は「残り時間」ではなく **warning を要求する elapsed time**
であるため、設計は「必要な残り時間 `W_remaining`」を決めてから `warn = max − W_remaining` へ変換する。

必要な残り時間は次の和である。名前は凍結 `R_restore_bound` と区別する (D75)。

```text
C_repo_known_safe = H_stop_actual + R + H_head
C_process_exit    = C_repo_known_safe + H_exit
W_remaining       = C_process_exit + S_cleanup + D_delivery
warn              = max_walltime − W_remaining
```

| 項 | 実体 | 現状 |
|---|---|---|
| `H_stop_actual` | `_stop_process` の TERM 待ち 5 s + KILL 待ち 5 s (`mutation_harness.py:1098-1113`) | **上限 10 s (構成上)。超過分 `H_stop_overrun` は未計測** |
| `R` | `_restore_targets` の所要時間 | **実測 (診断値): 観測 max 71.79 ms、p99 ≤ 61.78 ms** ([T-471] `RESULT.md`) |
| `H_head` | 復元直後の `_assert_head` = git subprocess (`:1330-1332`, `:605-608`) | **未計測。Lustre 上の git 呼出しであり R より大きくなりうる** |
| `H_exit` | handler 復旧・例外 unwind・lock close・stderr write (`:2084-2101`) | 未計測。通常は小さい |
| `S_cleanup` | 上記の未計測項と裾を吸収する設計余裕 | 設計値 |
| `D_delivery` | PBS が warning を要求した時刻から Python parent が受信するまでの遅延 | **未計測 (`UNKNOWN`)** |

## 2. 実測が変えたこと

**R は予算の支配項ではない。** 観測 max 71.79 ms は `H_stop_actual` の上限 10 s に対して 3 桁小さく、
`C_repo_known_safe` はほぼ `H_stop_actual + H_head` で決まる。

したがって warn margin の設計で精度を上げるべきなのは R ではなく:

1. `H_head` — 唯一の未計測かつ R より大きくなりうる項。
2. `D_delivery` — これが `UNKNOWN` である限り、どんな warn 値も certify できない。

R を再測定しても warn 値の精度はほぼ改善しない。

## 3. 候補値 (certify しない)

未計測項を保守側に置いた**候補**として:

```text
H_stop_actual ≤ 10 s            (構成上の 2 段 timeout の和)
R             ≤ 0.1 s           (観測 max 71.79 ms に丸め上げ。上限ではない)
H_head        ≤ 5 s             (未計測。git subprocess の保守的な置き値)
H_exit        ≤ 1 s             (未計測)
S_cleanup     = max(0.5 × 上記の和, 10 s) = 10 s
D_delivery    = UNKNOWN
```

`D_delivery` を除いた小計は 16.1 s、`S_cleanup` を加えて **26.1 s**。
現行 mitigation 構成の nominal grace 60 s (`elapstim_req="00:03:00,00:02:00"`) は
この小計を上回るが、**`D_delivery` が `UNKNOWN` である以上「60 s で足りる」と certify できない。**

## 4. 記録の訂正

[T-399] `RESULT.md` §T-360 への含意と、それを引いた worklog (191) の
「warn margin は構成で拡大可能であり**設計上の障害は残っていない**」という記述は、
本 wave の実測後は**射程が広すぎる**。正しくは:

- 拡大は構成上可能 (`elapstim_req` の warn 値は自由) — この部分は成立する。
- しかし `D_delivery` 未計測、`H_head` 未計測のため、**具体的な warn 値を certify する根拠は無い**。
  「障害が残っていない」ではなく「値を決める入力が 2 つ欠けている」が正しい。

[T-399] の RESULT は凍結文書のため書き換えない。本 wave の worklog で射程を訂正する。

## 5. 次に測るべきもの (裁定へ返す)

1. **`D_delivery`** — PBS の warning 要求時刻と Python parent の受信 event を同一 attempt へ束縛して
   反復観測する。これ無しに warn 値は certify できない。
2. **`H_head`** — `_assert_head` の git subprocess を Lustre 上で反復計測する。R より安く、
   予算への寄与は大きい。
3. **条件 3 を閉じる attempt** — production 相当の cleanup 列 (10 s + R 相当の仕事) を
   grace 内で完走させる probe leg。**これが本丸であり、R の精密化ではない** (`RESULT.md` §3)。
