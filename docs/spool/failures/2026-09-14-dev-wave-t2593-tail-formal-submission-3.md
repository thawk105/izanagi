---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2593-tail-formal-submission
seq: 3
---

## supersede 追記

- F355 **supersede: 2026-09-14** — 2026-09-02 の再発が「縮退経路が完了扱いで抜けている疑い」と書いた点を本 wave の実測が狭めた。[T-2593] wave では `producer: /proc/<pid>/stat を読めないため pid-only へ縮退します` を 8 回すべての待ち手で観測したが、偽完了は 1 回も起きず、8 回とも `.done` が実在するまで正しく待って戻った。したがって縮退メッセージ自体は偽完了の徴候ではなく、両者は独立に扱う。
