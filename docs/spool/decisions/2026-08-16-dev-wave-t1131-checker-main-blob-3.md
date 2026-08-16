---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1131-checker-main-blob
seq: 3
---

## {{D:red-checker-main-blob-authority}}. 非帰属判定の実行体を tested main の blob へ束縛し、待ち手は tip 束縛のまま残す

**決定:** 受入の赤を帰属 / 非帰属へ分類する実行体 (`tools/check_acceptance_reds.py`) の権威を
tested main の blob へ束縛する。具体的には次の 3 層を同時に満たす。

1. 待ち手は `tested_main` の blob sha、`tested_tip` の blob sha、**実際に実行した bytes** の
   blob sha の三方一致を要求し、いずれかが不成立・測定不能なら判定不能へ倒す。
   判定不能は受領証を発行せず、非帰属の根拠にしない。
2. 実行する bytes は `tested_main` の blob content から取り、隔離した Python の stdin へ渡す。
   pathname を実行に使わないため、測定と実行の間に file を差し替える窓が無い。
   判定コードは編集せず、既存の `repo_root` / `command_runner` の keyword seam を使う。
   本 gate が使う git と、判定コードが内部で使う git の**両方**を絶対 executable・固定 config・
   固定 env (履歴の別名解決の無効化を含む) へ揃える。
3. land は受領証を信用せず、`non-attributable-only` のときに `tested_main` と `tested_tip` の
   checker blob を自ら引いて比較し、不一致なら受入を拒否する。

**commit の一致は要求しない。** `tested_main != tested_tip` は正常であり、blob が同一なら受理する。
受領証 schema は変更しない。

**待ち手 (`tools/dev_wave_wait.py`) 自身は tested tip 束縛のまま残す。** したがって本決定が閉じるのは
「判定コード単独差し替え」の集合だけであり、待ち手を書き換えて偽の受領証を直接作る経路は開いている。
**この非対称は意図的である。**

**理由:**
- 判定される側が判定者を差し替えられる状態では、どのような批准機構を設計しても、
  その機構を経由せずに同じ救済ができる。順序として判定者の固定が先である。
- 待ち手を同じく main 束縛しない理由は D403 が既に述べている — 待ち手は wave 版を実行するため、
  同 file を編集する wave では main 版と恒久的に不一致になり、その wave の受入を永久に拒否する。
  判定コードは改修頻度が低くこの代償を受容できるが、待ち手は wave 運用の中核で頻繁に改修されるため
  代償が重い。非対称はこの費用差に基づく。
- 受領証へ実行 bytes の field を足さないのは D403 の却下理由をそのまま継承する
  (gate 通過が含意するため冗長で、schema 昇格自体が同型の事故源になる)。
- 判定不能を判定コードの rc=2 として表現しないのは、本 gate が判定コードを**起動する前**に
  発火するためである。rc=2 を偽造すると「判定コードが走って判定できなかった」と誤って記録する。
  停止の効果 (受領証を発行せず非帰属の根拠にしない) は同一である。

**却下した選択肢:**
- **land を編集しない (待ち手側の束縛だけで足りるとする)** — 待ち手が三方一致を強制すれば
  land の既存 tip 照合は main 照合と論理的に等価になる、という推論は成立する。しかし
  land が受領証を信用したままでは、待ち手を書き換えた wave に対して層が 1 枚しか無い。
  land の照合欠落は本件の問題記述そのものが名指ししている構成要素であり、scope 内である。
- **判定コードへ `--repo-root` 等の CLI flag を新設して blob を一時 path から起動する** —
  判定コードを編集すると、その wave 自身の tip 版が main 版と不一致になり、自分で自分を
  判定不能にする。修正が効くのが次 wave からになる代償と両立しない。
- **working tree の file を読んで blob と照合し、その file を実行する** — 測定と実行の間に
  差し替えの窓が残る。加えて改行変換や smudge filter が効く環境では、git 上 clean でも
  working tree の bytes が blob と異なり、正当な走行を過剰に拒否する。
- **判定コード内の git 呼び出しを判定コード自身で固定する** — 上と同じ理由で判定コードを
  編集できない。呼び出し側から `command_runner` を注入すれば、判定コードを変えずに
  内側の git だけを固定できる。
