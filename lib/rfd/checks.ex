# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT

defmodule RFD.Checks do
  @moduledoc """
  Guards for checks that would otherwise report a pass while measuring nothing.

  Each exists because a check written without it did exactly that; the incident
  is on the function. `ESCAPES.exs` holds the record and
  `test/escapes_test.exs` replays it.

  Every escape had one shape: a check that could not distinguish its outcomes.
  Zero hits from a file that does not exist reads the same as zero hits from a
  file that does. An empty token compares unequal to the previous one exactly
  as a fresh one would.
  """

  @doc """
  Run a command, returning `{output, exit_code}` from the command itself.

  Never inspect a command through a pipe: in zsh `$PIPESTATUS` is
  `$pipestatus`, and `cmd | tail` carries tail's status. Incidents: a clean
  build reported as a failure; a conflicted cherry-pick reported as clean.
  """
  def run_checked(cmd, args, opts \\ []) do
    {out, code} = System.cmd(cmd, args, [stderr_to_stdout: true] ++ opts)
    {out, code}
  end

  @doc "An empty value is a failure, never a result. Incident: a watcher read zero checks as ALL SETTLED."
  def require_nonempty(label, value)
  def require_nonempty(label, nil), do: {:error, "#{label}: nil is not a result"}

  def require_nonempty(label, value) when is_binary(value) do
    if String.trim(value) == "",
      do: {:error, "#{label}: empty value, which is not a result"},
      else: {:ok, value}
  end

  @doc """
  Absence proves nothing about a file never opened.

  Incident: grepping `egit.erl` for `merge_base` returned zero hits and was
  read as "absent"; the module is `git.erl`.
  """
  def require_file(label, path) do
    if File.exists?(path),
      do: {:ok, path},
      else: {:error, "#{label}: #{path} does not exist, so its contents conclude nothing"}
  end

  @doc """
  Search every member of a corpus, and refuse to conclude from a partial one.

  Incident: `grep 2235 SERIALS.exs` returned nothing and was used to justify
  deviating from the retraction rule; the serial is in `SERIALS-vsekai-fabric.exs`.
  """
  def require_corpus(label, _pattern, []),
    do: {:error, "#{label}: empty corpus, nothing was searched"}

  def require_corpus(label, pattern, paths) when is_list(paths) do
    case Enum.reject(paths, &File.exists?/1) do
      [] ->
        hits = Enum.filter(paths, fn p -> File.read!(p) =~ pattern end)
        {:ok, %{searched: length(paths), hits: hits}}

      missing ->
        {:error, "#{label}: corpus members absent: #{Enum.join(missing, ", ")}"}
    end
  end

  @doc """
  A control whose threshold never fired tested nothing.

  Incident: an `ar` response-file control used 400 objects, producing a 30 KB
  command line against a 32768-byte threshold, so the shim loaded, printed its
  banner, and never engaged.
  """
  def require_engaged(label, evidence) do
    case require_nonempty(label, evidence) do
      {:ok, e} ->
        {:ok, e}

      {:error, _} ->
        {:error, "#{label}: no evidence the mechanism engaged; the control proves nothing"}
    end
  end

  @doc "The negative control CLAUDE.md rule 2 requires: known-broken input must be rejected."
  def expect_fail(label, fun) when is_function(fun, 0) do
    case fun.() do
      {_, 0} -> {:error, "#{label}: broken input was accepted; the gate certifies the defect"}
      {_, code} -> {:ok, code}
    end
  end

  @doc "An unmet precondition is a failure, not a skip (rule 3). Incident: a parser control ran outside a git repository."
  def require_precondition(label, fun) when is_function(fun, 0) do
    case fun.() do
      {_, 0} -> {:ok, :met}
      {out, code} -> {:error, "#{label}: precondition unmet (exit #{code}): #{String.trim(out)}"}
    end
  end

  @doc """
  Text that passed through a shell may not be the text written.

  Incident: backticks inside a double-quoted `git commit -m` were evaluated as
  command substitution, a sentence vanished, and the commit reported success.
  """
  def require_literal(label, needle, haystack) when is_binary(haystack) do
    if String.contains?(haystack, needle),
      do: {:ok, needle},
      else: {:error, "#{label}: #{inspect(needle)} is absent; the shell rewrote it"}
  end
end
