---
name: scratch-space
description: >-
  Where throwaway work goes - temporary clones, builds and test output - so that
  two sessions on one machine never share, or delete, each other's directories.
---

# Scratch space

- **Create a fresh directory for throwaway work, once per task.** Put it under
  the temporary directory your harness names, or the system's when it names
  none, and start the name with what the task is:

  ```sh
  mktemp -d "/tmp/opencode/agent-kits-pr11-XXXXXX"
  ```

  ```powershell
  (New-Item -ItemType Directory (Join-Path ([IO.Path]::GetTempPath()) "agent-kits-pr11-$([guid]::NewGuid())")).FullName
  ```

- **Use the path it printed, literally, in every later call.** Do not compute it
  again: each call runs in a new process, so anything built from `$$`, the time
  or a counter names a different directory next time.
- **Never work in a fixed or guessed path** such as `/tmp/<repository>`. Another
  session may be using it, and deleting or re-cloning it destroys their work.
- **Delete only what you created, when the task ends.** Leave every other
  directory alone, however abandoned it looks.
- **Prefer `git worktree add <that directory> <branch>`** over a fresh clone when
  a local clone of the repository already exists.
