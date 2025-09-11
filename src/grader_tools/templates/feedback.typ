#set page(
  paper: "us-letter",
  header: grid(
    columns: (1fr, 1fr),
    align: (left, right),
    {%if logo -%}
    image("{{logo}}", width: 50pt)
    {% endif %}
  ),
  numbering: "1",
  columns: 2,
  footer: context [
    {{ student.firstName }} {{ student.lastName }}
    #h(1fr)
    #counter(page).display(
      "1/1",
      both: true,
    )
  ]
)

#show raw: set text(font: "Libertinus Serif")
#set par(
  justify: true
)

#place(
  top,
  float: true,
  scope: "parent",
  clearance: 2em,
)[
  #align(text(17pt)[
    *Scoresheet for {{ student.firstName }} {{ student.lastName }}* #h(1fr) *{{final_score | round(2)}}/{{final_max_score}} pts*
  ])

  #par(justify: true)[

    == Evaluation Details
    - *Name:* {{exam.meta.semester}} {{exam.meta.course}}
    - *Date:* {{date}}
    - *Score:* {{ score| round(2) }}/{{ maxScore }} pts (class: average={{exam_stats.mean | round(2)}}, min={{exam_stats.min | round(2)}}, max={{exam_stats.max | round(2)}})

    {% if comment %}
    === Feedback
    {{ comment }}
    {% endif %}

    == Criterion Grid
    #text(size: 9pt)[
      #table(
        columns: (1fr, 3fr, 1fr, 1fr),
        inset: 10pt,
        align: (center, left, center, right),
        table.header(
          [*ID*], [*Description*], [*Score*], [*Ratio* (%)]
        ),
        {% for id_outcome, outcome in outcomes.items() %}{% for id_criterion, criterion in outcome.criteria.items() %}
        {% if criterion.maxScore > 0 %}[*{{ criterion.id }}*], [{{ criterion.text }}], [ {{ criterion.score }}/{{ criterion.maxScore }}], [{{ (criterion.score / criterion.maxScore * 100) | round(1) }}% ],{% endif %}{% endfor %} {% endfor %}
      )
    ]
  ]
]

#pagebreak()

== List of sections
{% for section in sections %}
=== Section {{section.name}}: {{ section.title }} #h(1fr) {{ section.score }}/{{ section.maxScore }} pt(s)
{% for question in section.questions %}
===== Question {{ question.name }}: #h(1fr) {{ question.score }}/{{ question.maxScore }} pt(s)
- *Criterion:* {{ question.criterion.id }}
- *Enoncé:* `{{ question.text }}`
- *Level:* {% if question.label %}{{ question.label }}{% else %}Not evaluated{% endif %}
{% if question.comment %}
- *Feedback:*
{{ question.comment }}
{% endif %}
{% endfor %}
{% endfor %}
