#import table: cell, header

#show: doc => {
  set page(
    flipped: true,
    footer: {
      line(length: 100%, stroke: 0.5pt )
      context[
        * {{ year }} *,
        * {{ semester }} *,
        {{ course }},
        #emph[{{ teachers }}]
        #h(1fr)
        #counter(page).display("1/1", both: true)
      ]
    }
  )

  grid(
    columns: (1fr, 1fr),
    [
      #text(12pt, [{{ year }} {{ semester }} - {{ course }}], weight: 400)
      #v(0em)
      #text(17pt, [Grilles Critériées], weight: 600)
      #v(0em)
      #text(11pt, "{{ teachers }}", weight: 400, style: "italic")
    ],
    [
      {% if logo -%}
      #align(right)[
        #image("{{ logo }}", width: 25%)
      ]
      {% endif -%}
    ]
  )

  set par(justify: true)
  set text(size: 11pt)

  line(length: 100%, stroke: 0.5pt)
  v(1em)
  doc
}

#show table.cell.where(y: 0): set text(
  fill: white,
  weight: "bold",
)

= Grilles critériées

{% for outcome in outcomes %}
== {{ outcome.name }}

*Description* {{ outcome.text }}

=== Liste des critères

#block[
#set text(size: 8pt)

#table(
  columns: (2fr,1fr,1fr,1fr,1fr,1fr,1fr),
  align: (x, y) => if x == 0 { left } else { center },
  stroke: (x, y) => (
    left: if y == 0 and x > 0 { white } else { black },
    rest: black,
  ),
  fill: (_, y) => if y == 0 { black },
  table.header(
    [Critère],
    [Rédhibitoire],
    [Très insuffisant],
    [Insuffisant],
    [Passable],
    [Bien],
    [Au delà des attentes]
  ),
  {% set LEVELS_ORDER = ["Rédhibitoire", "Très insuffisant", "Insuffisant", "Passable", "Bien", "Au delà des attentes"] -%}
  {% for criterion in outcome.criteria -%}
    [*{{ criterion.name }}* : {{ criterion.text }}],
    {% for level_label in LEVELS_ORDER -%}
      {% set lvl = (criterion.levels | selectattr("label", "equalto", level_label) | list | first) -%}
      {% if lvl -%}
        cell(
          fill: white,
          [{{ lvl.text }}]
        ){% if not loop.last %},{% endif %}
      {% else -%}
        cell(fill: rgb(200, 200, 200), []) {% if not loop.last %},{% endif %}
      {% endif -%}
    {% endfor -%}
    {% if not loop.last %},{% endif %}
  {% endfor -%}
)
]

#pagebreak()

{% endfor %}
