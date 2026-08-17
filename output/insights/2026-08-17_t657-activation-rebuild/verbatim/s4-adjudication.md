# 段 4 裁定 — 実装しない (所有の衝突)

wave: `dev-wave-t657-activation-rebuild` / 2026-08-17 / 親

## 裁定

**実装しない。** 状態機械は `4 → 7 → 8 → 9` を通る。段 5・6 は飛ばす。

理由は技術的不能ではなく **所有の衝突** である。本 wave が実装しようとした面は、
別 wave `dev-wave-t1255-floor-freeze` が**同時刻に稼働して所有している**。

- 実測 (2026-08-17 09:22): `worktree-dev-wave-t1255-floor-freeze` は locked worktree として実在し、
  `pgrep` で段 3 の敵対子 2 本 (sol / luna) が走行中であった。
- 実測 (2026-08-17 12:26): 同 worktree は `9dcae82f` へ前進し、なお稼働中。
- その wave の scope は「versioned 床値 protocol の実発行 + live consumer (shell driver /
  `s8b_holdout_admission._authority` / `certified_writer_admission`) の配線」であり、
  本 wave の S2 と、S2 の前提である配線そのものである。
- 所有 allocation も独立に裏付けられた — consumer 配線 = [T-419] (3) / [T-1214]、
  実発行 = [T-1255] (`docs/spool/FOLDED.md:1361`, `:1403`、
  `docs/archive/worklog-phase3-0817-611.md:169`, `:565`)。

本 wave が先取りすると、固定 legacy path と versioned resolver の二重 authority が生じ、
resolver は count=0 または count=2 で fail-closed する。land も provenance 所有不一致で止まる。

## 所見の real / refuted

段 2 プラン 1 本、段 3 敵対 2 本 (sol=レンズ A、luna=レンズ B) の所見を親が裁定した。

