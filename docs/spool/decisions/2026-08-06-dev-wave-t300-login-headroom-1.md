---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t300-login-headroom
seq: 1
---

## {{D:login-headroom-admission}}. ログインノードの実行可否を空きメモリとキュー可用性で決める

**決定 (2026-08-06 ユーザー裁定、[T-300])。**

1. **性能測定** (ベンチ・calibration・noise floor・floor / oracle の本走) は、余裕の有無に
   かかわらず計算ノードで行う。この面は不変である (絶対規律 1)。
2. **それ以外** (テスト・ビルド・provenance 履歴監査) は、ログインノードの空きメモリが足りれば
   **ログインノードで実行する**。足りなければ計算ノードへ dispatch する。
   これは 2026-07-30 裁定「重い処理はログインノードで走らせない」(D103 決定 2 / 決定 4、
   D105 決定 2) を**非計測面について supersede** する。計測面の射程は変えない。
3. **判定量はユーザーが指した「合計メモリ使用量」** = user slice の raw `memory.current`。
   per-user 上限 16 GiB に対し**天井 14 GiB**。**reclaim 可能な file cache を差し引く案は採らない** —
   ユーザーが指した量の再定義になるため。差し引けば実効許容量はほぼ倍になるが別裁定が要る。
4. **キューが使えない (`qstat -Q` で対象 queue が `DIS` または `INA`) なら投げない。**
   投げても実行されないためである。その場合はログインノードで実行し、余裕も無ければ
   「いまは実行できない」として止める。**性能測定なら「いまは測定できない」と判断する** —
   ログインノードで測ることは選択肢にしない。
5. **観測不能は「キュー可用」へ倒す。** `qstat` が読めない・解釈できないことを理由に
   ログインノードへ重い処理を流し込まない (現行挙動と一致し、受理集合は単調)。
6. **1 コマンドへ渡す予算** = `min(4 GiB, 天井 − 現在使用量 − 生存中の予約 − 予備 2 GiB)`。
   予備 2 GiB と上限 4 GiB は**暫定値であり実測根拠が無い**。
   **並行セッション数に予備枠を比例させる案は棄却した** (2026-08-06 ユーザー是正) —
   各セッションの使用量は既に `memory.current` に含まれており二重計上になる。
   10 セッション運用では予備だけで天井を食い潰す。
7. **見積もりは前回の観測ピークを使う。** 操作ごとに記録し、前回 cap に当たった操作は
   次回 local を試さず即 dispatch する。記録の置き場は予約台帳と同じ repo 外 tmpfs とし、
   **repo へ実行状態を書かない** (git 差分衝突を作らないため)。
8. **実行は上限付き cgroup scope で囲う。** 見積もりが外れても被害はその scope に閉じる。
   `MemoryOOMGroup` は systemd 249 では transient property として受理されないので、
   child が自分の `memory.oom.group` へ 1 を書いて読み返す (2026-08-06 実測)。
9. **cap 到達後の自動 fallback は、local 試行の前後で tree と submodule の指紋が
   変わっていないときだけ**行う。「tree が clean か」で判定してはならない —
   開発中の tree はほぼ常に dirty であり、それでは通常の開発が止まる (実測)。
10. **実行場所を確定させる `--force-dispatch` を設ける。** 判定を迂回して従来の dispatch 経路を
    通る。変異 harness の dispatch mode がこれを要求する (本 wave が壊した契約の回復) ほか、
    正確な性能比較のように場所を固定したい場面でも使う。

**射程外 (実装しない)。** ログインノードでの build 解禁 (計測 build cache への流入を断つ
namespace 分離が前提)、AI の子プロセスを予約 API へ接続すること ([T-300] の本丸)、
CPU / I/O の市民性、4 値 outcome の台帳 schema 化。

## {{D:no-arbitrary-argv-bounded-launcher}}. 上限付き実行は entry point の内側に閉じ、汎用 launcher を作らない

段 2 のプランは `tools/pegasus/local_run.py` として**任意 argv を受け取る bounded launcher**を
提案したが、段 3 の敵対レンズ 2 本が独立に blocker を積み上げたため**設計ごと取り下げた**。

取り下げの根拠 (いずれも具体的な綴り・コードパス付きで示された):

- 内側の `tools/pegasus/` 実行体が `dispatch-required` でも、名前が性能語に一致しなければ通る
  (registry class の trampoline)
- `BASH_ENV` / `LD_PRELOAD` / `sitecustomize` / script 内部の `subprocess` は argv 検査で見えない
- `systemctl --user` / D-Bus の `StartTransientUnit` で sibling cgroup へ逃げられる
- `local-ok` は「certified peak 512 MiB 未満の実測済み」または grandfather 4 本の意味であり、
  最大 4 GiB を運ぶ launcher をそこへ置くと class の意味が壊れる (D175 / D188 の射程)

**代わりに、上限付き実行は `tools/run_tests.py` / `tools/check_ai_provenance.py` の内側に閉じる。**
hook は subprocess の内側を見ないので、raw `systemd-run` を許可する必要がない。むしろ
**LOGIN / SUSPECT では raw `systemd-run` を拒否する**。`_WRAPPERS` へは追加しない —
wrapper 化すると head の解釈が変わり、**これまで拒否されていた綴りが許可側へ移る回帰**が生じる
(段 3 レンズが `systemd-run -- python3 writer.py <build-variants 配下>` を具体例として示した)。

**帰結として、ユーザー依頼のうち「コンパイル」はまだログインノードへ移っていない。**
`cmake` / `make` / `g++-12` はログインノードに実在するので技術的には可能だが、
計測 build cache への流入を構造的に断つ設計が前提であり、それ自体が独立した作業になる。
