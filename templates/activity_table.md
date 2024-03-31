{% macro table(entries) -%}
<table>
<tbody>
{% for (dt, entry, repo) in entries %}
<tr>
<td>{{ dt }}</td>
<td>

{{ entry }}

</td>
<td>

{{ repo }}

</td>
</tr>
{% endfor %}
</tbody>
</table>
{%- endmacro %}

## recent activity

{{ table(entries[:5]) }}

<details>
<summary>show more...</summary>
{{ table(entries[5:]) }}
</details>