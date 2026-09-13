# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT

defmodule RFD.Escapes do
  @moduledoc """
  Defects that got past a check, as data.

  `CLAUDE.md` already says a check that passes on known-broken input is
  decoration, and that a silent skip reads exactly like a pass. Both were
  violated eleven times in one session by someone who had read them, so the
  gap is not the rule: a rule is advice you must recall while writing a
  one-line grep.

  A gate is fragile when a defect gets past it and nothing changes. It is
  antifragile when the escape makes it stronger. `ESCAPES.exs` records each
  one and names the guard that now catches its class; `test/escapes_test.exs`
  fails if a recorded escape has no guard, so the suite can only grow.
  """

  @guards ~w(run_checked require_nonempty require_file require_corpus
             require_engaged expect_fail require_precondition require_literal)a

  defstruct name: nil, escapes: []

  defmacro __using__(_) do
    quote do
      import RFD.Escapes, only: [escapes: 2]
    end
  end

  defmacro escapes(name, do: block) do
    quote do
      Module.register_attribute(__MODULE__, :esc_rows, accumulate: true)
      import RFD.Escapes.Fields
      unquote(block)
      import RFD.Escapes.Fields, only: []

      @esc_doc RFD.Escapes.build(unquote(name), @esc_rows)
      def __escapes__, do: @esc_doc

      use RFD.Corpus, kind: :escapes, via: :__escapes__, entries: :escapes
    end
  end

  @doc false
  def build(name, rows) do
    %__MODULE__{name: name, escapes: Enum.reverse(rows)} |> validate!()
  end

  @doc "Guards a row may name. A row naming anything else is a typo, not a guard."
  def guards, do: @guards

  defp validate!(%__MODULE__{escapes: []}) do
    raise ArgumentError, "an escape register with no rows records nothing"
  end

  defp validate!(%__MODULE__{escapes: rows} = doc) do
    for %{guard: g, reported: r, actual: a, on: on} <- rows do
      unless g in @guards do
        raise ArgumentError, "unknown guard #{inspect(g)}; known: #{inspect(@guards)}"
      end

      # The point of a row is the gap between the two. A row where they match
      # records no escape.
      if r == a do
        raise ArgumentError,
              "escape on #{on}: reported and actual are identical, so nothing escaped"
      end

      for {field, text} <- [reported: r, actual: a, on: on] do
        unless is_binary(text) and String.trim(text) != "" do
          raise ArgumentError, "escape #{field} must be non-empty text"
        end
      end
    end

    doc
  end

  defmodule Fields do
    @moduledoc "Field macros available inside an `escapes/2` block."

    defmacro escape(on, opts) do
      quote do
        @esc_rows %{
          on: unquote(on),
          guard: Keyword.fetch!(unquote(opts), :guard),
          reported: Keyword.fetch!(unquote(opts), :reported),
          actual: Keyword.fetch!(unquote(opts), :actual)
        }
      end
    end
  end
end