| # | 出所 | 判定 | 内容 | 親の処置 |
|---|---|---|---|---|
| 1 | A-2 | **refuted** | 親 brief の「create-only なので取り消せない」は誤り。`os.link()` は同一 path 上書きを防ぐだけで unlink は禁じていない。commit 前なら復旧可能 | brief の不変条件から撤回。次 wave へ「非 0 なら exact path を除去し index 再検査、commit しない」を申し送る |
| 2 | A-9 / B-6 | **refuted** | 親 brief の「追加のみだから履歴不変条件と衝突しない」は言い過ぎ。versioned artifact は `FROZEN_MANIFEST` の対象外であり、履歴不変検査が効くのは ratified closure に入ったときだけ。「衝突しない」ではなく「まだ検査対象ですらない」が正確 | brief の主張を訂正。誤った provenance 主張を記録に残さない |
| 3 | B-4 | **refuted** | 親の対ユーザー説明「旧 A/B/C の 3 択は全て失効した」は不正確。D444 の supersede は Q2 の束縛張り替えに限定され Q3 は残る。B は依然不許可、A は未失効、C は自動承認ではない | 本記録と対ユーザー報告で訂正済み |
| 4 | B-8 | **refuted** | 親の「D471 は S1 (activation record) も直接禁止する」は誤読。D471 の射程は床値 protocol の発行と resolver | S1 単独の禁止根拠は D471 ではなく #5 の構造的失敗である、と訂正 |
| 5 | A-4 / B-9 | **real** | S1 単独 land は構造的に失敗する。resolver は現行 contract 一致を exact 1 件要求するため g2 activation 後に g2 protocol が無いと count=0。さらに `campaign.lock` が contract hash と activation tuple を束縛するため、既存 g1 campaign は resume 拒否となり certified acceptance が `E1-stale` になる | S1 の単独実施を禁止として記録 |
| 6 | A-5 | **real** | 安全な最小単位は「配線 commit」+「S1/S2 atomic commit」の 2 段。record と head 定数の分離 commit は loader を壊す。配備には走行中 campaign の停止と全 process 再起動が要る | 次 wave への申し送りに記載 |
| 7 | A-7 | **real** | 単純な path 置換は admission を弱める。legacy anchor は HEAD の 100644 blob から読むが versioned namespace は working tree から読み、job の clean check は `output/` を全除外する。未 commit の canonical file が resolver authority になり得る | **最重要の申し送り。** 必要なのは path 置換ではなく、選ばれた record の HEAD exact blob 存在と bytes 一致を admission / driver / holdout の 3 境界で検査すること |
| 8 | A-8 | **real** | shell だけの変更では [T-419] (3) は閉じない。holdout authority が legacy HEAD blob と supplied g2 protocol を比較して拒否し、しかもその拒否は run directory / binary store / manifest 作成の**後** | 申し送り |
| 9 | A-8 | **real** | 配線のコード面検証は計算ノード実走なしで可能 (一時 Git repo と stub driver / subprocess)。ただし「運用確認済み」を名乗るには実機走が要る | 申し送り |
| 10 | B-1 | **real** | 派生 binding が fallout 一覧から漏れていた。`silo_ladder_rung1.py:274` は activation record の全 JSON を `runtime_modules` に含め、`:3562` が完全一致を要求する。test 側は動的 glob なので literal 置換は不要だが現行 evidence の再生成が要る | 申し送り |
| 11 | B-2 | **real** | [T-419] の実行成果物 (`t419_probe_causality.py:3395`) は常に現行 `lookup("pegasus")` を使うため、g1 pin を持つ既存 submission は g2 activation 後に `pin_verified=false` になる。歴史 lane への隔離条件が段 2 プランの成果物一覧に無い | 申し送り |
| 12 | B-3 | **refuted** | alias や旧 hash の一括置換は不可。`pegasus_floor_scoping.py:25` の `lookup` は関数 alias で固定 pin ではなく、`test_s1_direct_comparison.py:124` などの旧 pin は歴史成果物の pin | 一括置換を禁止として記録 |
| 13 | A-10 | **real** | 親の library 実測から「実装後も緑」は一般化できない。実測が捉えているのは「g2 calibration bytes が successor 候補として受理可能」までで、head load / resolver / execution receipt / result / report / ledger は捉えていない | brief (P4) の限界表明を維持し、実測の射程を本記録に明示 |
| 14 | B-7 | **real** | brief (P1) は正しい。worklog [T-1289] の「第 4 世代」は env contract の世代ではなく S8c の generation 条件。ただし T-1289 自体は `[T-1213]` として残存 | (P1) を確定。無関係項目として分離 |
| 15 | B-11 | **refuted** | D471 を解除する後続裁定は無い。最新は D479 で、床値 issuance blocker を変更していない | 発行の先行を禁止として維持 |
| 16 | B-12 | **real** | 旧 branch はコードを捨ててよいが、[T-660] の検出力実証 (変異 5/5) と E2E の historical / current 2 lane 分割は設計資産であり、ref 削除だけでは失われる | **本 wave で保全してから破棄する** (`preserved-t657-t660/`) |
| 17 | B-14 | **real** | fold / clean tree / provenance が land の構造的関門になる | 段 7・9 の手順に反映 |

## 本 wave が納めるもの

1. **旧 branch `worktree-dev-wave-t657-t660-g2-activation` の破棄** (2026-08-17 ユーザー指示)。
   worktree 残骸は無いことを実測済みのため ref 削除のみ。
2. **破棄前の証拠保全** — `preserved-t657-t660/` に旧 wave の裁定パッケージと変異台帳 2 件を退避。
   実行可能 script (`reissue_floor_protocol.sh`) は退避しない ([T-1255] が AI 実行可能な形へ
   設計変更中であり、旧 script は迂回経路として残すべきでないため)。
3. **本記録** — 段 1〜4 の逐語と、次 wave への申し送り。

## 次 wave ([T-1255] / [T-419] (3)) への申し送り

- 順序は「配線 → S1 (record + head 定数を同一 commit) → S2 (発行)」。S1 単独 land は禁止。
- 配線は path 置換ではなく **HEAD exact blob 束縛**を admission / driver / holdout の 3 境界へ置く。
- shell だけでは閉じない。holdout authority の legacy blob 比較が run 生成後に拒否する。
- `silo_ladder_rung1` の `runtime_modules` 派生 binding と、[T-419] submission の g1 pin 隔離を
  成果物一覧に含める。
- 配備時に走行中 campaign の停止と全 process 再起動が要る。
- 発行が非 0 で終わったら exact path を除去し index を再検査し、**commit しない**。
