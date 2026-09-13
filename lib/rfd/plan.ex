# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT

defmodule RFD.Plan do
  @moduledoc """
  An apparatus plan as Elixir data, and the `.usda` layer rendered from it.

  Modelled on `RFD.Register`. Renders the subset the apparatus uses: layer metadata with
  sublayers and `customLayerData`, `def` / `def Scope` / `over` prims nested arbitrarily,
  typed attributes, and relationships to prim paths.
  """

  @enforce_keys [:name]
  defstruct name: nil, meta: [], sublayers: [], data: [], prims: []

  @meta_keys ~w(metersPerUnit upAxis defaultPrim doc)a

  defmacro __using__(_) do
    quote do
      import RFD.Plan, only: [plan: 2]
    end
  end

  defmacro plan(name, do: block) do
    quote do
      import RFD.Plan.Fields
      @plan_doc RFD.Plan.build(unquote(name), unquote(collect(block)))
      import RFD.Plan.Fields, only: []
      def __plan__, do: @plan_doc
    end
  end

  @doc false
  # A do-block becomes a list before it is evaluated, which is what lets prims nest.
  def collect({:__block__, _, stmts}), do: {:__block__, [], []} |> with_list(stmts)
  def collect(nil), do: []
  def collect(stmt), do: with_list(nil, [stmt])

  defp with_list(_, stmts), do: quote(do: List.flatten([unquote_splicing(stmts)]))

  @doc false
  def build(name, entries) do
    %__MODULE__{
      name: name,
      meta: Keyword.take(flat_opts(entries, :meta), @meta_keys),
      sublayers: flat_list(entries, :sublayers),
      data: for({:data, k, t, v} <- entries, do: {k, t, v}),
      prims: for(%{__prim__: true} = p <- entries, do: p)
    }
    |> validate!()
  end

  defp flat_opts(entries, tag), do: for({^tag, kw} <- entries, kw <- kw, do: kw)
  defp flat_list(entries, tag), do: for({^tag, xs} <- entries, x <- xs, do: x)

  # --- the DSL surface ------------------------------------------------------------------

  defmodule Fields do
    @moduledoc false
    alias RFD.Plan

    def meta(kw), do: {:meta, kw}
    def sublayers(paths), do: {:sublayers, paths}

    for t <- ~w(string token int bool float float3)a do
      def unquote(t)(key, value), do: {:data, key, unquote(to_string(t)), value}

      def unquote(:"#{t}_list")(key, values),
        do: {:data, key, unquote(to_string(t) <> "[]"), values}
    end

    def attr(key, type, value), do: {:attr, key, type, value, []}
    def attr(key, type, value, opts), do: {:attr, key, type, value, opts}
    def rel(name, target) when is_binary(target), do: {:rel, name, [target]}
    def rel(name, targets) when is_list(targets), do: {:rel, name, targets}

    def doc(text), do: {:doc, text}
    def prim(name, body), do: Plan.build_prim(:def, nil, name, body)
    def scope(name, body), do: Plan.build_prim(:def, "Scope", name, body)
    def over(name, body), do: Plan.build_prim(:over, nil, name, body)
  end

  @doc false
  def build_prim(kind, schema, name, body) do
    body = body |> unblock() |> List.wrap() |> List.flatten()

    %{
      __prim__: true,
      kind: kind,
      schema: schema,
      name: name,
      doc:
        Enum.find_value(body, fn
          {:doc, d} -> d
          _ -> nil
        end),
      attrs: for({:attr, k, t, v, o} <- body, do: {k, t, v, o}),
      rels: for({:rel, n, ts} <- body, do: {n, ts}),
      children: for(%{__prim__: true} = c <- body, do: c)
    }
  end

  defp unblock([{:do, inner}]), do: inner
  defp unblock(other), do: other

  # --- validation -----------------------------------------------------------------------

  @doc "Every rule a plan has to meet, as the list of reasons it does not."
  def problems(%__MODULE__{} = p) do
    []
    |> check(is_binary(p.name) and p.name =~ ~r/^[A-Za-z][A-Za-z0-9_]*$/, "prim-safe name")
    |> check(p.prims != [], "a plan with no prim renders an empty layer")
    |> check(
      p.meta[:defaultPrim] in [nil | Enum.map(p.prims, & &1.name)],
      "defaultPrim #{inspect(p.meta[:defaultPrim])} names no prim in this layer"
    )
    |> Kernel.++(Enum.flat_map(p.prims, &prim_problems/1))
    |> Enum.reverse()
  end

  defp prim_problems(prim) do
    here =
      []
      |> check(
        is_binary(prim.name) and prim.name =~ ~r/^[A-Za-z][A-Za-z0-9_]*$/,
        "prim #{inspect(prim.name)} is not a prim-safe name"
      )
      |> check(
        Enum.all?(prim.rels, fn {_, ts} -> Enum.all?(ts, &String.starts_with?(&1, "/")) end),
        "prim #{prim.name}: a relationship target is an absolute prim path"
      )

    here ++ Enum.flat_map(prim.children, &prim_problems/1)
  end

  defp check(acc, true, _), do: acc
  defp check(acc, false, msg), do: [msg | acc]

  def validate!(%__MODULE__{} = p) do
    case problems(p) do
      [] ->
        p

      ps ->
        raise ArgumentError, "plan #{p.name} is outside its shape:\n  " <> Enum.join(ps, "\n  ")
    end
  end

  # --- rendering ------------------------------------------------------------------------

  @doc "The plan as a `.usda` layer."
  def usda(%__MODULE__{} = p) do
    meta =
      for({k, v} <- p.meta, do: "    #{k} = #{lit(v)}") ++
        sublayer_lines(p.sublayers) ++ data_lines(p.data)

    header = ["#usda 1.0", "("] ++ meta ++ [")", ""]
    body = p.prims |> Enum.map(&prim_lines(&1, 0)) |> Enum.intersperse([""]) |> List.flatten()
    Enum.join(header ++ body, "\n") <> "\n"
  end

  defp sublayer_lines([]), do: []

  defp sublayer_lines(paths) do
    last = length(paths) - 1

    rows =
      paths
      |> Enum.with_index()
      |> Enum.map(fn {p, i} -> "        @#{p}@" <> if(i == last, do: "", else: ",") end)

    ["    subLayers = ["] ++ rows ++ ["    ]"]
  end

  defp data_lines([]), do: []

  defp data_lines(data) do
    ["    customLayerData = {"] ++
      Enum.flat_map(data, fn {k, t, v} -> value_lines("        ", "#{t} #{k}", t, v) end) ++
      ["    }"]
  end

  defp prim_lines(prim, depth) do
    pad = String.duplicate("    ", depth)
    schema = if prim.schema, do: " #{prim.schema}", else: ""

    head =
      case prim[:doc] do
        nil ->
          ["#{pad}#{prim.kind}#{schema} #{q(prim.name)}"]

        d ->
          [
            "#{pad}#{prim.kind}#{schema} #{q(prim.name)} (",
            "#{pad}    doc = #{lit(d)}",
            "#{pad})"
          ]
      end

    attrs =
      Enum.flat_map(prim.attrs, fn {k, t, v, o} ->
        quals = [o[:custom] != false && "custom", o[:uniform] && "uniform"]
        decl = Enum.join(Enum.reject(quals, &(&1 in [nil, false])) ++ ["#{t} #{k}"], " ")
        value_lines(pad <> "    ", decl, t, v)
      end)

    rels = Enum.flat_map(prim.rels, &rel_lines(&1, pad <> "    "))

    kids =
      prim.children
      |> Enum.map(&prim_lines(&1, depth + 1))
      |> Enum.intersperse([""])
      |> List.flatten()

    sep = if attrs != [] and (rels != [] or kids != []), do: [""], else: []
    head ++ ["#{pad}{"] ++ attrs ++ sep ++ rels ++ kids ++ ["#{pad}}"]
  end

  defp rel_lines({name, [one]}, pad), do: ["#{pad}rel #{name} = <#{one}>"]

  defp rel_lines({name, many}, pad) do
    ["#{pad}rel #{name} = ["] ++ Enum.map(many, &"#{pad}    <#{&1}>,") ++ ["#{pad}]"]
  end

  defp value_lines(pad, decl, type, value) do
    cond do
      not String.ends_with?(type, "[]") -> ["#{pad}#{decl} = #{lit(value)}"]
      value in [nil, []] -> ["#{pad}#{decl} = []"]
      true -> ["#{pad}#{decl} = ["] ++ items(pad, List.wrap(value)) ++ ["#{pad}]"]
    end
  end

  defp items(pad, vs), do: Enum.map(vs, &"#{pad}    #{lit(&1)},")

  defp lit(true), do: "1"
  defp lit(false), do: "0"
  defp lit(v) when is_integer(v) or is_float(v), do: to_string(v)
  # A newline cannot survive a single-quoted USD string, so a multi-line value takes the
  # triple-quoted form and its lines are emitted raw: indenting them would change the value.
  defp lit(v) when is_binary(v) do
    if String.contains?(v, "\n"), do: block(v), else: q(v)
  end

  defp lit(v) when is_list(v), do: "(" <> Enum.map_join(v, ", ", &lit/1) <> ")"

  defp q(s), do: "\"" <> String.replace(s, ~r/["\\]/, fn c -> "\\" <> c end) <> "\""

  defp block(s) do
    ~s(""") <> String.replace(s, "\\", "\\\\") <> ~s(""")
  end
end
